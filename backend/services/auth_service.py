"""
Authentication Service - Device Code Flow & ROPC
Supports multiple authentication methods for obtaining Microsoft tokens
"""
import requests
import time
from datetime import datetime
from database import db
from models.token import Token


class AuthService:
    """Service for Microsoft OAuth authentication flows"""
    
    # Microsoft OAuth endpoints
    # Device Code works with /common, but ROPC needs /organizations or specific tenant
    AUTHORITY_COMMON = 'https://login.microsoftonline.com/common'
    AUTHORITY_ORGS = 'https://login.microsoftonline.com/organizations'
    
    DEVICE_CODE_URL = f'{AUTHORITY_COMMON}/oauth2/v2.0/devicecode'
    TOKEN_URL_COMMON = f'{AUTHORITY_COMMON}/oauth2/v2.0/token'
    TOKEN_URL_ORGS = f'{AUTHORITY_ORGS}/oauth2/v2.0/token'
    
    # Known Client IDs (FOCI - Family of Client IDs)
    CLIENT_IDS = {
        'graph_powershell': {
            'id': '14d82eec-204b-4c2f-b7e8-296a70dab67e',
            'name': 'Microsoft Graph PowerShell',
            'description': 'Full Graph API access'
        },
        'azure_powershell': {
            'id': '1950a258-227b-4e31-a9cf-717495945fc2',
            'name': 'Azure PowerShell',
            'description': 'Azure management + Graph'
        },
        'office_master': {
            'id': 'd3590ed6-52b3-4102-aeff-aad2292ab01c',
            'name': 'Microsoft Office',
            'description': 'Office 365 services'
        },
        'teams': {
            'id': '1fec8e78-bce4-4aaf-ab1b-5451cc387264',
            'name': 'Microsoft Teams',
            'description': 'Teams and Skype'
        },
        'outlook': {
            'id': 'd3590ed6-52b3-4102-aeff-aad2292ab01c',
            'name': 'Microsoft Outlook',
            'description': 'Email and Calendar'
        },
        'onedrive': {
            'id': 'ab9b8c07-8f02-4f72-87fa-80105867a763',
            'name': 'OneDrive SyncEngine',
            'description': 'OneDrive file access'
        },
        'sharepoint': {
            'id': '89bee1f7-5e6e-4d8a-9f3d-ecd601259da7',
            'name': 'SharePoint',
            'description': 'SharePoint Online'
        }
    }
    
    # Default scopes for different scenarios
    DEFAULT_SCOPES = {
        'full': 'https://graph.microsoft.com/.default offline_access',
        'graph': 'https://graph.microsoft.com/User.Read https://graph.microsoft.com/Mail.Read offline_access',
        'mail': 'https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/Mail.Send offline_access',
        'files': 'https://graph.microsoft.com/Files.ReadWrite.All offline_access',
        'teams': 'https://graph.microsoft.com/Chat.Read https://graph.microsoft.com/Chat.ReadWrite offline_access',
        'sharepoint': 'https://graph.microsoft.com/Sites.Read.All https://graph.microsoft.com/Sites.ReadWrite.All offline_access'
    }
    
    @classmethod
    def get_client_ids(cls):
        """Return list of available client IDs"""
        return cls.CLIENT_IDS
    
    @classmethod
    def get_scopes(cls):
        """Return available scope presets"""
        return cls.DEFAULT_SCOPES
    
    # =====================
    # DEVICE CODE FLOW
    # =====================
    
    @classmethod
    def start_device_code_flow(cls, client_id, scope='https://graph.microsoft.com/.default offline_access'):
        """
        Start Device Code Flow - Step 1
        Returns device code and user instructions
        """
        try:
            data = {
                'client_id': client_id,
                'scope': scope
            }
            
            response = requests.post(cls.DEVICE_CODE_URL, data=data)
            
            if response.status_code != 200:
                error_data = response.json()
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Failed to get device code'),
                    'error_code': error_data.get('error', 'unknown')
                }
            
            result = response.json()
            
            print(f"[DEBUG] Device code generated (first 20 chars): {result.get('device_code', '')[:20]}...")
            print(f"[DEBUG] User code: {result.get('user_code')}")
            
            return {
                'success': True,
                'device_code': result.get('device_code'),
                'user_code': result.get('user_code'),
                'verification_uri': result.get('verification_uri'),
                'expires_in': result.get('expires_in', 900),
                'interval': result.get('interval', 5),
                'message': result.get('message', f"Go to {result.get('verification_uri')} and enter code: {result.get('user_code')}")
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def poll_device_code(cls, client_id, device_code):
        """
        Poll for token after user authenticates - Step 2
        Returns token or status (pending/error)
        """
        try:
            print(f"[DEBUG] Polling with device_code (first 20 chars): {device_code[:20]}...")
            
            data = {
                'client_id': client_id,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            }
            
            response = requests.post(cls.TOKEN_URL_COMMON, data=data)
            result = response.json()
            
            print(f"[DEBUG] Poll response status: {response.status_code}")
            if response.status_code == 200:
                print(f"[DEBUG] Poll SUCCESS - response keys: {result.keys()}")
                if 'access_token' in result:
                    print(f"[DEBUG] access_token length: {len(result['access_token'])}")
                if 'refresh_token' in result:
                    print(f"[DEBUG] refresh_token length: {len(result['refresh_token'])}")
            else:
                print(f"[DEBUG] Poll response: {result}")
            
            if response.status_code == 200:
                # Success - got token
                token_result = cls._save_token_from_response(result, client_id, 'device_code')
                return token_result
            
            # Check for pending/slow_down errors
            error = result.get('error', '')
            
            if error == 'authorization_pending':
                return {
                    'success': False,
                    'status': 'pending',
                    'message': 'Waiting for user to authenticate...'
                }
            elif error == 'slow_down':
                return {
                    'success': False,
                    'status': 'slow_down',
                    'message': 'Polling too fast, slowing down...'
                }
            elif error == 'expired_token':
                return {
                    'success': False,
                    'status': 'expired',
                    'error': 'Device code expired. Please start over.'
                }
            elif error == 'authorization_declined':
                return {
                    'success': False,
                    'status': 'declined',
                    'error': 'User declined authorization'
                }
            else:
                return {
                    'success': False,
                    'status': 'error',
                    'error': result.get('error_description', f'Unknown error: {error}')
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status': 'error',
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }
    
    # =====================
    # ROPC FLOW
    # =====================
    
    @classmethod
    def authenticate_ropc(cls, username, password, client_id, scope='https://graph.microsoft.com/.default offline_access', tenant_id=None):
        """
        Resource Owner Password Credentials (ROPC) Flow
        WARNING: Only for lab environments without MFA!
        
        Args:
            username: User's UPN (email)
            password: User's password
            client_id: Azure AD Application Client ID
            scope: OAuth scopes
            tenant_id: Optional tenant ID. If not provided, uses 'organizations'
        
        Returns:
            dict with success status and token data or error
        """
        try:
            data = {
                'client_id': client_id,
                'scope': scope,
                'username': username,
                'password': password,
                'grant_type': 'password'
            }
            
            # Determine endpoint: specific tenant or organizations
            if tenant_id and tenant_id.strip():
                token_url = f'https://login.microsoftonline.com/{tenant_id.strip()}/oauth2/v2.0/token'
                print(f"[DEBUG] ROPC using tenant-specific endpoint: {tenant_id}")
            else:
                token_url = cls.TOKEN_URL_ORGS
                print(f"[DEBUG] ROPC using /organizations endpoint")
            
            response = requests.post(token_url, data=data)
            result = response.json()
            
            print(f"[DEBUG] ROPC response status: {response.status_code}")
            print(f"[DEBUG] ROPC response keys: {result.keys()}")
            if 'access_token' in result:
                print(f"[DEBUG] ROPC access_token length: {len(result['access_token'])}")
            if 'refresh_token' in result:
                print(f"[DEBUG] ROPC refresh_token length: {len(result['refresh_token'])}")
            
            if response.status_code == 200:
                # Success
                token_result = cls._save_token_from_response(result, client_id, 'ropc')
                return token_result
            else:
                # Error
                error = result.get('error', 'unknown')
                error_desc = result.get('error_description', 'Authentication failed')
                
                # Common ROPC errors
                if 'AADSTS50126' in error_desc:
                    error_msg = 'Invalid username or password'
                elif 'AADSTS50076' in error_desc or 'AADSTS50079' in error_desc:
                    error_msg = 'MFA required - ROPC cannot be used with MFA enabled accounts'
                elif 'AADSTS7000218' in error_desc:
                    error_msg = 'ROPC not allowed - check Azure AD settings'
                elif 'AADSTS50034' in error_desc:
                    error_msg = 'User not found'
                elif 'AADSTS50053' in error_desc:
                    error_msg = 'Account locked'
                elif 'AADSTS90002' in error_desc or 'AADSTS700016' in error_desc:
                    error_msg = 'Invalid tenant ID'
                else:
                    error_msg = error_desc
                
                return {
                    'success': False,
                    'error': error_msg,
                    'error_code': error
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # =====================
    # REFRESH TOKEN
    # =====================
    
    @classmethod
    def refresh_access_token(cls, refresh_token, client_id, scope=None):
        """
        Use refresh token to get new access token
        """
        try:
            data = {
                'client_id': client_id,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            if scope:
                data['scope'] = scope
            
            response = requests.post(cls.TOKEN_URL_COMMON, data=data)
            result = response.json()
            
            if response.status_code == 200:
                token_result = cls._save_token_from_response(result, client_id, 'refresh')
                return token_result
            else:
                return {
                    'success': False,
                    'error': result.get('error_description', 'Failed to refresh token'),
                    'error_code': result.get('error', 'unknown')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # =====================
    # HELPER METHODS
    # =====================
    
    @classmethod
    def _save_token_from_response(cls, response, client_id, auth_method):
        """Save token from OAuth response to database"""
        try:
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            expires_in = response.get('expires_in', 3600)
            scope = response.get('scope', '')
            
            print(f"[DEBUG] Save token - access_token present: {bool(access_token)}, refresh_token present: {bool(refresh_token)}")
            
            # Must have at least one token
            if not access_token and not refresh_token:
                return {
                    'success': False,
                    'error': 'No tokens in response'
                }
            
            # Calculate expiration
            expires_at = datetime.utcnow()
            from datetime import timedelta
            expires_at = expires_at + timedelta(seconds=expires_in)
            
            # Extract info from JWT (access_token or id_token)
            import json
            import base64
            
            upn = None
            audience = None
            tenant_id = None
            
            # Try to extract from access_token first, then id_token
            token_to_decode = access_token or response.get('id_token')
            
            if token_to_decode:
                try:
                    parts = token_to_decode.split('.')
                    if len(parts) >= 2:
                        payload = parts[1]
                        payload += '=' * (4 - len(payload) % 4)
                        payload_data = json.loads(base64.urlsafe_b64decode(payload))
                        
                        upn = payload_data.get('upn') or payload_data.get('unique_name') or payload_data.get('preferred_username')
                        audience = payload_data.get('aud')
                        tenant_id = payload_data.get('tid')
                        
                        # Use JWT exp if available
                        if payload_data.get('exp'):
                            expires_at = datetime.utcfromtimestamp(payload_data['exp'])
                except Exception as e:
                    print(f"[DEBUG] JWT decode error: {e}")
            
            saved_tokens = []
            
            # Create access token entry only if we have one
            if access_token:
                token = Token(
                    client_id=client_id,
                    upn=upn,
                    scope=scope,
                    audience=audience,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    imported_from=f'Auth:{auth_method}',
                    token_type='access_token',
                    source='auth'
                )
                db.session.add(token)
                saved_tokens.append(('access_token', token))
            
            # Also save refresh token as separate entry if present
            if refresh_token:
                rt_token = Token(
                    client_id=client_id,
                    upn=upn,
                    scope=scope,
                    audience=audience,
                    access_token=refresh_token,  # Store RT in access_token field for RT entries
                    refresh_token=refresh_token,
                    expires_at=None,  # Refresh tokens don't have clear expiration
                    imported_from=f'Auth:{auth_method}',
                    token_type='refresh_token',
                    source='auth'
                )
                db.session.add(rt_token)
                saved_tokens.append(('refresh_token', rt_token))
            
            db.session.commit()
            
            # Return the access token if we have one, otherwise the refresh token
            main_token = saved_tokens[0][1] if saved_tokens else None
            
            return {
                'success': True,
                'message': f'Token obtained via {auth_method}',
                'token': main_token.to_dict() if main_token else None,
                'access_token': access_token,  # RAW token from OAuth (not truncated)
                'refresh_token': refresh_token,  # RAW token from OAuth
                'upn': upn,
                'tenant_id': tenant_id,
                'expires_in': expires_in,
                'has_refresh_token': bool(refresh_token),
                'has_access_token': bool(access_token)
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"[DEBUG] Save token error: {e}")
            return {
                'success': False,
                'error': f'Failed to save token: {str(e)}'
            }
    
    @classmethod
    def validate_client_id(cls, client_id):
        """Check if client ID is in known list"""
        for key, info in cls.CLIENT_IDS.items():
            if info['id'] == client_id:
                return {
                    'valid': True,
                    'name': info['name'],
                    'description': info['description']
                }
        return {
            'valid': True,  # Allow custom client IDs
            'name': 'Custom Application',
            'description': 'User-provided client ID'
        }
