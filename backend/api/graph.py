"""
Graph API endpoints - WITH MULTI-TOKEN SUPPORT
Uses AudienceTokenManager for automatic token selection
"""
from flask import Blueprint, jsonify
from services.graph_service import GraphService
from services.token_service import TokenService
from services.cache_service import graph_cache
from services.audience_token_manager import AudienceTokenManager

graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

# MS Graph audience
MS_GRAPH_AUDIENCE = 'https://graph.microsoft.com'


def _get_ms_graph_token():
    """
    Get token for Microsoft Graph API
    
    Uses AudienceTokenManager for automatic selection/exchange
    """
    result = AudienceTokenManager.get_token_for_audience(MS_GRAPH_AUDIENCE)
    
    if not result['success']:
        return None, (jsonify({
            'success': False,
            'error': result.get('error', 'Failed to get MS Graph token'),
            'hint': result.get('hint', 'Ensure you have a valid token')
        }), 401)
    
    return result, None


@graph_bp.route('/me', methods=['GET'])
def get_user_profile():
    """Get current user profile - CACHED"""
    token_result, error = _get_ms_graph_token()
    if error:
        return error
    
    token_id = token_result.get('token_id')
    access_token = token_result.get('access_token')
    
    # Check cache first
    cached_data = graph_cache.get(token_id, 'user_profile')
    if cached_data:
        return jsonify(cached_data)
    
    # Create Graph service and get profile
    graph = GraphService(access_token)
    result = graph.get_user_profile()
    
    if result['success']:
        # Cache for 5 minutes
        graph_cache.set(token_id, 'user_profile', result, ttl_seconds=300)
        result['token_source'] = token_result.get('source')
        return jsonify(result)
    else:
        # Pass through the actual status code from Graph API
        status_code = 401
        if result.get('details'):
            if 'TooManyRequests' in result['details'] or '429' in result['details']:
                status_code = 429
        return jsonify(result), status_code


@graph_bp.route('/me/photo', methods=['GET'])
def get_user_photo():
    """Get current user photo"""
    token_result, error = _get_ms_graph_token()
    if error:
        return error
    
    access_token = token_result.get('access_token')
    
    graph = GraphService(access_token)
    result = graph.get_user_photo()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404


@graph_bp.route('/token-status', methods=['GET'])
def get_graph_token_status():
    """
    Check if MS Graph token is available
    
    Useful for UI to show status before making calls
    """
    result = AudienceTokenManager.get_token_for_audience(MS_GRAPH_AUDIENCE)
    
    return jsonify({
        'success': result['success'],
        'audience': MS_GRAPH_AUDIENCE,
        'source': result.get('source'),
        'token_id': result.get('token_id'),
        'error': result.get('error') if not result['success'] else None
    })
