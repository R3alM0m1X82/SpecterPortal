"""
Teams Service - Microsoft Teams Chat and Channels Operations
Handles Teams chats, messages, teams and channels via Microsoft Graph API
"""

import requests
from flask import current_app
from services.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)


class TeamsService:
    """Service for Microsoft Teams operations"""
    
    def __init__(self, access_token: str, token_id: int):
        """
        Initialize Teams service
        
        Args:
            access_token: Full Microsoft Graph API access token
            token_id: Token ID for cache management
        """
        self.access_token = access_token
        self.token_id = token_id
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
        self.cache = CacheService()
    
    def _make_request(self, endpoint, method='GET', extra_headers=None, **kwargs):
        """Make HTTP request to Microsoft Graph API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Merge extra headers if provided
        if extra_headers:
            headers.update(extra_headers)
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'data': response.json() if response.content else {},
                    'raw': response.content
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
    
    def list_chats(self, top: int = 50):
        """
        List user's chats (1-on-1 and group chats)
        
        Args:
            top: Number of chats to retrieve (default 50)
            
        Returns:
            Dict with chats list and metadata
        """
        endpoint = 'me/chats'
        params = {
            '$top': top,
            '$expand': 'members',
            '$orderby': 'lastMessagePreview/createdDateTime desc'
        }
        
        # Try cache first
        cached = self.cache.get(self.token_id, endpoint, params)
        if cached:
            return cached
        
        # Make API call
        result = self._make_request(endpoint, params=params)
        
        if result['success']:
            chats = result['data'].get('value', [])
            
            response = {
                'chats': chats,
                'count': len(chats),
                '@odata.nextLink': result['data'].get('@odata.nextLink')
            }
            
            # Cache for 2 minutes
            self.cache.set(self.token_id, endpoint, response, ttl_seconds=120, params=params)
            
            logger.info(f"Retrieved {len(chats)} chats")
            return response
        
        return result
    
    def get_chat_messages(self, chat_id: str, top: int = 50, load_all: bool = False):
        """
        Get messages from a specific chat
        
        Args:
            chat_id: Chat ID
            top: Number of messages to retrieve per page
            load_all: If True, load ALL messages following pagination
            
        Returns:
            Dict with messages list and metadata
        """
        endpoint = f'chats/{chat_id}/messages'
        params = {
            '$top': top,
            '$orderby': 'createdDateTime desc'
        }
        
        # NO CACHE for messages - they change too frequently!
        # Always fetch fresh data from Graph API
        
        # Make API call
        result = self._make_request(endpoint, params=params)
        
        if result['success']:
            messages = result['data'].get('value', [])
            next_link = result['data'].get('@odata.nextLink')
            
            # Load ALL pages if requested
            if load_all and next_link:
                logger.info(f"Loading all messages for chat {chat_id}, starting with {len(messages)} messages...")
                all_messages = messages.copy()
                page_count = 1
                
                while next_link and page_count < 10:  # Max 10 pages (500 messages) as safeguard
                    page_count += 1
                    logger.info(f"Loading page {page_count} from nextLink")
                    
                    # Use full nextLink URL
                    page_result = requests.get(
                        next_link,
                        headers={
                            'Authorization': f'Bearer {self.access_token}',
                            'Content-Type': 'application/json'
                        },
                        timeout=self.timeout
                    )
                    
                    if page_result.status_code == 200:
                        page_data = page_result.json()
                        page_messages = page_data.get('value', [])
                        all_messages.extend(page_messages)
                        next_link = page_data.get('@odata.nextLink')
                        logger.info(f"Page {page_count}: {len(page_messages)} messages, total: {len(all_messages)}")
                    else:
                        logger.warning(f"Failed to load page {page_count}: {page_result.status_code}")
                        break
                
                messages = all_messages
                next_link = None  # No more pages
                logger.info(f"Loaded all {len(messages)} messages across {page_count} pages")
            
            # Get current user info for isFromMe detection
            current_user = self.get_current_user()
            current_user_id = current_user.get('id') if current_user else None
            
            # Enrich messages with displayName lookup for empty names + isFromMe flag
            messages = self._enrich_message_names(messages, current_user_id)
            
            response = {
                'messages': messages,
                'count': len(messages),
                'chat_id': chat_id,
                'current_user_id': current_user_id,  # Include for frontend
                '@odata.nextLink': next_link
            }
            
            # NO CACHE for messages - always fresh data!
            
            logger.info(f"Retrieved {len(messages)} messages from chat {chat_id} (NO CACHE)")
            return response
        
        return result
    
    def _enrich_message_names(self, messages, current_user_id=None):
        """
        Enrich messages with user displayName when missing
        
        Args:
            messages: List of message objects
            current_user_id: Current user ID for isFromMe detection
            
        Returns:
            List of enriched messages
        """
        enriched = []
        for msg in messages:
            # Mark if message is from current user
            if current_user_id and msg.get('from') and msg['from'].get('user'):
                msg_user_id = msg['from']['user'].get('id')
                msg['isFromMe'] = (msg_user_id == current_user_id)
            else:
                msg['isFromMe'] = False
            
            # Check if displayName is missing or empty
            if (msg.get('from') and msg['from'].get('user') and 
                not msg['from']['user'].get('displayName')):
                
                user_id = msg['from']['user'].get('id')
                if user_id:
                    # Lookup user by ID
                    display_name = self._get_user_display_name(user_id)
                    if display_name:
                        msg['from']['user']['displayName'] = display_name
                        logger.debug(f"Enriched message with displayName: {display_name}")
            
            enriched.append(msg)
        
        return enriched
    
    def _get_user_display_name(self, user_id: str):
        """
        Get user displayName by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Display name or None if not found
        """
        endpoint = f'users/{user_id}'
        params = {'$select': 'displayName'}
        
        # Try cache first
        cached = self.cache.get(self.token_id, endpoint, params)
        if cached:
            return cached.get('displayName')
        
        result = self._make_request(endpoint, params=params)
        
        if result['success']:
            display_name = result['data'].get('displayName')
            # Cache user info for 10 minutes
            self.cache.set(self.token_id, endpoint, result['data'], ttl_seconds=600, params=params)
            return display_name
        
        return None
    
    def get_current_user(self):
        """
        Get current user information
        
        Returns:
            Dict with user info (id, displayName, userPrincipalName)
        """
        endpoint = 'me'
        params = {'$select': 'id,displayName,userPrincipalName'}
        
        # Try cache first (cache for 1 hour)
        cached = self.cache.get(self.token_id, endpoint, params)
        if cached:
            return cached
        
        result = self._make_request(endpoint, params=params)
        
        if result['success']:
            user_info = result['data']
            # Cache for 1 hour
            self.cache.set(self.token_id, endpoint, user_info, ttl_seconds=3600, params=params)
            return user_info
        
        return None
    
    def proxy_graph_image(self, image_url: str):
        """
        Proxy Graph API image request with authentication
        
        Args:
            image_url: Full Graph API image URL
            
        Returns:
            Dict with image binary data and content type
        """
        try:
            response = requests.get(
                image_url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.content,
                    'content_type': response.headers.get('Content-Type', 'image/png')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch image: {response.status_code}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_chat_message(self, chat_id: str, content: str, content_type: str = 'text'):
        """
        Send a message in a chat
        
        Args:
            chat_id: Chat ID
            content: Message content
            content_type: Content type ('text' or 'html')
            
        Returns:
            Dict with sent message details
        """
        endpoint = f'chats/{chat_id}/messages'
        
        # Prepare message body
        message_data = {
            'body': {
                'contentType': content_type,
                'content': content
            }
        }
        
        # Send message
        result = self._make_request(endpoint, method='POST', json=message_data)
        
        if result['success']:
            # Invalidate cache for this chat's messages
            # Note: Cache uses params, frontend uses timestamp to bypass
            self.cache.invalidate(self.token_id, endpoint)
            
            logger.info(f"Message sent to chat {chat_id}, cache invalidated")
            return {
                'success': True,
                'message': result['data'],
                'chat_id': chat_id
            }
        
        return result
    
    def list_teams(self):
        """
        List teams the user is member of
        
        Returns:
            Dict with teams list and metadata
        """
        endpoint = 'me/joinedTeams'
        
        # Try cache first
        cached = self.cache.get(self.token_id, endpoint)
        if cached:
            return cached
        
        # Make API call
        result = self._make_request(endpoint)
        
        if result['success']:
            teams = result['data'].get('value', [])
            
            response = {
                'teams': teams,
                'count': len(teams)
            }
            
            # Cache for 5 minutes
            self.cache.set(self.token_id, endpoint, response, ttl_seconds=300)
            
            logger.info(f"Retrieved {len(teams)} teams")
            return response
        
        return result
    
    def list_team_channels(self, team_id: str):
        """
        List channels of a specific team
        
        Args:
            team_id: Team ID
            
        Returns:
            Dict with channels list and metadata
        """
        endpoint = f'teams/{team_id}/channels'
        
        # Try cache first
        cached = self.cache.get(self.token_id, endpoint)
        if cached:
            return cached
        
        # Make API call
        result = self._make_request(endpoint)
        
        if result['success']:
            channels = result['data'].get('value', [])
            
            response = {
                'channels': channels,
                'count': len(channels),
                'team_id': team_id
            }
            
            # Cache for 5 minutes
            self.cache.set(self.token_id, endpoint, response, ttl_seconds=300)
            
            logger.info(f"Retrieved {len(channels)} channels for team {team_id}")
            return response
        
        return result
    
    def get_channel_messages(self, team_id: str, channel_id: str, top: int = 50):
        """
        Get messages from a specific channel
        
        Args:
            team_id: Team ID
            channel_id: Channel ID
            top: Number of messages to retrieve
            
        Returns:
            Dict with messages list and metadata
        """
        endpoint = f'teams/{team_id}/channels/{channel_id}/messages'
        params = {
            '$top': top,
            '$orderby': 'createdDateTime desc'
        }
        
        # Try cache first
        cached = self.cache.get(self.token_id, endpoint, params)
        if cached:
            return cached
        
        # Make API call
        result = self._make_request(endpoint, params=params)
        
        if result['success']:
            messages = result['data'].get('value', [])
            
            response = {
                'messages': messages,
                'count': len(messages),
                'team_id': team_id,
                'channel_id': channel_id,
                '@odata.nextLink': result['data'].get('@odata.nextLink')
            }
            
            # Cache for 1 minute
            self.cache.set(self.token_id, endpoint, response, ttl_seconds=60, params=params)
            
            logger.info(f"Retrieved {len(messages)} messages from channel {channel_id}")
            return response
        
        return result
    
    def send_channel_message(self, team_id: str, channel_id: str, content: str, 
                           content_type: str = 'html'):
        """
        Send a message in a channel
        
        Args:
            team_id: Team ID
            channel_id: Channel ID
            content: Message content
            content_type: Content type ('text' or 'html')
            
        Returns:
            Dict with sent message details
        """
        endpoint = f'teams/{team_id}/channels/{channel_id}/messages'
        
        # Prepare message body
        message_data = {
            'body': {
                'contentType': content_type,
                'content': content
            }
        }
        
        # Send message
        result = self._make_request(endpoint, method='POST', json=message_data)
        
        if result['success']:
            # Invalidate cache for this channel's messages
            self.cache.invalidate(self.token_id, endpoint)
            
            logger.info(f"Message sent to channel {channel_id} in team {team_id}")
            return {
                'success': True,
                'message': result['data'],
                'team_id': team_id,
                'channel_id': channel_id
            }
        
        return result
