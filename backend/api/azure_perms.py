"""
Azure Permissions API
Multi-token check for ARM, Storage, KeyVault permissions
Intelligently finds correct token for each resource type
Added cache support with force_refresh parameter
"""
from flask import Blueprint, jsonify, session, request
from models.token import Token
from services.permissions_service import PermissionsService
from datetime import datetime
import traceback
import sys
import os
import requests

# Import client_ids per app names
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'models'))
try:
    from client_ids import get_app_name
except:
    def get_app_name(cid): return cid

azure_perms_bp = Blueprint('azure_permissions', __name__, url_prefix='/api/azure/permissions')

def get_token_app_name(token):
    """
    Get token application name
    Uses get_app_name() from client_ids module
    """
    try:
        return get_app_name(token.client_id)
    except:
        return token.client_id or 'Unknown'

def get_token_value(token):
    """
    Get actual token string value
    Token model stores the actual token in 'access_token' field
    """
    # Token model use 'access_token' for save tokens
    return token.access_token

def find_token_for_audience(required_audience, required_scopes=None):
    """
    Find suitable token for specific audience
    PRIORITY: Active token first, then fallback to any matching token
    Returns (token, error_message)
    """
    print(f"[FIND-TOKEN] Searching for audience: {required_audience}")
    
    # Get ALL tokens from DB
    all_tokens = Token.query.all()
    
    if not all_tokens:
        return None, "No tokens available. Please authenticate first."
    
    print(f"[FIND-TOKEN] Total tokens in DB: {len(all_tokens)}")
    
    # Filter for access tokens only
    access_tokens = [t for t in all_tokens if t.token_type == 'access_token']
    
    print(f"[FIND-TOKEN] Access tokens: {len(access_tokens)}")
    
    if not access_tokens:
        return None, "No access tokens available. Please authenticate to get an access token."
    
    # PRIORITY 0: Check if ACTIVE token has the required audience
    active_token = Token.query.filter_by(is_active=True).first()
    if active_token and active_token.token_type == 'access_token':
        print(f"[FIND-TOKEN] Found ACTIVE token #{active_token.id}")
        
        # Check if active token has correct audience
        if active_token.audience and required_audience.lower() in active_token.audience.lower():
            # Check if active token is not expired
            if active_token.expires_at:
                try:
                    # expires_at is already a datetime object from DB, not string
                    from datetime import datetime
                    now = datetime.utcnow()
                    if now < active_token.expires_at:
                        print(f"[FIND-TOKEN] ✓ Using ACTIVE token #{active_token.id} (correct audience)")
                        return active_token, None
                    else:
                        print(f"[FIND-TOKEN] Active token #{active_token.id} is EXPIRED")
                except Exception as e:
                    print(f"[FIND-TOKEN] Error checking active token expiry: {e}")
            else:
                print(f"[FIND-TOKEN] ✓ Using ACTIVE token #{active_token.id} (no expiry, correct audience)")
                return active_token, None
        else:
            print(f"[FIND-TOKEN] Active token #{active_token.id} has WRONG audience: {active_token.audience}")
            print(f"[FIND-TOKEN] Falling back to search other tokens...")
            # CRITICAL: Get UPN from active token to search only tokens of the SAME user
            active_upn = active_token.upn
            print(f"[FIND-TOKEN] Active token UPN: {active_upn}")
    else:
        # No active token - search among all tokens (no UPN filter needed)
        active_upn = None
    
    # Strategy 1: Exact audience match (fallback if active token doesn't match)
    matching_tokens = []
    for token in access_tokens:
        # If we have an active token with wrong audience,
        # only search tokens from the SAME user (same UPN)
        if active_upn and token.upn != active_upn:
            continue  # Skip tokens from other users
        
        print(f"[FIND-TOKEN] Checking token #{token.id}: audience={token.audience}, scope={token.scope}")
        
        if token.audience and required_audience.lower() in token.audience.lower():
            print(f"[FIND-TOKEN] Token #{token.id} matches audience!")
            # Check if token is expired
            if token.expires_at:
                try:
                    # expires_at is already a datetime object from DB, not string
                    from datetime import datetime
                    now = datetime.utcnow()
                    if now < token.expires_at:
                        matching_tokens.append(token)
                        print(f"[FIND-TOKEN] Token #{token.id} is valid (not expired)")
                    else:
                        print(f"[FIND-TOKEN] Token #{token.id} is EXPIRED")
                except Exception as e:
                    print(f"[FIND-TOKEN] Error checking expiry for token #{token.id}: {e}")
                    # If can't parse expiry, include it anyway
                    matching_tokens.append(token)
            else:
                matching_tokens.append(token)
                print(f"[FIND-TOKEN] Token #{token.id} has no expiry, including anyway")
    
    print(f"[FIND-TOKEN] Found {len(matching_tokens)} matching tokens after audience check")
    
    # Strategy 2: Check scopes if no audience match
    if not matching_tokens and required_scopes:
        for token in access_tokens:
            # Apply same UPN filter for consistency
            if active_upn and token.upn != active_upn:
                continue  # Skip tokens from other users
            
            if token.scope:
                token_scopes_lower = token.scope.lower()
                if any(req_scope.lower() in token_scopes_lower for req_scope in required_scopes):
                    # Check if token is expired
                    if token.expires_at:
                        try:
                            from datetime import datetime
                            now = datetime.utcnow()
                            if now < token.expires_at:
                                matching_tokens.append(token)
                        except:
                            matching_tokens.append(token)
                    else:
                        matching_tokens.append(token)
    
    print(f"[FIND-TOKEN] Total matching tokens: {len(matching_tokens)}")
    
    if matching_tokens:
        # Return first matching token (fallback)
        print(f"[FIND-TOKEN] Using fallback token #{matching_tokens[0].id}")
        return matching_tokens[0], None
    
    # No matching token found - build helpful error message
    audience_display = required_audience.replace('https://', '').replace('/.default', '')
    
    # If we filtered by UPN, mention it in the error
    if active_upn:
        error_msg = f"No token found for user '{active_upn}' with audience '{audience_display}'. "
        print(f"[FIND-TOKEN] No matching token found for UPN: {active_upn}")
    else:
        error_msg = f"No active token found for '{audience_display}'. "
    
    # Check if user has Graph tokens but needs ARM
    if 'management' in required_audience.lower():
        if active_upn:
            # User-specific message
            has_graph = any('graph.microsoft.com' in (t.audience or '').lower() and t.upn == active_upn for t in access_tokens)
            if has_graph:
                error_msg += f"Use a Refresh Token for '{active_upn}' to obtain ARM token via FOCI exchange."
            else:
                error_msg += f"Please authenticate '{active_upn}' with Azure PowerShell or Azure CLI to get ARM token."
        else:
            # Generic message (no active token)
            has_graph = any('graph.microsoft.com' in (t.audience or '').lower() for t in access_tokens)
            if has_graph:
                error_msg += "You have Graph API tokens but need an Azure ARM token. "
                error_msg += "Please authenticate with Azure PowerShell or use 'Use RT' on a FOCI refresh token to get ARM token."
            else:
                error_msg += "Please authenticate to obtain an Azure Resource Manager (ARM) access token."
    elif 'storage' in required_audience.lower():
        error_msg += "Please authenticate to obtain a Storage access token."
    elif 'vault' in required_audience.lower():
        error_msg += "Please authenticate to obtain a Key Vault access token."
    else:
        error_msg += f"Please authenticate to obtain an access token for {audience_display}."
    
    return None, error_msg

