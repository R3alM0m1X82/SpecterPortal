"""
Permissions Service - Azure RBAC & Permissions Management
My Permissions, Role Assignments, Effective Permissions
Added cache system (20 min TTL) for NEW cached methods
"""
import requests
import time


class PermissionsService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://management.azure.com'
        self.graph_url = 'https://graph.microsoft.com/v1.0'
        self.api_version = '2022-04-01'  # Stable RBAC API version
        self.timeout = 30
        
        # Cache system 
        self.cache = {}
        self.cache_ttl = 1200  # 20 minutes
        
        # Key Vault RBAC roles mapping
        self.keyvault_roles = {
            'Key Vault Administrator': {
                'id': '00482a5a-887f-4fb3-b363-3b7fe8e74483',
                'actions': ['secrets_read', 'secrets_write', 'secrets_delete', 'certificates_read', 'certificates_write', 'keys_read', 'keys_write']
            },
            'Key Vault Secrets Officer': {
                'id': 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7',
                'actions': ['secrets_read', 'secrets_write', 'secrets_delete']
            },
            'Key Vault Secrets User': {
                'id': '4633458b-17de-408a-b874-0445c86b69e6',
                'actions': ['secrets_read']
            },
            'Key Vault Certificates Officer': {
                'id': 'a4417e6f-fecd-4de8-b567-7b0420556985',
                'actions': ['certificates_read', 'certificates_write', 'certificates_delete']
            },
            'Key Vault Certificates User': {
                'id': 'db79e9a7-68ee-4b58-9aeb-b90e7c24fcba',
                'actions': ['certificates_read']
            },
            'Key Vault Crypto Officer': {
                'id': '14b46e9e-c2b7-41b4-b07b-48a6ebf60603',
                'actions': ['keys_read', 'keys_write', 'keys_delete', 'keys_encrypt', 'keys_decrypt']
            },
            'Key Vault Crypto User': {
                'id': '12338af0-0e69-4776-bea7-57ae8d297424',
                'actions': ['keys_read', 'keys_encrypt', 'keys_decrypt']
            },
            'Key Vault Reader': {
                'id': '21090545-7ca7-4776-b22c-e363652d74d2',
                'actions': ['metadata_read']
            }
        }
    
    def _make_request(self, endpoint, method='GET', json_data=None, use_graph=False, **kwargs):
        """Make request to ARM or Graph API"""
        if use_graph:
            url = f"{self.graph_url}{endpoint}"
        else:
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
                    print(f"[429 Rate Limit] Waiting {retry_after}s before retry...")
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
                    
                    print(f"[PERMISSIONS ERROR] {method} {url}")
                    print(f"[PERMISSIONS ERROR] Status: {response.status_code}")
                    print(f"[PERMISSIONS ERROR] Code: {error_code}")
                    
                    is_permission_denied = response.status_code == 403
                    
                    result = {
                        'success': False,
                        'error': f'Permissions API returned {response.status_code}',
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
    
    # ==================== CACHE HELPERS ====================
    
    def _get_from_cache(self, cache_key):
        """Get data from cache if valid"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = time.time() - cached['timestamp']
            if age < self.cache_ttl:
                print(f"[CACHE HIT] {cache_key} (age: {int(age)}s)")
                return cached['data']
        return None
    
    def _set_cache(self, cache_key, data):
        """Store data in cache"""
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': data
        }
        print(f"[CACHE SET] {cache_key}")
    
    def _clear_cache_key(self, cache_key):
        """Clear specific cache entry"""
        if cache_key in self.cache:
            del self.cache[cache_key]
            print(f"[CACHE CLEAR] {cache_key}")
    
    def clear_all_cache(self):
        """Clear all cache entries"""
        self.cache.clear()
        print("[CACHE] All entries cleared")
    
    def _extract_oid_from_jwt(self):
        """
        Extract Object ID (OID) from JWT token
        Works for User tokens, Service Principal tokens, and Managed Identity tokens
        
        Returns:
            str: Object ID (GUID) or None if not found
        """
        import json
        import base64
        
        if not self.access_token:
            return None
        
        try:
            # Split JWT into parts
            parts = self.access_token.split('.')
            if len(parts) < 2:
                return None
            
            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            # OID claim is present in all Azure AD tokens
            # For users: unique object ID in the directory
            # For service principals: unique object ID in the directory
            # For managed identities: unique object ID in the directory
            oid = payload_data.get('oid') or payload_data.get('sub')
            
            return oid
            
        except Exception as e:
            print(f"[PERMISSIONS] Failed to extract OID from JWT: {e}")
            return None
    
    def _get_user_group_memberships(self, user_oid, graph_token=None):
        """
        Get user's group memberships from Graph API
        Requires a separate Graph token with Directory.Read.All permission
        
        Args:
            user_oid: User's Object ID
            graph_token: Optional Graph API token (if not provided, will skip group lookup)
            
        Returns:
            set: Set of group Object IDs, or empty set if failed/not available
        """
        if not graph_token:
            print(f"[PERMISSIONS] No Graph token provided - skipping group membership lookup")
            return set()
        
        try:
            # Use Graph API to get user's groups
            headers = {
                'Authorization': f'Bearer {graph_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.graph_url}/users/{user_oid}/memberOf?$select=id"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[PERMISSIONS] Graph API returned {response.status_code}")
                return set()
            
            data = response.json()
            groups = data.get('value', [])
            group_oids = {group['id'] for group in groups if 'id' in group}
            
            print(f"[PERMISSIONS] Found {len(group_oids)} group memberships via Graph API")
            for goid in list(group_oids)[:5]:  # Show first 5
                print(f"[PERMISSIONS]   - Group OID: {goid}")
            
            return group_oids
            
        except Exception as e:
            print(f"[PERMISSIONS] Failed to get group memberships: {e}")
            return set()
    
    # ==================== ORIGINAL METHODS ====================
    
    def get_my_role_assignments(self):
        """
        Get all role assignments for current principal
        Now includes group memberships and works for Service Principals/Managed Identities
        Handles case when /subscriptions returns 0 by trying known subscription IDs
        """
        # Extract OID from JWT token
        oid = self._extract_oid_from_jwt()
        if not oid:
            return {'success': False, 'error': 'Failed to extract OID from token'}
        
        print(f"[PERMISSIONS] Using OID: {oid}")
        
        # First get subscriptions
        subs_result = self._make_request(f'/subscriptions?api-version=2023-07-01')
        
        subscriptions = []
        if subs_result['success']:
            subscriptions = subs_result['data'].get('value', [])
            print(f"[MY ROLES] Found {len(subscriptions)} subscription(s) from /subscriptions query")
        else:
            print(f"[MY ROLES] ❌ Failed to get subscriptions: {subs_result.get('error')}")
        
        # If 0 subscriptions, try known subscription IDs from previous successful queries
        if not subscriptions:
            print(f"[MY ROLES] ⚠️ No subscriptions found via /subscriptions endpoint")
            print(f"[MY ROLES] 💡 Trying known subscription ID: 414a3c64-d834-4568-a53c-0b740e72bde4")
            
            # Try Microsoft Partner Network subscription (from previous successful query)
            known_sub_id = '414a3c64-d834-4568-a53c-0b740e72bde4'
            test_result = self._make_request(
                f'/subscriptions/{known_sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}&$filter=assignedTo(\'{oid}\')'
            )
            
            if test_result['success']:
                print(f"[MY ROLES] ✓ Known subscription ID is still accessible!")
                # Reconstruct subscription object for processing
                subscriptions = [{
                    'subscriptionId': known_sub_id,
                    'displayName': 'Microsoft Partner Network (cached)'
                }]
            else:
                print(f"[MY ROLES] ❌ Known subscription ID not accessible: {test_result.get('error')}")
                return {
                    'success': False,
                    'error': 'No subscriptions accessible. User may have resource-level permissions only. Unable to enumerate role assignments without subscription context.',
                    'error_type': 'no_subscriptions',
                    'roleAssignments': [],
                    'count': 0
                }
        
        # Collect all role assignments across subscriptions
        all_assignments = []
        
        for sub in subscriptions:
            sub_id = sub.get('subscriptionId')
            sub_name = sub.get('displayName')
            
            print(f"[MY ROLES] Querying assignments for subscription: {sub_name}")
            
            # Use assignedTo() instead of atScope()
            # assignedTo() includes:
            # - Direct assignments to the principal
            # - Assignments through group membership (if user)
            # - Works for Service Principals and Managed Identities
            result = self._make_request(
                f'/subscriptions/{sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}&$filter=assignedTo(\'{oid}\')'
            )
            
            if result['success']:
                assignments = result['data'].get('value', [])
                print(f"[MY ROLES] Found {len(assignments)} assignments in {sub_name}")
                
                for assignment in assignments:
                    all_assignments.append({
                        'id': assignment.get('id'),
                        'name': assignment.get('name'),
                        'subscriptionId': sub_id,
                        'subscriptionName': sub_name,
                        'roleDefinitionId': assignment.get('properties', {}).get('roleDefinitionId'),
                        'scope': assignment.get('properties', {}).get('scope'),
                        'principalId': assignment.get('properties', {}).get('principalId')
                    })
            else:
                print(f"[MY ROLES] ❌ Failed to query assignments for {sub_name}: {result.get('error')}")
        
        # Get role definitions details (role names)
        for assignment in all_assignments:
            role_def_id = assignment['roleDefinitionId']
            if role_def_id:
                role_result = self._make_request(
                    f'{role_def_id}?api-version={self.api_version}'
                )
                
                if role_result['success']:
                    role_data = role_result['data']
                    assignment['roleName'] = role_data.get('properties', {}).get('roleName')
                    assignment['roleType'] = role_data.get('properties', {}).get('type')
        
        print(f"[MY ROLES] Total assignments found: {len(all_assignments)}")
        
        return {
            'success': True,
            'roleAssignments': all_assignments,
            'count': len(all_assignments)
        }
    
    def get_role_assignments_for_subscription(self, subscription_id):
        """Get role assignments for specific subscription"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
        )
        
        if result['success']:
            assignments = result['data'].get('value', [])
            
            processed = []
            for assignment in assignments:
                role_def_id = assignment.get('properties', {}).get('roleDefinitionId')
                
                # Get role name
                role_name = 'Unknown'
                if role_def_id:
                    role_result = self._make_request(f'{role_def_id}?api-version={self.api_version}')
                    if role_result['success']:
                        role_name = role_result['data'].get('properties', {}).get('roleName', 'Unknown')
                
                processed.append({
                    'id': assignment.get('id'),
                    'name': assignment.get('name'),
                    'roleDefinitionId': role_def_id,
                    'roleName': role_name,
                    'scope': assignment.get('properties', {}).get('scope'),
                    'principalId': assignment.get('properties', {}).get('principalId')
                })
            
            return {
                'success': True,
                'roleAssignments': processed,
                'count': len(processed)
            }
        
        return result
    
    def get_role_assignments_for_resource(self, resource_id):
        """Get role assignments for specific resource"""
        result = self._make_request(
            f'{resource_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
        )
        
        if result['success']:
            assignments = result['data'].get('value', [])
            
            processed = []
            for assignment in assignments:
                role_def_id = assignment.get('properties', {}).get('roleDefinitionId')
                
                # Get role name
                role_name = 'Unknown'
                if role_def_id:
                    role_result = self._make_request(f'{role_def_id}?api-version={self.api_version}')
                    if role_result['success']:
                        role_name = role_result['data'].get('properties', {}).get('roleName', 'Unknown')
                
                processed.append({
                    'id': assignment.get('id'),
                    'name': assignment.get('name'),
                    'roleDefinitionId': role_def_id,
                    'roleName': role_name,
                    'scope': assignment.get('properties', {}).get('scope'),
                    'principalId': assignment.get('properties', {}).get('principalId')
                })
            
            return {
                'success': True,
                'roleAssignments': processed,
                'count': len(processed)
            }
        
        return result
    
    def check_keyvault_permissions(self, vault_id):
        """
        Check Key Vault specific permissions
        Returns which actions user can perform based on RBAC roles
        """
        result = self.get_role_assignments_for_resource(vault_id)
        
        if not result['success']:
            return result
        
        assignments = result['roleAssignments']
        
        # Determine permissions based on roles
        permissions = {
            'canReadSecrets': False,
            'canWriteSecrets': False,
            'canDeleteSecrets': False,
            'canReadCertificates': False,
            'canWriteCertificates': False,
            'canReadKeys': False,
            'canWriteKeys': False,
            'roles': []
        }
        
        for assignment in assignments:
            role_name = assignment.get('roleName', '')
            
            if role_name in self.keyvault_roles:
                role_info = self.keyvault_roles[role_name]
                actions = role_info['actions']
                
                permissions['roles'].append(role_name)
                
                if 'secrets_read' in actions:
                    permissions['canReadSecrets'] = True
                if 'secrets_write' in actions:
                    permissions['canWriteSecrets'] = True
                if 'secrets_delete' in actions:
                    permissions['canDeleteSecrets'] = True
                if 'certificates_read' in actions:
                    permissions['canReadCertificates'] = True
                if 'certificates_write' in actions:
                    permissions['canWriteCertificates'] = True
                if 'keys_read' in actions:
                    permissions['canReadKeys'] = True
                if 'keys_write' in actions:
                    permissions['canWriteKeys'] = True
        
        return {
            'success': True,
            'permissions': permissions,
            'roleAssignments': assignments
        }
    
    def get_all_resources(self):
        """
        Get all Azure resources across all subscriptions
        Equivalent to: Get-AzResource
        """
        # First get all subscriptions
        subs_result = self._make_request(f'/subscriptions?api-version=2023-07-01')
        
        if not subs_result['success']:
            return subs_result
        
        subscriptions = subs_result['data'].get('value', [])
        all_resources = []
        
        for sub in subscriptions:
            sub_id = sub.get('subscriptionId')
            sub_name = sub.get('displayName')
            
            # Get resources for this subscription
            result = self._make_request(
                f'/subscriptions/{sub_id}/resources?api-version=2021-04-01'
            )
            
            if result['success']:
                resources = result['data'].get('value', [])
                
                for resource in resources:
                    all_resources.append({
                        'id': resource.get('id'),
                        'name': resource.get('name'),
                        'type': resource.get('type'),
                        'location': resource.get('location'),
                        'subscriptionId': sub_id,
                        'subscriptionName': sub_name,
                        'resourceGroup': resource.get('id', '').split('/resourceGroups/')[1].split('/')[0] if '/resourceGroups/' in resource.get('id', '') else None
                    })
        
        return {
            'success': True,
            'resources': all_resources,
            'count': len(all_resources)
        }
    
    def get_resource_effective_permissions(self, resource_id):
        """
        Get effective permissions for a specific RESOURCE
        Equivalent to: GET /{resourceId}/providers/Microsoft.Authorization/permissions
        Returns: actions, notActions, dataActions, notDataActions
        """
        result = self._make_request(
            f'{resource_id}/providers/Microsoft.Authorization/permissions?api-version={self.api_version}'
        )
        
        if result['success']:
            permissions_list = result['data'].get('value', [])
            
            # Aggregate all permissions
            all_actions = []
            all_not_actions = []
            all_data_actions = []
            all_not_data_actions = []
            
            for perm in permissions_list:
                all_actions.extend(perm.get('actions', []))
                all_not_actions.extend(perm.get('notActions', []))
                all_data_actions.extend(perm.get('dataActions', []))
                all_not_data_actions.extend(perm.get('notDataActions', []))
            
            return {
                'success': True,
                'permissions': {
                    'actions': list(set(all_actions)),
                    'notActions': list(set(all_not_actions)),
                    'dataActions': list(set(all_data_actions)),
                    'notDataActions': list(set(all_not_data_actions))
                }
            }
        
        return result
    
    def get_all_effective_permissions(self):
        """
        Get effective permissions for ALL resources
        This is the PowerShell loop equivalent
        """
        # Get all resources
        resources_result = self.get_all_resources()
        
        if not resources_result['success']:
            return resources_result
        
        resources = resources_result['resources']
        
        # Get permissions for each resource
        results = []
        for resource in resources:
            resource_id = resource['id']
            perm_result = self.get_resource_effective_permissions(resource_id)
            
            if perm_result['success']:
                results.append({
                    'resourceId': resource_id,
                    'resourceName': resource['name'],
                    'resourceType': resource['type'],
                    'subscriptionName': resource['subscriptionName'],
                    'resourceGroup': resource['resourceGroup'],
                    'permissions': perm_result['permissions']
                })
        
        return {
            'success': True,
            'effectivePermissions': results,
            'count': len(results)
        }
    
    def get_all_role_assignments_complete(self, graph_token=None):
        """
        Get ALL role assignments (subscription + resource level) for current principal
        Uses Graph API to get group memberships and filters client-side
        Equivalent to: Get-AzRoleAssignment
        
        Args:
            graph_token: Optional Graph API token for group membership lookup
        """
        # Extract OID from JWT token
        oid = self._extract_oid_from_jwt()
        if not oid:
            return {'success': False, 'error': 'Failed to extract OID from token'}
        
        print(f"[ROLE ASSIGNMENTS ALL] Using OID: {oid}")
        
        # Try to get user's group memberships from Graph API
        # This requires a Graph token with Directory.Read.All
        group_oids = self._get_user_group_memberships(oid, graph_token)
        
        if group_oids:
            print(f"[ROLE ASSIGNMENTS ALL] User is member of {len(group_oids)} group(s)")
        else:
            print(f"[ROLE ASSIGNMENTS ALL] No group memberships found or Graph API not available")
        
        # Build list of principal IDs to match (user OID + group OIDs)
        principal_ids_to_match = {oid}  # User's own OID
        if group_oids:
            principal_ids_to_match.update(group_oids)
        
        print(f"[ROLE ASSIGNMENTS ALL] Matching {len(principal_ids_to_match)} principal ID(s):")
        for pid in principal_ids_to_match:
            print(f"[ROLE ASSIGNMENTS ALL]   → Principal ID: {pid}")
        
        # Get subscriptions
        print(f"[ROLE ASSIGNMENTS ALL] DEBUG: Calling GET /subscriptions...")
        subs_result = self._make_request(f'/subscriptions?api-version=2023-07-01')
        
        subscriptions = []
        if subs_result['success']:
            data = subs_result['data']
            subscriptions = data.get('value', [])
            print(f"[ROLE ASSIGNMENTS ALL] Found {len(subscriptions)} subscription(s)")
            print(f"[ROLE ASSIGNMENTS ALL] DEBUG: Raw response has 'value' with {len(subscriptions)} items")
            
            # DEBUG: Log subscription details
            if subscriptions:
                for sub in subscriptions[:3]:  # Show first 3
                    print(f"[ROLE ASSIGNMENTS ALL]   → Subscription: {sub.get('displayName')} ({sub.get('subscriptionId')})")
            else:
                print(f"[ROLE ASSIGNMENTS ALL] DEBUG: 'value' array is empty but query succeeded")
                print(f"[ROLE ASSIGNMENTS ALL] DEBUG: Full response keys: {list(data.keys())}")
        else:
            print(f"[ROLE ASSIGNMENTS ALL] ❌ Failed to get subscriptions: {subs_result.get('error')}")
            print(f"[ROLE ASSIGNMENTS ALL] DEBUG: Response was: {subs_result}")
        
        all_assignments = []
        
        # STRATEGY 1: If we have subscriptions, enumerate role assignments per subscription
        if subscriptions:
            print(f"[ROLE ASSIGNMENTS ALL] Using STRATEGY 1: Per-subscription enumeration")
            
            for sub in subscriptions:
                sub_id = sub.get('subscriptionId')
                sub_name = sub.get('displayName')
                
                print(f"[ROLE ASSIGNMENTS ALL] Processing subscription: {sub_name} ({sub_id})")
                
                # Get ALL role assignments for subscription (no filter)
                # We'll filter client-side to include group memberships
                result = self._make_request(
                    f'/subscriptions/{sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
                )
                
                if not result['success']:
                    print(f"[ROLE ASSIGNMENTS ALL] ❌ Failed to get assignments for {sub_name}: {result.get('error')}")
                    continue
                
                if result['success']:
                    assignments = result['data'].get('value', [])
                    
                    print(f"[ROLE ASSIGNMENTS ALL] Found {len(assignments)} total assignments in {sub_name}")
                    
                    matched_count = 0
                    skipped_count = 0
                    for assignment in assignments:
                        props = assignment.get('properties', {})
                        principal_id = props.get('principalId')
                        
                        # CLIENT-SIDE FILTER: Include if principalId matches user OID or any group OID
                        if principal_id not in principal_ids_to_match:
                            skipped_count += 1
                            continue  # Skip assignments for other users/groups
                        
                        print(f"[ROLE ASSIGNMENTS ALL] ✓ MATCHED assignment with principalId: {principal_id}")
                        matched_count += 1
                        role_def_id = props.get('roleDefinitionId')
                        
                        # Get role definition details
                        role_name = 'Unknown'
                        role_type = None
                        if role_def_id:
                            role_result = self._make_request(f'{role_def_id}?api-version={self.api_version}')
                            if role_result['success']:
                                role_props = role_result['data'].get('properties', {})
                                role_name = role_props.get('roleName', 'Unknown')
                                role_type = role_props.get('type')
                        
                        all_assignments.append({
                            'id': assignment.get('id'),
                            'name': assignment.get('name'),
                            'scope': props.get('scope'),
                            'roleDefinitionId': role_def_id,
                            'roleDefinitionName': role_name,
                            'roleType': role_type,
                            'principalId': props.get('principalId'),
                            'principalType': props.get('principalType'),
                            'subscriptionId': sub_id,
                            'subscriptionName': sub_name
                        })
                    
                    print(f"[ROLE ASSIGNMENTS ALL] Matched {matched_count} assignments for current principal in {sub_name}")
                    print(f"[ROLE ASSIGNMENTS ALL] Skipped {skipped_count} assignments (other principals)")
        
        # STRATEGY 2: If NO subscriptions found (user has only resource-level permissions),
        # try tenant-wide role assignments query
        else:
            print(f"[ROLE ASSIGNMENTS ALL] ⚠️ No subscriptions found!")
            print(f"[ROLE ASSIGNMENTS ALL] Using STRATEGY 2: Tenant-wide role assignments query")
            print(f"[ROLE ASSIGNMENTS ALL] NOTE: This requires elevated permissions")
            
            # Try tenant-wide query: Get ALL role assignments visible to this token
            result = self._make_request(
                f'/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
            )
            
            if not result['success']:
                error_msg = result.get('error', 'Unknown error')
                print(f"[ROLE ASSIGNMENTS ALL] ❌ Tenant-wide query failed: {error_msg}")
                
                # Check if it's a 403 (common for non-admin users)
                if '403' in error_msg or 'AuthorizationFailed' in error_msg:
                    print(f"[ROLE ASSIGNMENTS ALL] INFO: User lacks permissions for tenant-wide query")
                    print(f"[ROLE ASSIGNMENTS ALL] ⚡ TRYING STRATEGY 3: Using assignedTo() filter approach")
                    
                    # Strategy 3: Fall back to original method using assignedTo() filter
                    # This won't show group-inherited assignments perfectly, but better than nothing
                    try:
                        fallback_result = self.get_my_role_assignments()
                        if fallback_result['success']:
                            print(f"[ROLE ASSIGNMENTS ALL] ✓ Strategy 3 succeeded: Found {len(fallback_result.get('roleAssignments', []))} assignments via assignedTo() filter")
                            return fallback_result
                        else:
                            print(f"[ROLE ASSIGNMENTS ALL] ❌ Strategy 3 also failed: {fallback_result.get('error')}")
                    except Exception as e:
                        print(f"[ROLE ASSIGNMENTS ALL] ❌ Strategy 3 exception: {e}")
                    
                    # If all strategies failed, return helpful error
                    return {
                        'success': False,
                        'error': 'Unable to enumerate role assignments. No subscriptions found and tenant-wide query requires elevated permissions. Please ensure you have at least Reader role on a subscription, or use the "My Permissions" tab.',
                        'error_type': 'insufficient_permissions',
                        'roleAssignments': [],
                        'count': 0
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to enumerate role assignments: {error_msg}',
                        'roleAssignments': [],
                        'count': 0
                    }
            
            assignments = result['data'].get('value', [])
            print(f"[ROLE ASSIGNMENTS ALL] Found {len(assignments)} total assignments (tenant-wide)")
            
            matched_count = 0
            skipped_count = 0
            for assignment in assignments:
                props = assignment.get('properties', {})
                principal_id = props.get('principalId')
                
                # CLIENT-SIDE FILTER: Include if principalId matches user OID or any group OID
                if principal_id not in principal_ids_to_match:
                    skipped_count += 1
                    continue
                
                print(f"[ROLE ASSIGNMENTS ALL] ✓ MATCHED assignment with principalId: {principal_id}")
                matched_count += 1
                
                scope = props.get('scope', '')
                role_def_id = props.get('roleDefinitionId')
                
                # Extract subscription info from scope
                sub_id = None
                sub_name = None
                if '/subscriptions/' in scope:
                    parts = scope.split('/')
                    if 'subscriptions' in parts:
                        idx = parts.index('subscriptions')
                        if idx + 1 < len(parts):
                            sub_id = parts[idx + 1]
                            sub_name = f'Subscription-{sub_id[:8]}'  # Abbreviated
                
                # Get role definition details
                role_name = 'Unknown'
                role_type = None
                if role_def_id:
                    role_result = self._make_request(f'{role_def_id}?api-version={self.api_version}')
                    if role_result['success']:
                        role_props = role_result['data'].get('properties', {})
                        role_name = role_props.get('roleName', 'Unknown')
                        role_type = role_props.get('type')
                
                all_assignments.append({
                    'id': assignment.get('id'),
                    'name': assignment.get('name'),
                    'scope': scope,
                    'roleDefinitionId': role_def_id,
                    'roleDefinitionName': role_name,
                    'roleType': role_type,
                    'principalId': principal_id,
                    'principalType': props.get('principalType'),
                    'subscriptionId': sub_id,
                    'subscriptionName': sub_name
                })
            
            print(f"[ROLE ASSIGNMENTS ALL] Matched {matched_count} assignments for current principal")
            print(f"[ROLE ASSIGNMENTS ALL] Skipped {skipped_count} assignments (other principals)")
        
        print(f"[ROLE ASSIGNMENTS ALL] Total matched assignments across all subscriptions: {len(all_assignments)}")
        
        return {
            'success': True,
            'roleAssignments': all_assignments,
            'count': len(all_assignments)
        }
    
    # ==================== NEW CACHED METHODS ====================
    
    def get_subscriptions(self):
        """Get all subscriptions (with cache)"""
        cache_key = 'subscriptions'
        
        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        result = self._make_request(f'/subscriptions?api-version=2023-07-01')
        
        if result['success']:
            subscriptions = result['data'].get('value', [])
            formatted = {
                'success': True,
                'subscriptions': [{
                    'subscriptionId': sub.get('subscriptionId'),
                    'displayName': sub.get('displayName'),
                    'state': sub.get('state'),
                    'tenantId': sub.get('tenantId')
                } for sub in subscriptions]
            }
            
            # Cache result
            self._set_cache(cache_key, formatted)
            return formatted
        
        return result
    
    def get_my_permissions(self, subscription_id=None, force_refresh=False):
        """
        Get my permissions across all subscriptions or specific subscription
        Cached version with force_refresh option
        Now includes group memberships and works for Service Principals/Managed Identities
        """
        cache_key = f'my_permissions_{subscription_id or "all"}'
        
        # Check cache (unless force_refresh)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        else:
            self._clear_cache_key(cache_key)
        
        try:
            # Extract OID from JWT token
            oid = self._extract_oid_from_jwt()
            if not oid:
                return {'success': False, 'error': 'Failed to extract OID from token'}
            
            print(f"[PERMISSIONS] Using OID for permissions: {oid}")
            
            # Get subscriptions first
            subs_result = self.get_subscriptions()
            if not subs_result.get('success'):
                return subs_result
            
            subscriptions = subs_result['subscriptions']
            
            # Filter to specific subscription if requested
            if subscription_id:
                subscriptions = [s for s in subscriptions if s['subscriptionId'] == subscription_id]
                if not subscriptions:
                    return {'success': False, 'error': 'Subscription not found'}
            
            all_permissions = []
            
            for sub in subscriptions:
                sub_id = sub['subscriptionId']
                sub_name = sub['displayName']
                
                # Use assignedTo() instead of atScope()
                # assignedTo() includes:
                # - Direct assignments to the principal
                # - Assignments through group membership (if user)
                # - Works for Service Principals and Managed Identities
                result = self._make_request(
                    f'/subscriptions/{sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}&$filter=assignedTo(\'{oid}\')'
                )
                
                if not result['success']:
                    continue
                
                assignments = result['data'].get('value', [])
                
                for assignment in assignments:
                    props = assignment.get('properties', {})
                    
                    # Get role definition to get role name
                    role_def_id = props.get('roleDefinitionId')
                    if role_def_id:
                        role_result = self._make_request(f"{role_def_id}?api-version={self.api_version}")
                        role_name = 'Unknown Role'
                        if role_result['success']:
                            role_name = role_result['data'].get('properties', {}).get('roleName', 'Unknown Role')
                    else:
                        role_name = 'Unknown Role'
                    
                    scope = props.get('scope', '')
                    
                    all_permissions.append({
                        'subscription': sub_name,
                        'subscriptionId': sub_id,
                        'role': role_name,
                        'scope': scope,
                        'scopeType': self._get_scope_type(scope),
                        'principalId': props.get('principalId'),
                        'assignmentId': assignment.get('id')
                    })
            
            formatted = {
                'success': True,
                'permissions': all_permissions,
                'total': len(all_permissions)
            }
            
            # Cache result
            self._set_cache(cache_key, formatted)
            return formatted
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_role_assignments(self, subscription_id=None, force_refresh=False):
        """
        Get ALL role assignments (all principals) across subscriptions
        Cached version with force_refresh option
        """
        cache_key = f'role_assignments_{subscription_id or "all"}'
        
        # Check cache (unless force_refresh)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        else:
            self._clear_cache_key(cache_key)
        
        try:
            # Get subscriptions first
            subs_result = self.get_subscriptions()
            if not subs_result.get('success'):
                return subs_result
            
            subscriptions = subs_result['subscriptions']
            
            # Filter to specific subscription if requested
            if subscription_id:
                subscriptions = [s for s in subscriptions if s['subscriptionId'] == subscription_id]
                if not subscriptions:
                    return {'success': False, 'error': 'Subscription not found'}
            
            all_assignments = []
            
            for sub in subscriptions:
                sub_id = sub['subscriptionId']
                sub_name = sub['displayName']
                
                # Get ALL role assignments for this subscription (no filter)
                result = self._make_request(
                    f'/subscriptions/{sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
                )
                
                if not result['success']:
                    continue
                
                assignments = result['data'].get('value', [])
                
                for assignment in assignments:
                    props = assignment.get('properties', {})
                    
                    # Get role definition
                    role_def_id = props.get('roleDefinitionId')
                    if role_def_id:
                        role_result = self._make_request(f"{role_def_id}?api-version={self.api_version}")
                        role_name = 'Unknown Role'
                        role_type = 'CustomRole'
                        if role_result['success']:
                            role_props = role_result['data'].get('properties', {})
                            role_name = role_props.get('roleName', 'Unknown Role')
                            role_type = role_result['data'].get('properties', {}).get('type', 'CustomRole')
                    else:
                        role_name = 'Unknown Role'
                        role_type = 'CustomRole'
                    
                    scope = props.get('scope', '')
                    
                    all_assignments.append({
                        'subscription': sub_name,
                        'subscriptionId': sub_id,
                        'principalId': props.get('principalId'),
                        'principalType': props.get('principalType', 'Unknown'),
                        'role': role_name,
                        'roleType': role_type,
                        'scope': scope,
                        'scopeType': self._get_scope_type(scope),
                        'assignmentId': assignment.get('id'),
                        'createdOn': props.get('createdOn'),
                        'updatedOn': props.get('updatedOn')
                    })
            
            formatted = {
                'success': True,
                'assignments': all_assignments,
                'total': len(all_assignments)
            }
            
            # Cache result
            self._set_cache(cache_key, formatted)
            return formatted
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_effective_permissions(self, principal_id, subscription_id=None, force_refresh=False):
        """
        Get effective permissions for a specific PRINCIPAL (user/group/service principal)
        Resolves group memberships and inherited roles
        Cached version with force_refresh option
        """
        cache_key = f'effective_permissions_{principal_id}_{subscription_id or "all"}'
        
        # Check cache (unless force_refresh)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        else:
            self._clear_cache_key(cache_key)
        
        try:
            # Get subscriptions first
            subs_result = self.get_subscriptions()
            if not subs_result.get('success'):
                return subs_result
            
            subscriptions = subs_result['subscriptions']
            
            # Filter to specific subscription if requested
            if subscription_id:
                subscriptions = [s for s in subscriptions if s['subscriptionId'] == subscription_id]
                if not subscriptions:
                    return {'success': False, 'error': 'Subscription not found'}
            
            # Get principal info (Graph API - optional, for display)
            principal_info = {'displayName': 'Unknown', 'type': 'Unknown'}
            try:
                # Try to get user info
                user_result = self._make_request(f'/users/{principal_id}', use_graph=True)
                if user_result['success']:
                    principal_info = {
                        'displayName': user_result['data'].get('displayName', 'Unknown'),
                        'userPrincipalName': user_result['data'].get('userPrincipalName'),
                        'type': 'User'
                    }
                else:
                    # Try service principal
                    sp_result = self._make_request(f'/servicePrincipals/{principal_id}', use_graph=True)
                    if sp_result['success']:
                        principal_info = {
                            'displayName': sp_result['data'].get('displayName', 'Unknown'),
                            'appId': sp_result['data'].get('appId'),
                            'type': 'ServicePrincipal'
                        }
            except:
                pass
            
            # Get group memberships (for inherited permissions)
            group_ids = []
            try:
                groups_result = self._make_request(
                    f'/users/{principal_id}/transitiveMemberOf?$select=id',
                    use_graph=True
                )
                if groups_result['success']:
                    group_ids = [g['id'] for g in groups_result['data'].get('value', [])]
            except:
                pass
            
            all_principals = [principal_id] + group_ids
            
            effective_permissions = []
            
            for sub in subscriptions:
                sub_id = sub['subscriptionId']
                sub_name = sub['displayName']
                
                # Get ALL role assignments for this subscription
                result = self._make_request(
                    f'/subscriptions/{sub_id}/providers/Microsoft.Authorization/roleAssignments?api-version={self.api_version}'
                )
                
                if not result['success']:
                    continue
                
                assignments = result['data'].get('value', [])
                
                # Filter assignments for our principal + groups
                for assignment in assignments:
                    props = assignment.get('properties', {})
                    assigned_principal = props.get('principalId')
                    
                    if assigned_principal not in all_principals:
                        continue
                    
                    # Get role definition
                    role_def_id = props.get('roleDefinitionId')
                    if role_def_id:
                        role_result = self._make_request(f"{role_def_id}?api-version={self.api_version}")
                        role_name = 'Unknown Role'
                        if role_result['success']:
                            role_name = role_result['data'].get('properties', {}).get('roleName', 'Unknown Role')
                    else:
                        role_name = 'Unknown Role'
                    
                    scope = props.get('scope', '')
                    
                    # Determine if inherited (from group)
                    is_inherited = assigned_principal != principal_id
                    
                    effective_permissions.append({
                        'subscription': sub_name,
                        'subscriptionId': sub_id,
                        'role': role_name,
                        'scope': scope,
                        'scopeType': self._get_scope_type(scope),
                        'isInherited': is_inherited,
                        'assignedTo': 'Group' if is_inherited else 'Direct',
                        'assignmentId': assignment.get('id')
                    })
            
            formatted = {
                'success': True,
                'principal': principal_info,
                'permissions': effective_permissions,
                'total': len(effective_permissions),
                'directCount': len([p for p in effective_permissions if not p['isInherited']]),
                'inheritedCount': len([p for p in effective_permissions if p['isInherited']])
            }
            
            # Cache result
            self._set_cache(cache_key, formatted)
            return formatted
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== HELPERS ====================
    
    def _get_scope_type(self, scope):
        """Determine scope type from scope string"""
        if not scope:
            return 'Unknown'
        
        parts = scope.split('/')
        
        if len(parts) == 3 and parts[1] == 'subscriptions':
            return 'Subscription'
        elif 'resourceGroups' in scope:
            if scope.endswith(f"/resourceGroups/{parts[-1]}"):
                return 'ResourceGroup'
            else:
                return 'Resource'
        elif 'managementGroups' in scope:
            return 'ManagementGroup'
        else:
            return 'Other'
