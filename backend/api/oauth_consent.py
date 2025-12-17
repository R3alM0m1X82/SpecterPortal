"""
OAuth Consent API endpoints
Application Consent Auditor
Added owner analysis support
"""
from flask import Blueprint, jsonify, request
from services.oauth_consent_service import OAuthConsentService
from services.token_service import TokenService

oauth_consent_bp = Blueprint('oauth_consent', __name__, url_prefix='/api/oauth-consent')


def get_active_token_info():
    """Get access token and token ID from active token"""
    active_token = TokenService.get_active_token()
    if not active_token:
        return None, None
    return active_token.get('access_token'), active_token.get('id')


@oauth_consent_bp.route('', methods=['GET'])
def get_consent_audit():
    """
    Get full OAuth consent audit with risk assessment
    
    Returns all apps with consent and their risk scores
    """
    access_token, token_id = get_active_token_info()
    if not access_token:
        return jsonify({
            'success': False,
            'error': 'No active token. Please activate a token first.'
        }), 401
    
    try:
        service = OAuthConsentService(access_token, token_id)
        result = service.get_consent_audit()
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), result.get('status', 500)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@oauth_consent_bp.route('/risky', methods=['GET'])
def get_risky_apps():
    """
    Get only risky apps (Medium risk and above)
    
    Query params:
    - min_level: Minimum risk level (Low, Medium, High, Critical)
    """
    access_token, token_id = get_active_token_info()
    if not access_token:
        return jsonify({
            'success': False,
            'error': 'No active token. Please activate a token first.'
        }), 401
    
    min_level = request.args.get('min_level', 'Medium')
    
    try:
        service = OAuthConsentService(access_token, token_id)
        result = service.get_risky_apps_only(min_level)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), result.get('status', 500)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@oauth_consent_bp.route('/stats', methods=['GET'])
def get_consent_stats():
    """
    Get just the summary statistics without full app list
    Faster for dashboard widgets
    """
    access_token, token_id = get_active_token_info()
    if not access_token:
        return jsonify({
            'success': False,
            'error': 'No active token. Please activate a token first.'
        }), 401
    
    try:
        service = OAuthConsentService(access_token, token_id)
        result = service.get_consent_audit()
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), result.get('status', 500)
        
        return jsonify({
            'success': True,
            'stats': result.get('stats', {})
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@oauth_consent_bp.route('/batch-owners', methods=['POST'])
def get_consent_batch_owners():
    """
    Get owners for consent apps on-demand (lazy loading)
    Sprint 11.2
    
    POST body:
    {
      "appIds": ["id1", "id2", ...]
    }
    """
    access_token, token_id = get_active_token_info()
    if not access_token:
        return jsonify({
            'success': False,
            'error': 'No active token. Please activate a token first.'
        }), 401
    
    data = request.get_json() or {}
    app_ids = data.get('appIds', [])
    
    if not app_ids:
        return jsonify({
            'success': False,
            'error': 'appIds is required'
        }), 400
    
    try:
        service = OAuthConsentService(access_token, token_id)
        result = service.get_owners_for_consent_apps(app_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
