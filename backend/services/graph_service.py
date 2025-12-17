"""
Graph service - Microsoft Graph API client
"""
import requests
from flask import current_app


class GraphService:
    
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
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_profile(self):
        result = self._make_request('me')
        
        if result['success']:
            data = result['data']
            return {
                'success': True,
                'profile': {
                    'id': data.get('id'),
                    'displayName': data.get('displayName'),
                    'mail': data.get('mail'),
                    'userPrincipalName': data.get('userPrincipalName'),
                    'jobTitle': data.get('jobTitle'),
                    'officeLocation': data.get('officeLocation'),
                    'mobilePhone': data.get('mobilePhone'),
                    'businessPhones': data.get('businessPhones', []),
                    'preferredLanguage': data.get('preferredLanguage')
                }
            }
        
        return result
    
    def get_user_photo(self):
        result = self._make_request('me/photo')
        
        if not result['success']:
            return {
                'success': False,
                'error': 'No photo available'
            }
        
        photo_result = self._make_request('me/photo/$value')
        
        if photo_result['success']:
            return {
                'success': True,
                'has_photo': True,
                'photo_url': f"{self.base_url}/me/photo/$value"
            }
        
        return {
            'success': False,
            'has_photo': False
        }
