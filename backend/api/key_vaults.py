"""
Key Vaults API - Azure Key Vault endpoints
ARM enumeration,Data Plane (secrets, certs) + Access Policies management
SMART ENUMERATION - subscription_id parameter support
"""
from flask import Blueprint, request, jsonify, session
from models.token import Token
from services.keyvault_service import KeyVaultService
from services.permissions_service import PermissionsService
from datetime import datetime


key_vaults_bp = Blueprint('key_vaults', __name__)


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
    
    # Strategy 1: Exact audience match (fallback if active token doesn't match)
    matching_tokens = []
    for token in access_tokens:
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
    
    # Strategy 3: For vault.azure.net, check scope even without required_scopes parameter
    if not matching_tokens and 'vault.azure.net' in required_audience.lower():
        print(f"[FIND-TOKEN] No audience match for vault, checking scopes...")
        for token in access_tokens:
            if token.scope and 'vault.azure.net' in token.scope.lower():
                print(f"[FIND-TOKEN] Token #{token.id} matches vault scope!")
                # Check if token is expired
                if token.expires_at:
                    try:
                        from datetime import datetime
                        now = datetime.utcnow()
                        if now < token.expires_at:
                            matching_tokens.append(token)
                            print(f"[FIND-TOKEN] Token #{token.id} is valid")
                        else:
                            print(f"[FIND-TOKEN] Token #{token.id} is EXPIRED")
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
    if 'management' in required_audience.lower():
        error_msg = "No valid ARM token found"
    elif 'vault' in required_audience.lower():
        error_msg = "No valid Key Vault token found"
    else:
        audience_display = required_audience.replace('https://', '').replace('/.default', '')
        error_msg = f"No active token found for '{audience_display}'"
    
    return None, error_msg


@key_vaults_bp.route('', methods=['GET'])
def get_key_vaults():
    """
    Get Key Vaults for specified subscription(s)
    Original ARM enumeration
    SMART - supports subscription_id parameter
    
    Query Parameters:
    - subscription_id (optional): If provided, only enumerates Key Vaults in that subscription
                                  If not provided, enumerates all accessible subscriptions
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token using SAME pattern as azure_perms.py
    token, error_msg = find_token_for_audience('https://management.azure.com')
    
    if not token:
        return jsonify({
            'success': False,
            'error': error_msg,
            'needs_token': True,
            'audience': 'https://management.azure.com/.default'
        }), 200  # Return 200 not 403!
    
    print(f"[KEY VAULTS] Using token #{token.id} for ARM API")
    print(f"[KEY VAULTS] Token audience: {token.audience}")
    
    # Check if subscription_id parameter is provided
    subscription_id = request.args.get('subscription_id')
    
    if subscription_id:
        print(f"[KEY VAULTS] Using specific subscription: {subscription_id}")
        # Single subscription mode
        subscriptions = [{
            'subscriptionId': subscription_id,
            'displayName': subscription_id  # Will be enriched later if possible
        }]
        
        # Try to get actual subscription name
        permissions_service = PermissionsService(token.access_token)
        subs_result = permissions_service.get_subscriptions()
        if subs_result.get('success'):
            for sub in subs_result['subscriptions']:
                if sub['subscriptionId'] == subscription_id:
                    subscriptions[0]['displayName'] = sub['displayName']
                    break
    else:
        print("[KEY VAULTS] Enumerating all accessible subscriptions")
        # All subscriptions mode
        permissions_service = PermissionsService(token.access_token)
        subs_result = permissions_service.get_subscriptions()
        
        if not subs_result.get('success'):
            return jsonify(subs_result), 200
        
        subscriptions = subs_result['subscriptions']
    
    print(f"[KEY VAULTS] Processing {len(subscriptions)} subscription(s)")
    
    all_vaults = []
    errors = []  # Track errors per subscription
    
    for sub in subscriptions:
        sub_id = sub['subscriptionId']
        sub_name = sub['displayName']
        
        print(f"[KEY VAULTS] Enumerating Key Vaults in subscription '{sub_name}' ({sub_id})")
        
        kv_service = KeyVaultService(token.access_token)
        result = kv_service.get_key_vaults(sub_id)
        
        if result.get('success'):
            vaults = result.get('key_vaults', [])
            print(f"[KEY VAULTS] Found {len(vaults)} Key Vault(s) in '{sub_name}'")
            
            for vault in vaults:
                vault['subscription'] = sub_name
                vault['subscriptionId'] = sub_id
            all_vaults.extend(vaults)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"[KEY VAULTS] Error enumerating Key Vaults in '{sub_name}': {error_msg}")
            
            # Track the error
            errors.append({
                'subscription': sub_name,
                'error': error_msg
            })
            
            # Don't fail completely - just skip this subscription
            continue
    
    print(f"[KEY VAULTS] Total Key Vaults found: {len(all_vaults)}")
    
    # If ALL subscriptions failed, return error
    if len(errors) == len(subscriptions) and len(all_vaults) == 0:
        # Extract first error message (usually they're all the same)
        error_details = errors[0]['error'] if errors else 'Failed to enumerate Key Vaults'
        print(f"[KEY VAULTS] ❌ All subscriptions failed: {error_details}")
        
        return jsonify({
            'success': False,
            'error': error_details,
            'key_vaults': [],
            'total': 0
        }), 200  # Keep 200 for consistency with other endpoints
    
    # Partial success or full success
    return jsonify({
        'success': True,
        'key_vaults': all_vaults,
        'total': len(all_vaults),
        'errors': errors if errors else None  # Include partial errors if any
    })


@key_vaults_bp.route('/<vault_id_b64>/details', methods=['GET'])
def get_vault_details(vault_id_b64):
    """
    Get detailed Key Vault info (includes access policies)
    Added for access policies view
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    token, error_msg = find_token_for_audience('https://management.azure.com')
    
    if not token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    kv_service = KeyVaultService(token.access_token)
    result = kv_service.get_key_vault_details(vault_id)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 200


