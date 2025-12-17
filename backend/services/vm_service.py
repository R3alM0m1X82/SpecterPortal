"""
Azure VM Service
Handles VM operations including Managed Identity security scanning
"""
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


class VMService:
    """Service for Azure Virtual Machine security operations"""
    
    def __init__(self, access_token):
        """
        Initialize VM service
        
        Args:
            access_token: Azure ARM API token
        """
        self.access_token = access_token
        self.base_url = 'https://management.azure.com'
        self.api_version = '2023-03-01'
        self.rbac_api_version = '2022-04-01'
    
    def _make_request(self, endpoint, method='GET', data=None):
        """
        Make HTTP request to Azure Management API
        
        Args:
            endpoint: API endpoint (relative to base_url)
            method: HTTP method
            data: Request body for POST/PUT
            
        Returns:
            dict: Response with 'success', 'data', 'error' keys
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json() if response.content else {}
                }
            else:
                error_detail = response.json() if response.content else {}
                error_msg = error_detail.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                return {
                    'success': False,
                    'error': f'Azure API returned {response.status_code}: {error_msg}',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def scan_vms_managed_identities(self, subscription_id):
        """
        Scan all VMs in subscription for overly permissive Managed Identities
        
        Args:
            subscription_id: Azure subscription ID
            
        Returns:
            dict with:
                - success: bool
                - vms: list of VM objects with identity analysis
                - summary: dict with counts by risk level
                - criticalVMs: list of VMs with critical risk
        """
        print(f"[VM SCAN] Starting security scan for subscription: {subscription_id}")
        
        # Step 1: Get all VMs in subscription
        vms_result = self._make_request(
            f"/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version={self.api_version}"
        )
        
        if not vms_result['success']:
            return {
                'success': False,
                'error': f"Failed to enumerate VMs: {vms_result.get('error')}"
            }
        
        vms_data = vms_result['data'].get('value', [])
        print(f"[VM SCAN] Found {len(vms_data)} VMs")
        
        if not vms_data:
            return {
                'success': True,
                'vms': [],
                'summary': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'none': 0},
                'criticalVMs': []
            }
        
        # Step 2: Analyze each VM's Managed Identity in parallel
        analyzed_vms = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_vm = {
                executor.submit(self._analyze_vm_identity, vm, subscription_id): vm 
                for vm in vms_data
            }
            
            for future in as_completed(future_to_vm):
                vm = future_to_vm[future]
                try:
                    analysis = future.result()
                    analyzed_vms.append(analysis)
                except Exception as e:
                    print(f"[VM SCAN] Error analyzing VM {vm.get('name')}: {e}")
                    analyzed_vms.append({
                        'name': vm.get('name'),
                        'id': vm.get('id'),
                        'error': str(e),
                        'riskScore': 'Unknown'
                    })
        
        # Step 3: Calculate summary statistics
        summary = {
            'critical': sum(1 for vm in analyzed_vms if vm.get('riskScore') == 'Critical'),
            'high': sum(1 for vm in analyzed_vms if vm.get('riskScore') == 'High'),
            'medium': sum(1 for vm in analyzed_vms if vm.get('riskScore') == 'Medium'),
            'low': sum(1 for vm in analyzed_vms if vm.get('riskScore') == 'Low'),
            'none': sum(1 for vm in analyzed_vms if vm.get('riskScore') == 'None')
        }
        
        # Step 4: Get critical VMs for priority alerting
        critical_vms = [vm for vm in analyzed_vms if vm.get('riskScore') in ['Critical', 'High']]
        
        print(f"[VM SCAN] Scan complete - Critical: {summary['critical']}, High: {summary['high']}, Medium: {summary['medium']}, Low: {summary['low']}, None: {summary['none']}")
        
        return {
            'success': True,
            'vms': analyzed_vms,
            'summary': summary,
            'criticalVMs': critical_vms
        }
    
    def _analyze_vm_identity(self, vm, subscription_id):
        """
        Analyze single VM's Managed Identity and permissions
        
        Args:
            vm: VM object from Azure API
            subscription_id: Subscription ID
            
        Returns:
            dict: VM analysis with identity details and risk score
        """
        vm_name = vm.get('name')
        vm_id = vm.get('id')
        location = vm.get('location')
        identity = vm.get('identity', {})
        
        print(f"[VM SCAN] Analyzing VM: {vm_name}")
        
        # Check if Managed Identity enabled
        if not identity or identity.get('type') == 'None':
            return {
                'name': vm_name,
                'id': vm_id,
                'location': location,
                'identity': {
                    'enabled': False,
                    'type': None,
                    'principalId': None
                },
                'roleAssignments': [],
                'riskScore': 'None',
                'recommendations': []
            }
        
        identity_type = identity.get('type', 'Unknown')
        principal_id = identity.get('principalId')
        
        # Get role assignments for the identity
        role_assignments = []
        if principal_id:
            assignments_result = self._make_request(
                f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.rbac_api_version}&$filter=principalId eq '{principal_id}'"
            )
            
            if assignments_result['success']:
                assignments = assignments_result['data'].get('value', [])
                
                # Get role definition details
                for assignment in assignments:
                    props = assignment.get('properties', {})
                    role_def_id = props.get('roleDefinitionId')
                    scope = props.get('scope', '')
                    
                    role_name = 'Unknown'
                    if role_def_id:
                        role_result = self._make_request(f"{role_def_id}?api-version={self.rbac_api_version}")
                        if role_result['success']:
                            role_name = role_result['data'].get('properties', {}).get('roleName', 'Unknown')
                    
                    role_assignments.append({
                        'roleName': role_name,
                        'scope': scope,
                        'scopeLevel': self._get_scope_level(scope)
                    })
        
        # Calculate risk score
        risk_score, recommendations = self._calculate_vm_risk_score(role_assignments, vm_name)
        
        return {
            'name': vm_name,
            'id': vm_id,
            'location': location,
            'identity': {
                'enabled': True,
                'type': identity_type,
                'principalId': principal_id
            },
            'roleAssignments': role_assignments,
            'riskScore': risk_score,
            'recommendations': recommendations
        }
    
    def _get_scope_level(self, scope):
        """Determine scope level from scope string"""
        if not scope:
            return 'Unknown'
        
        parts = scope.split('/')
        if len(parts) <= 3:
            return 'Subscription'
        elif 'resourceGroups' in parts and len(parts) <= 5:
            return 'Resource Group'
        else:
            return 'Resource'
    
    def _calculate_vm_risk_score(self, role_assignments, vm_name):
        """
        Calculate risk score for VM based on Managed Identity permissions
        
        Args:
            role_assignments: List of role assignments
            vm_name: VM name for logging
            
        Returns:
            tuple: (risk_score: str, recommendations: list)
        """
        if not role_assignments:
            return 'Low', ['VM has Managed Identity but no role assignments - minimal attack surface']
        
        # Critical roles that allow full control
        critical_roles = ['Owner', 'User Access Administrator', 'Contributor']
        
        # High-risk roles
        high_risk_roles = [
            'Virtual Machine Contributor',
            'Storage Account Key Operator Access',
            'Key Vault Administrator',
            'Network Contributor'
        ]
        
        recommendations = []
        has_critical = False
        has_high = False
        has_subscription_scope = False
        
        for assignment in role_assignments:
            role_name = assignment.get('roleName', '')
            scope_level = assignment.get('scopeLevel', '')
            
            # Check for critical roles
            if any(critical in role_name for critical in critical_roles):
                has_critical = True
                recommendations.append(f"🚨 CRITICAL: VM has '{role_name}' role - full privilege escalation possible")
                recommendations.append(f"🎯 RED TEAM: Compromise this VM → Instant subscription/tenant control")
            
            # Check for high-risk roles
            elif any(high in role_name for high in high_risk_roles):
                has_high = True
                recommendations.append(f"⚠️ HIGH: VM has '{role_name}' role - significant lateral movement potential")
            
            # Check scope
            if scope_level == 'Subscription':
                has_subscription_scope = True
                recommendations.append(f"📊 WIDE SCOPE: '{role_name}' applies to entire subscription")
        
        # Determine overall risk
        if has_critical:
            risk_score = 'Critical'
            recommendations.append('💥 ATTACK PATH: Compromise VM → az login --identity → Full control')
            recommendations.append('🔒 MITIGATION: Remove overly permissive roles, use least privilege')
        elif has_high and has_subscription_scope:
            risk_score = 'High'
            recommendations.append('⚡ ATTACK PATH: VM compromise → Lateral movement to other resources')
            recommendations.append('🔒 MITIGATION: Scope roles to specific resources only')
        elif has_high:
            risk_score = 'Medium'
            recommendations.append('⚠️ Moderate risk - consider reducing permissions')
        else:
            risk_score = 'Low'
            recommendations.append('✓ Permissions appear reasonable - monitor for changes')
        
        return risk_score, recommendations
