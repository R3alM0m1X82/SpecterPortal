"""
Admin Actions API Routes 
Handles: Capability Check, FOCI Exchange, Password Reset, TAP, MFA Management
Location: api/admin_actions.py
"""
from flask import Blueprint, request, jsonify
from services.admin_actions_service import AdminActionsService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ========================================
# CAPABILITY CHECK 
# ========================================

@admin_bp.route('/check-capabilities', methods=['POST'])
def check_capabilities():
    """
    Check if current token has admin capabilities.
    
    Request:
        { 
            "access_token": "eyJ...",
            "action_type": "password_reset" | "tap_mfa" (optional)
        }
    
    Response:
        {
            "success": true,
            "has_admin_role": true/false,
            "has_required_scope": true/false,
            "can_perform_actions": true/false,
            "detected_roles": ["Global Administrator", ...],
            "detected_scopes": ["User.Read", ...],
            "missing_scopes": ["Directory.AccessAsUser.All", ...],
            "foci_available": true/false,
            "recommendation": null | "no_role" | "foci_auto_exchange" | "device_code_required" | "no_scope_no_foci",
            "action_type": "password_reset" | "tap_mfa" | null
        }
    """
    data = request.get_json()
    access_token = data.get('access_token')
    action_type = data.get('action_type')  # NEW: optional action_type filter
    
    if not access_token:
        return jsonify({'success': False, 'error': 'access_token required'}), 400
    
    result = AdminActionsService.check_capabilities(access_token, action_type=action_type)
    return jsonify(result)


@admin_bp.route('/foci-exchange', methods=['POST'])
def foci_exchange():
    """
    Perform FOCI exchange to get Azure PowerShell token with admin scopes.
    This is triggered manually by user button click.
    
    Request:
        { "access_token": "eyJ..." }
    
    Response (success):
        {
            "success": true,
            "access_token": "eyJ...",
            "capabilities": { ... },
            "expires_at": "2024-01-15T...",
            "client_id": "1950a258-..."
        }
    
    Response (error):
        {
            "success": false,
            "error": "No refresh token available..."
        }
    """
    data = request.get_json()
    access_token = data.get('access_token')
    
    if not access_token:
        return jsonify({'success': False, 'error': 'access_token required'}), 400
    
    result = AdminActionsService.foci_exchange_for_admin(access_token)
    return jsonify(result)


@admin_bp.route('/auto-acquire-token', methods=['POST'])
def auto_acquire_token():
    """
    AUTO-ACQUIRE TOKEN for Password Reset (FOCI) or TAP/MFA (Device Code).
    This endpoint handles automatic token acquisition based on action_type.
    
    For 'password_reset': Auto FOCI exchange with Azure PowerShell
    For 'tap_mfa': Requires device_code_data from frontend
    
    Request:
        {
            "access_token": "eyJ...",
            "action_type": "password_reset" | "tap_mfa",
            "device_code_data": { ... } (only for tap_mfa)
        }
    
    Response:
        {
            "success": true,
            "token_id": 123,
            "access_token": "eyJ...",
            "capabilities": { ... },
            "method": "foci_exchange" | "device_code"
        }
    """
    data = request.get_json()
    access_token = data.get('access_token')
    action_type = data.get('action_type')
    
    if not access_token or not action_type:
        return jsonify({'success': False, 'error': 'access_token and action_type required'}), 400
    
    if action_type == 'password_reset':
        # AUTO FOCI EXCHANGE for Password Reset
        result = AdminActionsService.auto_foci_exchange_password_reset(access_token)
        if result['success']:
            result['method'] = 'foci_exchange'
        return jsonify(result)
    
    elif action_type == 'tap_mfa':
        # Device Code Flow - frontend provides device_code_data
        device_code_data = data.get('device_code_data')
        
        if not device_code_data:
            return jsonify({
                'success': False,
                'error': 'device_code_data required for tap_mfa action_type'
            }), 400
        
        # Save token from device code data
        result = AdminActionsService.save_device_code_token(
            access_token=device_code_data.get('access_token'),
            refresh_token=device_code_data.get('refresh_token'),
            client_id=device_code_data.get('client_id'),
            source_method='device_code'
        )
        
        if result['success']:
            result['method'] = 'device_code'
        
        return jsonify(result)
    
    else:
        return jsonify({
            'success': False,
            'error': f'Invalid action_type: {action_type}. Must be password_reset or tap_mfa.'
        }), 400