# ==================== DATA PLANE ENDPOINTS ====================

@key_vaults_bp.route('/<vault_id_b64>/secrets', methods=['GET'])
def list_secrets(vault_id_b64):
    """
    List secrets in Key Vault (data plane)
    Secrets enumeration
    Auto-FOCI exchange for vault.azure.net if RT FOCI available
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    arm_token, error_msg = find_token_for_audience('https://management.azure.com')
    if not arm_token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Find Data Plane token
    dp_token, dp_error = find_token_for_audience('https://vault.azure.net')
    
    if not dp_token:
        return jsonify({
            'success': False,
            'error': 'No data plane token available',
            'needs_token': True,
            'audience': 'https://vault.azure.net'
        }), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    # Get vault details to get vault URI
    kv_service = KeyVaultService(arm_token.access_token, dp_token.access_token)
    vault_details = kv_service.get_key_vault_details(vault_id)
    
    if not vault_details.get('success'):
        return jsonify(vault_details), 200
    
    vault_uri = vault_details['vault'].get('vaultUri', '').rstrip('/')
    
    # List secrets
    result = kv_service.list_secrets(vault_uri)
    
    if result.get('success'):
        return jsonify(result)
    elif result.get('permission_denied'):
        return jsonify({
            **result,
            'hint': 'Grant yourself access with "Grant Self Access" button in Access Policies tab'
        }), 200
    else:
        return jsonify(result), 200


@key_vaults_bp.route('/<vault_id_b64>/secrets/<secret_name>', methods=['GET'])
def get_secret(vault_id_b64, secret_name):
    """
    Get secret value (plaintext) - REVEAL SECRET
    Secret value retrieval
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    arm_token, error_msg = find_token_for_audience('https://management.azure.com')
    if not arm_token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Find Data Plane token
    dp_token, dp_error = find_token_for_audience('https://vault.azure.net')
    
    if not dp_token:
        return jsonify({
            'success': False,
            'error': 'No data plane token available',
            'needs_token': True,
            'audience': 'https://vault.azure.net'
        }), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    # Get vault details
    kv_service = KeyVaultService(arm_token.access_token, dp_token.access_token)
    vault_details = kv_service.get_key_vault_details(vault_id)
    
    if not vault_details.get('success'):
        return jsonify(vault_details), 200
    
    vault_uri = vault_details['vault'].get('vaultUri', '').rstrip('/')
    
    # Get secret value
    result = kv_service.get_secret(vault_uri, secret_name)
    
    if result.get('success'):
        return jsonify(result)
    elif result.get('permission_denied'):
        return jsonify({
            **result,
            'hint': 'Missing Get permission on secrets'
        }), 200
    else:
        return jsonify(result), 200


