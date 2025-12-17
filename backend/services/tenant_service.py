"""
Tenant service - Azure AD/Entra ID enumeration
Added App Registration management (create, delete, secrets, owned)
Administrative Units with v1.0/beta fallback and member enumeration
Added User/Group creation and owned objects enumeration
Added Owner analysis and Role assignments tracking
"""
import requests
import time
from datetime import datetime, timedelta, timezone
from flask import current_app
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.entity_cache_service import EntityCacheService
from services.cache_service import graph_cache


class TenantService:
    
    def __init__(self, access_token, token_id=None):
        self.access_token = access_token
        self.token_id = token_id  # For caching owners
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
        self._entity_cache = None
    
    def _get_entity_cache(self):
        """Get or create EntityCacheService instance"""
        if not self._entity_cache:
            self._entity_cache = EntityCacheService(self.access_token)
        return self._entity_cache
    
    def _make_request(self, endpoint, method='GET', json_data=None, **kwargs):
        """Make request to Graph API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
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
                    print(f"[429 Rate Limit] Waiting {retry_after}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code in [200, 201, 202, 204]:
                    if response.status_code == 204 or not response.content:
                        return {'success': True, 'data': {}}
                    return {
                        'success': True,
                        'data': response.json()
                    }
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
                    
                    # VERBOSE LOGGING per debug
                    print(f"[API ERROR] {method} {url}")
                    print(f"[API ERROR] Status: {response.status_code}")
                    print(f"[API ERROR] Code: {error_code}")
                    print(f"[API ERROR] Message: {error_detail}")
                    
                    # Check if it's a permission denied error (403 Forbidden)
                    is_permission_denied = (
                        response.status_code == 403 or
                        'Forbidden' in error_detail or
                        'Insufficient privileges' in error_detail or
                        'Authorization_RequestDenied' in error_detail
                    )
                    
                    result = {
                        'success': False,
                        'error': f'API returned {response.status_code}',
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
        
        return {
            'success': False,
            'error': 'Rate limit exceeded (429) - Max retries reached'
        }
    
    def _make_request_with_fallback(self, v1_endpoint, beta_endpoint=None):
        """
        Make request with v1.0 → beta fallback.
        Tries v1.0 first, if 400/404 tries beta.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try v1.0 first
        v1_url = f"{self.base_url}/{v1_endpoint}"
        try:
            response = requests.get(v1_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'api_version': 'v1.0'
                }
            elif response.status_code in [400, 404] and beta_endpoint:
                # Try beta
                print(f"[FALLBACK] v1.0 returned {response.status_code}, trying beta...")
                beta_url = f"https://graph.microsoft.com/beta/{beta_endpoint}"
                beta_response = requests.get(beta_url, headers=headers, timeout=self.timeout)
                
                if beta_response.status_code == 200:
                    return {
                        'success': True,
                        'data': beta_response.json(),
                        'api_version': 'beta'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Both v1.0 and beta failed: {beta_response.status_code}',
                        'details': beta_response.text[:500]
                    }
            else:
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text[:500]
                }
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== USERS ====================
    

    # ==================== OWNER ANALYSIS ====================
    
    def _get_owners(self, entity_type, entity_id):
        """
        Get owners for a specific entity (servicePrincipal or application)
        
        Args:
            entity_type: 'servicePrincipals' or 'applications'
            entity_id: Entity object ID
        
        Returns:
            List of owner objects with displayName and userPrincipalName
        """
        endpoint = f'{entity_type}/{entity_id}/owners'
        result = self._make_request(endpoint)
        
        if result['success']:
            owners = result['data'].get('value', [])
            return [
                {
                    'id': o.get('id'),
                    'displayName': o.get('displayName'),
                    'userPrincipalName': o.get('userPrincipalName'),
                    'mail': o.get('mail')
                }
                for o in owners
            ]
        
        return []
    
    def _get_owners_batch(self, entity_type, entities, max_batch=30):
        """
        Get owners for multiple entities in batch with caching and parallelization
        Optimized with ThreadPoolExecutor (10x faster)
        
        Args:
            entity_type: 'servicePrincipals' or 'applications'
            entities: List of entity dicts with 'id' field
            max_batch: Maximum number of entities to fetch owners for (default 30)
        
        Returns:
            Dict mapping entity_id -> list of owners
        """
        owners_map = {}
        to_fetch = []
        
        # Only process first N entities to avoid rate limiting
        batch_entities = entities[:max_batch]
        
        # First pass: check cache
        for entity in batch_entities:
            entity_id = entity.get('id')
            if not entity_id:
                continue
            
            # Check cache first (20 min TTL)
            if self.token_id:
                cache_key = f'{entity_type}_owners_{entity_id}'
                cached_owners = graph_cache.get(self.token_id, cache_key)
                
                if cached_owners is not None:
                    owners_map[entity_id] = cached_owners
                    continue
            
            # Add to fetch list
            to_fetch.append(entity)
        
        # Second pass: parallel fetch for non-cached entities
        if to_fetch:
            def fetch_owners(entity):
                """Helper to fetch owners with error handling"""
                entity_id = entity.get('id')
                try:
                    owners = self._get_owners(entity_type, entity_id)
                    
                    # Cache result (20 min = 1200 seconds)
                    if self.token_id:
                        cache_key = f'{entity_type}_owners_{entity_id}'
                        graph_cache.set(self.token_id, cache_key, owners, ttl_seconds=1200)
                    
                    return entity_id, owners
                except Exception as e:
                    # Return empty on error
                    return entity_id, []
            
            # Parallel execution with max 10 workers (avoid rate limiting)
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_entity = {executor.submit(fetch_owners, entity): entity for entity in to_fetch}
                
                for future in as_completed(future_to_entity):
                    try:
                        entity_id, owners = future.result()
                        owners_map[entity_id] = owners
                    except Exception as e:
                        # Skip failed entities
                        pass
        
        return owners_map
    
    def _format_owner_display(self, owners):
        """
        Format owner(s) for display
        
        Args:
            owners: List of owner dicts
        
        Returns:
            String representation: "John Doe", "John Doe +1", or None
        """
        if not owners or len(owners) == 0:
            return None
        
        if len(owners) == 1:
            return owners[0].get('displayName', owners[0].get('userPrincipalName', 'Unknown'))
        
        # Multiple owners: show first + count
        first_owner = owners[0].get('displayName', owners[0].get('userPrincipalName', 'Unknown'))
        return f"{first_owner} +{len(owners) - 1}"
    
    def get_users(self, top=100):
        """Get all users with extended attributes"""
        select = 'id,displayName,userPrincipalName,mail,jobTitle,department,accountEnabled,userType,onPremisesSyncEnabled'
        result = self._make_request(f'users?$top={top}&$select={select}')
        
        if result['success']:
            users = result['data'].get('value', [])
            return {
                'success': True,
                'users': [self._format_user(u) for u in users],
                'count': len(users)
            }
        
        return result
    
    def get_user_details(self, user_id):
        """Get user details"""
        result = self._make_request(f'users/{user_id}')
        
        if result['success']:
            return {
                'success': True,
                'user': self._format_user_full(result['data'])
            }
        
        return result
    
    def search_users(self, query):
        """Search users"""
        result = self._make_request(f'users?$filter=startswith(displayName,\'{query}\') or startswith(userPrincipalName,\'{query}\')')
        
        if result['success']:
            users = result['data'].get('value', [])
            return {
                'success': True,
                'users': [self._format_user(u) for u in users]
            }
        
        return result
    
    def create_user(self, display_name, user_principal_name, password, mail_nickname=None, 
                    account_enabled=True, force_change_password=True, job_title=None, 
                    department=None, usage_location=None):
        """
        Create a new user
        """
        user_data = {
            'accountEnabled': account_enabled,
            'displayName': display_name,
            'mailNickname': mail_nickname or user_principal_name.split('@')[0],
            'userPrincipalName': user_principal_name,
            'passwordProfile': {
                'forceChangePasswordNextSignIn': force_change_password,
                'password': password
            }
        }
        
        if job_title:
            user_data['jobTitle'] = job_title
        if department:
            user_data['department'] = department
        if usage_location:
            user_data['usageLocation'] = usage_location
        
        result = self._make_request('users', method='POST', json_data=user_data)
        
        if result['success']:
            user = result['data']
            return {
                'success': True,
                'user': self._format_user(user),
                'message': f"User '{display_name}' created successfully"
            }
        
        return result
    
    def get_user_roles(self, user_id):
        """Get all directory roles assigned to a user"""
        cache = self._get_entity_cache()
        roles = cache.get_roles_for_user(user_id)
        
        return {
            'success': True,
            'roles': roles,
            'count': len(roles)
        }
    
    def get_user_licenses(self, user_id):
        """Get licenses assigned to a specific user"""
        result = self._make_request(f'users/{user_id}/licenseDetails')
        
        if result['success']:
            licenses = result['data'].get('value', [])
            cache = self._get_entity_cache()
            
            formatted = []
            for lic in licenses:
                sku_id = lic.get('skuId')
                resolved = cache.resolve_license(sku_id)
                
                formatted.append({
                    'id': lic.get('id'),
                    'skuId': sku_id,
                    'skuPartNumber': lic.get('skuPartNumber'),
                    'displayName': resolved.get('displayName', lic.get('skuPartNumber')),
                    'servicePlans': lic.get('servicePlans', [])
                })
            
            return {
                'success': True,
                'licenses': formatted,
                'count': len(formatted)
            }
        
        return result
    
    def get_user_mfa_status(self, user_id):
        """
        Get MFA status for a user.
        Requires UserAuthenticationMethod.Read.All scope.
        Optimized with batch query
        """
        result = self._make_request(f'users/{user_id}/authentication/methods')
        
        if result['success']:
            methods = result['data'].get('value', [])
            
            # Extract method types
            method_types = []
            for method in methods:
                odata_type = method.get('@odata.type', '')
                method_type = odata_type.replace('#microsoft.graph.', '')
                method_types.append(method_type)
            
            # MFA is enabled if user has any of these methods
            mfa_methods = ['phoneAuthenticationMethod', 'microsoftAuthenticatorAuthenticationMethod', 
                          'fido2AuthenticationMethod', 'softwareOathAuthenticationMethod']
            mfa_enabled = any(m in method_types for m in mfa_methods)
            
            return {
                'success': True,
                'mfaEnabled': mfa_enabled,
                'methods': method_types,
                'methodCount': len(method_types)
            }
        
        return result
    
    def get_users_mfa_batch(self, user_ids):
        """
        Get MFA status for multiple users in batch.
        Optimized batch query with error handling per user.
        """
        results = {}
        
        for user_id in user_ids:
            mfa_result = self.get_user_mfa_status(user_id)
            if mfa_result['success']:
                results[user_id] = {
                    'mfaEnabled': mfa_result['mfaEnabled'],
                    'methods': mfa_result['methods'],
                    'methodCount': mfa_result['methodCount']
                }
            else:
                # User doesn't have permission or user not found
                results[user_id] = {
                    'mfaEnabled': None,
                    'methods': [],
                    'methodCount': 0,
                    'error': mfa_result.get('error', 'Unknown error')
                }
        
        return {
            'success': True,
            'results': results,
            'count': len(results)
        }
    
    # ==================== GROUPS ====================
    
    def get_groups(self, top=100):
        """Get groups"""
        result = self._make_request(f'groups?$top={top}')
        
        if result['success']:
            groups = result['data'].get('value', [])
            return {
                'success': True,
                'groups': [self._format_group(g) for g in groups]
            }
        
        return result
    
    def search_groups(self, query):
        """Search groups"""
        result = self._make_request(f'groups?$filter=startswith(displayName,\'{query}\')')
        
        if result['success']:
            groups = result['data'].get('value', [])
            return {
                'success': True,
                'groups': [self._format_group(g) for g in groups]
            }
        
        return result
    
    def get_group_members(self, group_id):
        """Get members of a group"""
        result = self._make_request(f'groups/{group_id}/members')
        
        if result['success']:
            members = result['data'].get('value', [])
            return {
                'success': True,
                'members': [self._format_member(m) for m in members],
                'count': len(members)
            }
        
        return result
    
    def create_group(self, display_name, mail_nickname=None, description=None, 
                     group_types=None, security_enabled=True, mail_enabled=False):
        """
        Create a new group
        """
        group_data = {
            'displayName': display_name,
            'mailNickname': mail_nickname or display_name.replace(' ', '').lower(),
            'mailEnabled': mail_enabled,
            'securityEnabled': security_enabled,
            'groupTypes': group_types or []
        }
        
        if description:
            group_data['description'] = description
        
        result = self._make_request('groups', method='POST', json_data=group_data)
        
        if result['success']:
            group = result['data']
            return {
                'success': True,
                'group': self._format_group(group),
                'message': f"Group '{display_name}' created successfully"
            }
        
        return result
    
    # ==================== ADMINISTRATIVE UNITS ====================
    
    def get_admin_units(self, top=100):
        """
        Get administrative units using v1.0 → beta fallback
        """
        result = self._make_request_with_fallback(
            f'directory/administrativeUnits?$top={top}',
            f'directory/administrativeUnits?$top={top}'
        )
        
        if result['success']:
            units = result['data'].get('value', [])
            return {
                'success': True,
                'adminUnits': [self._format_admin_unit(u) for u in units],
                'count': len(units),
                'api_version': result.get('api_version', 'unknown')
            }
        
        return result
    
    def get_admin_unit_members(self, unit_id):
        """
        Get members of an administrative unit.
        Returns all member types (users, groups, devices, SPs).
        """
        print(f"[DEBUG AU-MEMBERS] Getting members for AU: {unit_id}")
        
        result = self._make_request_with_fallback(
            f'directory/administrativeUnits/{unit_id}/members',
            f'directory/administrativeUnits/{unit_id}/members'
        )
        
        print(f"[DEBUG AU-MEMBERS] API result success: {result.get('success')}")
        
        if result['success']:
            members = result['data'].get('value', [])
            print(f"[DEBUG AU-MEMBERS] Members count: {len(members)}")
            
            if len(members) > 0:
                print(f"[DEBUG AU-MEMBERS] First member: {members[0]}")
            
            # Separate by type as frontend expects
            users = []
            groups = []
            devices = []
            service_principals = []
            
            for member in members:
                member_type = member.get('@odata.type', '').replace('#microsoft.graph.', '')
                
                formatted_member = {
                    'id': member.get('id'),
                    'displayName': member.get('displayName'),
                    'userPrincipalName': member.get('userPrincipalName'),
                    'mail': member.get('mail'),
                    'type': member_type,
                    'accountEnabled': member.get('accountEnabled')
                }
                
                # Categorize by type
                if member_type == 'user':
                    users.append(formatted_member)
                elif member_type == 'group':
                    groups.append(formatted_member)
                elif member_type == 'device':
                    devices.append(formatted_member)
                elif member_type == 'servicePrincipal':
                    service_principals.append(formatted_member)
            
            print(f"[DEBUG AU-MEMBERS] Separated: {len(users)} users, {len(groups)} groups, {len(devices)} devices")
            
            return {
                'success': True,
                'users': users,
                'groups': groups,
                'devices': devices,
                'servicePrincipals': service_principals,
                'userCount': len(users),
                'groupCount': len(groups),
                'deviceCount': len(devices),
                'totalCount': len(members),
                'api_version': result.get('api_version', 'unknown')
            }
        else:
            print(f"[DEBUG AU-MEMBERS] API failed: {result.get('error')}")
        
        return result
    
    def get_admin_unit_scoped_roles(self, unit_id):
        """
        Get scoped role assignments for an administrative unit.
        Returns users with delegated admin roles within this AU.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try v1.0 first
        v1_url = f"{self.base_url}/administrativeUnits/{unit_id}/scopedRoleMembers"
        try:
            response = requests.get(v1_url, headers=headers, timeout=self.timeout)
            
            if response.status_code in [400, 404]:
                # Fallback to beta
                beta_url = f"https://graph.microsoft.com/beta/administrativeUnits/{unit_id}/scopedRoleMembers"
                response = requests.get(beta_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                scoped_members = response.json().get('value', [])
                
                formatted_roles = []
                for sm in scoped_members:
                    role_id = sm.get('roleId')
                    member_info = sm.get('roleMemberInfo', {})
                    
                    # Get role name
                    role_name = 'Unknown Role'
                    role_result = self._make_request(f'directoryRoles/{role_id}')
                    if role_result['success']:
                        role_name = role_result['data'].get('displayName', 'Unknown Role')
                    
                    formatted_roles.append({
                        'id': sm.get('id'),
                        'roleId': role_id,
                        'roleName': role_name,
                        'userId': member_info.get('id'),
                        'userDisplayName': member_info.get('displayName', 'Unknown'),
                        'userPrincipalName': member_info.get('userPrincipalName')
                    })
                
                return {
                    'success': True,
                    'scopedRoles': formatted_roles,
                    'count': len(formatted_roles)
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text[:500]
                }
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== DEVICES ====================
    
    def get_devices(self, top=100):
        """Get devices"""
        # $select optimized: only fields used in _format_device
        select = 'id,displayName,deviceId,operatingSystem,operatingSystemVersion,trustType,isCompliant,isManaged,accountEnabled,registrationDateTime'
        result = self._make_request(f'devices?$top={top}&$select={select}')
        
        if result['success']:
            devices = result['data'].get('value', [])
            return {
                'success': True,
                'devices': [self._format_device(d) for d in devices]
            }
        
        return result
    
    # ==================== DIRECTORY ROLES ====================
    
    def get_directory_roles(self):
        """Get directory roles with members"""
        result = self._make_request('directoryRoles?$expand=members')
        
        if result['success']:
            roles = result['data'].get('value', [])
            formatted_roles = []
            
            for role in roles:
                members = role.get('members', [])
                formatted_roles.append({
                    'id': role.get('id'),
                    'displayName': role.get('displayName'),
                    'description': role.get('description'),
                    'roleTemplateId': role.get('roleTemplateId'),
                    'memberCount': len(members),
                    'members': [self._format_member(m) for m in members[:10]]
                })
            
            return {
                'success': True,
                'directoryRoles': formatted_roles,
                'count': len(formatted_roles)
            }
        
        return result
    
    # ==================== SERVICE PRINCIPALS ====================
    
    def get_service_principals(self, top=100):
        """Get service principals with credential info"""
        # $select optimized: only fields used in _format_sp (includes credentials)
        select = 'id,appId,displayName,appDisplayName,servicePrincipalType,accountEnabled,passwordCredentials,keyCredentials'
        result = self._make_request(f'servicePrincipals?$top={top}&$select={select}')
        
        if result['success']:
            sps = result['data'].get('value', [])
            return {
                'success': True,
                'servicePrincipals': [self._format_sp(sp) for sp in sps]
            }
        
        return result
    
    def get_managed_identities(self, top=100):
        """Get managed identities (system and user-assigned)"""
        # Filter service principals by servicePrincipalType = ManagedIdentity
        select = 'id,appId,displayName,appDisplayName,servicePrincipalType,accountEnabled,passwordCredentials,keyCredentials,alternativeNames'
        filter_query = "servicePrincipalType eq 'ManagedIdentity'"
        result = self._make_request(f"servicePrincipals?$filter={filter_query}&$top={top}&$select={select}")
        
        if result['success']:
            mis = result['data'].get('value', [])
            return {
                'success': True,
                'managedIdentities': [self._format_managed_identity(mi) for mi in mis]
            }
        
        return result
    
    # ==================== APPLICATIONS ====================
    
    def get_applications(self, top=100):
        """Get app registrations"""
        # $select optimized: only fields used in _format_app (includes credentials)
        select = 'id,appId,displayName,createdDateTime,publisherDomain,signInAudience,passwordCredentials,keyCredentials'
        result = self._make_request(f'applications?$top={top}&$select={select}')
        
        if result['success']:
            apps = result['data'].get('value', [])
            return {
                'success': True,
                'applications': [self._format_app(a) for a in apps]
            }
        
        return result
    

    def get_owners_for_entities(self, entity_type, entity_ids):
        """
        Get owners for specific entities on-demand
        Lazy loading owners
        
        Args:
            entity_type: 'servicePrincipals' or 'applications'
            entity_ids: List of entity IDs to fetch owners for
        
        Returns:
            Dict mapping entity_id -> owner info
        """
        entities = [{'id': eid} for eid in entity_ids]
        owners_map = self._get_owners_batch(entity_type, entities, max_batch=len(entity_ids))
        
        # Format for frontend
        result = {}
        for entity_id, owners in owners_map.items():
            result[entity_id] = {
                'owner': self._format_owner_display(owners),
                'owners': owners,
                'ownerCount': len(owners)
            }
        
        return {
            'success': True,
            'owners': result,
            'count': len(result)
        }


    # ==================== ROLE ASSIGNMENTS ====================
    
    def _get_roles_for_sp(self, sp_id):
        """
        Get directory role assignments for a specific service principal
        
        Args:
            sp_id: Service Principal object ID
        
        Returns:
            List of role assignments with role info
        """
        # Query roleManagement for assignments to this principal
        filter_query = f"principalId eq '{sp_id}'"
        endpoint = f'roleManagement/directory/roleAssignments?$filter={filter_query}'
        result = self._make_request(endpoint)
        
        if not result['success']:
            return []
        
        assignments = result['data'].get('value', [])
        
        # Get role definitions for each assignment
        role_info_list = []
        cache = self._get_entity_cache()
        
        for assignment in assignments:
            role_def_id = assignment.get('roleDefinitionId')
            directory_scope_id = assignment.get('directoryScopeId', '/')
            
            # Resolve role name
            role_name = cache.resolve_role(role_def_id).get('displayName', 'Unknown Role')
            
            # Determine scope type
            if directory_scope_id == '/':
                scope_type = 'tenant'
                scope_name = 'Tenant-wide'
            elif directory_scope_id.startswith('/administrativeUnits/'):
                scope_type = 'au'
                au_id = directory_scope_id.replace('/administrativeUnits/', '')
                # Try to resolve AU name
                au_info = cache.resolve_admin_unit(au_id)
                scope_name = f"AU: {au_info.get('displayName', au_id[:8])}"
            else:
                scope_type = 'other'
                scope_name = directory_scope_id
            
            role_info_list.append({
                'id': assignment.get('id'),
                'roleDefinitionId': role_def_id,
                'roleName': role_name,
                'scopeType': scope_type,
                'scopeName': scope_name,
                'directoryScopeId': directory_scope_id
            })
        
        return role_info_list
    
    def _get_roles_batch(self, sps, max_batch=30):
        """
        Get role assignments for multiple service principals in batch with caching and parallelization
        Optimized with ThreadPoolExecutor (10x faster)
        
        Args:
            sps: List of service principal dicts with 'id' field
            max_batch: Maximum number of SPs to fetch roles for (default 30)
        
        Returns:
            Dict mapping sp_id -> list of role assignments
        """
        roles_map = {}
        to_fetch = []
        
        # Only process first N entities to avoid rate limiting
        batch_sps = sps[:max_batch]
        
        # First pass: check cache
        for sp in batch_sps:
            sp_id = sp.get('id')
            if not sp_id:
                continue
            
            # Check cache first (20 min TTL)
            if self.token_id:
                cache_key = f'sp_roles_{sp_id}'
                cached_roles = graph_cache.get(self.token_id, cache_key)
                
                if cached_roles is not None:
                    roles_map[sp_id] = cached_roles
                    continue
            
            # Add to fetch list
            to_fetch.append(sp)
        
        # Second pass: parallel fetch for non-cached entities
        if to_fetch:
            def fetch_roles(sp):
                """Helper to fetch roles with error handling"""
                sp_id = sp.get('id')
                try:
                    roles = self._get_roles_for_sp(sp_id)
                    
                    # Cache result (20 min = 1200 seconds)
                    if self.token_id:
                        cache_key = f'sp_roles_{sp_id}'
                        graph_cache.set(self.token_id, cache_key, roles, ttl_seconds=1200)
                    
                    return sp_id, roles
                except Exception as e:
                    # Return empty on error
                    return sp_id, []
            
            # Parallel execution with max 10 workers (avoid rate limiting)
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_sp = {executor.submit(fetch_roles, sp): sp for sp in to_fetch}
                
                for future in as_completed(future_to_sp):
                    try:
                        sp_id, roles = future.result()
                        roles_map[sp_id] = roles
                    except Exception as e:
                        # Skip failed entities
                        pass
        
        return roles_map
    
    def _format_role_display(self, roles):
        """
        Format role(s) for display
        
        Args:
            roles: List of role assignment dicts
        
        Returns:
            String representation: "Global Admin", "User Admin +1", or None
        """
        if not roles or len(roles) == 0:
            return None
        
        if len(roles) == 1:
            role = roles[0]
            if role['scopeType'] == 'tenant':
                return f"🛡️ {role['roleName']}"
            else:
                return f"👥 {role['roleName']} ({role['scopeName']})"
        
        # Multiple roles: show first + count
        first_role = roles[0]
        if first_role['scopeType'] == 'tenant':
            return f"🛡️ {first_role['roleName']} +{len(roles) - 1}"
        else:
            return f"👥 {first_role['roleName']} +{len(roles) - 1}"
    
    def get_roles_for_entities(self, entity_ids):
        """
        Get role assignments for specific service principals on-demand
        Lazy loading roles
        
        Args:
            entity_ids: List of service principal IDs to fetch roles for
        
        Returns:
            Dict mapping entity_id -> role info
        """
        entities = [{'id': eid} for eid in entity_ids]
        roles_map = self._get_roles_batch(entities, max_batch=len(entity_ids))
        
        # Format for frontend
        result = {}
        for entity_id, roles in roles_map.items():
            result[entity_id] = {
                'role': self._format_role_display(roles),
                'roles': roles,
                'roleCount': len(roles),
                'hasTenantRole': any(r['scopeType'] == 'tenant' for r in roles),
                'hasAURole': any(r['scopeType'] == 'au' for r in roles)
            }
        
        return {
            'success': True,
            'roles': result,
            'count': len(result)
        }

    def check_app_registration_policy(self):
        """Check if users can register applications"""
        result = self._make_request('policies/authorizationPolicy')
        
        if result['success']:
            policy = result['data']
            return {
                'success': True,
                'defaultUserRolePermissions': policy.get('defaultUserRolePermissions', {}),
                'allowedToCreateApps': policy.get('defaultUserRolePermissions', {}).get('allowedToCreateApps', False)
            }
        
        return result
    
    def check_create_permissions(self):
        """
        Check if current token has permissions to create users/groups.
        Check capabilities before showing Create button.
        
        Returns:
            dict with canCreateUsers and canCreateGroups flags
        """
        capabilities = {
            'success': True,
            'canCreateUsers': False,
            'canCreateGroups': False
        }
        
        # Try to get current user's roles/permissions
        # If we can access directory roles, we likely have admin permissions
        roles_result = self._make_request('me/memberOf')
        
        if roles_result['success']:
            memberships = roles_result['data'].get('value', [])
            
            # Check for admin roles
            admin_roles = [
                'Global Administrator',
                'User Administrator', 
                'Privileged Authentication Administrator',
                'Authentication Administrator',
                'Groups Administrator'
            ]
            
            for membership in memberships:
                display_name = membership.get('displayName', '')
                
                if any(role in display_name for role in admin_roles):
                    capabilities['canCreateUsers'] = True
                    capabilities['canCreateGroups'] = True
                    break
        
        # Alternative: Try to get authorization policy (requires Directory.Read.All)
        policy_result = self._make_request('policies/authorizationPolicy')
        if policy_result['success']:
            # If we can read this, we likely have elevated permissions
            capabilities['hasElevatedPermissions'] = True
        
        return capabilities
    
    def get_owned_applications(self):
        """Get applications owned by current user"""
        result = self._make_request('me/ownedObjects/microsoft.graph.application')
        
        if result['success']:
            apps = result['data'].get('value', [])
            return {
                'success': True,
                'applications': [self._format_app_full(a) for a in apps],
                'count': len(apps)
            }
        
        return result
    
    def create_application(self, display_name, sign_in_audience='AzureADMyOrg', redirect_uris=None, description=None):
        """Create a new App Registration"""
        app_data = {
            'displayName': display_name,
            'signInAudience': sign_in_audience
        }
        
        if description:
            app_data['description'] = description
        
        if redirect_uris:
            app_data['web'] = {
                'redirectUris': redirect_uris if isinstance(redirect_uris, list) else [redirect_uris]
            }
        
        result = self._make_request('applications', method='POST', json_data=app_data)
        
        if result['success']:
            app = result['data']
            return {
                'success': True,
                'application': self._format_app_full(app),
                'message': f"Application '{display_name}' created successfully"
            }
        
        return result
    
    def delete_application(self, app_object_id):
        """Delete an application (must be owner)"""
        result = self._make_request(f'applications/{app_object_id}', method='DELETE')
        
        if result['success']:
            return {
                'success': True,
                'message': f'Application {app_object_id} deleted successfully'
            }
        
        return result
    
    def get_application_secrets(self, app_object_id):
        """Get secrets metadata for an application"""
        result = self._make_request(f'applications/{app_object_id}?$select=id,displayName,passwordCredentials,keyCredentials')
        
        if result['success']:
            app = result['data']
            password_creds = app.get('passwordCredentials', [])
            key_creds = app.get('keyCredentials', [])
            
            secrets = []
            for cred in password_creds:
                secrets.append({
                    'keyId': cred.get('keyId'),
                    'displayName': cred.get('displayName'),
                    'type': 'secret',
                    'startDateTime': cred.get('startDateTime'),
                    'endDateTime': cred.get('endDateTime'),
                    'hint': cred.get('hint')
                })
            
            for cred in key_creds:
                secrets.append({
                    'keyId': cred.get('keyId'),
                    'displayName': cred.get('displayName'),
                    'type': 'certificate',
                    'startDateTime': cred.get('startDateTime'),
                    'endDateTime': cred.get('endDateTime')
                })
            
            return {
                'success': True,
                'secrets': secrets,
                'count': len(secrets)
            }
        
        return result
    
    def add_client_secret(self, app_object_id, description='SpecterPortal Secret', expiry_months=12):
        """Add a client secret to an application"""
        end_date = datetime.utcnow() + timedelta(days=expiry_months * 30)
        
        secret_data = {
            'passwordCredential': {
                'displayName': description,
                'endDateTime': end_date.isoformat() + 'Z'
            }
        }
        
        result = self._make_request(
            f'applications/{app_object_id}/addPassword',
            method='POST',
            json_data=secret_data
        )
        
        if result['success']:
            cred = result['data']
            return {
                'success': True,
                'secret': {
                    'keyId': cred.get('keyId'),
                    'displayName': cred.get('displayName'),
                    'secretText': cred.get('secretText'),
                    'startDateTime': cred.get('startDateTime'),
                    'endDateTime': cred.get('endDateTime'),
                    'hint': cred.get('hint')
                },
                'message': 'Secret created successfully. Copy the secret value now - it will not be shown again!'
            }
        
        return result
    
    def remove_client_secret(self, app_object_id, key_id):
        """Remove a client secret from an application"""
        result = self._make_request(
            f'applications/{app_object_id}/removePassword',
            method='POST',
            json_data={'keyId': key_id}
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'Secret {key_id} removed successfully'
            }
        
        return result
    
    # ==================== OWNED OBJECTS ====================
    
    def get_owned_objects(self, user_id=None):
        """
        Get all objects owned by a specific user or current user.
        Returns devices, groups, applications, and service principals.
        
        
        Args:
            user_id: Optional user ID. If None, returns owned objects of current user (me).
        """
        endpoint = f'users/{user_id}/ownedObjects' if user_id else 'me/ownedObjects'
        result = self._make_request(endpoint)
        
        if result['success']:
            owned = result['data'].get('value', [])
            
            # Categorize objects by type
            devices = []
            groups = []
            applications = []
            service_principals = []
            other = []
            
            for obj in owned:
                obj_type = obj.get('@odata.type', '').replace('#microsoft.graph.', '')
                
                if obj_type == 'device':
                    devices.append(self._format_device(obj))
                elif obj_type == 'group':
                    groups.append(self._format_group(obj))
                elif obj_type == 'application':
                    applications.append(self._format_app(obj))
                elif obj_type == 'servicePrincipal':
                    service_principals.append(self._format_sp(obj))
                else:
                    other.append({
                        'id': obj.get('id'),
                        'displayName': obj.get('displayName'),
                        'type': obj_type
                    })
            
            return {
                'success': True,
                'ownedObjects': {
                    'devices': devices,
                    'groups': groups,
                    'applications': applications,
                    'servicePrincipals': service_principals,
                    'other': other
                },
                'counts': {
                    'devices': len(devices),
                    'groups': len(groups),
                    'applications': len(applications),
                    'servicePrincipals': len(service_principals),
                    'other': len(other),
                    'total': len(owned)
                }
            }
        
        return result
    
    # ==================== ORGANIZATION ====================
    
    def get_organization(self):
        """Get organization info"""
        result = self._make_request('organization')
        
        if result['success']:
            orgs = result['data'].get('value', [])
            if orgs:
                return {
                    'success': True,
                    'organization': self._format_org(orgs[0])
                }
        
        return result
    
    def get_domains(self):
        """Get domains"""
        result = self._make_request('domains')
        
        if result['success']:
            domains = result['data'].get('value', [])
            return {
                'success': True,
                'domains': [self._format_domain(d) for d in domains]
            }
        
        return result
    
    # ==================== TENANT AUTH METHODS ====================
    
    def get_tenant_auth_methods_policy(self):
        """
        Get tenant-wide authentication methods policy.
        Shows MFA/TAP global policies and enabled auth methods.
        Requires: Policy.Read.All or Policy.ReadWrite.AuthenticationMethod
        """
        result = self._make_request('policies/authenticationMethodsPolicy')
        
        if result['success']:
            policy_data = result['data']
            
            # Parse authentication method configurations
            auth_methods = []
            config_list = policy_data.get('authenticationMethodConfigurations', [])
            
            for method in config_list:
                method_type = method.get('@odata.type', '').replace('#microsoft.graph.', '')
                auth_methods.append({
                    'id': method.get('id'),
                    'type': method_type,
                    'state': method.get('state', 'disabled'),
                    'includeTargets': method.get('includeTargets', []),
                    'excludeTargets': method.get('excludeTargets', [])
                })
            
            return {
                'success': True,
                'policy': {
                    'id': policy_data.get('id'),
                    'displayName': policy_data.get('displayName', 'Authentication Methods Policy'),
                    'description': policy_data.get('description'),
                    'registrationEnforcement': policy_data.get('registrationEnforcement', {}),
                    'authenticationMethodConfigurations': auth_methods
                }
            }
        
        # Propagate permission_denied flag if present
        if result.get('permission_denied'):
            return {
                'success': False,
                'error': 'Insufficient privileges to read authentication methods policy',
                'permission_denied': True,
                'error_code': result.get('error_code'),
                'details': result.get('details')
            }
        
        return result
    
    def get_auth_strength_policies(self):
        """
        Get all authentication strength policies.
        Shows custom auth strength combinations (built-in + custom).
        Requires: Policy.Read.All or Policy.ReadWrite.ConditionalAccess
        """
        result = self._make_request('policies/authenticationStrengthPolicies')
        
        if result['success']:
            policies = result['data'].get('value', [])
            
            formatted_policies = []
            for policy in policies:
                formatted_policies.append({
                    'id': policy.get('id'),
                    'displayName': policy.get('displayName'),
                    'description': policy.get('description'),
                    'policyType': policy.get('policyType', 'builtIn'),
                    'createdDateTime': policy.get('createdDateTime'),
                    'modifiedDateTime': policy.get('modifiedDateTime'),
                    'allowedCombinations': policy.get('allowedCombinations', []),
                    'combinationCount': len(policy.get('allowedCombinations', []))
                })
            
            return {
                'success': True,
                'policies': formatted_policies,
                'count': len(formatted_policies)
            }
        
        # Propagate permission_denied flag if present
        if result.get('permission_denied'):
            return {
                'success': False,
                'error': 'Insufficient privileges to read authentication strength policies',
                'permission_denied': True,
                'error_code': result.get('error_code'),
                'details': result.get('details')
            }
        
        return result
    
    def get_authorization_policy(self):
        """
        Get tenant authorization policy.
        Shows default user permissions, guest restrictions, external collaboration settings.
        Requires: Policy.Read.All
        """
        result = self._make_request('policies/authorizationPolicy')
        
        if result['success']:
            policy = result['data']
            
            # DEBUG: Print raw JSON to see actual values
            print(f"[DEBUG AUTHORIZATION POLICY] Raw JSON:")
            print(f"  allowedToCreateApps (from defaultUserRolePermissions): {policy.get('defaultUserRolePermissions', {}).get('allowedToCreateApps', 'FIELD_NOT_PRESENT')}")
            print(f"  allowedToCreateSecurityGroups: {policy.get('defaultUserRolePermissions', {}).get('allowedToCreateSecurityGroups', 'FIELD_NOT_PRESENT')}")
            print(f"  blockMsolPowerShell: {policy.get('blockMsolPowerShell', 'FIELD_NOT_PRESENT')}")
            print(f"  allowInvitesFrom: {policy.get('allowInvitesFrom', 'FIELD_NOT_PRESENT')}")
            
            # Extract key settings
            default_user_role = policy.get('defaultUserRolePermissions', {})
            guest_user_role = policy.get('guestUserRoleId')
            
            return {
                'success': True,
                'policy': {
                    'id': policy.get('id'),
                    'displayName': policy.get('displayName', 'Authorization Policy'),
                    'description': policy.get('description'),
                    # Default User Permissions
                    'allowedToCreateApps': default_user_role.get('allowedToCreateApps'),
                    'allowedToCreateSecurityGroups': default_user_role.get('allowedToCreateSecurityGroups'),
                    'allowedToCreateTenants': default_user_role.get('allowedToCreateTenants'),
                    'allowedToReadOtherUsers': default_user_role.get('allowedToReadOtherUsers'),
                    'allowedToReadBitlockerKeysForOwnedDevice': default_user_role.get('allowedToReadBitlockerKeysForOwnedDevice'),
                    # Guest & External Collaboration
                    'guestUserRoleId': guest_user_role,
                    'allowInvitesFrom': policy.get('allowInvitesFrom'),
                    'allowEmailVerifiedUsersToJoinOrganization': policy.get('allowEmailVerifiedUsersToJoinOrganization'),
                    'allowedToSignUpEmailBasedSubscriptions': policy.get('allowedToSignUpEmailBasedSubscriptions'),
                    # Security Settings
                    'blockMsolPowerShell': policy.get('blockMsolPowerShell'),
                    # Permissions Grant Policy
                    'permissionGrantPolicyIdsAssignedToDefaultUserRole': policy.get('permissionGrantPolicyIdsAssignedToDefaultUserRole', [])
                }
            }
        
        # Propagate permission_denied flag if present
        if result.get('permission_denied'):
            return {
                'success': False,
                'error': 'Insufficient privileges to read authorization policy',
                'permission_denied': True,
                'error_code': result.get('error_code'),
                'details': result.get('details')
            }
        
        return result
    
    # ==================== CACHE MANAGEMENT ====================
    
    def prefetch_all_entities(self, force=False):
        """Prefetch all entities into cache for faster subsequent lookups"""
        cache = self._get_entity_cache()
        stats = cache.prefetch_all(force=force)
        
        return {
            'success': True,
            'message': f'Prefetched {sum(stats.values())} entities',
            'stats': stats
        }
    
    def get_cache_stats(self):
        """Get cache statistics"""
        cache = self._get_entity_cache()
        return {
            'success': True,
            'stats': cache.get_cache_stats()
        }
    
    def clear_cache(self, entity_type=None):
        """Clear cache for entity type or all"""
        cache = self._get_entity_cache()
        cache.clear_cache(entity_type)
        
        return {
            'success': True,
            'message': f'Cleared cache for {entity_type or "all entities"}'
        }
    
    # ==================== FORMATTERS ====================
    
    def _format_user(self, user):
        return {
            'id': user.get('id'),
            'displayName': user.get('displayName'),
            'userPrincipalName': user.get('userPrincipalName'),
            'mail': user.get('mail'),
            'jobTitle': user.get('jobTitle'),
            'department': user.get('department'),
            'accountEnabled': user.get('accountEnabled', True),
            'userType': user.get('userType', 'Member'),
            'onPremisesSyncEnabled': user.get('onPremisesSyncEnabled', False)
        }
    
    def _format_user_full(self, user):
        formatted = self._format_user(user)
        formatted.update({
            'mobilePhone': user.get('mobilePhone'),
            'officeLocation': user.get('officeLocation'),
            'createdDateTime': user.get('createdDateTime'),
            'lastSignInDateTime': user.get('signInActivity', {}).get('lastSignInDateTime')
        })
        return formatted
    
    def _format_member(self, member):
        """Format a group/role member"""
        member_type = member.get('@odata.type', '').replace('#microsoft.graph.', '')
        
        return {
            'id': member.get('id'),
            'displayName': member.get('displayName'),
            'userPrincipalName': member.get('userPrincipalName'),
            'mail': member.get('mail'),
            'type': member_type
        }
    

    # ==================== PERMISSION ANALYSIS ====================
    
    # Risk scoring for Application Permissions
    CRITICAL_PERMISSIONS = [
        'RoleManagement.ReadWrite.Directory',
        'Application.ReadWrite.All',
        'AppRoleAssignment.ReadWrite.All',
        'Directory.AccessAsUser.All',
        'Domain.ReadWrite.All'
    ]
    
    HIGH_RISK_PERMISSIONS = [
        'Directory.ReadWrite.All',
        'Mail.ReadWrite',
        'Files.ReadWrite.All',
        'Sites.FullControl.All',
        'User.ReadWrite.All',
        'Group.ReadWrite.All',
        'Policy.ReadWrite.ConditionalAccess',
        'PrivilegedAccess.ReadWrite.AzureResources'
    ]
    
    MEDIUM_RISK_PERMISSIONS = [
        'User.Read.All',
        'Group.Read.All',
        'Directory.Read.All',
        'Mail.Read',
        'Files.Read.All',
        'Sites.Read.All',
        'Calendars.ReadWrite'
    ]
    
    def _analyze_sp_permissions(self, sp):
        """
        Analyze Application Permissions for a service principal and calculate risk
        
        Args:
            sp: Service principal object with appRoles or oauth2PermissionGrants
        
        Returns:
            Dict with risk analysis
        """
        # Get app roles (Application Permissions) assigned TO this SP
        sp_id = sp.get('id')
        
        # Fetch appRoleAssignments for this SP
        result = self._make_request(f'servicePrincipals/{sp_id}/appRoleAssignedTo')
        
        if not result['success']:
            return {
                'riskLevel': 'Unknown',
                'riskScore': 0,
                'permissions': [],
                'criticalCount': 0,
                'highCount': 0,
                'mediumCount': 0
            }
        
        assignments = result['data'].get('value', [])
        
        # Resolve permission names
        permission_names = []
        cache = self._get_entity_cache()
        
        for assignment in assignments:
            resource_id = assignment.get('resourceId')
            app_role_id = assignment.get('appRoleId')
            
            # Try to resolve permission name
            # This requires fetching the resource SP to get appRoles
            resource_result = self._make_request(f'servicePrincipals/{resource_id}?$select=appRoles,displayName')
            if resource_result['success']:
                resource_sp = resource_result['data']
                app_roles = resource_sp.get('appRoles', [])
                
                for role in app_roles:
                    if role.get('id') == app_role_id:
                        permission_names.append({
                            'name': role.get('value'),
                            'displayName': role.get('displayName'),
                            'resource': resource_sp.get('displayName', 'Microsoft Graph')
                        })
                        break
        
        # Calculate risk score
        critical_perms = []
        high_perms = []
        medium_perms = []
        
        for perm in permission_names:
            perm_name = perm['name']
            if perm_name in self.CRITICAL_PERMISSIONS:
                critical_perms.append(perm)
            elif perm_name in self.HIGH_RISK_PERMISSIONS:
                high_perms.append(perm)
            elif perm_name in self.MEDIUM_RISK_PERMISSIONS:
                medium_perms.append(perm)
        
        # Calculate overall risk
        risk_score = (len(critical_perms) * 100) + (len(high_perms) * 50) + (len(medium_perms) * 25)
        
        if len(critical_perms) > 0:
            risk_level = 'Critical'
        elif len(high_perms) >= 2:
            risk_level = 'High'
        elif len(high_perms) == 1 or len(medium_perms) >= 3:
            risk_level = 'Medium'
        elif len(medium_perms) > 0:
            risk_level = 'Low'
        else:
            risk_level = 'None'
        
        return {
            'riskLevel': risk_level,
            'riskScore': risk_score,
            'permissions': permission_names,
            'criticalPermissions': critical_perms,
            'highPermissions': high_perms,
            'mediumPermissions': medium_perms,
            'criticalCount': len(critical_perms),
            'highCount': len(high_perms),
            'mediumCount': len(medium_perms),
            'totalCount': len(permission_names)
        }
    
    def get_risky_service_principals(self, min_risk='Medium'):
        """
        Get service principals with risky Application Permissions
                
        Args:
            min_risk: Minimum risk level to include ('Low', 'Medium', 'High', 'Critical')
        
        Returns:
            List of risky SPs with permission analysis
        """
        # Get all service principals
        sp_result = self.get_service_principals(top=999)
        if not sp_result['success']:
            return sp_result
        
        all_sps = sp_result['servicePrincipals']
        
        # Filter out ManagedIdentity type (analyze only normal SPs)
        normal_sps = [sp for sp in all_sps if sp.get('servicePrincipalType') != 'ManagedIdentity']
        
        # Analyze permissions for each SP (this will be slow, consider caching)
        risky_sps = []
        risk_levels = ['Critical', 'High', 'Medium', 'Low']
        min_risk_idx = risk_levels.index(min_risk) if min_risk in risk_levels else 2
        
        for sp in normal_sps[:50]:  # Limit to first 50 to avoid timeout
            risk_analysis = self._analyze_sp_permissions(sp)
            
            # Check if meets minimum risk threshold
            if risk_analysis['riskLevel'] in risk_levels[:min_risk_idx + 1]:
                sp['riskAnalysis'] = risk_analysis
                risky_sps.append(sp)
        
        # Sort by risk score (highest first)
        risky_sps.sort(key=lambda x: x['riskAnalysis']['riskScore'], reverse=True)
        
        return {
            'success': True,
            'riskyServicePrincipals': risky_sps,
            'count': len(risky_sps),
            'analyzed': min(50, len(normal_sps)),
            'total': len(normal_sps)
        }

    def _format_credentials(self, password_creds, key_creds):
        """Format credentials info for SP/App"""
        has_secret = len(password_creds) > 0 if password_creds else False
        has_cert = len(key_creds) > 0 if key_creds else False
        
        # Find earliest expiry among VALID (future) credentials only
        # Ignore already expired credentials unless ALL are expired
        now = datetime.now(timezone.utc)
        earliest_expiry = None
        earliest_valid_expiry = None  # Only future credentials
        
        all_creds = (password_creds or []) + (key_creds or [])
        for cred in all_creds:
            end_date = cred.get('endDateTime')
            if end_date:
                # Track absolute earliest (including expired)
                if not earliest_expiry or end_date < earliest_expiry:
                    earliest_expiry = end_date
                
                # Track earliest VALID (future only)
                try:
                    expiry_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if expiry_date > now:  # Only future credentials
                        if not earliest_valid_expiry or end_date < earliest_valid_expiry:
                            earliest_valid_expiry = end_date
                except:
                    pass
        
        # Use earliest valid credential if available, otherwise use absolute earliest
        display_expiry = earliest_valid_expiry if earliest_valid_expiry else earliest_expiry
        
        # Credential type string
        if has_secret and has_cert:
            cred_type = 'both'
        elif has_secret:
            cred_type = 'secret'
        elif has_cert:
            cred_type = 'certificate'
        else:
            cred_type = 'none'
        
        # Calculate expiry status for UI based on display_expiry
        expiry_status = 'valid'
        if display_expiry:
            try:
                expiry_date = datetime.fromisoformat(display_expiry.replace('Z', '+00:00'))
                now = datetime.now(expiry_date.tzinfo)
                days_until_expiry = (expiry_date - now).days
                
                if days_until_expiry < 0:
                    expiry_status = 'expired'
                elif days_until_expiry < 30:
                    expiry_status = 'expiring_soon'
                elif days_until_expiry < 90:
                    expiry_status = 'expiring'
            except:
                pass
        
        return {
            'hasSecret': has_secret,
            'hasCertificate': has_cert,
            'secretCount': len(password_creds) if password_creds else 0,
            'certificateCount': len(key_creds) if key_creds else 0,
            'credentialType': cred_type,
            'earliestExpiry': display_expiry,
            'expiryStatus': expiry_status
        }
    
    def _format_sp(self, sp, owners=None):
        """Format service principal with credentials and owner"""
        creds = self._format_credentials(
            sp.get('passwordCredentials'),
            sp.get('keyCredentials')
        )
        
        formatted = {
            'id': sp.get('id'),
            'appId': sp.get('appId'),
            'displayName': sp.get('displayName'),
            'appDisplayName': sp.get('appDisplayName'),
            'servicePrincipalType': sp.get('servicePrincipalType'),
            'accountEnabled': sp.get('accountEnabled', True),
            'credentials': creds
        }
        
        # Add owner info if available
        if owners is not None:
            formatted['owner'] = self._format_owner_display(owners)
            formatted['owners'] = owners
        
        return formatted
    
    def _format_managed_identity(self, mi, owners=None):
        """Format managed identity with additional context and owner"""
        creds = self._format_credentials(
            mi.get('passwordCredentials'),
            mi.get('keyCredentials')
        )
        
        # Extract resource info from alternativeNames (contains Azure resource ID)
        alternative_names = mi.get('alternativeNames', [])
        resource_id = alternative_names[0] if alternative_names else None
        
        # Parse resource type from resource ID
        resource_type = 'Unknown'
        if resource_id:
            # Example: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{name}
            parts = resource_id.split('/')
            if 'providers' in parts:
                provider_idx = parts.index('providers')
                if provider_idx + 2 < len(parts):
                    resource_type = parts[provider_idx + 2]  # e.g., "virtualMachines"
        
        formatted = {
            'id': mi.get('id'),
            'appId': mi.get('appId'),
            'displayName': mi.get('displayName'),
            'appDisplayName': mi.get('appDisplayName'),
            'servicePrincipalType': mi.get('servicePrincipalType'),
            'accountEnabled': mi.get('accountEnabled', True),
            'resourceId': resource_id,
            'resourceType': resource_type,
            'credentials': creds
        }
        
        # Add owner info if available
        if owners is not None:
            formatted['owner'] = self._format_owner_display(owners)
            formatted['owners'] = owners
        
        return formatted
    
    def _format_app(self, app, owners=None):
        """Format application with credentials and owner"""
        creds = self._format_credentials(
            app.get('passwordCredentials'),
            app.get('keyCredentials')
        )
        
        formatted = {
            'id': app.get('id'),
            'appId': app.get('appId'),
            'displayName': app.get('displayName'),
            'createdDateTime': app.get('createdDateTime'),
            'publisherDomain': app.get('publisherDomain'),
            'signInAudience': app.get('signInAudience'),
            'credentials': creds
        }
        
        # Add owner info if available
        if owners is not None:
            formatted['owner'] = self._format_owner_display(owners)
            formatted['owners'] = owners
        
        return formatted
    
    def _format_app_full(self, app, owners=None):
        """Format app with full details for owned apps"""
        formatted = self._format_app(app, owners)
        formatted.update({
            'description': app.get('description'),
            'notes': app.get('notes'),
            'web': app.get('web', {}),
            'spa': app.get('spa', {}),
            'publicClient': app.get('publicClient', {})
        })
        return formatted
    
    def _format_device(self, device):
        return {
            'id': device.get('id'),
            'displayName': device.get('displayName'),
            'deviceId': device.get('deviceId'),
            'operatingSystem': device.get('operatingSystem'),
            'operatingSystemVersion': device.get('operatingSystemVersion'),
            'trustType': device.get('trustType'),
            'isCompliant': device.get('isCompliant'),
            'isManaged': device.get('isManaged'),
            'accountEnabled': device.get('accountEnabled'),
            'registrationDateTime': device.get('registrationDateTime'),
            'registeredOwner': None
        }
    
    def _format_group(self, group):
        return {
            'id': group.get('id'),
            'displayName': group.get('displayName'),
            'description': group.get('description'),
            'groupTypes': group.get('groupTypes', []),
            'mail': group.get('mail'),
            'securityEnabled': group.get('securityEnabled', False)
        }
    
    def _format_admin_unit(self, unit):
        return {
            'id': unit.get('id'),
            'displayName': unit.get('displayName'),
            'description': unit.get('description'),
            'isMemberManagementRestricted': unit.get('isMemberManagementRestricted', False),
            'membershipType': unit.get('membershipType', 'Assigned'),
            'membershipRule': unit.get('membershipRule'),
            'membershipRuleProcessingState': unit.get('membershipRuleProcessingState')
        }
    
    def _format_org(self, org):
        return {
            'id': org.get('id'),
            'displayName': org.get('displayName'),
            'tenantType': org.get('tenantType'),
            'verifiedDomains': org.get('verifiedDomains', []),
            'createdDateTime': org.get('createdDateTime')
        }
    
    def _format_domain(self, domain):
        return {
            'id': domain.get('id'),
            'isDefault': domain.get('isDefault', False),
            'isVerified': domain.get('isVerified', False),
            'authenticationType': domain.get('authenticationType')
        }
    
    def _format_role(self, role):
        return {
            'id': role.get('id'),
            'displayName': role.get('displayName'),
            'description': role.get('description'),
            'roleTemplateId': role.get('roleTemplateId')
        }
    
    def resolve_principals_batch(self, principals):
        """
        Resolve multiple principals (Users, ServicePrincipals, Groups) in batch
        
        Args:
            principals: List of dicts [{"id": "guid", "type": "User|ServicePrincipal|Group"}, ...]
        
        Returns:
            Dict mapping principal ID to display name: {"guid": "name", ...}
        """
        result = {}
        
        # Group principals by type for efficient batch queries
        users_ids = [p['id'] for p in principals if p['type'] == 'User']
        sp_ids = [p['id'] for p in principals if p['type'] == 'ServicePrincipal']
        group_ids = [p['id'] for p in principals if p['type'] == 'Group']
        
        # Resolve Users
        for user_id in users_ids:
            try:
                response = self._make_request(f'users/{user_id}?$select=id,userPrincipalName,displayName')
                if response['success']:
                    user = response['data']
                    result[user_id] = user.get('userPrincipalName') or user.get('displayName') or user_id
                else:
                    result[user_id] = user_id[:8] + '...'
            except Exception as e:
                print(f"[RESOLVE] Failed to resolve user {user_id}: {e}")
                result[user_id] = user_id[:8] + '...'
        
        # Resolve Service Principals
        for sp_id in sp_ids:
            try:
                response = self._make_request(f'servicePrincipals/{sp_id}?$select=id,displayName,appDisplayName')
                if response['success']:
                    sp = response['data']
                    result[sp_id] = sp.get('displayName') or sp.get('appDisplayName') or sp_id
                else:
                    result[sp_id] = sp_id[:8] + '...'
            except Exception as e:
                print(f"[RESOLVE] Failed to resolve service principal {sp_id}: {e}")
                result[sp_id] = sp_id[:8] + '...'
        
        # Resolve Groups
        for group_id in group_ids:
            try:
                response = self._make_request(f'groups/{group_id}?$select=id,displayName,mailNickname')
                if response['success']:
                    group = response['data']
                    result[group_id] = group.get('displayName') or group.get('mailNickname') or group_id
                else:
                    result[group_id] = group_id[:8] + '...'
            except Exception as e:
                print(f"[RESOLVE] Failed to resolve group {group_id}: {e}")
                result[group_id] = group_id[:8] + '...'
        
        return result

