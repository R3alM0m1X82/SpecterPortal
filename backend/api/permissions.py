"""
Permissions API - Analyze active token permissions and capabilities
Optimized for cache performance
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.permission_service import PermissionService
from services.roles_service import RolesService

permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/permissions')


def get_active_token():
    """Get active token and validate"""
    token_dict = TokenService.get_active_token()
    if not token_dict:
        return None, None, None, {'success': False, 'error': 'No active token'}
    
    access_token_full = token_dict.get('access_token_full')
    upn = token_dict.get('upn')
    
    if not access_token_full or access_token_full.endswith('...'):
        return None, None, None, {'success': False, 'error': 'Active token is invalid or truncated'}
    
    return access_token_full, upn, token_dict, None


@permissions_bp.route('/analyze', methods=['GET'])
def analyze_permissions():
    """
    Analyze current active token and return all permissions/capabilities
    This is the main endpoint for permission detection
    
    Note: AU-scoped roles are NOT in JWT wids claims.
    They're only visible via Graph API /roleAssignments.
    Dashboard's /api/roles/active-user-info handles AU detection (cached).
    """
    access_token, upn, token_dict, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        # Step 1: Analyze JWT claims (directory-level roles from wids)
        result = PermissionService.analyze_admin_capabilities(access_token)
        
        if not result['success']:
            return jsonify(result), 500
        
        # Note: AU-scoped roles are NOT in JWT wids claims
        # They're only visible via Graph API roleAssignments
        # Dashboard's active-user-info endpoint handles AU detection (cached)
        result['has_au_scoped_roles'] = False
        
        # Step 2: Add privilege badge
        result['privilege_badge'] = PermissionService.get_privilege_badge(
            result['privilege_level']
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[Permissions API] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@permissions_bp.route('/extract', methods=['GET'])
def extract_permissions():
    """
    Extract raw permission data from token (roles, scopes, claims)
    Lighter endpoint for quick checks
    """
    access_token, _, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        result = PermissionService.extract_permissions(access_token)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@permissions_bp.route('/check/<action_id>', methods=['GET'])
def check_action(action_id):
    """
    Check if a specific action is available
    
    Valid action_ids:
    - create_user
    - reset_password
    - manage_tap
    - manage_mfa
    - manage_groups
    - manage_applications
    - assign_licenses
    - manage_roles
    - manage_conditional_access
    - manage_devices
    """
    access_token, _, _, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        result = PermissionService.check_specific_action(access_token, action_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@permissions_bp.route('/actions', methods=['GET'])
def list_actions():
    """
    List all available admin actions and their requirements
    Does not require active token - just returns the action definitions
    """
    actions = {}
    
    for action_id, action_config in PermissionService.ADMIN_ACTIONS.items():
        actions[action_id] = {
            'name': action_config['name'],
            'description': action_config['description'],
            'required_roles': action_config['required_roles'],
            'required_scopes': action_config['required_scopes'],
            'risk_level': action_config['risk_level'],
            'notes': action_config.get('notes')
        }
    
    return jsonify({
        'success': True,
        'actions': actions,
        'count': len(actions)
    })


@permissions_bp.route('/roles', methods=['GET'])
def list_directory_roles():
    """
    List all known directory roles with their GUIDs
    Useful for reference
    """
    roles = PermissionService.get_all_known_roles()
    
    # Sort by name
    roles.sort(key=lambda x: x['name'])
    
    return jsonify({
        'success': True,
        'roles': roles,
        'count': len(roles)
    })


@permissions_bp.route('/decode', methods=['POST'])
def decode_token():
    """
    Decode any JWT token (for debugging)
    Accepts token in request body
    """
    data = request.get_json() or {}
    token = data.get('token')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'token is required in request body'
        }), 400
    
    try:
        claims = PermissionService.decode_jwt(token)
        
        if claims:
            return jsonify({
                'success': True,
                'claims': claims
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to decode token'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
