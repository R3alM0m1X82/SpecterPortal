"""
Storage Service - Azure Storage Account enumeration
Enumerate Storage Accounts (blobs, queues, tables, files)
Security Audit (firewall, public access, encryption, keys)
Audience: https://storage.azure.com/.default
"""
import requests
import time
import sys


class StorageService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://management.azure.com'
        self.api_version = '2023-01-01'
        self.timeout = 30
    
    def _make_request(self, endpoint, method='GET', json_data=None, **kwargs):
        """Make request to ARM API for Storage resources"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    json=json_data,
                    **kwargs
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"[429 Rate Limit] Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code in [200, 201, 202, 204]:
                    if response.status_code == 204 or not response.content:
                        return {'success': True, 'data': {}}
                    return {'success': True, 'data': response.json()}
                else:
                    error_detail = response.text
                    error_code = None
                    try:
                        error_json = response.json()
                        if 'error' in error_json:
                            error_detail = error_json['error'].get('message', response.text)
                            error_code = error_json['error'].get('code', None)
                    except:
                        pass
                    
                    print(f"[STORAGE ERROR] {method} {url}")
                    print(f"[STORAGE ERROR] Status: {response.status_code}")
                    print(f"[STORAGE ERROR] Code: {error_code}")
                    
                    is_permission_denied = response.status_code == 403
                    
                    result = {
                        'success': False,
                        'error': f'Storage API returned {response.status_code}',
                        'details': error_detail,
                        'error_code': error_code
                    }
                    
                    if is_permission_denied:
                        result['permission_denied'] = True
                    
                    return result
                    
            except requests.exceptions.Timeout:
                return {'success': False, 'error': 'Request timeout'}
            except requests.exceptions.RequestException as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    # ==================== STORAGE ACCOUNTS ====================
    
    def get_storage_accounts(self, subscription_id):
        """Get storage accounts in subscription"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version={self.api_version}'
        )
        
        if result['success']:
            accounts = result['data'].get('value', [])
            return {
                'success': True,
                'storage_accounts': [{
                    'name': a.get('name'),
                    'location': a.get('location'),
                    'id': a.get('id'),
                    'kind': a.get('kind'),
                    'sku': a.get('sku', {}).get('name'),
                    'primaryEndpoints': a.get('properties', {}).get('primaryEndpoints', {}),
                    'provisioningState': a.get('properties', {}).get('provisioningState'),
                    'tags': a.get('tags', {})
                } for a in accounts]
            }
        
        return result
    
    # ==================== SECURITY AUDIT ====================
    
    def get_storage_account_properties(self, storage_account_id):
        """
        PHASE 1: Get detailed storage account properties
        Returns: network rules, firewall, public access, encryption
        """
        print(f"[STORAGE DEBUG] ========================================")
        print(f"[STORAGE DEBUG] get_storage_account_properties CALLED")
        print(f"[STORAGE DEBUG] storage_account_id: {storage_account_id}")
        print(f"[STORAGE DEBUG] ========================================")
        sys.stdout.flush()
        
        result = self._make_request(
            f'/{storage_account_id}?api-version={self.api_version}'
        )
        
        print(f"[STORAGE DEBUG] Request result success: {result.get('success')}")
        sys.stdout.flush()
        
        if result['success']:
            data = result['data']
            props = data.get('properties', {})
            
            # DEBUG: Print raw properties to see what we're getting
            print(f"[STORAGE DEBUG] Raw properties keys: {list(props.keys())}")
            print(f"[STORAGE DEBUG] networkAcls: {props.get('networkAcls')}")
            print(f"[STORAGE DEBUG] publicNetworkAccess: {props.get('publicNetworkAccess')}")
            print(f"[STORAGE DEBUG] allowBlobPublicAccess: {props.get('allowBlobPublicAccess')}")
            sys.stdout.flush()
            
            # Extract network rules
            network_rules = props.get('networkAcls', {})
            default_action = network_rules.get('defaultAction', 'Allow')
            ip_rules = network_rules.get('ipRules', [])
            vnet_rules = network_rules.get('virtualNetworkRules', [])
            
            print(f"[STORAGE DEBUG] Parsed - defaultAction: {default_action}, ipRules: {len(ip_rules)}, vnetRules: {len(vnet_rules)}")
            sys.stdout.flush()
            
            # Public network access
            public_network_access = props.get('publicNetworkAccess', 'Enabled')
            allow_blob_public_access = props.get('allowBlobPublicAccess', False)
            
            # Encryption
            encryption = props.get('encryption', {})
            
            return {
                'success': True,
                'properties': {
                    'name': data.get('name'),
                    'id': data.get('id'),
                    'location': data.get('location'),
                    'firewall': {
                        'defaultAction': default_action,
                        'allowAllIPs': default_action == 'Allow' and len(ip_rules) == 0,
                        'ipRulesCount': len(ip_rules),
                        'ipRules': ip_rules,
                        'vnetRulesCount': len(vnet_rules)
                    },
                    'publicAccess': {
                        'publicNetworkAccess': public_network_access,
                        'allowBlobPublicAccess': allow_blob_public_access,
                        'publicAccessEnabled': public_network_access == 'Enabled' and allow_blob_public_access
                    },
                    'encryption': {
                        'keySource': encryption.get('keySource', 'Microsoft.Storage'),
                        'requireInfrastructureEncryption': encryption.get('requireInfrastructureEncryption', False)
                    },
                    'https': {
                        'supportsHttpsTrafficOnly': props.get('supportsHttpsTrafficOnly', True)
                    },
                    'minimumTlsVersion': props.get('minimumTlsVersion', 'TLS1_0')
                }
            }
        
        print(f"[STORAGE DEBUG] Request FAILED or no success")
        print(f"[STORAGE DEBUG] Error: {result.get('error')}")
        print(f"[STORAGE DEBUG] Details: {result.get('details')}")
        print(f"[STORAGE DEBUG] Error code: {result.get('error_code')}")
        sys.stdout.flush()
        return result
    
    def list_containers(self, storage_account_id):
        """
        PHASE 2: List blob containers using ARM API
        """
        result = self._make_request(
            f'/{storage_account_id}/blobServices/default/containers?api-version={self.api_version}'
        )
        
        if result['success']:
            containers = result['data'].get('value', [])
            return {
                'success': True,
                'containers': [{
                    'name': c.get('name'),
                    'id': c.get('id'),
                    'publicAccess': c.get('properties', {}).get('publicAccess', 'None'),
                    'hasImmutabilityPolicy': c.get('properties', {}).get('hasImmutabilityPolicy', False),
                    'hasLegalHold': c.get('properties', {}).get('hasLegalHold', False),
                    'lastModifiedTime': c.get('properties', {}).get('lastModifiedTime'),
                    'leaseStatus': c.get('properties', {}).get('leaseStatus'),
                    'metadata': c.get('properties', {}).get('metadata', {})
                } for c in containers]
            }
        
        return result
    
    def get_storage_keys(self, storage_account_id):
        """
        PHASE 3: Attempt to retrieve storage account keys
        This will succeed only if user has 'Microsoft.Storage/storageAccounts/listKeys/action' permission
        """
        result = self._make_request(
            f'/{storage_account_id}/listKeys?api-version={self.api_version}',
            method='POST'
        )
        
        if result['success']:
            keys = result['data'].get('keys', [])
            return {
                'success': True,
                'accessible': True,
                'keys': [{
                    'keyName': k.get('keyName'),
                    'value': k.get('value'),
                    'permissions': k.get('permissions')
                } for k in keys]
            }
        elif result.get('permission_denied'):
            return {
                'success': True,
                'accessible': False,
                'error': 'Insufficient permissions to list keys'
            }
        
        return result
    
    def list_blobs(self, storage_account_name, container_name, blob_endpoint):
        """
        List blobs in a public container via direct Azure Blob REST API
        This bypasses CORS issues by calling from server-side
        """
        try:
            list_blobs_url = f"{blob_endpoint}{container_name}?restype=container&comp=list"
            
            response = requests.get(list_blobs_url, timeout=30)
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                
                root = ET.fromstring(response.content)
                blobs = []
                
                # Parse XML response
                for blob_elem in root.findall('.//Blob'):
                    name_elem = blob_elem.find('Name')
                    props_elem = blob_elem.find('Properties')
                    
                    if name_elem is not None and props_elem is not None:
                        name = name_elem.text
                        size_elem = props_elem.find('Content-Length')
                        content_type_elem = props_elem.find('Content-Type')
                        last_modified_elem = props_elem.find('Last-Modified')
                        
                        blobs.append({
                            'name': name,
                            'size': int(size_elem.text) if size_elem is not None else 0,
                            'contentType': content_type_elem.text if content_type_elem is not None else 'unknown',
                            'lastModified': last_modified_elem.text if last_modified_elem is not None else None,
                            'url': f"{blob_endpoint}{container_name}/{name}"
                        })
                
                return {
                    'success': True,
                    'blobs': blobs,
                    'count': len(blobs)
                }
            else:
                return {
                    'success': False,
                    'error': f'Azure Blob API returned {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse blob list: {str(e)}'
            }
    
    def security_audit(self, storage_account_id):
        """
        Comprehensive security audit combining all phases
        """
        audit_results = {
            'success': True,
            'storage_account_id': storage_account_id,
            'risks': [],
            'warnings': [],
            'passed': []
        }
        
        # Phase 1: Properties
        props_result = self.get_storage_account_properties(storage_account_id)
        if props_result['success']:
            props = props_result['properties']
            audit_results['properties'] = props
            
            # Check firewall
            if props['firewall']['allowAllIPs']:
                audit_results['risks'].append({
                    'severity': 'HIGH',
                    'category': 'Network Security',
                    'issue': 'Firewall allows all IPs (0.0.0.0/0)',
                    'recommendation': 'Restrict network access to specific IP ranges'
                })
            else:
                audit_results['passed'].append('Firewall configured with IP restrictions')
            
            # Check public blob access
            if props['publicAccess']['publicAccessEnabled']:
                audit_results['warnings'].append({
                    'severity': 'MEDIUM',
                    'category': 'Public Access',
                    'issue': 'Blob public access is enabled at account level',
                    'recommendation': 'Disable public blob access unless specifically required'
                })
            else:
                audit_results['passed'].append('Public blob access disabled')
            
            # Check HTTPS only
            if not props['https']['supportsHttpsTrafficOnly']:
                audit_results['risks'].append({
                    'severity': 'HIGH',
                    'category': 'Encryption in Transit',
                    'issue': 'HTTP traffic is allowed (insecure)',
                    'recommendation': 'Enable HTTPS only traffic'
                })
            else:
                audit_results['passed'].append('HTTPS-only traffic enforced')
            
            # Check TLS version
            if props['minimumTlsVersion'] in ['TLS1_0', 'TLS1_1']:
                audit_results['warnings'].append({
                    'severity': 'MEDIUM',
                    'category': 'Encryption',
                    'issue': f'Outdated TLS version: {props["minimumTlsVersion"]}',
                    'recommendation': 'Upgrade to TLS 1.2 or higher'
                })
            else:
                audit_results['passed'].append(f'Modern TLS version: {props["minimumTlsVersion"]}')
        
        # Phase 2: Containers
        containers_result = self.list_containers(storage_account_id)
        if containers_result['success']:
            containers = containers_result['containers']
            audit_results['containers_count'] = len(containers)
            
            public_containers = [c for c in containers if c['publicAccess'] != 'None']
            if public_containers:
                audit_results['risks'].append({
                    'severity': 'CRITICAL',
                    'category': 'Public Access',
                    'issue': f'{len(public_containers)} container(s) have public access',
                    'details': [c['name'] for c in public_containers],
                    'recommendation': 'Review and restrict public container access'
                })
                audit_results['public_containers'] = public_containers
            else:
                audit_results['passed'].append('No containers with public access')
        
        # Phase 3: Keys
        keys_result = self.get_storage_keys(storage_account_id)
        if keys_result.get('accessible'):
            audit_results['risks'].append({
                'severity': 'CRITICAL',
                'category': 'Access Control',
                'issue': 'Storage account keys are accessible',
                'recommendation': 'Keys provide full access to storage. Verify RBAC permissions.',
                'keys_available': True
            })
            audit_results['keys_accessible'] = True
        else:
            audit_results['passed'].append('Storage account keys protected (no access)')
            audit_results['keys_accessible'] = False
        
        # Calculate risk score
        critical_count = len([r for r in audit_results['risks'] if r['severity'] == 'CRITICAL'])
        high_count = len([r for r in audit_results['risks'] if r['severity'] == 'HIGH'])
        medium_count = len([w for w in audit_results['warnings'] if w['severity'] == 'MEDIUM'])
        
        audit_results['risk_score'] = {
            'critical': critical_count,
            'high': high_count,
            'medium': medium_count,
            'total_issues': critical_count + high_count + medium_count,
            'passed_checks': len(audit_results['passed'])
        }
        
        return audit_results
