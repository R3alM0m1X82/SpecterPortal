"""
Tenant API
Added App Registration management endpoints (create, delete, secrets, owned)
Added group members endpoint
Added User/Group creation and owned objects enumeration
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.tenant_service import TenantService
from services.cache_service import graph_cache

tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/tenant')


def get_active_token():
    """
    Get active token dictionary and validate.
    Priority:
    1. Authorization header (if present)
    2. Active token from database (fallback)
    """
    # Check Authorization header first
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        access_token = auth_header.replace('Bearer ', '')
        # Return token from header with fake token_id for cache
        # We use a hash of the token as cache key
        import hashlib
        token_hash = hashlib.md5(access_token.encode()).hexdigest()[:8]
        return f'header_{token_hash}', access_token, None
    
    # Fallback to active token from database
    token_dict = TokenService.get_active_token()
    if not token_dict:
        return None, None, {'success': False, 'error': 'No active token'}
    
    token_id = token_dict.get('id')
    access_token_full = token_dict.get('access_token_full')
    
    if not access_token_full or access_token_full.endswith('...'):
        return None, None, {'success': False, 'error': 'Active token is invalid or truncated'}
    
    return token_id, access_token_full, None


# ==================== USERS ====================

@tenant_bp.route('/users', methods=['GET'])
def get_users():
    """Get users"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_users', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_users(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_users', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    
    # Required fields
    display_name = data.get('displayName')
    user_principal_name = data.get('userPrincipalName')
    password = data.get('password')
    
    if not display_name or not user_principal_name or not password:
        return jsonify({
            'success': False,
            'error': 'displayName, userPrincipalName, and password are required'
        }), 400
    
    try:
        service = TenantService(access_token, token_id)
        result = service.create_user(
            display_name=display_name,
            user_principal_name=user_principal_name,
            password=password,
            mail_nickname=data.get('mailNickname'),
            account_enabled=data.get('accountEnabled', True),
            force_change_password=data.get('forceChangePassword', True),
            job_title=data.get('jobTitle'),
            department=data.get('department'),
            usage_location=data.get('usageLocation')
        )
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_users')
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/users/search', methods=['GET'])
def search_users():
    """Search users"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter q is missing'}), 400

    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.search_users(query)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/users/mfa-batch', methods=['POST'])
def get_users_mfa_batch():
    """Get MFA status for multiple users in batch"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    user_ids = data.get('userIds', [])
    
    if not user_ids:
        return jsonify({'success': False, 'error': 'userIds array is required'}), 400
    
    # Check cache first for each user
    cache_key = 'mfa_batch'
    cached_results = {}
    uncached_ids = []
    
    for user_id in user_ids:
        cached = graph_cache.get(token_id, f'user_mfa_{user_id}')
        if cached:
            cached_results[user_id] = cached
        else:
            uncached_ids.append(user_id)
    
    # If all cached, return immediately
    if not uncached_ids:
        return jsonify({
            'success': True,
            'results': cached_results,
            'count': len(cached_results),
            'cached': True
        })
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_users_mfa_batch(uncached_ids)
        
        if result['success']:
            # Cache individual results (TTL 300s = 5 min)
            for user_id, mfa_data in result['results'].items():
                graph_cache.set(token_id, f'user_mfa_{user_id}', mfa_data, ttl_seconds=900)
            
            # Merge cached and new results
            all_results = {**cached_results, **result['results']}
            
            return jsonify({
                'success': True,
                'results': all_results,
                'count': len(all_results),
                'cached': len(cached_results),
                'fetched': len(result['results'])
            })
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _auto_acquire_graph_token():
    """
    Auto-acquire Microsoft Graph API token.
    Strategy:
    1. Search for existing valid Graph token
    2. If not found, use refresh token from SAME USER as active token
    3. Return token or None
    
    Returns:
        tuple: (access_token, token_id, error_dict)
        - If successful: (token_string, token_id, None)
        - If failed: (None, None, {'error_type': ..., 'error': ...})
    """
    from models.token import Token
    from datetime import datetime
    from database import db
    import requests
    import json
    import base64
    
    # STEP 1: Search for existing valid Graph token
    graph_tokens = Token.query.filter(
        Token.token_type == 'access_token',
        Token.audience.like('%graph.microsoft.com%')
    ).all()
    
    print(f"[AUTO-GRAPH] Found {len(graph_tokens)} Graph tokens in DB")
    
    # Check for valid (non-expired) token
    for token in graph_tokens:
        if token.expires_at:
            now = datetime.utcnow()
            if now < token.expires_at:
                print(f"[AUTO-GRAPH] ✓ Using existing Graph token #{token.id}")
                return (token.access_token, token.id, None)
            else:
                print(f"[AUTO-GRAPH] Token #{token.id} is expired")
        else:
            # No expiry info, assume valid
            print(f"[AUTO-GRAPH] ✓ Using Graph token #{token.id} (no expiry)")
            return (token.access_token, token.id, None)
    
    # STEP 2: Get active token to determine current user context
    print(f"[AUTO-GRAPH] No valid Graph token - searching for refresh token...")
    
    active_token = Token.query.filter_by(is_active=True).first()
    
    if not active_token:
        print(f"[AUTO-GRAPH] ❌ No active token found")
        return (None, None, {
            'error_type': 'no_graph_token',
            'error': 'UPN resolution unavailable: No active token. Please activate a token first.'
        })
    
    # Get UPN from active token
    active_upn = active_token.upn
    print(f"[AUTO-GRAPH] Active token UPN: {active_upn}")
    
    # STEP 3: Find refresh token for SAME USER as active token
    if active_upn:
        refresh_tokens = Token.query.filter(
            Token.token_type == 'refresh_token',
            Token.upn == active_upn
        ).all()
        
        print(f"[AUTO-GRAPH] Found {len(refresh_tokens)} refresh tokens for UPN: {active_upn}")
    else:
        # No UPN in active token, try to find any RT (fallback)
        print(f"[AUTO-GRAPH] Active token has no UPN, searching for any refresh token...")
        refresh_tokens = Token.query.filter(
            Token.token_type == 'refresh_token'
        ).all()
        print(f"[AUTO-GRAPH] Found {len(refresh_tokens)} refresh tokens")
    
    if not refresh_tokens:
        print(f"[AUTO-GRAPH] ❌ No refresh tokens available for user {active_upn}")
        return (None, None, {
            'error_type': 'no_graph_token',
            'error': f'UPN resolution unavailable: No refresh token for user {active_upn}. Authenticate with Microsoft Graph PowerShell to enable UPN resolution.'
        })
    
    # Helper function to extract JWT claims
    def extract_jwt_claims(access_token):
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return {}
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data
        except:
            return {}
    
    # STEP 4: Try each refresh token until one works
    # Use the RT's ORIGINAL client_id (usually Azure PowerShell with Directory.AccessAsUser.All)
    for rt in refresh_tokens:
        try:
            print(f"[AUTO-GRAPH] Attempting refresh with RT #{rt.id} (UPN: {rt.upn}, client: {rt.client_id})...")
            
            # Use refresh token to get Graph token
            # Use the RT's ORIGINAL client_id (e.g. Azure PowerShell has Directory.AccessAsUser.All pre-consent)
            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            
            payload = {
                'client_id': rt.client_id,  # Use ORIGINAL client_id from RT
                'grant_type': 'refresh_token',
                'refresh_token': rt.refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'  # Inherits all consented permissions
            }
            
            response = requests.post(token_url, data=payload, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 3600)
                
                print(f"[AUTO-GRAPH] ✅ Successfully obtained Graph token via refresh")
                
                # Extract JWT claims
                jwt_claims = extract_jwt_claims(new_access_token)
                audience = jwt_claims.get('aud', 'https://graph.microsoft.com')
                upn = jwt_claims.get('upn') or rt.upn or 'Auto-refreshed'
                scope = jwt_claims.get('scp', 'Graph API')
                
                print(f"[AUTO-GRAPH] Token UPN: {upn}, Scopes: {scope}")
                
                # Calculate expires_at
                expires_at = datetime.utcnow()
                from datetime import timedelta
                expires_at = expires_at + timedelta(seconds=expires_in)
                
                # Create new Token instance
                new_token = Token(
                    client_id=rt.client_id,  # Keep original client_id
                    upn=upn,
                    scope=scope,
                    audience=audience,
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                    expires_at=expires_at,
                    token_type='access_token',
                    source='auto_refresh_graph',
                    imported_from='Auto-refresh for UPN resolution'
                )
                
                # Save to database
                db.session.add(new_token)
                db.session.commit()
                
                print(f"[AUTO-GRAPH] ✅ Saved new Graph token as #{new_token.id} for {upn}")
                
                return (new_access_token, new_token.id, None)
            else:
                error_data = response.json() if response.text else {}
                error_desc = error_data.get('error_description', f'HTTP {response.status_code}')
                print(f"[AUTO-GRAPH] RT #{rt.id} failed: {error_desc[:150]}...")
                continue
                
        except Exception as e:
            print(f"[AUTO-GRAPH] RT #{rt.id} error: {e}")
            continue
    
    # STEP 5: All refresh tokens failed
    print(f"[AUTO-GRAPH] ❌ All refresh attempts failed for user {active_upn}")
    return (None, None, {
        'error_type': 'no_graph_token',
        'error': f'UPN resolution unavailable: Failed to obtain Graph token for {active_upn}. User may lack necessary permissions (User.Read.All, Directory.Read.All).'
    })




