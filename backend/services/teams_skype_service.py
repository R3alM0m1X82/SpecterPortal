"""
Teams Skype Service - Skype API operations for Teams
Uses skypeToken to access Teams conversations via Skype backend
"""

import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class TeamsSkypeService:
    """Service for Teams operations via Skype API"""
    
    def __init__(self, skype_token: str, chat_service_url: str):
        """
        Initialize Teams Skype service
        
        Args:
            skype_token: Skype token (JWT)
            chat_service_url: Chat service URL from regionGtms
        """
        self.skype_token = skype_token
        self.chat_service_url = chat_service_url
        self.timeout = current_app.config.get('GRAPH_API_TIMEOUT', 30)
    
    def _make_request(self, url: str, method: str = 'GET', json_data: dict = None) -> dict:
        """
        Make HTTP request to Skype API
        
        Args:
            url: Full URL to request
            method: HTTP method (GET, POST)
            json_data: JSON body for POST requests
            
        Returns:
            Dict with success status and data/error
        """
        headers = {
            'Authentication': f'skypetoken={self.skype_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # Disable SSL verification for lab environments
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=self.timeout, verify=False)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            if response.status_code in [200, 201, 202]:
                # Try to parse JSON
                try:
                    return {
                        'success': True,
                        'data': response.json()
                    }
                except ValueError:
                    return {
                        'success': True,
                        'data': response.text
                    }
            else:
                logger.error(f"Skype API returned {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def list_conversations(self, page_size: int = 500) -> dict:
        """
        List user's conversations
        
        Args:
            page_size: Number of conversations to retrieve
            
        Returns:
            Dict with conversations list
        """
        url = f"{self.chat_service_url}/v1/users/ME/conversations"
        params = f"?view=msnp24Equivalent&pageSize={page_size}"
        
        result = self._make_request(url + params)
        
        if result['success']:
            conversations = result['data'].get('conversations', [])
            return {
                'success': True,
                'conversations': conversations,
                'count': len(conversations)
            }
        
        return result
    
    def get_conversation_messages(self, conversation_link: str, page_size: int = 200, 
                                 start_time: int = 0) -> dict:
        """
        Get messages from a conversation
        
        Args:
            conversation_link: Full URL to conversation (from conversation list)
            page_size: Number of messages to retrieve
            start_time: Start time for messages (0 = all)
            
        Returns:
            Dict with messages list
        """
        url = f"{conversation_link}?startTime={start_time}&view=msnp24Equivalent&pageSize={page_size}"
        
        result = self._make_request(url)
        
        if result['success']:
            messages = result['data'].get('messages', [])
            return {
                'success': True,
                'messages': messages,
                'count': len(messages)
            }
        
        return result
    
    def send_conversation_message(self, conversation_link: str, content: str, 
                                 message_type: str = 'RichText/Html') -> dict:
        """
        Send a message to a conversation
        
        Args:
            conversation_link: Full URL to conversation
            content: Message content
            message_type: Message type (default: RichText/Html)
            
        Returns:
            Dict with sent message info
        """
        message_data = {
            'messagetype': message_type,
            'content': content
        }
        
        result = self._make_request(conversation_link, method='POST', json_data=message_data)
        
        if result['success']:
            # Extract message ID from response if available
            message_id = 'Unknown'
            if isinstance(result['data'], dict):
                message_id = result['data'].get('OriginalArrivalTime', 'Unknown')
            
            return {
                'success': True,
                'message_id': message_id,
                'data': result['data']
            }
        
        return result
