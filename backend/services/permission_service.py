"""
Permission Service - Analyze JWT tokens to detect available permissions
Extracts roles, scopes, and determines what admin actions are available
Complete Azure AD role mapping from Microsoft docs
"""
import json
import base64
from datetime import datetime


class PermissionService:
    """Service for analyzing JWT tokens and determining available permissions"""
    
    # Complete Directory Role GUIDs → Human readable names
    # Source: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference
    DIRECTORY_ROLES = {
        # Global/Privileged Roles
        '62e90394-69f5-4237-9190-012177145e10': 'Global Administrator',
        'e8611ab8-c189-46e8-94e1-60213ab1f814': 'Privileged Role Administrator',
        '7be44c8a-adaf-4e2a-84d6-ab2649e08a13': 'Privileged Authentication Administrator',
        
        # User Management
        'fe930be7-5e62-47db-91af-98c3a49a38b1': 'User Administrator',
        '729827e3-9c14-49f7-bb1b-9608f156bbb8': 'Helpdesk Administrator',
        '966707d0-3269-4727-9be2-8c3a10f19b9d': 'Password Administrator',
        '88d8e3e3-8f55-4a1e-953a-9b9898b8876b': 'Directory Readers',
        'd29b2b05-8046-44ba-8758-1e26182fcf32': 'Directory Writers',
        'fdd7a751-b60b-444a-984c-02652fe8fa1c': 'Groups Administrator',
        '45d8d3c5-c802-45c6-b32a-1d70b5e1e86e': 'Identity Governance Administrator',
        
        # Authentication
        'c4e39bd9-1100-46d3-8c65-fb160da0071f': 'Authentication Administrator',
        '0526716b-113d-4c15-b2c8-68e3c22b9f80': 'Authentication Policy Administrator',
        'b0f54661-2d74-4c50-afa3-1ec803f12efe': 'Billing Administrator',
        
        # Security
        '194ae4cb-b126-40b2-bd5b-6091b380977d': 'Security Administrator',
        '5d6b6bb7-de71-4623-b4af-96380a352509': 'Security Reader',
        '17315797-102d-40b4-93e0-432062caca18': 'Compliance Administrator',
        'd37c8bed-0711-4417-ba38-b4abe66ce4c2': 'Network Administrator',
        '3edaf663-341e-4475-9f94-5c398ef6c070': 'Security Operator',
        '892c5842-a9a6-463a-8041-72aa08ca3cf6': 'Cloud App Security Administrator',
        'c430b396-e693-46cc-96f3-db01bf8bb62a': 'Attack Simulation Administrator',
        '9c6df0f2-1e7c-4dc3-b195-66dfbd24aa8f': 'Attack Payload Author',
        
        # Application Management
        '9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3': 'Application Administrator',
        '158c047a-c907-4556-b7ef-446551a6b5f7': 'Cloud Application Administrator',
        'cf1c38e5-3621-4004-a7cb-879624dced7c': 'Application Developer',
        
        # Conditional Access
        'b1be1c3e-b65d-4f19-8427-f6fa0d97feb9': 'Conditional Access Administrator',
        
        # Exchange & Communication
        '29232cdf-9323-42fd-ade2-1d097af3e4de': 'Exchange Administrator',
        '31392ffb-586c-42d1-9346-e59415a2cc4e': 'Exchange Recipient Administrator',
        '2b745bdf-0803-4d80-aa65-822c4493daac': 'Office Apps Administrator',
        
        # SharePoint & Teams
        'f28a1f50-f6e7-4571-818b-6a12f2af6b6c': 'SharePoint Administrator',
        '790c1fb9-7f7d-4f88-86a1-ef1f95c05c1b': 'Teams Administrator',
        '69091246-20e8-4a56-aa4d-066075b2a7a8': 'Teams Communications Administrator',
        'baf37b3a-610e-45da-9e62-d9d1e5e8914b': 'Teams Communications Support Engineer',
        'f70938a0-fc10-4177-9e90-2178f8765737': 'Teams Communications Support Specialist',
        'aa38014f-0993-46e9-9b45-30501a20909d': 'Teams Devices Administrator',
        
        # Device Management
        '7698a772-787b-4ac8-901f-60d6b08affd2': 'Cloud Device Administrator',
        '9f06204d-73c1-4d4c-880a-6edb90606fd8': 'Azure AD Joined Device Local Administrator',
        '3a2c62db-5318-420d-8d74-23affee5d9d5': 'Intune Administrator',
        '38a96431-2bdf-4b4c-8b6e-5d3d8abac1a4': 'Desktop Analytics Administrator',
        '644ef478-e28f-4e28-b9dc-3fdde9aa0b1f': 'Printer Administrator',
        'e8cef6f1-e4bd-4ea8-bc07-4b8d950f4477': 'Printer Technician',
        
        # License Management
        '4d6ac14f-3453-41d0-bef9-a3e0c569773a': 'License Administrator',
        
        # Service Support
        'f023fd81-a637-4b56-95fd-791ac0226033': 'Service Support Administrator',
        'ac16e43d-7b2d-40e0-ac05-243ff356ab5b': 'Message Center Privacy Reader',
        '75934031-6c7e-415a-99d7-48dbd49e875e': 'Message Center Reader',
        
        # Azure & Hybrid
        '7495fdc4-34c4-4d15-a289-98788ce399fd': 'Azure DevOps Administrator',
        '8329153b-31d0-4727-b945-745eb3bc5f31': 'Hybrid Identity Administrator',
        '74ef975b-6605-40af-a5d2-b9539d836353': 'Azure Information Protection Administrator',
        
        # Dynamics & Power Platform
        '44367163-eba1-44c3-98af-f5787879f96a': 'Dynamics 365 Administrator',
        '11648597-926c-4cf3-9c36-bcebb0ba8dcc': 'Power Platform Administrator',
        
        # Search
        '0964bb5e-9bdb-4d7b-ac29-58e794862a40': 'Search Administrator',
        '8835291a-918c-4fd7-a9ce-faa49f0cf7d9': 'Search Editor',
        
        # External Identity
        '31e939ad-9672-4796-9c2e-873181342d2d': 'External Identity Provider Administrator',
        '6e591065-9bad-43ed-90f3-e9424366d2f0': 'External ID User Flow Administrator',
        'a9ea8996-122f-4c74-9520-8edcd192826c': 'B2C IEF Keyset Administrator',
        'aaf43236-0c0d-4d5f-883a-6955382ac081': 'B2C IEF Policy Administrator',
        'be2f45a1-457d-42af-a067-6ec1fa63bc45': 'External ID User Flow Attribute Administrator',
        
        # Other Services
        '74c39d2f-5b14-4015-8b95-c2c0f9c69cd1': 'Kaizala Administrator',
        'b5a8dcf3-09d5-43a9-a639-8e29ef291470': 'Knowledge Administrator',
        '744ec460-397e-42ad-a462-8b3f9747a02c': 'Knowledge Manager',
        '507f53e4-4e52-4077-abd3-d2e1558b6ea2': 'Attribute Assignment Reader',
        '58a13ea3-c632-46ae-9ee0-9c0d43cd7f3d': 'Attribute Definition Reader',
        'ffd52fa5-98dc-465c-991d-fc073eb59f8f': 'Attribute Assignment Administrator',
        '8424c6f0-a189-499e-bbd0-26c1753c96d4': 'Attribute Definition Administrator',
        
        # Reports
        '4a5d8f65-41da-4de4-8968-e035b65339cf': 'Reports Reader',
        
        # Insights
        'eb1f4a8d-243a-41f0-9fbd-c7cdf6c5ef7c': 'Insights Administrator',
        '25df335f-86eb-4119-b717-0ff02de207e9': 'Insights Analyst',
        '31e939ad-9672-4796-9c2e-873181342d2d': 'Insights Business Leader',
        
        # Windows Update
        '0f971eea-41eb-4569-a71e-57bb8a3eff1e': 'Windows Update Deployment Administrator',
        
        # Virtual Visits
        'e300d9e7-4a2b-4295-9eff-f1c78b36cc98': 'Virtual Visits Administrator',
        
        # Viva
        'd45c9c31-79b7-481e-a3f5-e3faebd6ce1d': 'Viva Goals Administrator',
        'f6fb98da-4598-4e25-bc1a-9c4e0ff3de76': 'Viva Pulse Administrator',
        
        # Edge
        '3f1acade-1e04-4fbc-9b69-f0302cd84aef': 'Edge Administrator',
        
        # Yammer
        '810a2642-a034-447f-a5e8-41beaa378541': 'Yammer Administrator',
        
        # Guest/Member
        '10dae51f-b6af-4016-8d66-8c2a99b929b3': 'Guest User',
        'a0b1b346-4d3e-4e8b-98f8-753987be4970': 'Guest Inviter',
        
        # Fabric
        'a9ea8996-122f-4c74-9520-8edcd192826c': 'Fabric Administrator',
        
        # Domain
        '8ac3fc64-6eca-42ea-9e69-59f4c7b60eb2': 'Domain Name Administrator',
        
        # Lifecycle Workflows
        '5b5d5c39-8b9c-4802-8506-e8f62f0f3e50': 'Lifecycle Workflows Administrator',
        
        # Permissions Management
        'af78dc32-cf4d-46f9-ba4e-4428526346b5': 'Permissions Management Administrator',
        
        # Organizational Messages
        '9c6df0f2-1e7c-4dc3-b195-66dfbd24aa8f': 'Organizational Messages Writer',
    }
    
    # Privileged roles that can perform sensitive operations
    PRIVILEGED_ROLE_NAMES = {
        'Global Administrator',
        'Privileged Role Administrator',
        'Privileged Authentication Administrator',
        'User Administrator',
        'Helpdesk Administrator',  # Added!
        'Password Administrator',
        'Authentication Administrator',
        'Security Administrator',
        'Exchange Administrator',
        'SharePoint Administrator',
        'Application Administrator',
        'Cloud Application Administrator',
        'Conditional Access Administrator',
        'Intune Administrator',
        'Cloud Device Administrator',
        'Hybrid Identity Administrator',
        'Groups Administrator',
        'License Administrator',
        'Teams Administrator',
        'Identity Governance Administrator',
    }
    
    # Admin actions and their requirements
    ADMIN_ACTIONS = {
        'create_user': {
            'name': 'Create User',
            'description': 'Create new users in the directory',
            'required_roles': [
                'Global Administrator',
                'User Administrator'
            ],
            'required_scopes': ['User.ReadWrite.All'],
            'risk_level': 'high'
        },
        'reset_password': {
            'name': 'Reset Password',
            'description': 'Reset user passwords',
            'required_roles': [
                'Global Administrator',
                'User Administrator', 
                'Password Administrator',
                'Helpdesk Administrator',  # Added!
                'Authentication Administrator',
                'Privileged Authentication Administrator'
            ],
            'required_scopes': ['UserAuthenticationMethod.ReadWrite.All', 'User.ReadWrite.All'],
            'risk_level': 'high',
            'notes': 'Cannot reset passwords for users with higher privilege roles'
        },
        'manage_tap': {
            'name': 'Manage TAP',
            'description': 'Create/manage Temporary Access Pass',
            'required_roles': [
                'Global Administrator',
                'Authentication Administrator',
                'Privileged Authentication Administrator'
            ],
            'required_scopes': ['UserAuthenticationMethod.ReadWrite.All'],
            'risk_level': 'high'
        },
        'manage_mfa': {
            'name': 'Manage MFA',
            'description': 'View/manage user MFA methods',
            'required_roles': [
                'Global Administrator',
                'Authentication Administrator',
                'Privileged Authentication Administrator'
            ],
            'required_scopes': ['UserAuthenticationMethod.ReadWrite.All'],
            'risk_level': 'high'
        },
        'manage_groups': {
            'name': 'Manage Groups',
            'description': 'Create/modify groups',
            'required_roles': [
                'Global Administrator',
                'User Administrator',
                'Groups Administrator'
            ],
            'required_scopes': ['Group.ReadWrite.All'],
            'risk_level': 'medium'
        },
        'manage_applications': {
            'name': 'Manage Applications',
            'description': 'Create/modify app registrations',
            'required_roles': [
                'Global Administrator',
                'Application Administrator',
                'Cloud Application Administrator'
            ],
            'required_scopes': ['Application.ReadWrite.All'],
            'risk_level': 'medium',
            'notes': 'Standard users can also create apps if policy allows'
        },
        'assign_licenses': {
            'name': 'Assign Licenses',
            'description': 'Assign/remove user licenses',
            'required_roles': [
                'Global Administrator',
                'User Administrator',
                'License Administrator'
            ],
            'required_scopes': ['User.ReadWrite.All', 'Directory.ReadWrite.All'],
            'risk_level': 'medium'
        },
        'manage_roles': {
            'name': 'Manage Directory Roles',
            'description': 'Assign/remove directory roles',
            'required_roles': [
                'Global Administrator',
                'Privileged Role Administrator'
            ],
            'required_scopes': ['RoleManagement.ReadWrite.Directory'],
            'risk_level': 'critical'
        },
        'manage_conditional_access': {
            'name': 'Manage Conditional Access',
            'description': 'Create/modify CA policies',
            'required_roles': [
                'Global Administrator',
                'Conditional Access Administrator',
                'Security Administrator'
            ],
            'required_scopes': ['Policy.ReadWrite.ConditionalAccess'],
            'risk_level': 'critical'
        },
        'manage_devices': {
            'name': 'Manage Devices',
            'description': 'Manage Azure AD joined devices',
            'required_roles': [
                'Global Administrator',
                'Cloud Device Administrator',
                'Intune Administrator'
            ],
            'required_scopes': ['Device.ReadWrite.All'],
            'risk_level': 'medium'
        }
    }
    
    @staticmethod
    def decode_jwt(token):
        """
        Decode JWT token and extract all claims
        Returns dict with all claims or None if invalid
        """
        if not token:
            return None
        
        try:
            parts = token.split('.')
            if len(parts) < 2:
                return None
            
            # Decode payload (part 1)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data
            
        except Exception as e:
            print(f"[!] JWT decode error: {e}")
            return None
    
    @staticmethod
    def extract_permissions(access_token):
        """
        Extract all permission-related claims from access token
        Returns structured permission data
        """
        claims = PermissionService.decode_jwt(access_token)
        
        if not claims:
            return {
                'success': False,
                'error': 'Failed to decode token'
            }
        
        # Extract key claims
        result = {
            'success': True,
            'token_info': {
                'upn': claims.get('upn') or claims.get('unique_name'),
                'name': claims.get('name'),
                'oid': claims.get('oid'),  # Object ID
                'tid': claims.get('tid'),  # Tenant ID
                'aud': claims.get('aud'),  # Audience
                'app_displayname': claims.get('app_displayname'),
                'appid': claims.get('appid'),
                'iat': claims.get('iat'),  # Issued at
                'exp': claims.get('exp'),  # Expires
                'ipaddr': claims.get('ipaddr'),  # IP address
            },
            'directory_roles': [],
            'directory_role_ids': [],
            'app_roles': [],
            'scopes': [],
            'raw_claims': {}
        }
        
        # Extract Directory Roles (wids claim)
        wids = claims.get('wids', [])
        if isinstance(wids, str):
            wids = [wids]
        
        result['directory_role_ids'] = wids
        for wid in wids:
            role_name = PermissionService.DIRECTORY_ROLES.get(wid, f'Unknown Role ({wid})')
            if role_name not in result['directory_roles']:
                result['directory_roles'].append(role_name)
        
        # Extract App Roles (roles claim) - for application permissions
        roles = claims.get('roles', [])
        if isinstance(roles, str):
            roles = [roles]
        result['app_roles'] = roles
        
        # Extract Scopes (scp claim) - for delegated permissions
        scp = claims.get('scp', '')
        if isinstance(scp, str):
            result['scopes'] = [s.strip() for s in scp.split(' ') if s.strip()]
        elif isinstance(scp, list):
            result['scopes'] = scp
        
        # Store some raw claims for debugging
        result['raw_claims'] = {
            'wids': wids,
            'roles': roles,
            'scp': scp,
            'amr': claims.get('amr', []),  # Authentication methods
            'acr': claims.get('acr'),  # Authentication context class
            'auth_time': claims.get('auth_time'),
        }
        
        return result
    
    @staticmethod
    def analyze_admin_capabilities(access_token):
        """
        Analyze token and determine which admin actions are available
        Returns detailed capability analysis
        """
        permissions = PermissionService.extract_permissions(access_token)
        
        if not permissions.get('success'):
            return permissions
        
        user_roles = set(permissions['directory_roles'])
        user_scopes = set(permissions['scopes'])
        user_app_roles = set(permissions['app_roles'])
        
        # Combine scopes and app_roles for permission checking
        all_permissions = user_scopes | user_app_roles
        
        capabilities = {}
        
        for action_id, action_config in PermissionService.ADMIN_ACTIONS.items():
            # Check if user has any required role
            required_roles = set(action_config['required_roles'])
            has_role = bool(user_roles & required_roles)
            matching_roles = list(user_roles & required_roles)
            
            # Check if user has any required scope
            required_scopes = set(action_config['required_scopes'])
            has_scope = bool(all_permissions & required_scopes)
            matching_scopes = list(all_permissions & required_scopes)
            
            # Determine if action is available
            # PRIORITY 1: If user has required ROLE → action is available
            # (they can always request a new token with the required scope)
            # PRIORITY 2: If user doesn't have role but has SCOPE → action is available
            # (delegated permission scenario)
            if has_role:
                is_available = True
                availability_reason = 'has_required_role'
            elif has_scope:
                is_available = True
                availability_reason = 'has_required_scope'
            else:
                is_available = False
                availability_reason = 'missing_both'
            
            capabilities[action_id] = {
                'name': action_config['name'],
                'description': action_config['description'],
                'available': is_available,
                'availability_reason': availability_reason if is_available or not (has_role or has_scope) else None,
                'has_required_role': has_role,
                'has_required_scope': has_scope,
                'matching_roles': matching_roles,
                'matching_scopes': matching_scopes,
                'required_roles': action_config['required_roles'],
                'required_scopes': action_config['required_scopes'],
                'risk_level': action_config['risk_level'],
                'notes': action_config.get('notes')
            }
        
        # Calculate summary
        available_actions = [k for k, v in capabilities.items() if v['available']]
        
        # Determine privilege level based on roles
        privilege_level = 'standard'
        if 'Global Administrator' in user_roles:
            privilege_level = 'global_admin'
        elif any(r in user_roles for r in ['Privileged Role Administrator', 'Privileged Authentication Administrator']):
            privilege_level = 'privileged_admin'
        elif any(r in user_roles for r in ['User Administrator', 'Security Administrator', 'Exchange Administrator', 'SharePoint Administrator']):
            privilege_level = 'high_admin'
        elif any(r in user_roles for r in ['Password Administrator', 'Helpdesk Administrator', 'Authentication Administrator']):
            privilege_level = 'limited_admin'
        elif any(r in user_roles for r in PermissionService.PRIVILEGED_ROLE_NAMES):
            privilege_level = 'has_privileged_roles'
        elif len(user_roles) > 0:
            privilege_level = 'has_roles'
        
        return {
            'success': True,
            'user_info': permissions['token_info'],
            'directory_roles': permissions['directory_roles'],
            'directory_role_ids': permissions['directory_role_ids'],
            'scopes': permissions['scopes'],
            'app_roles': permissions['app_roles'],
            'privilege_level': privilege_level,
            'capabilities': capabilities,
            'available_actions': available_actions,
            'available_count': len(available_actions),
            'total_actions': len(capabilities),
            'raw_claims': permissions['raw_claims']
        }
    
    @staticmethod
    def get_privilege_badge(privilege_level):
        """Get badge info for privilege level"""
        badges = {
            'global_admin': {
                'label': 'Global Administrator',
                'color': 'red',
                'icon': '👑',
                'description': 'Full administrative access to all features'
            },
            'privileged_admin': {
                'label': 'Privileged Admin',
                'color': 'orange',
                'icon': '⚡',
                'description': 'Can manage roles and privileged authentication'
            },
            'high_admin': {
                'label': 'High-Level Admin',
                'color': 'orange',
                'icon': '🔥',
                'description': 'Elevated administrative privileges'
            },
            'limited_admin': {
                'label': 'Limited Admin',
                'color': 'yellow',
                'icon': '🔧',
                'description': 'Password/Helpdesk administrative capabilities'
            },
            'has_privileged_roles': {
                'label': 'Has Privileged Roles',
                'color': 'blue',
                'icon': '🛡️',
                'description': 'Has some privileged directory roles'
            },
            'has_roles': {
                'label': 'Has Roles',
                'color': 'blue',
                'icon': '📋',
                'description': 'Has directory roles assigned'
            },
            'standard': {
                'label': 'Standard User',
                'color': 'gray',
                'icon': '👤',
                'description': 'No administrative roles'
            }
        }
        return badges.get(privilege_level, badges['standard'])
    
    @staticmethod
    def is_privileged_role(role_name):
        """Check if a role name is considered privileged"""
        return role_name in PermissionService.PRIVILEGED_ROLE_NAMES
    
    @staticmethod
    def check_specific_action(access_token, action_id):
        """
        Check if a specific action is available
        Quick check for a single action
        """
        if action_id not in PermissionService.ADMIN_ACTIONS:
            return {
                'success': False,
                'error': f'Unknown action: {action_id}'
            }
        
        analysis = PermissionService.analyze_admin_capabilities(access_token)
        
        if not analysis.get('success'):
            return analysis
        
        capability = analysis['capabilities'].get(action_id)
        
        return {
            'success': True,
            'action': action_id,
            'available': capability['available'],
            'details': capability
        }
    
    @staticmethod
    def get_all_known_roles():
        """Get all known directory roles with their GUIDs"""
        return [
            {'id': guid, 'name': name, 'isPrivileged': name in PermissionService.PRIVILEGED_ROLE_NAMES}
            for guid, name in PermissionService.DIRECTORY_ROLES.items()
        ]