@tenant_bp.route('/resolve-principals', methods=['POST'])
def resolve_principals():
    """
    Resolve multiple principal IDs (Users, ServicePrincipals, Groups) to display names
    
    Request body:
    [
        {"id": "principal-guid", "type": "User"},
        {"id": "principal-guid", "type": "ServicePrincipal"},
        {"id": "principal-guid", "type": "Group"}
    ]
    
    Response:
    {
        "success": true,
        "principals": {
            "principal-guid": "display-name",
            ...
        }
    }
    """
    data = request.get_json() or []
    
    if not isinstance(data, list):
        return jsonify({
            'success': False,
            'error': 'Request body must be an array of principals'
        }), 400
    
    # Auto-acquire Graph token (existing or refresh)
    access_token, token_id, error = _auto_acquire_graph_token()
    
    if error:
        # No Graph token available - return 200 OK with empty principals (non-blocking)
        print(f"[RESOLVE-PRINCIPALS] {error['error']}")
        return jsonify({
            'success': False,
            'error_type': error['error_type'],
            'error': error['error'],
            'principals': {},
            'count': 0
        }), 200  # 200 OK - not a blocking error
    
    # Validate token
    if not access_token or access_token.endswith('...'):
        return jsonify({
            'success': False,
            'error_type': 'invalid_token',
            'error': 'Graph token is invalid or truncated',
            'principals': {},
            'count': 0
        }), 200
    
    try:
        service = TenantService(access_token, token_id)
        resolved = service.resolve_principals_batch(data)
        
        return jsonify({
            'success': True,
            'principals': resolved,
            'count': len(resolved)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'principals': {},
            'count': 0
        }), 500


