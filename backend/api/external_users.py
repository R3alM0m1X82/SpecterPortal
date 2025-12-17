"""
External Users API endpoints
Handles guest/external user enumeration from Azure AD
"""

from flask import Blueprint, jsonify, request
from services.external_users_service import ExternalUsersService
from services.token_service import TokenService

external_users_bp = Blueprint('external_users', __name__)

def get_access_token():
    """Get the current active access token"""
    active_token = TokenService.get_active_token()
    if not active_token:
        return None
    # TokenService.get_active_token() returns a dict
    if isinstance(active_token, dict):
        return active_token.get('access_token')
    # Fallback for object-style access
    return getattr(active_token, 'access_token', None)


@external_users_bp.route('/api/external-users', methods=['GET'])
def get_external_users():
    """Get all external/guest users"""
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    result = service.get_external_users()
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@external_users_bp.route('/api/external-users/stats', methods=['GET'])
def get_external_users_stats():
    """Get statistics about external users"""
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    result = service.get_external_users()
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result.get('stats', {}))


@external_users_bp.route('/api/external-users/<user_id>', methods=['GET'])
def get_external_user_details(user_id):
    """Get detailed information about a specific external user"""
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    result = service.get_guest_details(user_id)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@external_users_bp.route('/api/external-users/<user_id>/memberships', methods=['GET'])
def get_external_user_memberships(user_id):
    """Get group memberships for an external user"""
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    result = service.get_user_memberships(user_id)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@external_users_bp.route('/api/external-users/inactive', methods=['GET'])
def get_inactive_guests():
    """Get external users who haven't signed in recently"""
    days = request.args.get('days', 90, type=int)
    
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    result = service.get_inactive_guests(days)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@external_users_bp.route('/api/external-users/export', methods=['GET'])
def export_external_users():
    """Export external users to CSV"""
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'No active token'}), 401
    
    service = ExternalUsersService(access_token)
    
    from flask import Response
    csv_data = service.export_guests()
    
    if isinstance(csv_data, dict) and 'error' in csv_data:
        return jsonify(csv_data), 500
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=external_users.csv'}
    )
