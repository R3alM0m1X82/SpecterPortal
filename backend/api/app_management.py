"""
App Management API - Create, Delete, Manage App Registrations
Works with standard user permissions when "Users can register applications" = Yes
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.app_management_service import AppManagementService

app_mgmt_bp = Blueprint('app_management', __name__, url_prefix='/api/apps')


def get_active_token():
    """Get active token and validate"""
    token_dict = TokenService.get_active_token()
    if not token_dict:
        return None, None, {'success': False, 'error': 'No active token'}
    
    access_token_full = token_dict.get('access_token_full')
    
    if not access_token_full or access_token_full.endswith('...'):
        return None, None, {'success': False, 'error': 'Active token is invalid or truncated'}
    
    return token_dict.get('id'), access_token_full, None


@app_mgmt_bp.route('/policy', methods=['GET'])
def check_app_registration_policy():
    """Check if users can register applications"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = AppManagementService(access_token)
        result = service.check_app_registration_allowed()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/my-apps', methods=['GET'])
def get_my_applications():
    """Get applications owned by current user"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = AppManagementService(access_token)
        result = service.get_my_applications()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/create', methods=['POST'])
def create_application():
    """Create a new App Registration"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    display_name = data.get('displayName')
    
    if not display_name:
        return jsonify({'success': False, 'error': 'displayName is required'}), 400
    
    if len(display_name) < 1 or len(display_name) > 120:
        return jsonify({'success': False, 'error': 'displayName must be 1-120 characters'}), 400
    
    try:
        service = AppManagementService(access_token)
        result = service.create_application(
            display_name=display_name,
            sign_in_audience=data.get('signInAudience', 'AzureADMyOrg'),
            redirect_uris=data.get('redirectUris', []),
            description=data.get('description')
        )
        
        if result['success']:
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/<app_object_id>', methods=['GET'])
def get_application_details(app_object_id):
    """Get details of a specific application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = AppManagementService(access_token)
        result = service.get_application_details(app_object_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/<app_object_id>', methods=['DELETE'])
def delete_application(app_object_id):
    """Delete an App Registration"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = AppManagementService(access_token)
        result = service.delete_application(app_object_id)
        
        if result['success']:
            return jsonify(result), 200
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/<app_object_id>/secrets', methods=['POST'])
def add_client_secret(app_object_id):
    """Add a client secret to an application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    description = data.get('description', 'SpecterPortal Secret')
    expiry_months = data.get('expiryMonths', 12)
    
    # Validate expiry months
    if expiry_months not in [1, 6, 12, 24]:
        return jsonify({'success': False, 'error': 'expiryMonths must be 1, 6, 12, or 24'}), 400
    
    try:
        service = AppManagementService(access_token)
        result = service.add_client_secret(
            app_object_id=app_object_id,
            description=description,
            expiry_months=expiry_months
        )
        
        if result['success']:
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app_mgmt_bp.route('/<app_object_id>/secrets/<key_id>', methods=['DELETE'])
def remove_client_secret(app_object_id, key_id):
    """Remove a client secret from an application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = AppManagementService(access_token)
        result = service.remove_client_secret(app_object_id, key_id)
        
        if result['success']:
            return jsonify(result), 200
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