# ==================== GROUPS ====================

@tenant_bp.route('/groups', methods=['GET'])
def get_groups():
    """Get groups"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_groups', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_groups(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_groups', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/groups', methods=['POST'])
def create_group():
    """
    Create a new group
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    
    # Required field
    display_name = data.get('displayName')
    
    if not display_name:
        return jsonify({
            'success': False,
            'error': 'displayName is required'
        }), 400
    
    try:
        service = TenantService(access_token, token_id)
        result = service.create_group(
            display_name=display_name,
            mail_nickname=data.get('mailNickname'),
            description=data.get('description'),
            group_types=data.get('groupTypes'),
            security_enabled=data.get('securityEnabled', True),
            mail_enabled=data.get('mailEnabled', False)
        )
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_groups')
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/groups/search', methods=['GET'])
def search_groups():
    """Search groups"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter q is missing'}), 400

    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.search_groups(query)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/groups/<group_id>/members', methods=['GET'])
def get_group_members(group_id):
    """Get members of a group"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_group_members(group_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== OWNED OBJECTS ====================

@tenant_bp.route('/owned-objects', methods=['GET'])
def get_owned_objects():
    """
    Get all objects owned by a specific user or current user.
    Returns devices, groups, applications, and service principals.
    
    
    Query params:
        user_id: Optional user ID. If not provided, returns owned objects of current user.
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    user_id = request.args.get('user_id')
    
    # Build cache key based on user_id
    cache_key = f'owned_objects_{user_id}' if user_id else 'owned_objects_me'
    cached = graph_cache.get(token_id, cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_owned_objects(user_id=user_id)
        
        if result['success']:
            graph_cache.set(token_id, cache_key, result, ttl_seconds=600)
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== DEVICES ====================

@tenant_bp.route('/devices', methods=['GET'])
def get_devices():
    """Get devices"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_devices', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_devices(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_devices', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ADMIN UNITS ====================

