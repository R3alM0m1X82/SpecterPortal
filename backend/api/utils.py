"""
Utils API endpoints
Token utilities for power users
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.utils_service import UtilsService

utils_bp = Blueprint('utils', __name__, url_prefix='/api/utils')


def _get_active_token_or_error():
    """Helper to get active token or return error"""
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    if not token.get('access_token_full') or token['access_token_full'].endswith('...'):
        return None, (jsonify({
            'success': False,
            'error': 'Active token is truncated or invalid'
        }), 401)

    return token, None


@utils_bp.route('/decode-jwt', methods=['POST'])
def decode_jwt():
    """
    Decode JWT Access Token
    
    POST /api/utils/decode-jwt
    
    Request body (optional):
    {
        "access_token": "eyJhbGc..."  // If not provided, uses active token
    }
    
    Returns:
    {
        "success": true,
        "header": {...},
        "payload": {...},
        "expires_in_seconds": 3600,
        "is_expired": false,
        "identity": "user@domain.com"
    }
    """
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')
        
        # If no token provided, use active token
        if not access_token:
            token, error = _get_active_token_or_error()
            if error:
                return error
            access_token = token['access_token_full']
        
        result = UtilsService.decode_jwt(access_token)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Decode JWT error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@utils_bp.route('/analyze-scope', methods=['POST'])
def analyze_scope():
    """
    Analyze token scopes and return capabilities
    
    POST /api/utils/analyze-scope
    
    Request body (optional):
    {
        "scope": "User.Read Files.ReadWrite.All"  // If not provided, uses active token scope
    }
    
    Returns:
    {
        "success": true,
        "scopes": ["User.Read", "Files.ReadWrite.All"],
        "capabilities": {
            "User Operations": ["Read own profile"],
            "File Operations": ["Read/write all files"]
        },
        "missing_high_value": ["User.ReadWrite.All", ...],
        "admin_scopes": ["Files.ReadWrite.All"],
        "warnings": [...]
    }
    """
    try:
        data = request.get_json() or {}
        scope = data.get('scope')
        
        # If no scope provided, use active token scope
        if not scope:
            token, error = _get_active_token_or_error()
            if error:
                return error
            scope = token.get('scope', '')
        
        result = UtilsService.analyze_scope(scope)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Analyze scope error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@utils_bp.route('/validate-token', methods=['POST'])
def validate_token():
    """
    Validate JWT token structure, expiration, and claims
    
    POST /api/utils/validate-token
    
    Request body (optional):
    {
        "access_token": "eyJhbGc..."  // If not provided, uses active token
    }
    
    Returns:
    {
        "success": true,
        "valid": true,
        "checks": {
            "structure": {"valid": true, "message": "..."},
            "expiration": {"valid": true, "message": "Valid for 2h 30m"},
            "audience": {"valid": true, "audience": "graph.microsoft.com"},
            "issuer": {"valid": true, "issuer": "sts.windows.net/..."}
        },
        "warnings": [],
        "can_be_used": true
    }
    """
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')
        
        # If no token provided, use active token
        if not access_token:
            token, error = _get_active_token_or_error()
            if error:
                return error
            access_token = token['access_token_full']
        
        result = UtilsService.validate_token(access_token)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Validate token error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@utils_bp.route('/generate-curl', methods=['POST'])
def generate_curl():
    """
    Generate cURL command for Microsoft Graph API
    
    POST /api/utils/generate-curl
    
    Request body (optional):
    {
        "access_token": "eyJhbGc...",  // If not provided, uses active token
        "endpoint": "https://graph.microsoft.com/v1.0/users",
        "method": "GET"
    }
    
    Returns:
    {
        "success": true,
        "curl_command": "curl -X GET ..."
    }
    """
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')
        endpoint = data.get('endpoint')
        method = data.get('method', 'GET')
        
        # If no token provided, use active token
        if not access_token:
            token, error = _get_active_token_or_error()
            if error:
                return error
            access_token = token['access_token_full']
        
        result = UtilsService.generate_curl(access_token, endpoint, method)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Generate cURL error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@utils_bp.route('/export-json', methods=['POST'])
def export_json():
    """
    Export token to JSON format
    
    POST /api/utils/export-json
    
    Request body (optional):
    {
        "token_id": 62  // If not provided, exports active token
    }
    
    Returns:
    {
        "success": true,
        "json_output": {...}
    }
    """
    try:
        data = request.get_json() or {}
        token_id = data.get('token_id')
        
        # Get token data
        if token_id:
            token = TokenService.get_token_by_id(token_id, full=True)
            if not token:
                return jsonify({
                    'success': False,
                    'error': f'Token {token_id} not found'
                }), 404
        else:
            token = TokenService.get_active_token()
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'No active token'
                }), 401
        
        result = UtilsService.export_token_json(token)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Export JSON error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@utils_bp.route('/generate-powershell', methods=['POST'])
def generate_powershell():
    """
    Generate PowerShell script for Microsoft Graph API
    
    POST /api/utils/generate-powershell
    
    Request body (optional):
    {
        "access_token": "eyJhbGc...",  // If not provided, uses active token
        "endpoint": "https://graph.microsoft.com/v1.0/users"
    }
    
    Returns:
    {
        "success": true,
        "powershell_script": "..."
    }
    """
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')
        endpoint = data.get('endpoint')
        
        # If no token provided, use active token
        if not access_token:
            token, error = _get_active_token_or_error()
            if error:
                return error
            access_token = token['access_token_full']
        
        result = UtilsService.generate_powershell(access_token, endpoint)
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Generate PowerShell error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
