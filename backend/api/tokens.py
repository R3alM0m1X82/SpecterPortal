"""
Token API endpoints - WITH MULTI-TOKEN SUPPORT
"""
import base64
import json
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.audience_token_manager import AudienceTokenManager

tokens_bp = Blueprint('tokens', __name__, url_prefix='/api/tokens')


@tokens_bp.route('', methods=['GET'])
def get_tokens():
    tokens = TokenService.get_all_tokens()
    return jsonify({
        'success': True,
        'tokens': tokens,
        'count': len(tokens)
    })


@tokens_bp.route('/<int:token_id>', methods=['GET'])
def get_token(token_id):
    # Returns complete token
    token = TokenService.get_token_by_id(token_id, full=True)
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Token not found'
        }), 404
    
    return jsonify({
        'success': True,
        'token': token
    })


@tokens_bp.route('/active', methods=['GET'])
def get_active_token():
    token = TokenService.get_active_token()
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'No active token'
        }), 404
    
    return jsonify({
        'success': True,
        'token': token
    })


@tokens_bp.route('/import', methods=['POST'])
def import_tokens():
    try:
        json_data = request.get_json()
        
        if not json_data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        data = json_data.get('data')
        filename = json_data.get('filename', 'unknown.json')
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing "data" field in request'
            }), 400
        
        result = TokenService.import_from_json(data, filename)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tokens_bp.route('/import-jwt', methods=['POST'])
def import_jwt():
    """
    Import a raw JWT access token.
    Expects JSON body: { "jwt": "eyJ..." }
    """
    from database import db
    from models.token import Token
    from datetime import datetime
    
    try:
        data = request.get_json()
        if not data or 'jwt' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing jwt field'
            }), 400
        
        jwt_token = data['jwt'].strip()
        
        # Validate JWT format (3 parts separated by dots)
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return jsonify({
                'success': False,
                'error': 'Invalid JWT format: expected 3 parts separated by dots'
            }), 400
        
        # Decode the payload (middle part)
        try:
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            # Replace URL-safe characters
            payload_b64 = payload_b64.replace('-', '+').replace('_', '/')
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to decode JWT payload: {str(e)}'
            }), 400
        
        # Extract claims from payload
        upn = payload.get('upn') or payload.get('unique_name') or payload.get('preferred_username')
        aud = payload.get('aud', '')
        appid = payload.get('appid') or payload.get('azp', '')
        scp = payload.get('scp', '')
        exp = payload.get('exp')
        
        # Parse expiration
        expires_at = None
        if exp:
            try:
                expires_at = datetime.utcfromtimestamp(exp)
            except:
                pass
        
        # Check if token is expired
        if expires_at and expires_at < datetime.utcnow():
            return jsonify({
                'success': False,
                'error': 'Token is expired'
            }), 400
        
        # Create token directly in database
        token = Token(
            client_id=appid or 'unknown',
            upn=upn,
            scope=scp,
            audience=aud,
            access_token=jwt_token,
            refresh_token=None,
            expires_at=expires_at,
            imported_from='jwt_import',
            token_type='access_token',
            source='jwt_import'
        )
        
        db.session.add(token)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'JWT imported successfully',
            'imported': 1,
            'token_id': token.id,
            'token_info': {
                'upn': upn,
                'audience': aud,
                'token_type': 'access_token'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tokens_bp.route('/<int:token_id>/activate', methods=['POST'])
def activate_token(token_id):
    result = TokenService.activate_token(token_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404


@tokens_bp.route('/<int:token_id>', methods=['DELETE'])
def delete_token(token_id):
    result = TokenService.delete_token(token_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404


@tokens_bp.route('/expired', methods=['DELETE'])
def delete_expired_tokens():
    """Delete all expired access tokens"""
    result = TokenService.delete_expired_tokens()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================
# Multi-Token System Endpoints
# ============================================

@tokens_bp.route('/audiences', methods=['GET'])
def get_available_audiences():
    """
    Get list of available audiences for current user
    
    Returns which audiences have tokens and FOCI capability
    """
    result = AudienceTokenManager.get_available_audiences()
    
    return jsonify({
        'success': True,
        **result
    })


@tokens_bp.route('/audience/<path:audience>', methods=['GET'])
def get_token_for_audience(audience):
    """
    Get or create token for specific audience
    
    Will automatically:
    1. Return existing token if available
    2. FOCI exchange if needed
    
    Example: /api/tokens/audience/https://graph.windows.net
    """
    # URL decode the audience
    audience = audience.replace('%3A', ':').replace('%2F', '/')
    
    result = AudienceTokenManager.get_token_for_audience(audience)
    
    if result['success']:
        # Don't return full access_token in response
        return jsonify({
            'success': True,
            'token_id': result.get('token_id'),
            'source': result.get('source'),
            'upn': result.get('upn'),
            'audience': audience
        })
    else:
        return jsonify(result), 400


@tokens_bp.route('/exchange', methods=['POST'])
def foci_exchange():
    """
    Force FOCI token exchange for specific audience
    
    Request body:
    {
        "audience": "https://graph.windows.net"
    }
    
    Will create new token via FOCI exchange
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('audience'):
            return jsonify({
                'success': False,
                'error': 'Missing "audience" in request body'
            }), 400
        
        audience = data['audience']
        
        result = AudienceTokenManager.get_token_for_audience(audience)
        
        if result['success']:
            return jsonify({
                'success': True,
                'token_id': result.get('token_id'),
                'source': result.get('source'),
                'upn': result.get('upn'),
                'audience': audience,
                'expires_at': result.get('expires_at')
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tokens_bp.route('/status', methods=['GET'])
def get_multi_token_status():
    """
    Get overall multi-token system status
    
    Returns:
    - Primary token info
    - Available audiences
    - FOCI capability
    """
    # Get primary token
    primary = TokenService.get_active_token()
    
    if not primary:
        return jsonify({
            'success': False,
            'error': 'No active token',
            'hint': 'Please activate a token first'
        }), 404
    
    # Get audience info
    audiences = AudienceTokenManager.get_available_audiences(primary.get('upn'))
    
    return jsonify({
        'success': True,
        'primary_token': {
            'id': primary.get('id'),
            'upn': primary.get('upn'),
            'audience': primary.get('audience'),
            'client_app': primary.get('client_app_name'),
            'is_foci': primary.get('is_foci'),
            'has_refresh_token': primary.get('has_refresh_token'),
            'expires_at': primary.get('expires_at')
        },
        'audiences': audiences.get('audiences', {}),
        'foci_available': audiences.get('foci_available', False),
        'known_audiences': AudienceTokenManager.AUDIENCES
    })