@tenant_bp.route('/admin-units', methods=['GET'])
def get_admin_units():
    """Get administrative units"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_admin_units', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_admin_units(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_admin_units', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/admin-units/<unit_id>/members', methods=['GET'])
def get_admin_unit_members(unit_id):
    """Get members of an administrative unit"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_admin_unit_members(unit_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/admin-units/<unit_id>/scoped-roles', methods=['GET'])
def get_admin_unit_scoped_roles(unit_id):
    """Get scoped role assignments for an administrative unit"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_admin_unit_scoped_roles(unit_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ORGANIZATION ====================

@tenant_bp.route('/organization', methods=['GET'])
def get_organization():
    """Get organization info"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_organization')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_organization()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_organization', result, ttl_seconds=600)
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/domains', methods=['GET'])
def get_domains():
    """Get domains"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_domains')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_domains()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_domains', result, ttl_seconds=600)
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/directory-roles', methods=['GET'])
def get_directory_roles():
    """Get directory roles"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_directory_roles')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_directory_roles()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_directory_roles', result, ttl_seconds=600)
            return jsonify(result)
            
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== APPLICATIONS - READ ====================

@tenant_bp.route('/service-principals', methods=['GET'])
def get_service_principals():
    """Get service principals"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_service_principals', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_service_principals(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_service_principals', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route("/managed-identities", methods=["GET"])
def get_managed_identities():
    """Get managed identities (system and user-assigned)"""
    top = request.args.get("top", 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, "tenant_managed_identities", {"top": top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_managed_identities(top=top)
        
        if result["success"]:
            graph_cache.set(token_id, "tenant_managed_identities", result, ttl_seconds=900, params={"top": top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tenant_bp.route('/applications', methods=['GET'])
def get_applications():
    """Get app registrations"""
    top = request.args.get('top', 100, type=int)
    
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_applications', {'top': top})
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_applications(top=top)
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_applications', result, ttl_seconds=900, params={'top': top})
            return jsonify(result)
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== APPLICATIONS - MANAGEMENT ====================

@tenant_bp.route('/applications/policy', methods=['GET'])
def check_app_policy():
    """Check if users can register applications"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.check_app_registration_policy()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/check-create-permissions', methods=['GET'])
def check_create_permissions():
    """
    Check if current token has permissions to create users/groups.
    
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.check_create_permissions()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications/owned', methods=['GET'])
def get_owned_applications():
    """Get applications owned by current user"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_owned_applications()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications', methods=['POST'])
