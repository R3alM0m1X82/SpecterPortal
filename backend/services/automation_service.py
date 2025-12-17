"""
Azure Automation Service
Handles Automation Account operations including Managed Identity analysis
"""
import requests
import json


class AutomationService:
    """Service for Azure Automation Account operations"""
    
    def __init__(self, access_token):
        """
        Initialize Automation service
        
        Args:
            access_token: Azure ARM API token
        """
        self.access_token = access_token
        self.base_url = 'https://management.azure.com'
        self.api_version = '2023-11-01'
    
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
                
                print(f"[AUTOMATION ERROR] {method} {url}")
                print(f"[AUTOMATION ERROR] Status: {response.status_code}")
                print(f"[AUTOMATION ERROR] Message: {error_msg}")
                
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
    
    def check_managed_identity(self, automation_account_id):
        """
        Check Automation Account Managed Identity and its permissions
        
        Args:
            automation_account_id: Full resource ID of Automation Account
                                  Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Automation/automationAccounts/{name}
        
        Returns:
            dict with:
                - success: bool
                - identity: dict with identity details
                - roleAssignments: list of role assignments
                - riskScore: string (Critical/High/Medium/Low)
                - recommendations: list of security recommendations
        """
        print(f"[AUTOMATION MI] Checking Managed Identity for: {automation_account_id}")
        
        # Step 1: Get Automation Account details
        endpoint = f"{automation_account_id}?api-version={self.api_version}"
        print(f"[AUTOMATION MI] GET endpoint: {endpoint}")
        print(f"[AUTOMATION MI] Full URL: {self.base_url}{endpoint}")
        
        result = self._make_request(endpoint)
        
        if not result['success']:
            return {
                'success': False,
                'error': f"Failed to get Automation Account details: {result.get('error')}"
            }
        
        account_data = result['data']
        identity = account_data.get('identity', {})
        
        # Check if Managed Identity is enabled
        if not identity or identity.get('type') == 'None':
            print(f"[AUTOMATION MI] No Managed Identity enabled")
            return {
                'success': True,
                'identity': {
                    'enabled': False,
                    'type': None,
                    'principalId': None
                },
                'roleAssignments': [],
                'riskScore': 'None',
                'recommendations': ['Consider enabling Managed Identity for keyless authentication']
            }
        
        identity_type = identity.get('type', 'Unknown')
        principal_id = identity.get('principalId')
        
        print(f"[AUTOMATION MI] Identity enabled - Type: {identity_type}, Principal ID: {principal_id}")
        
        # Step 2: Get role assignments for the Managed Identity
        subscription_id = automation_account_id.split('/')[2]
        
        role_assignments_result = self._make_request(
            f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=principalId eq '{principal_id}'"
        )
        
        role_assignments = []
        if role_assignments_result['success']:
            assignments = role_assignments_result['data'].get('value', [])
            print(f"[AUTOMATION MI] Found {len(assignments)} role assignments")
            
            # Get role definition details for each assignment
            for assignment in assignments:
                props = assignment.get('properties', {})
                role_def_id = props.get('roleDefinitionId')
                scope = props.get('scope', '')
                
                # Get role definition name
                role_name = 'Unknown'
                role_type = 'Unknown'
                if role_def_id:
                    role_result = self._make_request(f"{role_def_id}?api-version=2022-04-01")
                    if role_result['success']:
                        role_props = role_result['data'].get('properties', {})
                        role_name = role_props.get('roleName', 'Unknown')
                        role_type = role_props.get('type', 'Unknown')
                
                role_assignments.append({
                    'id': assignment.get('id'),
                    'roleName': role_name,
                    'roleType': role_type,
                    'scope': scope,
                    'scopeLevel': self._get_scope_level(scope)
                })
        
        # Step 3: Risk scoring
        risk_score, recommendations = self._calculate_risk_score(role_assignments)
        
        print(f"[AUTOMATION MI] Risk Score: {risk_score}")
        print(f"[AUTOMATION MI] Recommendations: {len(recommendations)}")
        
        return {
            'success': True,
            'identity': {
                'enabled': True,
                'type': identity_type,
                'principalId': principal_id
            },
            'roleAssignments': role_assignments,
            'riskScore': risk_score,
            'recommendations': recommendations,
            'automationAccountId': automation_account_id
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
    
    def _calculate_risk_score(self, role_assignments):
        """
        Calculate risk score based on role assignments
        
        Args:
            role_assignments: List of role assignment dicts
            
        Returns:
            tuple: (risk_score: str, recommendations: list)
        """
        if not role_assignments:
            return 'Low', ['No role assignments found - identity has minimal permissions']
        
        # High-risk roles
        critical_roles = ['Owner', 'User Access Administrator']
        high_risk_roles = ['Contributor', 'Virtual Machine Contributor', 'Storage Account Key Operator Access']
        
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
                recommendations.append(f"🚨 CRITICAL: '{role_name}' role allows full control - immediate privilege escalation risk")
            
            # Check for high-risk roles
            elif any(high in role_name for high in high_risk_roles):
                has_high = True
                recommendations.append(f"⚠️ HIGH: '{role_name}' role provides extensive permissions")
            
            # Check scope level
            if scope_level == 'Subscription':
                has_subscription_scope = True
                recommendations.append(f"📊 Wide scope: '{role_name}' applies to entire subscription")
        
        # Determine overall risk score
        if has_critical:
            risk_score = 'Critical'
        elif has_high and has_subscription_scope:
            risk_score = 'High'
        elif has_high:
            risk_score = 'Medium'
        else:
            risk_score = 'Low'
        
        # Add general recommendations
        if risk_score in ['Critical', 'High']:
            recommendations.append('💡 Consider principle of least privilege - reduce role permissions')
            recommendations.append('🎯 RED TEAM: This Managed Identity is a high-value target for privilege escalation')
        
        return risk_score, recommendations
