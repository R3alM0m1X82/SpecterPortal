"""
Teams Secrets Scanner Service
Orchestrates scanning of Teams conversations for secrets/credentials
Uses Skype API for message access + SecretDetector for pattern matching
"""
import uuid
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime
from flask import current_app
from services.skype_service import SkypeService
from services.teams_skype_service import TeamsSkypeService
from services.secret_detector import SecretDetector, SecretMatch
from services.token_service import TokenService
import logging

logger = logging.getLogger(__name__)


class TeamsScanManager:
    """Manager for Teams conversation scanning operations"""
    
    # In-memory storage for active scans
    active_scans: Dict[str, Dict] = {}
    scan_lock = threading.Lock()
    
    @staticmethod
    def create_scan(token_id: int, options: Dict) -> Dict:
        """
        Create a new scan session
        
        Args:
            token_id: Token ID to use for scanning
            options: Scan options (max_conversations, enabled_patterns, etc)
            
        Returns:
            Dict with scan_id and initial status
        """
        scan_id = str(uuid.uuid4())[:8]  # Short UUID
        
        # Get token info
        token = TokenService.get_token_by_id(token_id)
        if not token:
            return {
                'success': False,
                'error': 'Token not found'
            }
        
        # Initialize scan entry
        scan_entry = {
            'scan_id': scan_id,
            'token_id': token_id,
            'status': 'initializing',
            'start_time': int(time.time()),
            'end_time': None,
            'user_email': token.get('upn', 'Unknown'),
            'options': options,
            'progress': {
                'total_conversations': 0,
                'scanned_conversations': 0,
                'total_messages': 0,
                'secrets_found': 0,
                'current_conversation_name': '',
                'percent': 0
            },
            'secrets': [],
            'conversations': [],
            'error': None
        }
        
        with TeamsScanManager.scan_lock:
            TeamsScanManager.active_scans[scan_id] = scan_entry
        
        logger.info(f"Created scan {scan_id} for token {token_id}")
        
        return {
            'success': True,
            'scan_id': scan_id,
            'scan': scan_entry
        }
    
    @staticmethod
    def start_scan(scan_id: str) -> Dict:
        """
        Start scanning process in background thread
        
        Args:
            scan_id: Scan ID to start
            
        Returns:
            Dict with success status
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            
            if scan['status'] != 'initializing':
                return {
                    'success': False,
                    'error': f'Scan already {scan["status"]}'
                }
        
        # Capture Flask app for worker thread
        app = current_app._get_current_object()
        
        # Start scan in background thread
        scan_thread = threading.Thread(
            target=TeamsScanManager._run_scan_worker,
            args=(scan_id, app),
            daemon=True
        )
        scan_thread.start()
        
        logger.info(f"Started scan {scan_id} in background thread")
        
        return {
            'success': True,
            'message': 'Scan started'
        }
    
    @staticmethod
    def _run_scan_worker(scan_id: str, app):
        """
        Worker thread that performs the actual scanning
        
        Args:
            scan_id: Scan ID to process
            app: Flask application instance
        """
        with app.app_context():
            try:
                with TeamsScanManager.scan_lock:
                    scan = TeamsScanManager.active_scans.get(scan_id)
                    if not scan:
                        return
                    
                    scan['status'] = 'running'
                    token_id = scan['token_id']
                    options = scan['options']
                
                logger.info(f"[{scan_id}] Starting scan worker")
                
                # Get token
                token = TokenService.get_token_by_id(token_id)
                if not token:
                    TeamsScanManager._update_scan_error(scan_id, 'Token not found')
                    return
                
                # DEBUG: Log token info
                print(f"[{scan_id}] Token keys: {list(token.keys())}")
                print(f"[{scan_id}] Token has 'access_token_full': {'access_token_full' in token}")
                print(f"[{scan_id}] Token has 'access_token': {'access_token' in token}")
                if 'access_token_full' in token:
                    token_full_len = len(token['access_token_full']) if token['access_token_full'] else 0
                    print(f"[{scan_id}] Token 'access_token_full' length: {token_full_len}")
                if 'access_token' in token:
                    token_len = len(token['access_token']) if token['access_token'] else 0
                    print(f"[{scan_id}] Token 'access_token' length: {token_len}")
                
                # Get Skype token
                logger.info(f"[{scan_id}] Requesting Skype token")
                access_token_to_use = token.get('access_token_full') or token.get('access_token')
                print(f"[{scan_id}] Using access_token length: {len(access_token_to_use) if access_token_to_use else 0}")
                
                skype_result = SkypeService.get_or_create_skype_token(
                    token_id=token_id,
                    access_token=access_token_to_use,
                    audience=token['audience']
                )
                
                if not skype_result['success']:
                    TeamsScanManager._update_scan_error(scan_id, f"Skype token error: {skype_result.get('error')}")
                    return
                
                skype_token_data = skype_result['skype_token']
                
                # Initialize Teams service
                teams_service = TeamsSkypeService(
                    skype_token=skype_token_data['skype_token'],
                    chat_service_url=skype_token_data['chat_service_url']
                )
                
                # Get conversations
                logger.info(f"[{scan_id}] Fetching conversations")
                conv_result = teams_service.list_conversations(page_size=500)
                
                if not conv_result['success']:
                    TeamsScanManager._update_scan_error(scan_id, f"Failed to get conversations: {conv_result.get('error')}")
                    return
                
                conversations = conv_result['conversations']
                
                # Filter conversations
                filtered_convs = []
                for conv in conversations:
                    # Skip notification threads
                    if conv.get('threadProperties', {}).get('threadType') == 'streamofnotifications':
                        continue
                    
                    # Skip empty conversations if option enabled
                    if options.get('skip_empty', True):
                        if conv.get('properties', {}).get('isemptyconversation') == 'True':
                            continue
                    
                    filtered_convs.append(conv)
                
                # Apply max conversations limit
                max_conversations = options.get('max_conversations', 100)
                filtered_convs = filtered_convs[:max_conversations]
                
                # Update progress
                with TeamsScanManager.scan_lock:
                    scan = TeamsScanManager.active_scans[scan_id]
                    scan['progress']['total_conversations'] = len(filtered_convs)
                
                logger.info(f"[{scan_id}] Scanning {len(filtered_convs)} conversations")
                
                # Initialize secret detector
                detector = SecretDetector()
                
                # Scan each conversation
                for idx, conv in enumerate(filtered_convs):
                    # Check if scan was stopped
                    with TeamsScanManager.scan_lock:
                        scan = TeamsScanManager.active_scans.get(scan_id)
                        if not scan or scan['status'] == 'stopped':
                            logger.info(f"[{scan_id}] Scan stopped by user")
                            return
                    
                    conv_id = conv.get('id', '')
                    conv_name = TeamsScanManager._get_conversation_name(conv)
                    messages_link = conv.get('messages', '')
                    
                    if not messages_link:
                        continue
                    
                    # Update current conversation
                    with TeamsScanManager.scan_lock:
                        scan = TeamsScanManager.active_scans[scan_id]
                        scan['progress']['current_conversation_name'] = conv_name
                    
                    logger.info(f"[{scan_id}] Scanning conversation: {conv_name}")
                    
                    # Get messages
                    try:
                        msg_result = teams_service.get_conversation_messages(
                            conversation_link=messages_link,
                            page_size=200
                        )
                        
                        if not msg_result['success']:
                            logger.warning(f"[{scan_id}] Failed to get messages for {conv_name}: {msg_result.get('error')}")
                            continue
                        
                        messages = msg_result['messages']
                        
                        # Scan messages for secrets
                        secrets = detector.scan_messages(
                            messages=messages,
                            conversation_id=conv_id,
                            conversation_name=conv_name
                        )
                        
                        # Update scan results
                        with TeamsScanManager.scan_lock:
                            scan = TeamsScanManager.active_scans[scan_id]
                            
                            # Add secrets
                            for secret in secrets:
                                scan['secrets'].append({
                                    'id': str(uuid.uuid4())[:8],
                                    'secret_type': secret.secret_type.value,
                                    'value': secret.raw_value,  # Full unredacted secret value
                                    'redacted_value': secret.redacted_value,
                                    'confidence': secret.confidence,
                                    'entropy': secret.entropy,
                                    'severity': secret.severity,
                                    'conversation_id': secret.conversation_id,
                                    'conversation_name': secret.conversation_name,
                                    'message_id': secret.message_id,
                                    'sender': secret.sender,
                                    'timestamp': secret.timestamp,
                                    'context_before': secret.context_before,
                                    'context_after': secret.context_after,
                                    'message_content': secret.message_content,
                                    'extra_data': secret.extra_data
                                })
                            
                            # Update progress
                            scan['progress']['scanned_conversations'] = idx + 1
                            scan['progress']['total_messages'] += len(messages)
                            scan['progress']['secrets_found'] = len(scan['secrets'])
                            scan['progress']['percent'] = int(((idx + 1) / len(filtered_convs)) * 100)
                            
                            # Add conversation to list
                            scan['conversations'].append({
                                'id': conv_id,
                                'name': conv_name,
                                'messages_count': len(messages),
                                'secrets_found': len(secrets)
                            })
                        
                        logger.info(f"[{scan_id}] Found {len(secrets)} secrets in {conv_name}")
                        
                    except Exception as e:
                        logger.error(f"[{scan_id}] Error scanning conversation {conv_name}: {str(e)}")
                        continue
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                
                # Mark scan as completed
                with TeamsScanManager.scan_lock:
                    scan = TeamsScanManager.active_scans[scan_id]
                    scan['status'] = 'completed'
                    scan['end_time'] = int(time.time())
                    scan['progress']['percent'] = 100
                    scan['progress']['current_conversation_name'] = 'Completed'
                
                logger.info(f"[{scan_id}] Scan completed - Found {scan['progress']['secrets_found']} secrets")
                
            except Exception as e:
                logger.error(f"[{scan_id}] Scan worker error: {str(e)}")
                TeamsScanManager._update_scan_error(scan_id, f"Scan error: {str(e)}")
    
    @staticmethod
    def _get_conversation_name(conv: Dict) -> str:
        """Extract conversation name from conversation object"""
        # Try topic first
        topic = conv.get('threadProperties', {}).get('topic', '')
        if topic and topic.strip():
            return topic.strip()
        
        # Try space thread topic
        space_topic = conv.get('threadProperties', {}).get('spaceThreadTopic', '')
        if space_topic and space_topic.strip():
            return space_topic.strip()
        
        # Try last message sender
        last_msg = conv.get('lastMessage', {})
        sender = last_msg.get('imdisplayname', '')
        if sender and not sender.startswith('8:'):
            return f"Chat with {sender}"
        
        # Fallback
        conv_id = conv.get('id', '')
        if 'meeting_' in conv_id:
            return "Meeting Chat"
        elif '@thread' in conv_id:
            return "Group Chat"
        
        return "Unknown Chat"
    
    @staticmethod
    def _update_scan_error(scan_id: str, error: str):
        """Update scan with error status"""
        with TeamsScanManager.scan_lock:
            if scan_id in TeamsScanManager.active_scans:
                scan = TeamsScanManager.active_scans[scan_id]
                scan['status'] = 'error'
                scan['error'] = error
                scan['end_time'] = int(time.time())
        logger.error(f"[{scan_id}] {error}")
    
    @staticmethod
    def get_scan_progress(scan_id: str) -> Dict:
        """
        Get current scan progress
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict with progress info
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            
            return {
                'success': True,
                'scan_id': scan_id,
                'status': scan['status'],
                'progress': scan['progress'],
                'start_time': scan['start_time'],
                'end_time': scan['end_time'],
                'error': scan.get('error')
            }
    
    @staticmethod
    def get_scan_results(scan_id: str, filters: Optional[Dict] = None) -> Dict:
        """
        Get scan results with optional filtering
        
        Args:
            scan_id: Scan ID
            filters: Optional filters (severity, secret_type, limit)
            
        Returns:
            Dict with results
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            secrets = scan['secrets']
            
            # Apply filters
            if filters:
                severity_filter = filters.get('severity')
                if severity_filter:
                    secrets = [s for s in secrets if s['severity'] == severity_filter]
                
                type_filter = filters.get('secret_type')
                if type_filter:
                    secrets = [s for s in secrets if s['secret_type'] == type_filter]
                
                limit = filters.get('limit', 500)
                secrets = secrets[:limit]
            
            return {
                'success': True,
                'scan_id': scan_id,
                'status': scan['status'],
                'progress': scan['progress'],
                'secrets': secrets,
                'total_secrets': len(scan['secrets']),
                'filtered_count': len(secrets),
                'conversations': scan['conversations']
            }
    
    @staticmethod
    def stop_scan(scan_id: str) -> Dict:
        """
        Stop a running scan
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict with success status
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            
            if scan['status'] != 'running':
                return {
                    'success': False,
                    'error': f'Scan is {scan["status"]}, cannot stop'
                }
            
            scan['status'] = 'stopped'
            scan['end_time'] = int(time.time())
        
        logger.info(f"Stopped scan {scan_id}")
        
        return {
            'success': True,
            'message': 'Scan stopped'
        }
    
    @staticmethod
    def delete_scan(scan_id: str) -> Dict:
        """
        Delete a scan from memory
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict with success status
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            del TeamsScanManager.active_scans[scan_id]
        
        logger.info(f"Deleted scan {scan_id}")
        
        return {
            'success': True,
            'message': 'Scan deleted'
        }
    
    @staticmethod
    def list_scans() -> Dict:
        """
        List all active scans
        
        Returns:
            Dict with list of scans
        """
        with TeamsScanManager.scan_lock:
            scans = []
            for scan_id, scan in TeamsScanManager.active_scans.items():
                scans.append({
                    'scan_id': scan_id,
                    'status': scan['status'],
                    'user_email': scan['user_email'],
                    'start_time': scan['start_time'],
                    'end_time': scan['end_time'],
                    'progress': scan['progress']
                })
        
        return {
            'success': True,
            'scans': scans,
            'count': len(scans)
        }
    
    @staticmethod
    def get_message_context(scan_id: str, message_id: str) -> Dict:
        """
        Get context messages around a specific message (for viewing full conversation)
        
        Args:
            scan_id: Scan ID
            message_id: Message ID to get context for
            
        Returns:
            Dict with context messages
        """
        # For now, return the secret's context (before/after text)
        # In future, could fetch actual surrounding messages from API
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            
            # Find secret with this message_id
            for secret in scan['secrets']:
                if secret['message_id'] == message_id:
                    return {
                        'success': True,
                        'message_id': message_id,
                        'context': {
                            'before': secret['context_before'],
                            'message': secret['message_content'],
                            'after': secret['context_after'],
                            'conversation_name': secret['conversation_name'],
                            'sender': secret['sender'],
                            'timestamp': secret['timestamp']
                        }
                    }
            
            return {
                'success': False,
                'error': 'Message not found'
            }
    
    @staticmethod
    def export_results(scan_id: str) -> Dict:
        """
        Export scan results in TruffleHog-compatible format
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict with export data
        """
        with TeamsScanManager.scan_lock:
            if scan_id not in TeamsScanManager.active_scans:
                return {
                    'success': False,
                    'error': 'Scan not found'
                }
            
            scan = TeamsScanManager.active_scans[scan_id]
            
            export_data = {
                'scan_info': {
                    'scan_id': scan_id,
                    'scan_time': datetime.fromtimestamp(scan['start_time']).isoformat(),
                    'user_email': scan['user_email'],
                    'conversations_scanned': scan['progress']['scanned_conversations'],
                    'messages_scanned': scan['progress']['total_messages'],
                    'secrets_found': len(scan['secrets'])
                },
                'results': []
            }
            
            for secret in scan['secrets']:
                export_data['results'].append({
                    'DetectorType': secret['secret_type'],
                    'Verified': False,
                    'Raw': secret['value'],  # Full secret value
                    'Redacted': secret['redacted_value'],  # Redacted for display
                    'Confidence': secret['confidence'],
                    'Severity': secret['severity'],
                    'Entropy': secret['entropy'],
                    'ExtraData': {
                        'sender': secret['sender'],
                        'conversation_id': secret['conversation_id'],
                        'conversation_name': secret['conversation_name'],
                        **secret.get('extra_data', {})
                    },
                    'SourceMetadata': {
                        'Data': {
                            'Teams': {
                                'message_id': secret['message_id'],
                                'timestamp': secret['timestamp'],
                                'context_before': secret['context_before'],
                                'context_after': secret['context_after']
                            }
                        }
                    }
                })
            
            return {
                'success': True,
                'export': export_data
            }