def create_application():
    """Create a new App Registration"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    display_name = data.get('displayName')
    
    if not display_name:
        return jsonify({'success': False, 'error': 'displayName is required'}), 400
    
    try:
        service = TenantService(access_token, token_id)
        result = service.create_application(
            display_name=display_name,
            sign_in_audience=data.get('signInAudience', 'AzureADMyOrg'),
            redirect_uris=data.get('redirectUris'),
            description=data.get('description')
        )
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_applications')
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications/<app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete an application (must be owner)"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.delete_application(app_id)
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_applications')
            return jsonify(result)
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications/<app_id>/secrets', methods=['GET'])
def get_application_secrets(app_id):
    """Get secrets metadata for an application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_application_secrets(app_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications/<app_id>/secrets', methods=['POST'])
def add_application_secret(app_id):
    """Add a client secret to an application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    
    try:
        service = TenantService(access_token, token_id)
        result = service.add_client_secret(
            app_object_id=app_id,
            description=data.get('description', 'SpecterPortal Secret'),
            expiry_months=data.get('expiryMonths', 12)
        )
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_applications')
            return jsonify(result), 201
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/applications/<app_id>/secrets/<key_id>', methods=['DELETE'])
def remove_application_secret(app_id, key_id):
    """Remove a client secret from an application"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        service = TenantService(access_token, token_id)
        result = service.remove_client_secret(app_id, key_id)
        
        if result['success']:
            # Invalidate cache
            graph_cache.invalidate(token_id, 'tenant_applications')
            return jsonify(result)
        
        return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TENANT AUTH METHODS ====================

@tenant_bp.route('/auth-methods-policy', methods=['GET'])
def get_auth_methods_policy():
    """Get tenant-wide authentication methods policy"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_auth_methods_policy')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_tenant_auth_methods_policy()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_auth_methods_policy', result, ttl_seconds=1800)
            return jsonify(result)
        
        # Check if it's a permission denied error
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/auth-strength-policies', methods=['GET'])
def get_auth_strength_policies():
    """Get authentication strength policies"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_auth_strength_policies')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_auth_strength_policies()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_auth_strength_policies', result, ttl_seconds=1800)
            return jsonify(result)
        
        # Check if it's a permission denied error
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@tenant_bp.route('/authorization-policy', methods=['GET'])
def get_authorization_policy():
    """Get tenant authorization policy"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    cached = graph_cache.get(token_id, 'tenant_authorization_policy')
    if cached:
        return jsonify(cached)
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_authorization_policy()
        
        if result['success']:
            graph_cache.set(token_id, 'tenant_authorization_policy', result, ttl_seconds=1800)
            return jsonify(result)
        
        # Check if it's a permission denied error
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/cache/flush', methods=['POST'])
def flush_cache():
    """Flush all cached data for current token - useful for debugging"""
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    try:
        # Get all cache keys for this token
        cache_keys = [
            'tenant_organization',
            'tenant_domains', 
            'tenant_auth_methods_policy',
            'tenant_auth_strength_policies',
            'tenant_authorization_policy',
            'tenant_managed_identities',
            'tenant_service_principals'
        ]
        
        flushed = []
        for key in cache_keys:
            if graph_cache.delete(token_id, key):
                flushed.append(key)
        
        return jsonify({
            'success': True,
            'message': f'Flushed {len(flushed)} cache entries',
            'flushed_keys': flushed
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== OWNERS (On-Demand Loading) ====================

@tenant_bp.route('/batch-owners', methods=['POST'])
def get_batch_owners():
    """
    Get owners for multiple entities on-demand (lazy loading)
    
    
    POST body:
    {
      "entityType": "servicePrincipals" or "applications",
      "entityIds": ["id1", "id2", ...]
    }
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    entity_type = data.get('entityType')
    entity_ids = data.get('entityIds', [])
    
    if not entity_type or not entity_ids:
        return jsonify({
            'success': False,
            'error': 'entityType and entityIds are required'
        }), 400
    
    if entity_type not in ['servicePrincipals', 'applications']:
        return jsonify({
            'success': False,
            'error': 'entityType must be servicePrincipals or applications'
        }), 400
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_owners_for_entities(entity_type, entity_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/batch-roles', methods=['POST'])
def get_batch_roles():
    """
    Get role assignments for service principals on-demand (lazy loading)
    
    
    POST body:
    {
      "entityIds": ["sp_id1", "sp_id2", ...]
    }
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    data = request.get_json() or {}
    entity_ids = data.get('entityIds', [])
    
    if not entity_ids:
        return jsonify({
            'success': False,
            'error': 'entityIds is required'
        }), 400
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_roles_for_entities(entity_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tenant_bp.route('/risky-sps', methods=['GET'])
def get_risky_sps():
    """
    Get service principals with risky Application Permissions
    
    
    Query params:
    - min_risk: Minimum risk level (Low, Medium, High, Critical) - default Medium
    """
    token_id, access_token, error = get_active_token()
    if error:
        return jsonify(error), 401
    
    min_risk = request.args.get('min_risk', 'Medium')
    
    try:
        service = TenantService(access_token, token_id)
        result = service.get_risky_service_principals(min_risk)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
