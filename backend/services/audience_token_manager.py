"""
Audience Token Manager - Multi-Token System
Automatically selects or creates tokens for specific audiences

Flow:
1. User activates primary token (as usual)
2. Services call get_token_for_audience('graph.windows.net')
3. Manager finds existing token with same UPN + audience
4. If not found → FOCI exchange from primary's RT
5. Returns access_token ready to use
"""
import requests
import json
import base64
from datetime import datetime
from database import db
from models.token import Token


class AudienceTokenManager:
    """Manages automatic token selection based on audience"""
    
    # Known audiences
    AUDIENCES = {
        'ms_graph': 'https://graph.microsoft.com',
        'aad_graph': 'https://graph.windows.net',
        'azure_mgmt': 'https://management.azure.com',
        'outlook': 'https://outlook.office365.com',
        'skype': 'https://api.spaces.skype.com',
    }
    
    # FOCI client for token exchange
    FOCI_CLIENT_ID = 'd3590ed6-52b3-4102-aeff-aad2292ab01c'  # Office Master
    
    @staticmethod
    def get_token_for_audience(audience, primary_token=None):
        """
        Get access token for specific audience
        
        Args:
            audience: Target audience URL (e.g., 'https://graph.windows.net')
            primary_token: Optional primary token dict (if not provided, gets active)
            
        Returns:
            dict with 'success', 'access_token', 'token_id', etc.
        """
        # Normalize audience URL
        audience = AudienceTokenManager._normalize_audience(audience)
        
        # Get primary token if not provided
        if not primary_token:
            primary_token = AudienceTokenManager._get_primary_token()
            if not primary_token:
                return {
                    'success': False,
                    'error': 'No active token found',
                    'hint': 'Please activate a token first'
                }
        
        primary_upn = primary_token.get('upn')
        primary_audience = AudienceTokenManager._normalize_audience(
            primary_token.get('audience', '')
        )
        
        # Case 1: Primary token already has correct audience
        if primary_audience == audience:
            access_token = primary_token.get('access_token_full') or primary_token.get('access_token')
            if access_token and not access_token.endswith('...'):
                return {
                    'success': True,
                    'access_token': access_token,
                    'token_id': primary_token.get('id'),
                    'source': 'primary',
                    'upn': primary_upn
                }
        
        # Case 2: Search for existing token with same UPN + target audience
        existing = AudienceTokenManager._find_token_by_audience(primary_upn, audience)
        if existing:
            # Check if expired
            if existing.is_expired:
                # Try to refresh or delete
                db.session.delete(existing)
                db.session.commit()
            else:
                return {
                    'success': True,
                    'access_token': existing.access_token,
                    'token_id': existing.id,
                    'source': 'existing',
                    'upn': existing.upn
                }
        
        # Case 3: FOCI exchange from primary's refresh token
        refresh_token = primary_token.get('refresh_token_full')
        if not refresh_token:
            # Try to find RT with same UPN
            refresh_token = AudienceTokenManager._find_refresh_token(primary_upn)
        
        if not refresh_token:
            return {
                'success': False,
                'error': f'No token available for audience: {audience}',
                'hint': 'No refresh token available for FOCI exchange',
                'audience_needed': audience
            }
        
        # Perform FOCI exchange
        result = AudienceTokenManager._foci_exchange(
            refresh_token, 
            audience, 
            primary_upn,
            primary_token.get('id')
        )
        
        return result
    
    @staticmethod
    def _get_primary_token():
        """Get currently active (primary) token"""
        token = Token.query.filter_by(is_active=True).first()
        if token:
            return token.to_dict_full()
        return None
    
    @staticmethod
    def _normalize_audience(audience):
        """Normalize audience URL (remove trailing slash, etc.)"""
        if not audience:
            return ''
        audience = audience.strip().rstrip('/')
        # Handle common variations
        if audience == 'https://graph.microsoft.com/':
            audience = 'https://graph.microsoft.com'
        return audience
    
    @staticmethod
    def _find_token_by_audience(upn, audience):
        """Find existing access token with same UPN and audience"""
        if not upn:
            return None
        
        # Search for matching token
        tokens = Token.query.filter(
            Token.upn == upn,
            Token.token_type == 'access_token',
            Token.expires_at > datetime.utcnow()  # Not expired
        ).all()
        
        for token in tokens:
            token_audience = AudienceTokenManager._normalize_audience(token.audience)
            if token_audience == audience:
                return token
        
        return None
    
    @staticmethod
    def _find_refresh_token(upn):
        """Find refresh token for UPN"""
        if not upn:
            return None
        
        # First try to find FOCI refresh token
        rt = Token.query.filter(
            Token.upn == upn,
            Token.token_type == 'refresh_token'
        ).first()
        
        if rt:
            return rt.access_token  # RT is stored in access_token field
        
        # Fallback: find any access_token with refresh_token
        token = Token.query.filter(
            Token.upn == upn,
            Token.refresh_token.isnot(None)
        ).first()
        
        if token:
            return token.refresh_token
        
        return None
    
    @staticmethod
    def _foci_exchange(refresh_token, audience, upn, parent_token_id=None):
        """
        Perform FOCI token exchange
        
        Uses Office Master client to get new AT for different audience
        """
        try:
            # Prepare request
            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            
            # Build scope from audience
            scope = f'{audience}/.default offline_access'
            
            data = {
                'client_id': AudienceTokenManager.FOCI_CLIENT_ID,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'scope': scope
            }
            
            # Make request
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': 'FOCI exchange failed',
                    'details': error_data.get('error_description', response.text),
                    'status_code': response.status_code
                }
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            
            if not access_token:
                return {
                    'success': False,
                    'error': 'No access_token in response'
                }
            
            # Extract info from JWT
            expires_at = AudienceTokenManager._extract_expires(access_token)
            jwt_audience = AudienceTokenManager._extract_audience(access_token)
            jwt_upn = AudienceTokenManager._extract_upn(access_token)
            
            # Create new token in database
            new_token = Token(
                client_id=AudienceTokenManager.FOCI_CLIENT_ID,
                upn=jwt_upn or upn,
                scope=token_data.get('scope'),
                audience=jwt_audience or audience,
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at,
                token_type='access_token',
                source='foci_exchange',
                parent_token_id=parent_token_id,
                imported_from='FOCI Exchange'
            )
            
            db.session.add(new_token)
            db.session.commit()
            
            return {
                'success': True,
                'access_token': access_token,
                'token_id': new_token.id,
                'source': 'foci_exchange',
                'upn': new_token.upn,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'Network error during FOCI exchange',
                'details': str(e)
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': 'FOCI exchange failed',
                'details': str(e)
            }
    
    @staticmethod
    def _extract_expires(access_token):
        """Extract exp claim from JWT"""
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            exp = payload_data.get('exp')
            if exp:
                return datetime.utcfromtimestamp(exp)
            return None
        except:
            return None
    
    @staticmethod
    def _extract_audience(access_token):
        """Extract aud claim from JWT"""
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            return payload_data.get('aud')
        except:
            return None
    
    @staticmethod
    def _extract_upn(access_token):
        """Extract upn claim from JWT"""
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            return payload_data.get('upn') or payload_data.get('unique_name')
        except:
            return None
    
    @staticmethod
    def get_available_audiences(upn=None):
        """
        Get list of available audiences for current user
        
        Returns dict of audience -> token_id (or None if needs FOCI)
        """
        if not upn:
            primary = AudienceTokenManager._get_primary_token()
            if primary:
                upn = primary.get('upn')
        
        if not upn:
            return {}
        
        # Get all non-expired tokens for this UPN
        tokens = Token.query.filter(
            Token.upn == upn,
            Token.token_type == 'access_token'
        ).all()
        
        result = {}
        for token in tokens:
            audience = AudienceTokenManager._normalize_audience(token.audience)
            if audience:
                # Check if expired
                if token.is_expired:
                    result[audience] = {'available': False, 'reason': 'expired'}
                else:
                    result[audience] = {
                        'available': True,
                        'token_id': token.id,
                        'expires_at': token.expires_at.isoformat() if token.expires_at else None
                    }
        
        # Check if FOCI exchange is possible
        has_rt = AudienceTokenManager._find_refresh_token(upn)
        
        return {
            'audiences': result,
            'foci_available': bool(has_rt),
            'upn': upn
        }
