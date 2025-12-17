"""
Roles API - Directory Roles and License management
Added active-user-info endpoint for Dashboard
Added au-scoped endpoint for AU-scoped roles enumeration
Enhanced active-user-info with AU-scoped role detection
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.roles_service import RolesService
from services.admin_actions_service import AdminActionsService
from services.cache_service import graph_cache

roles_bp = Blueprint('roles', __name__, url_prefix='/api/roles')


def get_active_token():
    """Get active token and validate"""
    token_dict = TokenService.get_active_token()
    if not token_dict:
        return None, None, None, {'success': False, 'error': 'No active token'}
    
    token_id = token_dict.get('id')
    access_token_full = token_dict.get('access_token_full')
    upn = token_dict.get('upn')
    
    if not access_token_full or access_token_full.endswith('...'):
        return None, None, None, {'success': False, 'error': 'Active token is invalid'}
    
    return token_id, access_token_full, upn, None


@roles_bp.route('/active-user-info', methods=['GET'])
def get_active_user_info():
    """
    Get roles and licenses for the active token's user - for Dashboard
    Now includes AU-scoped roles detection
    """
    token_id, access_token, upn, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    if not upn:
        return jsonify({'success': False, 'error': 'No UPN in active token'}), 400
    
    # Check cache
    cached = graph_cache.get(token_id, 'active_user_info')
    if cached:
        return jsonify(cached)
    
    try:
        # Step 1: Get directory-level roles and licenses (from /me/memberOf)
        service = RolesService(access_token)
        result = service.get_user_info_with_roles_licenses(upn)
        result['upn'] = upn
        
        if not result['success']:
            return jsonify(result), 500
        
        # Step 2: Check for AU-scoped roles using AdminActionsService
        print(f"[Active User Info] Checking AU-scoped roles for {upn}...")
        au_roles = AdminActionsService._check_au_scoped_roles(access_token)
        
        if au_roles:
            print(f"[Active User Info] Found {len(au_roles)} AU-scoped role(s)")
            
            # Extract role names (remove "(AU: ...)" suffix)
            au_role_names = []
            existing_roles = set(role.get('displayName', '') for role in result.get('roles', []))
            
            for au_role_str in au_roles:
                # "Helpdesk Administrator (AU: c4351d8e...)" -> "Helpdesk Administrator"
                role_name = au_role_str.split(' (AU:')[0]
                if role_name not in existing_roles:
                    au_role_names.append(role_name)
            
            # Add AU-scoped roles to the roles list
            if au_role_names:
                for role_name in au_role_names:
                    result['roles'].append({
                        'displayName': role_name,
                        'id': 'au-scoped',  # Placeholder ID
                        'description': 'AU-scoped role',
                        'roleTemplateId': 'unknown'
                    })
                
                result['has_au_scoped_roles'] = True
                result['au_scoped_roles'] = au_roles  # Keep full strings with AU IDs
                print(f"[Active User Info] Added {len(au_role_names)} unique AU-scoped roles")
        else:
            print("[Active User Info] No AU-scoped roles found")
            result['has_au_scoped_roles'] = False
        
        # Cache the enriched result
        graph_cache.set(token_id, 'active_user_info', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[Active User Info] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/user/<user_id>/roles', methods=['GET'])
def get_user_roles(user_id):
    """Get directory roles for a specific user"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = RolesService(access_token)
        result = service.get_user_roles(user_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/user/<user_id>/licenses', methods=['GET'])
def get_user_licenses(user_id):
    """Get licenses for a specific user"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = RolesService(access_token)
        result = service.get_user_licenses(user_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/directory-roles', methods=['GET'])
def get_directory_roles():
    """Get all directory roles"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'directory_roles')
    if cached:
        return jsonify(cached)
    
    try:
        service = RolesService(access_token)
        result = service.get_directory_roles()
        
        if result['success']:
            graph_cache.set(token_id, 'directory_roles', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/directory-roles/<role_id>/members', methods=['GET'])
def get_role_members(role_id):
    """Get members of a directory role"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = RolesService(access_token)
        result = service.get_role_members(role_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/licenses', methods=['GET'])
def get_licenses():
    """Get all subscribed SKUs"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'subscribed_skus')
    if cached:
        return jsonify(cached)
    
    try:
        service = RolesService(access_token)
        result = service.get_subscribed_skus()
        
        if result['success']:
            graph_cache.set(token_id, 'subscribed_skus', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/licenses/<sku_id>/users', methods=['GET'])
def get_license_users(sku_id):
    """Get users with a specific license"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = RolesService(access_token)
        result = service.get_license_users(sku_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/privileged', methods=['GET'])
def get_privileged_roles():
    """Get privileged roles with members"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'privileged_roles')
    if cached:
        return jsonify(cached)
    
    try:
        service = RolesService(access_token)
        result = service.get_privileged_roles()
        
        if result['success']:
            graph_cache.set(token_id, 'privileged_roles', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@roles_bp.route('/security-summary', methods=['GET'])
def get_security_summary():
    """Get security summary"""
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'security_summary')
    if cached:
        return jsonify(cached)
    
    try:
        service = RolesService(access_token)
        result = service.get_security_summary()
        
        if result['success']:
            graph_cache.set(token_id, 'security_summary', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# NEW: AU-Scoped Roles Endpoint
# ============================================================

@roles_bp.route('/au-scoped', methods=['GET'])
def get_au_scoped_roles():
    """
    Get ALL AU-scoped role assignments in the tenant.
    Enumerates all Administrative Units and their scoped role members.
    
    This is useful for security audits to find delegated admin permissions
    that aren't visible in the standard /directoryRoles endpoint.
    
    Returns:
        - administrative_units: List of AUs with their scoped role assignments
        - au_scoped_roles: Flat list of all AU-scoped assignments
        - role_summary: Aggregated view by role name
        - total_assignments: Total count of AU-scoped role assignments
    """
    token_id, access_token, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    # Check cache (longer TTL since this is expensive)
    cached = graph_cache.get(token_id, 'au_scoped_roles')
    if cached:
        return jsonify(cached)
    
    try:
        service = RolesService(access_token)
        result = service.get_all_au_scoped_roles()
        
        if result['success']:
            # Cache for 10 minutes (this query can be slow)
            graph_cache.set(token_id, 'au_scoped_roles', result, ttl_seconds=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
