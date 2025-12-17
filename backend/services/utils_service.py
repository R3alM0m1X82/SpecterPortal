"""
Utils Service - JWT Decoding, Scope Analysis, Token Validation
Token utilities for power users
"""
import json
import base64
from datetime import datetime


class UtilsService:
    
    # Microsoft Graph Scopes Catalog
    SCOPE_CAPABILITIES = {
        # User & Profile
        'User.Read': {
            'category': 'User Operations',
            'allows': ['Read own profile', 'View own properties'],
            'requires_admin': False
        },
        'User.ReadWrite': {
            'category': 'User Operations',
            'allows': ['Update own profile', 'Change own properties'],
            'requires_admin': False
        },
        'User.ReadBasic.All': {
            'category': 'User Operations',
            'allows': ['Read basic info of all users', 'View display names'],
            'requires_admin': False
        },
        'User.Read.All': {
            'category': 'User Operations',
            'allows': ['Read all user profiles', 'View all user properties'],
            'requires_admin': False
        },
        'User.ReadWrite.All': {
            'category': 'User Operations',
            'allows': ['Read/write all users', 'Update user properties', 'Reset passwords', 'Assign licenses'],
            'requires_admin': True
        },
        
        # Directory & Groups
        'Directory.Read.All': {
            'category': 'Directory Operations',
            'allows': ['Read directory data', 'Read groups', 'Read devices', 'Read applications'],
            'requires_admin': False
        },
        'Directory.ReadWrite.All': {
            'category': 'Directory Operations',
            'allows': ['Read/write directory', 'Create/delete groups', 'Manage devices', 'Manage applications'],
            'requires_admin': True
        },
        'Group.Read.All': {
            'category': 'Group Operations',
            'allows': ['Read all groups', 'View group memberships'],
            'requires_admin': False
        },
        'Group.ReadWrite.All': {
            'category': 'Group Operations',
            'allows': ['Create/delete groups', 'Manage group memberships', 'Update group properties'],
            'requires_admin': True
        },
        
        # Mail
        'Mail.Read': {
            'category': 'Mail Operations',
            'allows': ['Read own mailbox', 'View emails and folders'],
            'requires_admin': False
        },
        'Mail.ReadWrite': {
            'category': 'Mail Operations',
            'allows': ['Read/write own mailbox', 'Create/delete emails', 'Move emails'],
            'requires_admin': False
        },
        'Mail.Send': {
            'category': 'Mail Operations',
            'allows': ['Send mail as user', 'Send emails on behalf of user'],
            'requires_admin': False
        },
        
        # Files & OneDrive
        'Files.Read': {
            'category': 'File Operations',
            'allows': ['Read own files', 'Download files from OneDrive'],
            'requires_admin': False
        },
        'Files.ReadWrite': {
            'category': 'File Operations',
            'allows': ['Read/write own files', 'Upload/delete files in OneDrive'],
            'requires_admin': False
        },
        'Files.Read.All': {
            'category': 'File Operations',
            'allows': ['Read all files', 'Access shared files', 'Download any file'],
            'requires_admin': False
        },
        'Files.ReadWrite.All': {
            'category': 'File Operations',
            'allows': ['Read/write all files', 'Upload/delete any file', 'Modify SharePoint libraries'],
            'requires_admin': True
        },
        
        # Sites & SharePoint
        'Sites.Read.All': {
            'category': 'SharePoint Operations',
            'allows': ['Read all SharePoint sites', 'Access site collections', 'View lists and libraries'],
            'requires_admin': False
        },
        'Sites.ReadWrite.All': {
            'category': 'SharePoint Operations',
            'allows': ['Read/write all sites', 'Create/delete lists', 'Modify site permissions'],
            'requires_admin': True
        },
        
        # Roles
        'RoleManagement.Read.Directory': {
            'category': 'Role Operations',
            'allows': ['Read directory roles', 'View role assignments'],
            'requires_admin': False
        },
        'RoleManagement.ReadWrite.Directory': {
            'category': 'Role Operations',
            'allows': ['Manage directory roles', 'Assign/remove roles', 'Privilege escalation possible'],
            'requires_admin': True
        },
        
        # Chat & Teams
        'Chat.Read': {
            'category': 'Teams Operations',
            'allows': ['Read user chats', 'Access Teams messages'],
            'requires_admin': False
        },
        'Chat.ReadWrite': {
            'category': 'Teams Operations',
            'allows': ['Read/write chats', 'Send Teams messages', 'Delete messages'],
            'requires_admin': False
        },
        
        # Application
        'Application.Read.All': {
            'category': 'Application Operations',
            'allows': ['Read all applications', 'View service principals', 'Read app registrations'],
            'requires_admin': False
        },
        'Application.ReadWrite.All': {
            'category': 'Application Operations',
            'allows': ['Create/modify applications', 'Add credentials to apps', 'Backdoor apps'],
            'requires_admin': True
        }
    }
    
    @staticmethod
    def decode_jwt(access_token):
        """
        Decode JWT Access Token and extract all claims
        
        Returns:
        {
            'success': True,
            'header': {...},
            'payload': {...},
            'expires_in_seconds': 3600,
            'is_expired': False,
            'identity': 'user@domain.com' or 'AppName (SP)'
        }
        """
        if not access_token:
            return {
                'success': False,
                'error': 'No access token provided'
            }
        
        try:
            parts = access_token.split('.')
            if len(parts) != 3:
                return {
                    'success': False,
                    'error': 'Invalid JWT format (expected 3 parts)'
                }
            
            # Decode header
            header_data = UtilsService._decode_jwt_part(parts[0])
            
            # Decode payload
            payload_data = UtilsService._decode_jwt_part(parts[1])
            
            # Calculate expiration
            expires_in_seconds = None
            is_expired = False
            
            if payload_data.get('exp'):
                exp_timestamp = payload_data['exp']
                exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
                now = datetime.utcnow()
                
                expires_in_seconds = int((exp_datetime - now).total_seconds())
                is_expired = expires_in_seconds < 0
            
            # Determine identity
            identity = None
            identity_type = None
            
            if payload_data.get('upn'):
                identity = payload_data['upn']
                identity_type = 'user'
            elif payload_data.get('app_displayname'):
                identity = f"{payload_data['app_displayname']} (Service Principal)"
                identity_type = 'service_principal'
            elif payload_data.get('appid'):
                identity = f"App ID: {payload_data['appid']}"
                identity_type = 'service_principal'
            
            return {
                'success': True,
                'header': header_data,
                'payload': payload_data,
                'expires_in_seconds': expires_in_seconds,
                'is_expired': is_expired,
                'identity': identity,
                'identity_type': identity_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to decode JWT: {str(e)}'
            }
    
    @staticmethod
    def _decode_jwt_part(part):
        """Decode JWT header or payload"""
        # Add padding
        part += '=' * (4 - len(part) % 4)
        decoded = base64.urlsafe_b64decode(part)
        return json.loads(decoded)
    
    @staticmethod
    def analyze_scope(scope_string):
        """
        Analyze scopes and return capabilities
        
        Returns:
        {
            'success': True,
            'scopes': ['User.Read', 'Files.ReadWrite.All'],
            'capabilities': {
                'User Operations': [...],
                'File Operations': [...]
            },
            'missing_high_value': ['User.ReadWrite.All', ...],
            'admin_scopes': ['Files.ReadWrite.All'],
            'warnings': [...]
        }
        """
        if not scope_string:
            return {
                'success': False,
                'error': 'No scope provided'
            }
        
        # Parse scopes
        scopes = [s.strip() for s in scope_string.split() if s.strip()]
        
        # Analyze capabilities
        capabilities = {}
        admin_scopes = []
        unknown_scopes = []
        
        for scope in scopes:
            # Remove audience prefix if present
            scope_clean = scope.split('/')[-1]
            
            if scope_clean in UtilsService.SCOPE_CAPABILITIES:
                scope_info = UtilsService.SCOPE_CAPABILITIES[scope_clean]
                category = scope_info['category']
                
                if category not in capabilities:
                    capabilities[category] = []
                
                capabilities[category].extend(scope_info['allows'])
                
                if scope_info['requires_admin']:
                    admin_scopes.append(scope_clean)
            else:
                unknown_scopes.append(scope_clean)
        
        # Find missing high-value scopes
        high_value_scopes = [
            'User.ReadWrite.All',
            'Directory.ReadWrite.All',
            'RoleManagement.ReadWrite.Directory',
            'Application.ReadWrite.All',
            'Files.ReadWrite.All'
        ]
        
        missing_high_value = [s for s in high_value_scopes if s not in scopes]
        
        # Generate warnings
        warnings = []
        if 'RoleManagement.ReadWrite.Directory' in scopes:
            warnings.append('⚠️ Privilege escalation possible via role assignments')
        if 'Application.ReadWrite.All' in scopes:
            warnings.append('⚠️ Can backdoor applications with credentials')
        if 'User.ReadWrite.All' in scopes:
            warnings.append('⚠️ Can reset passwords and assign licenses')
        
        return {
            'success': True,
            'scopes': scopes,
            'capabilities': capabilities,
            'missing_high_value': missing_high_value,
            'admin_scopes': admin_scopes,
            'unknown_scopes': unknown_scopes,
            'warnings': warnings,
            'total_scopes': len(scopes)
        }
    
    @staticmethod
    def validate_token(access_token):
        """
        Validate JWT token structure, expiration, and claims
        
        Returns:
        {
            'success': True,
            'valid': True,
            'checks': {
                'structure': {'valid': True, 'message': '...'},
                'expiration': {'valid': False, 'message': 'Expired 2h ago'},
                'audience': {'valid': True, 'audience': 'graph.microsoft.com'},
                'issuer': {'valid': True, 'issuer': 'sts.windows.net/...'}
            },
            'warnings': [...],
            'can_be_used': False
        }
        """
        if not access_token:
            return {
                'success': False,
                'error': 'No access token provided'
            }
        
        checks = {}
        warnings = []
        
        # Decode token
        decode_result = UtilsService.decode_jwt(access_token)
        
        if not decode_result['success']:
            return {
                'success': True,
                'valid': False,
                'checks': {
                    'structure': {
                        'valid': False,
                        'message': decode_result.get('error', 'Invalid JWT structure')
                    }
                },
                'warnings': ['Token cannot be decoded'],
                'can_be_used': False
            }
        
        payload = decode_result['payload']
        
        # Check 1: Structure
        checks['structure'] = {
            'valid': True,
            'message': 'Valid JWT structure (3 parts)'
        }
        
        # Check 2: Expiration
        if decode_result['is_expired']:
            exp_seconds = abs(decode_result['expires_in_seconds'])
            hours = exp_seconds // 3600
            minutes = (exp_seconds % 3600) // 60
            
            checks['expiration'] = {
                'valid': False,
                'message': f'Expired {hours}h {minutes}m ago',
                'expires_in_seconds': decode_result['expires_in_seconds']
            }
            warnings.append('⚠️ Token is expired - refresh needed')
        else:
            exp_seconds = decode_result['expires_in_seconds']
            hours = exp_seconds // 3600
            minutes = (exp_seconds % 3600) // 60
            
            checks['expiration'] = {
                'valid': True,
                'message': f'Valid for {hours}h {minutes}m',
                'expires_in_seconds': exp_seconds
            }
        
        # Check 3: Audience
        audience = payload.get('aud', 'Unknown')
        checks['audience'] = {
            'valid': bool(audience),
            'audience': audience,
            'message': f'Audience: {audience}'
        }
        
        # Check 4: Issuer
        issuer = payload.get('iss', 'Unknown')
        expected_issuer = 'https://sts.windows.net/' in issuer or 'https://login.microsoftonline.com/' in issuer
        
        checks['issuer'] = {
            'valid': expected_issuer,
            'issuer': issuer,
            'message': f'Issuer: {issuer[:50]}...' if len(issuer) > 50 else f'Issuer: {issuer}'
        }
        
        if not expected_issuer:
            warnings.append('⚠️ Unexpected issuer - may not be Microsoft token')
        
        # Check 5: Claims presence
        required_claims = ['aud', 'iss', 'exp', 'iat']
        missing_claims = [c for c in required_claims if c not in payload]
        
        if missing_claims:
            warnings.append(f'⚠️ Missing claims: {", ".join(missing_claims)}')
        
        # Determine if token can be used
        can_be_used = (
            checks['structure']['valid'] and
            checks['expiration']['valid'] and
            checks['audience']['valid']
        )
        
        # Overall validity
        valid = all(check.get('valid', False) for check in checks.values())
        
        return {
            'success': True,
            'valid': valid,
            'checks': checks,
            'warnings': warnings,
            'can_be_used': can_be_used,
            'identity': decode_result.get('identity'),
            'identity_type': decode_result.get('identity_type')
        }
    
    @staticmethod
    def generate_curl(access_token, endpoint=None, method='GET'):
        """
        Generate cURL command for Microsoft Graph API (both Bash and PowerShell)
        
        Returns:
        {
            'success': True,
            'bash_command': 'curl.exe ...',
            'powershell_command': 'Invoke-WebRequest ...'
        }
        """
        if not access_token:
            return {
                'success': False,
                'error': 'No access token provided'
            }
        
        if not endpoint:
            endpoint = 'https://graph.microsoft.com/v1.0/me'
        
        # Bash/Linux cURL (use curl.exe on Windows)
        bash_command = f"""curl.exe -X {method} \\
  '{endpoint}' \\
  -H 'Authorization: Bearer {access_token}' \\
  -H 'Content-Type: application/json'"""
        
        # PowerShell Invoke-WebRequest
        powershell_command = f"""$headers = @{{
    'Authorization' = 'Bearer {access_token}'
    'Content-Type' = 'application/json'
}}

Invoke-WebRequest -Uri '{endpoint}' `
    -Method {method} `
    -Headers $headers"""
        
        return {
            'success': True,
            'bash_command': bash_command,
            'powershell_command': powershell_command,
            'endpoint': endpoint,
            'method': method
        }
    
    @staticmethod
    def export_token_json(token_data):
        """
        Export token to JSON format
        
        Returns:
        {
            'success': True,
            'json_output': {...}
        }
        """
        if not token_data:
            return {
                'success': False,
                'error': 'No token data provided'
            }
        
        export_data = {
            'token_id': token_data.get('id'),
            'client_id': token_data.get('client_id'),
            'client_app_name': token_data.get('client_app_name'),
            'upn': token_data.get('upn'),
            'scope': token_data.get('scope'),
            'audience': token_data.get('audience'),
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': token_data.get('expires_at'),
            'token_type': token_data.get('token_type'),
            'exported_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Remove None values
        export_data = {k: v for k, v in export_data.items() if v is not None}
        
        return {
            'success': True,
            'json_output': export_data
        }
    
    @staticmethod
    def generate_powershell(access_token, endpoint=None):
        """
        Generate PowerShell script for Microsoft Graph API
        
        Returns:
        {
            'success': True,
            'powershell_script': '...'
        }
        """
        if not access_token:
            return {
                'success': False,
                'error': 'No access token provided'
            }
        
        if not endpoint:
            endpoint = 'https://graph.microsoft.com/v1.0/me'
        
        powershell_script = f"""# Microsoft Graph API - PowerShell Script
$token = "{access_token}"
$headers = @{{
    'Authorization' = "Bearer $token"
    'Content-Type' = 'application/json'
}}

# Make API call
$result = Invoke-RestMethod -Uri '{endpoint}' `
    -Headers $headers `
    -Method GET

# Display result
$result | ConvertTo-Json -Depth 10"""
        
        return {
            'success': True,
            'powershell_script': powershell_script,
            'endpoint': endpoint
        }
