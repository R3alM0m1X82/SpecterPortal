"""
Teams API Routes
Exposes Microsoft Teams functionality via REST endpoints
"""

from flask import Blueprint, request, jsonify
from services.teams_service import TeamsService
from services.token_service import TokenService
import logging

logger = logging.getLogger(__name__)

# Create blueprint
teams_bp = Blueprint('teams', __name__, url_prefix='/api/teams')


def _get_active_token():
    """Get the currently active token's full access token and ID"""
    token_service = TokenService()
    active_token = token_service.get_active_token()
    
    if not active_token:
        raise ValueError("No active token found")
    
    # Use access_token_full, not truncated version
    return active_token['access_token_full'], active_token['id']


@teams_bp.route('/chats', methods=['GET'])
def list_chats():
    """
    GET /api/teams/chats
    List user's chats
    
    Query params:
        - top: Number of chats (default 50)
    """
    try:
        # Get parameters
        top = request.args.get('top', 50, type=int)
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get chats
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.list_chats(top=top)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing chats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/chats/<chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """
    GET /api/teams/chats/{chat_id}/messages
    Get messages from a specific chat
    
    Query params:
        - top: Number of messages per page (default 50)
        - load_all: Load all messages following pagination (default true)
    """
    try:
        # Get parameters
        top = request.args.get('top', 50, type=int)
        load_all = request.args.get('load_all', 'true').lower() == 'true'
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get messages
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.get_chat_messages(chat_id, top=top, load_all=load_all)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/chats/<chat_id>/messages', methods=['POST'])
def send_chat_message(chat_id):
    """
    POST /api/teams/chats/{chat_id}/messages
    Send a message in a chat
    
    Body:
        {
            "content": "Message text",
            "contentType": "text" | "html"  (optional, default "text")
        }
    """
    try:
        # Get request data
        data = request.get_json()
        content = data.get('content')
        content_type = data.get('contentType', 'text')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Send message
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.send_chat_message(chat_id, content, content_type)
        
        return jsonify(result), 201
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending chat message: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/teams', methods=['GET'])
def list_teams():
    """
    GET /api/teams/teams
    List user's joined teams
    """
    try:
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get teams
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.list_teams()
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing teams: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/teams/<team_id>/channels', methods=['GET'])
def list_team_channels(team_id):
    """
    GET /api/teams/teams/{team_id}/channels
    List channels of a specific team
    """
    try:
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get channels
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.list_team_channels(team_id)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing team channels: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/teams/<team_id>/channels/<channel_id>/messages', methods=['GET'])
def get_channel_messages(team_id, channel_id):
    """
    GET /api/teams/teams/{team_id}/channels/{channel_id}/messages
    Get messages from a specific channel
    
    Query params:
        - top: Number of messages (default 50)
    """
    try:
        # Get parameters
        top = request.args.get('top', 50, type=int)
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get messages
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.get_channel_messages(team_id, channel_id, top=top)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting channel messages: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/teams/<team_id>/channels/<channel_id>/messages', methods=['POST'])
def send_channel_message(team_id, channel_id):
    """
    POST /api/teams/teams/{team_id}/channels/{channel_id}/messages
    Send a message in a channel
    
    Body:
        {
            "content": "Message text",
            "contentType": "text" | "html"  (optional, default "html")
        }
    """
    try:
        # Get request data
        data = request.get_json()
        content = data.get('content')
        content_type = data.get('contentType', 'html')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Send message
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.send_channel_message(team_id, channel_id, content, content_type)
        
        return jsonify(result), 201
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending channel message: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    GET /api/teams/me
    Get current user information
    """
    try:
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Get current user
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.get_current_user()
        
        if result:
            return jsonify({'success': True, 'user': result}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to get user info'}), 500
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/proxy/image', methods=['GET'])
def proxy_graph_image():
    """
    GET /api/teams/proxy/image?url=<graph_api_image_url>
    Proxy Graph API image requests with authentication
    """
    try:
        image_url = request.args.get('url')
        
        if not image_url:
            return jsonify({'error': 'URL parameter required'}), 400
        
        # Validate URL is from Graph API
        if not image_url.startswith('https://graph.microsoft.com/'):
            return jsonify({'error': 'Invalid URL - must be Graph API'}), 400
        
        # Get active token
        access_token, token_id = _get_active_token()
        
        # Proxy image
        teams_service = TeamsService(access_token, token_id)
        result = teams_service.proxy_graph_image(image_url)
        
        if result['success']:
            from flask import Response
            return Response(
                result['data'],
                mimetype=result['content_type'],
                headers={'Cache-Control': 'public, max-age=3600'}  # Cache 1 hour
            )
        else:
            return jsonify({'error': result['error']}), 500
        
    except ValueError as e:
        logger.error(f"Token error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error proxying image: {str(e)}")
        return jsonify({'error': str(e)}), 500