@key_vaults_bp.route('/<vault_id_b64>/certificates', methods=['GET'])
def list_certificates(vault_id_b64):
    """
    List certificates in Key Vault (data plane)
    Certificates enumeration
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    arm_token, error_msg = find_token_for_audience('https://management.azure.com')
    if not arm_token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Find Data Plane token
    dp_token, dp_error = find_token_for_audience('https://vault.azure.net')
    
    if not dp_token:
        return jsonify({
            'success': False,
            'error': 'No data plane token available',
            'needs_token': True,
            'audience': 'https://vault.azure.net'
        }), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    # Get vault details
    kv_service = KeyVaultService(arm_token.access_token, dp_token.access_token)
    vault_details = kv_service.get_key_vault_details(vault_id)
    
    if not vault_details.get('success'):
        return jsonify(vault_details), 200
    
    vault_uri = vault_details['vault'].get('vaultUri', '').rstrip('/')
    
    # List certificates
    result = kv_service.list_certificates(vault_uri)
    
    if result.get('success'):
        return jsonify(result)
    elif result.get('permission_denied'):
        return jsonify({
            **result,
            'hint': 'Grant yourself access with "Grant Self Access" button'
        }), 200
    else:
        return jsonify(result), 200


# ==================== ACCESS POLICIES (Management Plane) ====================

@key_vaults_bp.route('/<vault_id_b64>/access-policies', methods=['GET'])
def get_access_policies(vault_id_b64):
    """
    Get current access policies for Key Vault
    View who has data plane permissions
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    token, error_msg = find_token_for_audience('https://management.azure.com')
    
    if not token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    kv_service = KeyVaultService(token.access_token)
    result = kv_service.get_access_policies(vault_id)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 200


@key_vaults_bp.route('/<vault_id_b64>/access-policies/grant', methods=['POST'])
def grant_self_access(vault_id_b64):
    """
    GRANT SELF ACCESS - Add access policy for current user
    "Grant Self Access" attack chain
    """
    if 'authenticated' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Find ARM token
    token, error_msg = find_token_for_audience('https://management.azure.com')
    
    if not token:
        return jsonify({'success': False, 'error': error_msg}), 200
    
    # Decode vault_id
    import base64
    try:
        vault_id = base64.urlsafe_b64decode(vault_id_b64).decode('utf-8')
    except:
        return jsonify({'success': False, 'error': 'Invalid vault_id encoding'}), 400
    
    # Get request body (optional custom permissions)
    data = request.get_json() or {}
    
    # Extract principal_id and tenant_id from ARM token if not provided
    import jwt
    try:
        decoded = jwt.decode(token.access_token, options={"verify_signature": False})
        principal_id = data.get('principal_id') or decoded.get('oid')
        tenant_id = data.get('tenant_id') or decoded.get('tid')
        
        if not principal_id or not tenant_id:
            return jsonify({
                'success': False,
                'error': 'Could not extract principal_id or tenant_id from token',
                'hint': 'Provide principal_id and tenant_id in request body'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Token parsing failed: {str(e)}'
        }), 400
    
    # Get custom permissions or use defaults (full access)
    secrets_perms = data.get('secrets')
    certs_perms = data.get('certificates')
    keys_perms = data.get('keys')
    
    # Grant access policy
    kv_service = KeyVaultService(token.access_token)
    result = kv_service.set_access_policy(
        vault_id=vault_id,
        principal_id=principal_id,
        tenant_id=tenant_id,
        secrets_permissions=secrets_perms,
        certificates_permissions=certs_perms,
        keys_permissions=keys_perms
    )
    
    if result.get('success'):
        return jsonify(result)
    elif result.get('rbac_enabled'):
        return jsonify(result), 400
    else:
        return jsonify(result), 200
