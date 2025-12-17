"""
Refresh Token API endpoints
"""
from flask import Blueprint, request, jsonify
from services.refresh_service import RefreshTokenService

refresh_bp = Blueprint('refresh', __name__, url_prefix='/api/refresh')


@refresh_bp.route('/<int:token_id>/use', methods=['POST'])
def use_refresh_token(token_id):
    """
    Use a refresh token to obtain a new access token
    
    Body (optional):
        {
            "target_client_id": "client-id-of-foci-app",
            "target_resource": "https://graph.microsoft.com/.default"
        }
    """
    try:
        data = request.get_json() or {}
        target_client_id = data.get('target_client_id')
        target_resource = data.get('target_resource')
        
        result = RefreshTokenService.use_refresh_token(
            token_id,
            target_client_id=target_client_id,
            target_resource=target_resource
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@refresh_bp.route('/<int:token_id>/foci-targets', methods=['GET'])
def get_foci_targets(token_id):
    """
    Get list of FOCI apps available for this refresh token
    """
    try:
        result = RefreshTokenService.get_foci_targets(token_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@refresh_bp.route('/stats', methods=['GET'])
def get_refresh_stats():
    """Get refresh token statistics"""
    try:
        stats = RefreshTokenService.get_refresh_token_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500