"""
Teams Skype API Routes
Exposes Teams functionality via Skype API (no Chat.Read scope required)
"""

from flask import Blueprint, request, jsonify
from services.skype_service import SkypeService
from services.teams_skype_service import TeamsSkypeService
from services.token_service import TokenService
import logging

logger = logging.getLogger(__name__)

# Create blueprint
teams_skype_bp = Blueprint('teams_skype', __name__, url_prefix='/api/teams/skype')


def _get_active_token_for_skype():
    """Get the currently active token if it's valid for Skype API"""
    token_service = TokenService()
    active_token = token_service.get_active_token()
    
    if not active_token:
        raise ValueError("No active token found")
    
    # Check if token is for Skype resource
    audience = active_token.get('audience', '')
    if 'api.spaces.skype.com' not in audience:
        raise ValueError(f"Active token is for '{audience}', not for Skype API. Please use a Refresh Token to generate an Access Token for 'https://api.spaces.skype.com'")
    
    return active_token


@teams_skype_bp.route('/exchange', methods=['POST'])
def exchange_token():
    """
    POST /api/teams/skype/exchange
    Exchange Access Token for Skype Token
    
    Uses the currently active token
    """
    try:
        # Get active token
        active_token = _get_active_token_for_skype()
        
        # Exchange for Skype token
        result = SkypeService.get_or_create_skype_token(
            token_id=active_token['id'],
            access_token=active_token['access_token_full'],
            audience=active_token['audience']
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error exchanging token: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_skype_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """
    GET /api/teams/skype/conversations
    List user's conversations via Skype API
    
    Query params:
        - page_size: Number of conversations (default 500)
    """
    try:
        # Get active token
        active_token = _get_active_token_for_skype()
        
        # Get or create Skype token
        skype_result = SkypeService.get_or_create_skype_token(
            token_id=active_token['id'],
            access_token=active_token['access_token_full'],
            audience=active_token['audience']
        )
        
        if not skype_result['success']:
            return jsonify(skype_result), 400
        
        skype_token_data = skype_result['skype_token']
        
        # Get conversations
        page_size = request.args.get('page_size', 500, type=int)
        
        teams_service = TeamsSkypeService(
            skype_token=skype_token_data['skype_token'],
            chat_service_url=skype_token_data['chat_service_url']
        )
        
        result = teams_service.list_conversations(page_size=page_size)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_skype_bp.route('/conversations/messages', methods=['POST'])
def get_conversation_messages():
    """
    POST /api/teams/skype/conversations/messages
    Get messages from a conversation
    
    Body:
        {
            "conversation_link": "https://...",
            "page_size": 200,  // optional
            "start_time": 0     // optional
        }
    """
    try:
        # Get request data
        data = request.get_json()
        conversation_link = data.get('conversation_link')
        
        if not conversation_link:
            return jsonify({'success': False, 'error': 'conversation_link is required'}), 400
        
        page_size = data.get('page_size', 200)
        start_time = data.get('start_time', 0)
        
        # Get active token
        active_token = _get_active_token_for_skype()
        
        # Get or create Skype token
        skype_result = SkypeService.get_or_create_skype_token(
            token_id=active_token['id'],
            access_token=active_token['access_token_full'],
            audience=active_token['audience']
        )
        
        if not skype_result['success']:
            return jsonify(skype_result), 400
        
        skype_token_data = skype_result['skype_token']
        
        # Get messages
        teams_service = TeamsSkypeService(
            skype_token=skype_token_data['skype_token'],
            chat_service_url=skype_token_data['chat_service_url']
        )
        
        result = teams_service.get_conversation_messages(
            conversation_link=conversation_link,
            page_size=page_size,
            start_time=start_time
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_skype_bp.route('/conversations/send', methods=['POST'])
def send_conversation_message():
    """
    POST /api/teams/skype/conversations/send
    Send a message to a conversation
    
    Body:
        {
            "conversation_link": "https://...",
            "content": "Message text",
            "message_type": "RichText/Html"  // optional
        }
    """
    try:
        # Get request data
        data = request.get_json()
        conversation_link = data.get('conversation_link')
        content = data.get('content')
        
        if not conversation_link:
            return jsonify({'success': False, 'error': 'conversation_link is required'}), 400
        
        if not content:
            return jsonify({'success': False, 'error': 'content is required'}), 400
        
        message_type = data.get('message_type', 'RichText/Html')
        
        # Get active token
        active_token = _get_active_token_for_skype()
        
        # Get or create Skype token
        skype_result = SkypeService.get_or_create_skype_token(
            token_id=active_token['id'],
            access_token=active_token['access_token_full'],
            audience=active_token['audience']
        )
        
        if not skype_result['success']:
            return jsonify(skype_result), 400
        
        skype_token_data = skype_result['skype_token']
        
        # Send message
        teams_service = TeamsSkypeService(
            skype_token=skype_token_data['skype_token'],
            chat_service_url=skype_token_data['chat_service_url']
        )
        
        result = teams_service.send_conversation_message(
            conversation_link=conversation_link,
            content=content,
            message_type=message_type
        )
        
        return jsonify(result), 201 if result['success'] else 400
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_skype_bp.route('/proxy/image', methods=['GET'])
def proxy_image():
    """
    GET /api/teams/skype/proxy/image?url=<image_url>
    Proxy endpoint for Skype ASM images that require authentication
    """
    try:
        import requests
        from flask import Response
        
        image_url = request.args.get('url')
        
        if not image_url:
            return jsonify({'success': False, 'error': 'url parameter is required'}), 400
        
        # Get active token
        active_token = _get_active_token_for_skype()
        
        # Get or create Skype token
        skype_result = SkypeService.get_or_create_skype_token(
            token_id=active_token['id'],
            access_token=active_token['access_token_full'],
            audience=active_token['audience']
        )
        
        if not skype_result['success']:
            return jsonify(skype_result), 400
        
        skype_token = skype_result['skype_token']['skype_token']
        
        # Fetch image with Skype token
        headers = {
            'Authorization': f'skypetoken={skype_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Return image with correct content type
            content_type = response.headers.get('Content-Type', 'image/png')
            return Response(response.content, mimetype=content_type)
        else:
            logger.error(f"Failed to fetch image: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Failed to fetch image: {response.status_code}'
            }), response.status_code
            
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error proxying image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

