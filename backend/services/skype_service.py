"""
Skype Service - Exchange Access Token for Skype Token
Handles obtaining skypeToken from Teams authsvc endpoint
"""

import requests
import jwt
import json
import logging
from datetime import datetime
from flask import current_app
from database import db
from models.skype_token import SkypeToken

logger = logging.getLogger(__name__)


class SkypeService:
    """Service for obtaining and managing Skype tokens"""
    
    TEAMS_AUTHSVC_URL = "https://teams.microsoft.com/api/authsvc/v1.0/authz"
    REQUIRED_RESOURCE = "https://api.spaces.skype.com"
    
    @staticmethod
    def get_or_create_skype_token(token_id: int, access_token: str, audience: str) -> dict:
        """
        Get existing valid Skype token or create new one
        
        Args:
            token_id: Token ID in database
            access_token: Full access token for api.spaces.skype.com
            audience: Token audience (must contain api.spaces.skype.com)
            
        Returns:
            Dict with skype_token info or error
        """
        # Validate that token is for Skype API
        if SkypeService.REQUIRED_RESOURCE not in audience:
            logger.error(f"Token audience '{audience}' does not contain '{SkypeService.REQUIRED_RESOURCE}'")
            return {
                'success': False,
                'error': f"Token must be for resource '{SkypeService.REQUIRED_RESOURCE}'"
            }
        
        # Check if we have a valid cached Skype token
        existing = SkypeToken.query.filter_by(token_id=token_id).first()
        
        if existing:
            now_ts = int(datetime.utcnow().timestamp())
            if now_ts < existing.expires_at:
                logger.info(f"Using cached Skype token for token_id {token_id}")
                return {
                    'success': True,
                    'skype_token': existing.to_dict(),
                    'cached': True
                }
            else:
                # Token expired, delete it
                logger.info(f"Skype token for token_id {token_id} expired, requesting new one")
                db.session.delete(existing)
                db.session.commit()
        
        # Request new Skype token
        logger.info(f"Requesting new Skype token for token_id {token_id}")
        result = SkypeService._request_skype_token(access_token)
        
        if not result['success']:
            return result
        
        # Parse and store the new token
        try:
            response_data = result['data']
            skype_token_jwt = response_data['tokens']['skypeToken']
            
            # Decode JWT to extract claims
            decoded = jwt.decode(skype_token_jwt, options={"verify_signature": False})
            
            # Extract chat service URL
            chat_service_url = response_data['regionGtms']['chatService']
            
            # Create database entry
            skype_token_entry = SkypeToken(
                token_id=token_id,
                skype_token=skype_token_jwt,
                skype_id=decoded.get('skypeid', ''),
                chat_service_url=chat_service_url,
                issued_at=decoded.get('iat', 0),
                expires_at=decoded.get('exp', 0),
                settings_raw=json.dumps(response_data)
            )
            
            db.session.add(skype_token_entry)
            db.session.commit()
            
            logger.info(f"Successfully created Skype token for token_id {token_id}")
            
            return {
                'success': True,
                'skype_token': skype_token_entry.to_dict(),
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Skype token response: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to parse response: {str(e)}"
            }
    
    @staticmethod
    def _request_skype_token(access_token: str) -> dict:
        """
        Request Skype token from Teams authsvc endpoint
        
        Args:
            access_token: Access token for api.spaces.skype.com
            
        Returns:
            Dict with success status and data/error
        """
        # DEBUG: Log token format
        print(f"[DEBUG] Token length: {len(access_token)}")
        print(f"[DEBUG] Token starts with: {access_token[:50] if len(access_token) > 50 else access_token}")
        print(f"[DEBUG] Token ends with: {access_token[-50:] if len(access_token) > 50 else access_token}")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # Disable SSL verification for lab environments (corporate proxies/self-signed certs)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.post(
                SkypeService.TEAMS_AUTHSVC_URL,
                headers=headers,
                json={},  # Empty JSON body required by authsvc endpoint
                timeout=current_app.config.get('GRAPH_API_TIMEOUT', 30),
                verify=False  # Disable SSL verification for lab environment
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                print(f"[DEBUG] Response text: {response.text[:200]}")
                logger.error(f"Teams authsvc returned status {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}",
                    'details': response.text
                }
                
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_skype_token_by_id(skype_token_id: int) -> dict:
        """Get Skype token by ID"""
        skype_token = SkypeToken.query.get(skype_token_id)
        
        if not skype_token:
            return {
                'success': False,
                'error': 'Skype token not found'
            }
        
        # Check if expired
        now_ts = int(datetime.utcnow().timestamp())
        if now_ts >= skype_token.expires_at:
            return {
                'success': False,
                'error': 'Skype token expired',
                'skype_token': skype_token.to_dict()
            }
        
        return {
            'success': True,
            'skype_token': skype_token.to_dict()
        }
    
    @staticmethod
    def delete_skype_token(token_id: int) -> dict:
        """Delete Skype token for a given token_id"""
        skype_token = SkypeToken.query.filter_by(token_id=token_id).first()
        
        if not skype_token:
            return {
                'success': False,
                'error': 'Skype token not found'
            }
        
        db.session.delete(skype_token)
        db.session.commit()
        
        return {'success': True}