@azure_perms_bp.route('/my-roles', methods=['GET'])
def get_my_roles():
    """
    Get Azure RBAC role assignments for current principal
    Multi-token check: finds ARM token automatically
    """
    try:
        # Find ARM token
        required_audience = 'https://management.azure.com'
        required_scopes = ['https://management.azure.com/.default', 'https://management.core.windows.net']
        
        token, error_msg = find_token_for_audience(required_audience, required_scopes)
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg,
                'requiresAudience': 'https://management.azure.com/.default',
                'suggestion': 'Authenticate with Azure PowerShell client to get ARM token'
            }), 200  # Still 200 to avoid frontend error handling
        
        print(f"[PERMISSIONS] Using token #{token.id} for ARM API")
        print(f"[PERMISSIONS] Token audience: {token.audience}")
        print(f"[PERMISSIONS] Token app: {get_token_app_name(token)}")
        
        # Initialize permissions service
        permissions_service = PermissionsService(get_token_value(token))
        
        # Get role assignments
        result = permissions_service.get_my_role_assignments()
        
        if result['success']:
            return jsonify({
                'success': True,
                'roleAssignments': result.get('roleAssignments', []),
                'count': result.get('count', 0),
                'tokenUsed': {
                    'id': token.id,
                    'app': get_token_app_name(token),
                    'audience': token.audience
                }
            })
        else:
            # Check if it's permission denied
            if result.get('permission_denied'):
                return jsonify({
                    'success': False,
                    'error': 'Permission denied. Your account does not have the required permissions to view role assignments.',
                    'details': result.get('details', ''),
                    'requiredPermission': 'Microsoft.Authorization/roleAssignments/read',
                    'tokenUsed': {
                        'id': token.id,
                        'app': get_token_app_name(token)
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'details': result.get('details', ''),
                    'tokenUsed': {
                        'id': token.id,
                        'app': get_token_app_name(token)
                    }
                }), 200
                
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_my_roles:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/subscription/<subscription_id>/roles', methods=['GET'])
def get_subscription_roles(subscription_id):
    """Get role assignments for specific subscription"""
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_role_assignments_for_subscription(subscription_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'roleAssignments': result.get('roleAssignments', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_subscription_roles:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/resource/<path:resource_id>/roles', methods=['GET'])
def get_resource_roles(resource_id):
    """Get role assignments for specific resource"""
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_role_assignments_for_resource(resource_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'roleAssignments': result.get('roleAssignments', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_resource_roles:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/keyvault/<vault_id>/permissions', methods=['GET'])
def check_keyvault_permissions(vault_id):
    """Check Key Vault specific permissions"""
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.check_keyvault_permissions(vault_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'permissions': result.get('permissions', {}),
                'roleAssignments': result.get('roleAssignments', [])
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in check_keyvault_permissions:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/check-tokens', methods=['GET'])
def check_available_tokens():
    """
    Utility endpoint to check what tokens are available
    Helps debug token audience issues
    """
    try:
        all_tokens = Token.query.all()
        
        tokens_info = []
        for token in all_tokens:
            if token.token_type == 'access_token':
                is_expired = False
                if token.expires_at:
                    try:
                        expires_at = datetime.fromisoformat(token.expires_at.replace('Z', '+00:00'))
                        is_expired = datetime.now(expires_at.tzinfo) >= expires_at
                    except:
                        pass
                
                tokens_info.append({
                    'id': token.id,
                    'app': get_token_app_name(token),
                    'audience': token.audience,
                    'scope_preview': token.scope[:100] + '...' if token.scope and len(token.scope) > 100 else token.scope,
                    'is_expired': is_expired,
                    'is_active': token.is_active
                })
        
        return jsonify({
            'success': True,
            'total_tokens': len(tokens_info),
            'tokens': tokens_info,
            'has_arm_token': any('management.azure.com' in (t['audience'] or '').lower() for t in tokens_info),
            'has_graph_token': any('graph.microsoft.com' in (t['audience'] or '').lower() for t in tokens_info),
            'has_storage_token': any('storage.azure.com' in (t['audience'] or '').lower() for t in tokens_info)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@azure_perms_bp.route('/effective-all', methods=['GET'])
def get_all_effective_permissions():
    """
    Get effective permissions for ALL resources
    PowerShell equivalent: foreach($Resource in Get-AzResource) { GET /permissions }
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        print(f"[EFFECTIVE PERMS] Using token #{token.id} for ARM API")
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_all_effective_permissions()
        
        if result['success']:
            return jsonify({
                'success': True,
                'effectivePermissions': result.get('effectivePermissions', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[EFFECTIVE PERMS ERROR] Exception:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/role-assignments-all', methods=['GET'])
def get_all_role_assignments():
    """
    Get ALL role assignments (subscription + resource level)
    PowerShell equivalent: Get-AzRoleAssignment
    Now includes group memberships via Graph API
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        print(f"[ROLE ASSIGNMENTS ALL] Using token #{token.id} for ARM API")
        
        # Try to find Graph token for group membership lookup (optional)
        graph_token_obj, _ = find_token_for_audience('https://graph.microsoft.com')
        graph_token = get_token_value(graph_token_obj) if graph_token_obj else None
        
        if graph_token:
            print(f"[ROLE ASSIGNMENTS ALL] Found Graph token for group membership lookup")
        else:
            print(f"[ROLE ASSIGNMENTS ALL] No Graph token available - will show only direct assignments")
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_all_role_assignments_complete(graph_token=graph_token)
        
        if result['success']:
            return jsonify({
                'success': True,
                'roleAssignments': result.get('roleAssignments', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[ROLE ASSIGNMENTS ALL ERROR] Exception:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/resources', methods=['GET'])
def get_all_resources():
    """
    Get all Azure resources
    PowerShell equivalent: Get-AzResource
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_all_resources()
        
        if result['success']:
            return jsonify({
                'success': True,
                'resources': result.get('resources', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[RESOURCES ERROR] Exception:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

# ==================== NEW ENDPOINTS WITH CACHE SUPPORT ====================

@azure_perms_bp.route('/my', methods=['GET'])
def get_my_permissions():
    """
    Get my Azure RBAC permissions ( with cache)
    Query params:
    - subscription_id (optional): Filter to specific subscription
    - force_refresh (optional): Bypass cache and force new query (default: false)
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg,
                'needs_token': True,
                'audience': 'https://management.azure.com/.default'
            }), 200
        
        subscription_id = request.args.get('subscription_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_my_permissions(
            subscription_id=subscription_id,
            force_refresh=force_refresh
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_my_permissions:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/assignments', methods=['GET'])
def get_all_assignments():
    """
    Get ALL role assignments (all principals) across subscriptions (with cache)
    Query params:
    - subscription_id (optional): Filter to specific subscription
    - force_refresh (optional): Bypass cache and force new query (default: false)
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg,
                'needs_token': True,
                'audience': 'https://management.azure.com/.default'
            }), 200
        
        subscription_id = request.args.get('subscription_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_all_role_assignments(
            subscription_id=subscription_id,
            force_refresh=force_refresh
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_all_assignments:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/effective/<principal_id>', methods=['GET'])
def get_effective_permissions(principal_id):
    """
    Get effective permissions for a specific principal (with cache)
    Includes direct assignments + inherited from groups
    Query params:
    - subscription_id (optional): Filter to specific subscription
    - force_refresh (optional): Bypass cache and force new query (default: false)
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg,
                'needs_token': True,
                'audience': 'https://management.azure.com/.default'
            }), 200
        
        subscription_id = request.args.get('subscription_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_effective_permissions(
            principal_id=principal_id,
            subscription_id=subscription_id,
            force_refresh=force_refresh
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_effective_permissions:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """
    Get all Azure subscriptions (uses cached data from permissions_service)
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg,
                'needs_token': True,
                'audience': 'https://management.azure.com/.default'
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        result = permissions_service.get_subscriptions()
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 200
            
    except Exception as e:
        print("[PERMISSIONS ERROR] Exception in get_subscriptions:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@azure_perms_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear all cached permissions data
    Admin/debugging endpoint
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'No ARM token available'
            }), 200
        
        permissions_service = PermissionsService(get_token_value(token))
        permissions_service.clear_all_cache()
        
        return jsonify({
            'success': True,
            'message': 'All cache entries cleared'
        })
        
    except Exception as e:
        print("[CACHE ERROR] Exception in clear_cache:")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

# ==================== UPN RESOLUTION ====================

@azure_perms_bp.route('/resolve-principal/<object_id>', methods=['GET'])
def resolve_principal(object_id):
    """
    Resolve objectId to UPN/displayName via Microsoft Graph API
    
    For Key Vault Access Policies UPN display
    
    Tries:
    1. User lookup (returns UPN)
    2. Service Principal lookup (returns displayName)
    3. Group lookup (returns displayName)
    
    Response:
    {
        "success": true,
        "principal": {
            "objectId": "...",
            "userPrincipalName": "user@domain.com",  # If user
            "displayName": "Name",
            "principalType": "User|ServicePrincipal|Group"
        }
    }
    """
    try:
        # Find Graph token
        token, error_msg = find_token_for_audience('https://graph.microsoft.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'No Microsoft Graph token available',
                'hint': 'Acquire token with audience: https://graph.microsoft.com'
            }), 200
        
        graph_token = get_token_value(token)
        
        headers = {
            'Authorization': f'Bearer {graph_token}',
            'Content-Type': 'application/json'
        }
        
        # Try 1: User
        try:
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/users/{object_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return jsonify({
                    'success': True,
                    'principal': {
                        'objectId': object_id,
                        'userPrincipalName': user_data.get('userPrincipalName'),
                        'displayName': user_data.get('displayName'),
                        'principalType': 'User'
                    }
                })
        except:
            pass
        
        # Try 2: Service Principal
        try:
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/servicePrincipals/{object_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                sp_data = response.json()
                return jsonify({
                    'success': True,
                    'principal': {
                        'objectId': object_id,
                        'displayName': sp_data.get('displayName'),
                        'appId': sp_data.get('appId'),
                        'principalType': 'ServicePrincipal'
                    }
                })
        except:
            pass
        
        # Try 3: Group
        try:
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/groups/{object_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                group_data = response.json()
                return jsonify({
                    'success': True,
                    'principal': {
                        'objectId': object_id,
                        'displayName': group_data.get('displayName'),
                        'principalType': 'Group'
                    }
                })
        except:
            pass
        
        # Not found
        return jsonify({
            'success': False,
            'error': 'Principal not found',
            'objectId': object_id
        }), 200
        
    except Exception as e:
        print(f"[RESOLVE PRINCIPAL ERROR] {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== GLOBAL ADMIN ELEVATION ====================

@azure_perms_bp.route('/elevation-status', methods=['GET'])
def get_elevation_status():
    """
    Check if current user has User Access Administrator at root scope (/)
    
    Returns:
    {
        "success": true,
        "isGlobalAdmin": true/false,
        "isElevated": true/false,
        "roleAssignmentId": "..." (if elevated),
        "userInfo": {
            "objectId": "...",
            "upn": "..."
        }
    }
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Check if token has Global Admin role (wid: 62e90394-69f5-4237-9190-012177145e10)
        import jwt
        decoded = jwt.decode(get_token_value(token), options={"verify_signature": False})
        wids = decoded.get('wids', [])
        is_global_admin = '62e90394-69f5-4237-9190-012177145e10' in wids
        
        user_oid = decoded.get('oid')
        user_upn = decoded.get('upn')
        
        # Check if user has UAA role at root scope
        headers = {
            'Authorization': f'Bearer {get_token_value(token)}',
            'Content-Type': 'application/json'
        }
        
        # List role assignments at root scope
        response = requests.get(
            'https://management.azure.com/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=atScope()',
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to query role assignments: {response.status_code}'
            }), 200
        
        assignments = response.json().get('value', [])
        
        # User Access Administrator role definition ID
        uaa_role_id = '/providers/Microsoft.Authorization/roleDefinitions/18d7d88d-d35e-4fb5-a5c3-7773c20a72d9'
        
        # Find if current user has UAA at root scope
        elevated_assignment = None
        for assignment in assignments:
            if (assignment.get('properties', {}).get('scope') == '/' and
                assignment.get('properties', {}).get('roleDefinitionId') == uaa_role_id and
                assignment.get('properties', {}).get('principalId') == user_oid):
                elevated_assignment = assignment
                break
        
        return jsonify({
            'success': True,
            'isGlobalAdmin': is_global_admin,
            'isElevated': elevated_assignment is not None,
            'roleAssignmentId': elevated_assignment.get('name') if elevated_assignment else None,
            'userInfo': {
                'objectId': user_oid,
                'upn': user_upn
            }
        })
        
    except Exception as e:
        print("[ELEVATION-STATUS ERROR]", str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@azure_perms_bp.route('/elevate-access', methods=['POST'])
def elevate_access():
    """
    Elevate Global Admin to User Access Administrator at root scope (/)
    
    Microsoft API: POST https://management.azure.com/providers/Microsoft.Authorization/elevateAccess?api-version=2016-07-01
    
    Returns:
    {
        "success": true,
        "message": "Access elevated successfully"
    }
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Verify user is Global Admin
        import jwt
        decoded = jwt.decode(get_token_value(token), options={"verify_signature": False})
        wids = decoded.get('wids', [])
        is_global_admin = '62e90394-69f5-4237-9190-012177145e10' in wids
        
        if not is_global_admin:
            return jsonify({
                'success': False,
                'error': 'User is not a Global Administrator. Elevation requires Global Admin role.'
            }), 200
        
        # Call Microsoft elevation API
        headers = {
            'Authorization': f'Bearer {get_token_value(token)}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://management.azure.com/providers/Microsoft.Authorization/elevateAccess?api-version=2016-07-01',
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Access elevated successfully. You now have User Access Administrator role at root scope (/).'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Elevation failed: HTTP {response.status_code}',
                'details': response.text
            }), 200
        
    except Exception as e:
        print("[ELEVATE-ACCESS ERROR]", str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@azure_perms_bp.route('/elevate-access', methods=['DELETE'])
def remove_elevation():
    """
    Remove User Access Administrator role assignment at root scope (/)
    
    Finds the role assignment and deletes it
    
    Returns:
    {
        "success": true,
        "message": "Elevation removed successfully"
    }
    """
    try:
        # Find ARM token
        token, error_msg = find_token_for_audience('https://management.azure.com')
        
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Get current user's objectId
        import jwt
        decoded = jwt.decode(get_token_value(token), options={"verify_signature": False})
        user_oid = decoded.get('oid')
        
        headers = {
            'Authorization': f'Bearer {get_token_value(token)}',
            'Content-Type': 'application/json'
        }
        
        # List role assignments at root scope
        response = requests.get(
            'https://management.azure.com/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=atScope()',
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to query role assignments: {response.status_code}'
            }), 200
        
        assignments = response.json().get('value', [])
        
        # User Access Administrator role definition ID
        uaa_role_id = '/providers/Microsoft.Authorization/roleDefinitions/18d7d88d-d35e-4fb5-a5c3-7773c20a72d9'
        
        # Find the role assignment to delete
        assignment_to_delete = None
        for assignment in assignments:
            if (assignment.get('properties', {}).get('scope') == '/' and
                assignment.get('properties', {}).get('roleDefinitionId') == uaa_role_id and
                assignment.get('properties', {}).get('principalId') == user_oid):
                assignment_to_delete = assignment
                break
        
        if not assignment_to_delete:
            return jsonify({
                'success': False,
                'error': 'No elevated access found to remove'
            }), 200
        
        # Delete the role assignment
        assignment_id = assignment_to_delete.get('name')
        delete_url = f'https://management.azure.com/providers/Microsoft.Authorization/roleAssignments/{assignment_id}?api-version=2022-04-01'
        
        delete_response = requests.delete(
            delete_url,
            headers=headers,
            timeout=15
        )
        
        if delete_response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Elevation removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to remove elevation: HTTP {delete_response.status_code}',
                'details': delete_response.text
            }), 200
        
    except Exception as e:
        print("[REMOVE-ELEVATION ERROR]", str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
