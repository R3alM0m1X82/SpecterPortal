"""
Refresh Token Service 
Use JWT 'exp' claim instead of 'expires_in' for accurate expiration
Better token validation
AUDIENCE NORMALIZATION - GUID audience from Microsoft 
"""
import requests
import json
import base64
from datetime import datetime, timedelta
from database import db
from models.token import Token
from client_ids import is_foci_app, get_app_name, normalize_audience


class RefreshTokenService:
    
    TOKEN_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    @staticmethod
    def use_refresh_token(refresh_token_id, target_client_id=None, target_resource=None):
        """Use a refresh token to obtain a new access token"""
        rt = Token.query.get(refresh_token_id)
        
        if not rt:
            return {'success': False, 'error': 'Refresh token not found'}
        
        if rt.token_type != 'refresh_token':
            return {'success': False, 'error': 'Token is not a refresh token'}
        
        # Determine target client ID
        if target_client_id:
            if not is_foci_app(rt.client_id) or not is_foci_app(target_client_id):
                return {
                    'success': False,
                    'error': 'Cross-app refresh requires both apps to be FOCI members'
                }
            client_id = target_client_id
        else:
            client_id = rt.client_id
        
        # Determine scope
        scope = target_resource or "https://graph.microsoft.com/.default"
        
        # Prepare token request
        token_data = {
            'client_id': client_id,
            'grant_type': 'refresh_token',
            'refresh_token': rt.access_token,
            'scope': scope
        }
        
        try:
            # Request new access token
            response = requests.post(
                RefreshTokenService.TOKEN_ENDPOINT,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': f"Token request failed: {response.status_code}",
                    'error_description': error_data.get('error_description', 'Unknown error'),
                    'error_code': error_data.get('error')
                }
            
            token_response = response.json()
            access_token = token_response.get('access_token')
            new_refresh_token = token_response.get('refresh_token')
            
            if not access_token:
                return {'success': False, 'error': 'No access token in response'}
            
            # VALIDATE AND PARSE TOKEN
            token_info = RefreshTokenService._validate_and_parse_token(access_token)
            if not token_info:
                return {
                    'success': False,
                    'error': 'Generated token is not a valid JWT'
                }
            
            # Use 'exp' claim from JWT, not expires_in from response
            exp_timestamp = token_info.get('exp')
            if exp_timestamp:
                expires_at = datetime.utcfromtimestamp(exp_timestamp)
            else:
                # Fallback to expires_in if no exp claim
                expires_in = token_response.get('expires_in', 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Extract token details
            raw_audience = token_info.get('aud')
            
            # Normalize audience (GUID → Resource URL)
            # Microsoft sometimes returns aud=client_id instead of aud=resource
            # Example: aud="cfa8b339..." instead of aud="https://vault.azure.net"
            audience = normalize_audience(raw_audience, requested_scope=scope)
            
            actual_scope = token_info.get('scp', token_info.get('roles', ''))
            upn = token_info.get('upn') or rt.upn
            
            # Create new access token
            new_token = Token(
                client_id=client_id,
                upn=upn,
                scope=actual_scope if isinstance(actual_scope, str) else ' '.join(actual_scope),
                audience=audience,  # ← Now uses normalized audience!
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at,
                token_type='access_token',
                source='refresh',
                parent_token_id=rt.id,
                imported_from=f'Refreshed from RT#{rt.id}'
            )
            
            db.session.add(new_token)
            rt.mark_used()
            
            if new_refresh_token and new_refresh_token != rt.access_token:
                rt.access_token = new_refresh_token
                rt.mark_used()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully obtained new access token for {get_app_name(client_id)}',
                'new_token': new_token.to_dict(),
                'token_info': {
                    'audience': audience,
                    'raw_audience': raw_audience,  # For debugging
                    'scopes': actual_scope,
                    'upn': upn,
                    'expires_at': expires_at.isoformat(),
                    'valid_jwt': True
                },
                'refresh_token_updated': bool(new_refresh_token and new_refresh_token != rt.access_token),
                'is_foci': is_foci_app(client_id)
            }
            
        except requests.RequestException as e:
            db.session.rollback()
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    @staticmethod
    def _validate_and_parse_token(access_token):
        """Validate and parse JWT token"""
        try:
            parts = access_token.split('.')
            
            if len(parts) != 3:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            if 'aud' not in payload_data or 'exp' not in payload_data:
                return None
            
            return payload_data
            
        except Exception as e:
            print(f"[!] Token validation error: {e}")
            return None
    
    @staticmethod
    def get_foci_targets(refresh_token_id):
        """Get list of available FOCI apps"""
        rt = Token.query.get(refresh_token_id)
        
        if not rt:
            return {'success': False, 'error': 'Refresh token not found'}
        
        if rt.token_type != 'refresh_token':
            return {'success': False, 'error': 'Token is not a refresh token'}
        
        if not is_foci_app(rt.client_id):
            return {
                'success': False,
                'error': f'{get_app_name(rt.client_id)} is not a FOCI app',
                'foci_compatible': False
            }
        
        from client_ids import FOCI_APPS
        
        foci_apps = [
            {
                'client_id': cid,
                'app_name': name,
                'is_current': cid == rt.client_id
            }
            for cid, name in FOCI_APPS.items()
        ]
        
        return {
            'success': True,
            'foci_compatible': True,
            'source_app': get_app_name(rt.client_id),
            'source_client_id': rt.client_id,
            'available_targets': foci_apps,
            'total_count': len(foci_apps)
        }
    
    @staticmethod
    def get_refresh_token_stats():
        """Get statistics about refresh tokens"""
        from client_ids import get_all_foci_apps
        
        total_rt = Token.query.filter_by(token_type='refresh_token').count()
        foci_rt = Token.query.filter(
            Token.token_type == 'refresh_token',
            Token.client_id.in_(get_all_foci_apps())
        ).count()
        
        used_rt = db.session.query(Token).filter(
            Token.token_type == 'refresh_token',
            Token.children.any()
        ).count()
        
        return {
            'total_refresh_tokens': total_rt,
            'foci_refresh_tokens': foci_rt,
            'used_refresh_tokens': used_rt,
            'unused_refresh_tokens': total_rt - used_rt
        }
