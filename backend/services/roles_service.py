"""
Roles & Licenses Service - Directory Roles and License enumeration
Added get_user_roles and get_user_licenses methods
Added complete role enumeration including AU-scoped roles
Added tenant-wide AU-scoped roles enumeration
"""
import requests
import time
from flask import current_app


class RolesService:
    
    # Complete list of privileged role template IDs
    PRIVILEGED_ROLE_TEMPLATES = {
        '62e90394-69f5-4237-9190-012177145e10': 'Global Administrator',
        'e8611ab8-c189-46e8-94e1-60213ab1f814': 'Privileged Role Administrator',
        '7be44c8a-adaf-4e2a-84d6-ab2649e08a13': 'Privileged Authentication Administrator',
        'fe930be7-5e62-47db-91af-98c3a49a38b1': 'User Administrator',
        '729827e3-9c14-49f7-bb1b-9608f156bbb8': 'Helpdesk Administrator',
        '966707d0-3269-4727-9be2-8c3a10f19b9d': 'Password Administrator',
        'c4e39bd9-1100-46d3-8c65-fb160da0071f': 'Authentication Administrator',
        '194ae4cb-b126-40b2-bd5b-6091b380977d': 'Security Administrator',
        '9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3': 'Application Administrator',
        '158c047a-c907-4556-b7ef-446551a6b5f7': 'Cloud Application Administrator',
        'b1be1c3e-b65d-4f19-8427-f6fa0d97feb9': 'Conditional Access Administrator',
        '29232cdf-9323-42fd-ade2-1d097af3e4de': 'Exchange Administrator',
        'f28a1f50-f6e7-4571-818b-6a12f2af6b6c': 'SharePoint Administrator',
        '790c1fb9-7f7d-4f88-86a1-ef1f95c05c1b': 'Teams Administrator',
        '7698a772-787b-4ac8-901f-60d6b08affd2': 'Cloud Device Administrator',
        '3a2c62db-5318-420d-8d74-23affee5d9d5': 'Intune Administrator',
        'fdd7a751-b60b-444a-984c-02652fe8fa1c': 'Groups Administrator',
        '4d6ac14f-3453-41d0-bef9-a3e0c569773a': 'License Administrator',
        '8329153b-31d0-4727-b945-745eb3bc5f31': 'Hybrid Identity Administrator',
        '45d8d3c5-c802-45c6-b32a-1d70b5e1e86e': 'Identity Governance Administrator',
    }
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
    
    def _make_request(self, endpoint, method='GET', **kwargs):
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
                    **kwargs
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"[429 Rate Limit] Waiting {retry_after}s before retry...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code in [200, 201, 202]:
                    return {
                        'success': True,
                        'data': response.json() if response.content else {}
                    }
                else:
                    return {
                        'success': False,
                        'error': f'API returned {response.status_code}',
                        'details': response.text
                    }
                    
            except requests.exceptions.Timeout:
                return {'success': False, 'error': 'Request timeout'}
            except requests.exceptions.RequestException as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Rate limit exceeded'}
    
    def get_user_roles(self, user_id):
        """
        Get directory roles assigned to a specific user
        Includes both tenant-wide roles AND AU-scoped roles
        """
        all_roles = []
        
        # 1. Get tenant-wide roles via memberOf
        result = self._make_request(
            f'users/{user_id}/memberOf/microsoft.graph.directoryRole'
        )
        
        if result['success']:
            roles = result['data'].get('value', [])
            for r in roles:
                all_roles.append(self._format_user_role(r, scope='tenant'))
        
        # 2. Get AU-scoped roles via scopedRoleMemberOf
        scoped_result = self._make_request(
            f'users/{user_id}/scopedRoleMemberOf'
        )
        
        if scoped_result['success']:
            scoped_roles = scoped_result['data'].get('value', [])
            for sr in scoped_roles:
                formatted = self._format_scoped_role(sr)
                if formatted:
                    all_roles.append(formatted)
        
        return {
            'success': True,
            'roles': all_roles,
            'count': len(all_roles)
        }
    
    def get_user_scoped_roles(self, user_id):
        """
        Get ONLY AU-scoped roles for a user
        Uses /users/{id}/scopedRoleMemberOf endpoint
        """
        result = self._make_request(
            f'users/{user_id}/scopedRoleMemberOf'
        )
        
        if result['success']:
            scoped_roles = result['data'].get('value', [])
            formatted_roles = []
            
            for sr in scoped_roles:
                formatted = self._format_scoped_role(sr)
                if formatted:
                    formatted_roles.append(formatted)
            
            return {
                'success': True,
                'scoped_roles': formatted_roles,
                'count': len(formatted_roles)
            }
        
        return result
    
    def _format_scoped_role(self, scoped_role):
        """
        Format a scoped role membership
        The scopedRoleMemberOf returns objects with roleId (directoryRole id) and 
        administrativeUnitId
        """
        role_id = scoped_role.get('roleId')
        au_id = scoped_role.get('administrativeUnitId')
        
        # Get the actual role details to find roleTemplateId
        role_details = self._make_request(f'directoryRoles/{role_id}')
        
        if role_details['success']:
            role_data = role_details['data']
            template_id = role_data.get('roleTemplateId')
            
            # Get AU name
            au_name = None
            if au_id:
                au_details = self._make_request(f'administrativeUnits/{au_id}')
                if au_details['success']:
                    au_name = au_details['data'].get('displayName')
            
            return {
                'id': role_id,
                'displayName': role_data.get('displayName'),
                'description': role_data.get('description'),
                'roleTemplateId': template_id,
                'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES,
                'scope': 'administrative_unit',
                'administrativeUnitId': au_id,
                'administrativeUnitName': au_name or au_id
            }
        
        return None
    
    # ============================================================
    # NEW: Tenant-wide AU-Scoped Roles Enumeration
    # ============================================================
    
    def get_all_au_scoped_roles(self):
        """
        Enumerate ALL AU-scoped role assignments in the tenant.
        Iterates through all Administrative Units and collects their scopedRoleMembers.
        Uses v1.0 → beta fallback for compatibility.
        
        Returns:
            - List of all AU-scoped role assignments with user/AU/role details
            - Grouped by Administrative Unit
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Step 1: Get all Administrative Units with v1.0 → beta fallback
        admin_units = []
        api_version = 'v1.0'
        
        # Try v1.0 first
        v1_url = f'{self.base_url}/administrativeUnits'
        try:
            response = requests.get(v1_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                admin_units = response.json().get('value', [])
            elif response.status_code in [400, 404]:
                # Fallback to beta
                beta_url = 'https://graph.microsoft.com/beta/administrativeUnits'
                beta_response = requests.get(beta_url, headers=headers, timeout=self.timeout)
                
                if beta_response.status_code == 200:
                    admin_units = beta_response.json().get('value', [])
                    api_version = 'beta'
                else:
                    return {
                        'success': False,
                        'error': f'Both v1.0 and beta failed for administrativeUnits',
                        'details': beta_response.text[:500]
                    }
            else:
                return {
                    'success': False,
                    'error': f'Failed to get Administrative Units: {response.status_code}',
                    'details': response.text[:500]
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception calling API: {str(e)}'
            }
        
        if not admin_units:
            return {
                'success': True,
                'au_scoped_roles': [],
                'administrative_units': [],
                'total_assignments': 0,
                'message': 'No Administrative Units found in tenant'
            }
        
        # Build a cache for role template lookups
        role_cache = {}
        
        # Step 2: For each AU, get scoped role members
        all_assignments = []
        au_details = []
        
        for au in admin_units:
            au_id = au.get('id')
            au_name = au.get('displayName', 'Unknown AU')
            au_desc = au.get('description', '')
            
            # Get scoped role members for this AU using the same API version that worked
            if api_version == 'beta':
                scoped_url = f'https://graph.microsoft.com/beta/administrativeUnits/{au_id}/scopedRoleMembers'
            else:
                scoped_url = f'{self.base_url}/administrativeUnits/{au_id}/scopedRoleMembers'
            
            try:
                members_response = requests.get(scoped_url, headers=headers, timeout=self.timeout)
                
                # If v1.0 fails, try beta
                if members_response.status_code in [400, 404] and api_version == 'v1.0':
                    scoped_url = f'https://graph.microsoft.com/beta/administrativeUnits/{au_id}/scopedRoleMembers'
                    members_response = requests.get(scoped_url, headers=headers, timeout=self.timeout)
                
                if members_response.status_code == 200:
                    scoped_members = members_response.json().get('value', [])
                else:
                    scoped_members = []
            except Exception as e:
                scoped_members = []
            
            au_assignments = []
            
            for sm in scoped_members:
                assignment = self._format_au_scoped_assignment(sm, au_id, au_name, role_cache)
                if assignment:
                    au_assignments.append(assignment)
                    all_assignments.append(assignment)
            
            au_details.append({
                'id': au_id,
                'displayName': au_name,
                'description': au_desc,
                'scopedRoleCount': len(au_assignments),
                'assignments': au_assignments
            })
        
        # Sort: AUs with most assignments first
        au_details.sort(key=lambda x: -x['scopedRoleCount'])
        
        # Group all assignments by role for summary
        role_summary = {}
        for assignment in all_assignments:
            role_name = assignment['roleName']
            if role_name not in role_summary:
                role_summary[role_name] = {
                    'roleName': role_name,
                    'roleTemplateId': assignment['roleTemplateId'],
                    'isPrivileged': assignment['isPrivileged'],
                    'count': 0,
                    'users': []
                }
            role_summary[role_name]['count'] += 1
            role_summary[role_name]['users'].append({
                'displayName': assignment['userDisplayName'],
                'userPrincipalName': assignment['userPrincipalName'],
                'auName': assignment['administrativeUnitName']
            })
        
        role_summary_list = sorted(role_summary.values(), key=lambda x: -x['count'])
        
        return {
            'success': True,
            'administrative_units': au_details,
            'au_scoped_roles': all_assignments,
            'role_summary': role_summary_list,
            'total_aus': len(admin_units),
            'total_assignments': len(all_assignments),
            'aus_with_assignments': len([au for au in au_details if au['scopedRoleCount'] > 0]),
            'api_version': api_version
        }
    
    def _format_au_scoped_assignment(self, scoped_member, au_id, au_name, role_cache):
        """
        Format a scoped role member from an AU's scopedRoleMembers endpoint.
        
        The scopedRoleMembers endpoint returns:
        {
            "id": "assignment-id",
            "roleId": "directory-role-id",
            "roleMemberInfo": {
                "id": "user-id",
                "displayName": "User Name" (may not be present)
            }
        }
        """
        role_id = scoped_member.get('roleId')
        member_info = scoped_member.get('roleMemberInfo', {})
        
        if not role_id:
            return None
        
        # Get role details (with caching to avoid repeated calls)
        if role_id not in role_cache:
            role_result = self._make_request(f'directoryRoles/{role_id}')
            if role_result['success']:
                role_cache[role_id] = role_result['data']
            else:
                role_cache[role_id] = None
        
        role_data = role_cache.get(role_id)
        
        if not role_data:
            return None
        
        template_id = role_data.get('roleTemplateId')
        
        # Get user ID from roleMemberInfo
        user_id = member_info.get('id')
        user_display_name = member_info.get('displayName')
        user_upn = member_info.get('userPrincipalName')
        
        # Always fetch full user details since roleMemberInfo is often incomplete
        if user_id:
            user_result = self._make_request(f'users/{user_id}')
            if user_result['success']:
                user_data = user_result['data']
                user_display_name = user_data.get('displayName', user_display_name or 'Unknown')
                user_upn = user_data.get('userPrincipalName', user_upn or 'Unknown')
        
        return {
            'assignmentId': scoped_member.get('id'),
            'roleId': role_id,
            'roleName': role_data.get('displayName'),
            'roleTemplateId': template_id,
            'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES,
            'userId': user_id,
            'userDisplayName': user_display_name or 'Unknown',
            'userPrincipalName': user_upn or 'Unknown',
            'administrativeUnitId': au_id,
            'administrativeUnitName': au_name,
            'scope': 'administrative_unit'
        }
    
    # ============================================================
    # Existing methods below (unchanged)
    # ============================================================
    
    def get_user_licenses(self, user_id):
        """Get licenses assigned to a specific user"""
        result = self._make_request(
            f'users/{user_id}?$select=id,displayName,assignedLicenses,licenseAssignmentStates'
        )
        
        if not result['success']:
            return result
        
        user_data = result['data']
        assigned_licenses = user_data.get('assignedLicenses', [])
        
        if not assigned_licenses:
            return {
                'success': True,
                'licenses': [],
                'count': 0
            }
        
        # Get SKU details to map skuId to friendly names
        skus_result = self._make_request('subscribedSkus')
        sku_map = {}
        if skus_result['success']:
            for sku in skus_result['data'].get('value', []):
                sku_map[sku.get('skuId')] = {
                    'skuPartNumber': sku.get('skuPartNumber'),
                    'displayName': self._get_license_name(sku.get('skuPartNumber', ''))
                }
        
        licenses = []
        for lic in assigned_licenses:
            sku_id = lic.get('skuId')
            sku_info = sku_map.get(sku_id, {})
            licenses.append({
                'skuId': sku_id,
                'skuPartNumber': sku_info.get('skuPartNumber', 'Unknown'),
                'displayName': sku_info.get('displayName', 'Unknown License')
            })
        
        return {
            'success': True,
            'licenses': licenses,
            'count': len(licenses)
        }
    
    def get_user_info_with_roles_licenses(self, user_id):
        """Get complete user info with roles (including AU-scoped) and licenses"""
        roles_result = self.get_user_roles(user_id)
        licenses_result = self.get_user_licenses(user_id)
        
        return {
            'success': True,
            'roles': roles_result.get('roles', []) if roles_result['success'] else [],
            'roles_count': roles_result.get('count', 0) if roles_result['success'] else 0,
            'licenses': licenses_result.get('licenses', []) if licenses_result['success'] else [],
            'licenses_count': licenses_result.get('count', 0) if licenses_result['success'] else 0,
            'roles_error': roles_result.get('error') if not roles_result['success'] else None,
            'licenses_error': licenses_result.get('error') if not licenses_result['success'] else None
        }
    
    def get_directory_roles(self):
        """
        Get all directory roles that have been activated in the tenant
        Note: This only returns roles that have been "activated" (assigned to at least one user)
        """
        # $select optimized: role fields + member fields in $expand
        select = 'id,displayName,description,roleTemplateId'
        expand = 'members($select=id,displayName,userPrincipalName,accountEnabled)'
        result = self._make_request(f'directoryRoles?$select={select}&$expand={expand}')
        
        if result['success']:
            roles = result['data'].get('value', [])
            return {
                'success': True,
                'roles': [self._format_role(r) for r in roles],
                'count': len(roles),
                'note': 'Only shows activated roles (roles with at least one assignment in history)'
            }
        
        return result
    
    def get_all_role_templates(self):
        """
        Get all available directory role templates (not just activated ones)
        This returns ALL roles available in Azure AD, regardless of activation status
        """
        result = self._make_request('directoryRoleTemplates')
        
        if result['success']:
            templates = result['data'].get('value', [])
            return {
                'success': True,
                'templates': [self._format_role_template(t) for t in templates],
                'count': len(templates)
            }
        
        return result
    
    def get_directory_roles_with_all_members(self):
        """
        Get all activated directory roles with their members
        This is the comprehensive view for the Roles tab
        """
        # First get activated roles - $select optimized
        select = 'id,displayName,description,roleTemplateId'
        expand = 'members($select=id,displayName,userPrincipalName,accountEnabled)'
        result = self._make_request(f'directoryRoles?$select={select}&$expand={expand}')
        
        if not result['success']:
            return result
        
        roles = result['data'].get('value', [])
        formatted_roles = []
        
        for role in roles:
            template_id = role.get('roleTemplateId')
            members = role.get('members', [])
            
            formatted_roles.append({
                'id': role.get('id'),
                'displayName': role.get('displayName'),
                'description': role.get('description'),
                'roleTemplateId': template_id,
                'memberCount': len(members),
                'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES,
                'members': [self._format_member(m) for m in members]
            })
        
        # Sort by member count descending, then by name
        formatted_roles.sort(key=lambda x: (-x['memberCount'], x['displayName']))
        
        return {
            'success': True,
            'roles': formatted_roles,
            'count': len(formatted_roles),
            'total_assignments': sum(r['memberCount'] for r in formatted_roles)
        }
    
    def get_role_members(self, role_id):
        """Get members of a specific directory role"""
        result = self._make_request(f'directoryRoles/{role_id}/members')
        
        if result['success']:
            members = result['data'].get('value', [])
            return {
                'success': True,
                'members': [self._format_member(m) for m in members],
                'count': len(members)
            }
        
        return result
    
    def get_subscribed_skus(self):
        """Get all subscribed SKUs (licenses)"""
        # $select optimized: only fields used in _format_license
        select = 'id,skuId,skuPartNumber,prepaidUnits,consumedUnits,capabilityStatus'
        result = self._make_request(f'subscribedSkus?$select={select}')
        
        if result['success']:
            skus = result['data'].get('value', [])
            return {
                'success': True,
                'licenses': [self._format_license(s) for s in skus],
                'count': len(skus)
            }
        
        return result
    
    def get_license_users(self, sku_id):
        """Get users assigned to a specific license"""
        result = self._make_request(
            f"users?$filter=assignedLicenses/any(l:l/skuId eq {sku_id})&$select=id,displayName,userPrincipalName,accountEnabled"
        )
        
        if result['success']:
            users = result['data'].get('value', [])
            return {
                'success': True,
                'users': [self._format_user(u) for u in users],
                'count': len(users)
            }
        
        return result
    
    def get_privileged_roles(self):
        """Get privileged roles with their members (security-critical roles)"""
        # $select optimized
        select = 'id,displayName,description,roleTemplateId'
        expand = 'members($select=id,displayName,userPrincipalName,accountEnabled)'
        result = self._make_request(f'directoryRoles?$select={select}&$expand={expand}')
        
        if not result['success']:
            return result
        
        roles = result['data'].get('value', [])
        privileged = []
        
        for role in roles:
            template_id = role.get('roleTemplateId')
            if template_id in self.PRIVILEGED_ROLE_TEMPLATES:
                members = role.get('members', [])
                privileged.append({
                    'roleId': role.get('id'),
                    'roleTemplateId': template_id,
                    'displayName': role.get('displayName'),
                    'description': role.get('description'),
                    'memberCount': len(members),
                    'members': [self._format_member(m) for m in members]
                })
        
        privileged.sort(key=lambda x: x['memberCount'], reverse=True)
        
        return {
            'success': True,
            'privileged_roles': privileged,
            'total_privileged_users': sum(r['memberCount'] for r in privileged)
        }
    
    def get_security_summary(self):
        """Get security summary with findings and recommendations"""
        priv_result = self.get_privileged_roles()
        if not priv_result['success']:
            return priv_result
        
        lic_result = self.get_subscribed_skus()
        
        findings = []
        
        for role in priv_result.get('privileged_roles', []):
            if role['displayName'] == 'Global Administrator' and role['memberCount'] > 5:
                findings.append({
                    'severity': 'high',
                    'finding': f"Too many Global Administrators ({role['memberCount']} users)",
                    'recommendation': 'Reduce to maximum 2-4 Global Admins and use PIM for just-in-time access'
                })
            
            if role['memberCount'] > 0:
                disabled = [m for m in role['members'] if not m.get('accountEnabled', True)]
                if disabled:
                    findings.append({
                        'severity': 'medium',
                        'finding': f"Disabled accounts in {role['displayName']} role",
                        'recommendation': 'Remove disabled accounts from privileged roles'
                    })
        
        if lic_result.get('success'):
            for lic in lic_result.get('licenses', []):
                if lic.get('usagePercent', 0) > 95:
                    findings.append({
                        'severity': 'medium',
                        'finding': f"License {lic['displayName']} at {lic['usagePercent']}% capacity",
                        'recommendation': 'Consider purchasing additional licenses'
                    })
        
        return {
            'success': True,
            'total_privileged_users': priv_result.get('total_privileged_users', 0),
            'privileged_roles': priv_result.get('privileged_roles', []),
            'licenses': lic_result.get('licenses', []) if lic_result.get('success') else [],
            'security_findings': findings
        }
    
    def _format_role(self, role):
        members = role.get('members', [])
        template_id = role.get('roleTemplateId')
        return {
            'id': role.get('id'),
            'displayName': role.get('displayName'),
            'description': role.get('description'),
            'roleTemplateId': template_id,
            'memberCount': len(members),
            'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES
        }
    
    def _format_role_template(self, template):
        """Format a directory role template"""
        template_id = template.get('id')
        return {
            'id': template_id,
            'displayName': template.get('displayName'),
            'description': template.get('description'),
            'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES
        }
    
    def _format_user_role(self, role, scope='tenant'):
        """Format role for user-specific query (no members)"""
        template_id = role.get('roleTemplateId')
        return {
            'id': role.get('id'),
            'displayName': role.get('displayName'),
            'description': role.get('description'),
            'roleTemplateId': template_id,
            'isPrivileged': template_id in self.PRIVILEGED_ROLE_TEMPLATES,
            'scope': scope
        }
    
    def _format_member(self, member):
        member_type = member.get('@odata.type', '').replace('#microsoft.graph.', '')
        return {
            'id': member.get('id'),
            'displayName': member.get('displayName'),
            'userPrincipalName': member.get('userPrincipalName'),
            'accountEnabled': member.get('accountEnabled', True),
            'memberType': member_type
        }
    
    def _format_license(self, sku):
        prepaid = sku.get('prepaidUnits', {})
        enabled = prepaid.get('enabled', 0)
        consumed = sku.get('consumedUnits', 0)
        available = enabled - consumed
        usage_percent = round((consumed / enabled * 100) if enabled > 0 else 0, 1)
        
        return {
            'id': sku.get('id'),
            'skuId': sku.get('skuId'),
            'skuPartNumber': sku.get('skuPartNumber'),
            'displayName': self._get_license_name(sku.get('skuPartNumber', '')),
            'prepaidUnits': prepaid,
            'consumedUnits': consumed,
            'availableUnits': available,
            'usagePercent': usage_percent,
            'capabilityStatus': sku.get('capabilityStatus')
        }
    
    def _format_user(self, user):
        return {
            'id': user.get('id'),
            'displayName': user.get('displayName'),
            'userPrincipalName': user.get('userPrincipalName'),
            'accountEnabled': user.get('accountEnabled', True)
        }
    
    def _get_license_name(self, sku_part):
        """Map SKU part numbers to friendly names"""
        license_names = {
            'ENTERPRISEPACK': 'Office 365 E3',
            'ENTERPRISEPREMIUM': 'Office 365 E5',
            'SPE_E3': 'Microsoft 365 E3',
            'SPE_E5': 'Microsoft 365 E5',
            'SPB': 'Microsoft 365 Business Premium',
            'O365_BUSINESS_ESSENTIALS': 'Microsoft 365 Business Basic',
            'O365_BUSINESS_PREMIUM': 'Microsoft 365 Business Standard',
            'EXCHANGESTANDARD': 'Exchange Online Plan 1',
            'EXCHANGEENTERPRISE': 'Exchange Online Plan 2',
            'EMS': 'Enterprise Mobility + Security E3',
            'EMSPREMIUM': 'Enterprise Mobility + Security E5',
            'AAD_PREMIUM': 'Azure AD Premium P1',
            'AAD_PREMIUM_P2': 'Azure AD Premium P2',
            'POWER_BI_PRO': 'Power BI Pro',
            'POWER_BI_STANDARD': 'Power BI Free',
            'PROJECTPROFESSIONAL': 'Project Plan 3',
            'VISIOCLIENT': 'Visio Plan 2',
            'TEAMS_EXPLORATORY': 'Teams Exploratory',
            'FLOW_FREE': 'Power Automate Free',
            'POWERAPPS_VIRAL': 'Power Apps Plan 2 Trial',
        }
        return license_names.get(sku_part, sku_part)