# ========================================
# USER MANAGEMENT
# ========================================

@admin_bp.route('/create-user', methods=['POST'])
def create_user():
    """Create a new user in Azure AD"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_data = data.get('user_data')
    
    if not access_token or not user_data:
        return jsonify({'success': False, 'error': 'access_token and user_data required'}), 400
    
    result = AdminActionsService.create_user(access_token, user_data)
    return jsonify(result)


# ========================================
# PASSWORD RESET
# ========================================

@admin_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset a user's password"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    new_password = data.get('new_password')
    force_change = data.get('force_change', True)
    
    if not access_token or not user_id or not new_password:
        return jsonify({'success': False, 'error': 'access_token, user_id, and new_password required'}), 400
    
    result = AdminActionsService.reset_password(access_token, user_id, new_password, force_change)
    return jsonify(result)


# ========================================
# TAP MANAGEMENT
# ========================================

@admin_bp.route('/tap/create', methods=['POST'])
def create_tap():
    """Create a Temporary Access Pass"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    lifetime = data.get('lifetime_minutes', 60)
    is_usable_once = data.get('is_usable_once', False)
    
    if not access_token or not user_id:
        return jsonify({'success': False, 'error': 'access_token and user_id required'}), 400
    
    result = AdminActionsService.create_tap(access_token, user_id, lifetime, is_usable_once)
    return jsonify(result)


@admin_bp.route('/tap/list', methods=['POST'])
def list_tap():
    """List TAPs for a user"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    
    if not access_token or not user_id:
        return jsonify({'success': False, 'error': 'access_token and user_id required'}), 400
    
    result = AdminActionsService.list_tap(access_token, user_id)
    return jsonify(result)


@admin_bp.route('/tap/delete', methods=['POST'])
def delete_tap():
    """Delete a TAP"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    tap_id = data.get('tap_id')
    
    if not access_token or not user_id or not tap_id:
        return jsonify({'success': False, 'error': 'access_token, user_id, and tap_id required'}), 400
    
    result = AdminActionsService.delete_tap(access_token, user_id, tap_id)
    return jsonify(result)


# ========================================
# MFA / AUTH METHODS
# ========================================

@admin_bp.route('/auth-methods/list', methods=['POST'])
def list_auth_methods():
    """List authentication methods for a user"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    
    if not access_token or not user_id:
        return jsonify({'success': False, 'error': 'access_token and user_id required'}), 400
    
    result = AdminActionsService.list_auth_methods(access_token, user_id)
    return jsonify(result)


@admin_bp.route('/auth-methods/delete', methods=['POST'])
def delete_auth_method():
    """Delete an authentication method"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    method_type = data.get('method_type')
    method_id = data.get('method_id')
    
    if not access_token or not user_id or not method_type or not method_id:
        return jsonify({'success': False, 'error': 'access_token, user_id, method_type, and method_id required'}), 400
    
    result = AdminActionsService.delete_auth_method(access_token, user_id, method_type, method_id)
    return jsonify(result)


@admin_bp.route('/auth-methods/add-phone', methods=['POST'])
def add_phone_method():
    """Add a phone authentication method"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    phone_number = data.get('phone_number')
    phone_type = data.get('phone_type', 'mobile')
    
    if not access_token or not user_id or not phone_number:
        return jsonify({'success': False, 'error': 'access_token, user_id, and phone_number required'}), 400
    
    result = AdminActionsService.add_phone_method(access_token, user_id, phone_number, phone_type)
    return jsonify(result)


@admin_bp.route('/auth-methods/add-email', methods=['POST'])
def add_email_method():
    """Add an email authentication method"""
    data = request.get_json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    email_address = data.get('email_address')
    
    if not access_token or not user_id or not email_address:
        return jsonify({'success': False, 'error': 'access_token, user_id, and email_address required'}), 400
    
    result = AdminActionsService.add_email_method(access_token, user_id, email_address)
    return jsonify(result)
