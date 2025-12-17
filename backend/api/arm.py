"""
ARM API Blueprint - Azure Resources enumeration
Endpoint for VMs, Storage, KeyVault, SQL, App Services, Automation Account
+ VM Actions: start/stop/restart/deallocate/run command/status
+ Automation: runbooks, hybrid workers, permissions
+ Cache: Subscriptions cached 20 min per token
+ Auto-activation: Se token attivo non ha audience ARM, cerca e attiva token ARM con stesso UPN
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.arm_service import ARMService
from services.storage_service import StorageService
from services.keyvault_service import KeyVaultService
from models.token import Token
from database import db
from datetime import datetime
import time

arm_bp = Blueprint('arm', __name__, url_prefix='/api/azure')

# Subscription cache - {token_id: (data, timestamp)}
_subscription_cache = {}
_CACHE_TTL = 1200  # 20 minuti
arm_bp = Blueprint('arm', __name__, url_prefix='/api/azure')

# Subscription cache - {token_id: (data, timestamp)}
_subscription_cache = {}
_CACHE_TTL = 1200  # 20 minuti


def get_active_token():
    """
    Get active token for ARM API with auto-activation
    
    Logic:
    1. Get current active token
    2. Check if it has ARM audience (https://management.azure.com)
    3. If yes: use it
    4. If no: find ARM token with same UPN and auto-activate (multi-token mode)
    5. Return ARM token or error
    """
    active_token = TokenService.get_active_token()
    if not active_token:
        return None, None, {'success': False, 'error': 'No active token'}
    
    token_id = active_token.get('id')
    access_token = active_token.get('access_token')
    audience = active_token.get('audience', '')
    upn = active_token.get('upn')
    
    if not access_token:
        return None, None, {'success': False, 'error': 'Invalid token data'}
    
    # Check if current token has ARM audience
    if 'management.azure.com' in audience or 'management.core.windows.net' in audience:
        print(f"[ARM] Using active token #{token_id} (already ARM)")
        return token_id, access_token, None
    
    # Current token is NOT ARM (probably Graph) - search for ARM token with same UPN
    print(f"[ARM] Active token #{token_id} has wrong audience: {audience}")
    print(f"[ARM] Searching for ARM token with UPN: {upn}")
    
    # Find valid ARM tokens with same UPN
    arm_tokens = Token.query.filter(
        Token.token_type == 'access_token',
        Token.upn == upn,
        Token.expires_at > datetime.utcnow(),
        db.or_(
            Token.audience.like('%management.azure.com%'),
            Token.audience.like('%management.core.windows.net%')
        )
    ).order_by(Token.expires_at.desc()).all()
    
    if not arm_tokens:
        # No ARM token for current user - check if there are ARM tokens from OTHER users
        print(f"[ARM] No ARM token found for {upn}, checking for cross-user tokens...")
        
        other_arm_tokens = Token.query.filter(
            Token.token_type == 'access_token',
            Token.upn != upn,  # Different user!
            Token.expires_at > datetime.utcnow(),
            db.or_(
                Token.audience.like('%management.azure.com%'),
                Token.audience.like('%management.core.windows.net%')
            )
        ).order_by(Token.expires_at.desc()).all()
        
        if other_arm_tokens:
            # Found ARM tokens from other users - return warning with options
            available_users = []
            for token in other_arm_tokens[:5]:  # Max 5 users
                available_users.append({
                    'token_id': token.id,
                    'upn': token.upn,
                    'expires_at': token.expires_at.isoformat() if token.expires_at else None
                })
            
            print(f"[ARM] ⚠️ Found {len(other_arm_tokens)} ARM tokens from other users")
            
            return None, None, {
                'success': False,
                'error': f'No ARM token found for {upn}',
                'cross_user_tokens_available': True,
                'available_tokens': available_users,
                'hint': 'ARM tokens are available for other users. You can activate one of them to proceed.',
                'current_upn': upn
            }
        else:
            # No ARM tokens at all
            return None, None, {
                'success': False, 
                'error': 'No valid ARM token found',
                'hint': f'Please acquire an ARM access token',
                'current_token_audience': audience
            }
    
    # Auto-activate the most recent ARM token (multi-token mode - don't deactivate others)
    arm_token = arm_tokens[0]
    
    if not arm_token.is_active:
        print(f"[ARM] Auto-activating token #{arm_token.id} for {upn}")
        arm_token.is_active = True
        arm_token.mark_used()
        db.session.commit()
        
        # Notification payload (frontend will show toast)
        notification = {
            'auto_activated': True,
            'token_id': arm_token.id,
            'upn': arm_token.upn,
            'message': f'✅ Auto-activated ARM token #{arm_token.id} for Azure resources'
        }
    else:
        print(f"[ARM] Using already active ARM token #{arm_token.id}")
        notification = None
    
    return arm_token.id, arm_token.access_token, notification


def get_cached_subscriptions(token_id, access_token):
    """Get subscriptions with cache (20 min TTL)"""
    cache_key = f"subs_{token_id}"
    now = time.time()
    
    # Check cache
    if cache_key in _subscription_cache:
        cached_data, timestamp = _subscription_cache[cache_key]
        if now - timestamp < _CACHE_TTL:
            print(f"[CACHE HIT] subscriptions for token {token_id}")
            return cached_data
    
    # Cache miss - fetch from API
    print(f"[CACHE MISS] subscriptions for token {token_id}")
    service = ARMService(access_token)
    result = service.get_subscriptions()
    
    # Cache successful responses
    if result.get('success'):
        _subscription_cache[cache_key] = (result, now)
    
    return result


# ==================== SUBSCRIPTIONS ====================

@arm_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """Get all Azure subscriptions (cached 20 min)"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        result = get_cached_subscriptions(token_id, access_token)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== RESOURCE GROUPS ====================

@arm_bp.route('/subscriptions/<subscription_id>/resource-groups', methods=['GET'])
def get_resource_groups(subscription_id):
    """Get resource groups for subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_resource_groups(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== VIRTUAL MACHINES ====================

@arm_bp.route('/subscriptions/<subscription_id>/vms', methods=['GET'])
def get_virtual_machines(subscription_id):
    """Get VMs in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_virtual_machines(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/status', methods=['POST'])
def get_vm_status():
    """Get VM power state"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.get_vm_status(vm_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/start', methods=['POST'])
def vm_start():
    """Start a VM"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.vm_start(vm_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/stop', methods=['POST'])
def vm_stop():
    """Stop (shutdown) a VM"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.vm_stop(vm_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/restart', methods=['POST'])
def vm_restart():
    """Restart a VM"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.vm_restart(vm_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/deallocate', methods=['POST'])
def vm_deallocate():
    """Deallocate (stop + release) a VM"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.vm_deallocate(vm_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/run-command', methods=['POST'])
def vm_run_command():
    """Execute command on VM"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    command_id = data.get('commandId', 'RunShellScript')  # Default Linux
    script = data.get('script')
    parameters = data.get('parameters')
    
    if not vm_id or not script:
        return jsonify({'success': False, 'error': 'vmId and script required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.vm_run_command(vm_id, command_id, script, parameters)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/extract-mi-token', methods=['POST'])
def extract_vm_managed_identity_token():
    """Extract Managed Identity token from VM (RED TEAM)"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    vm_id = data.get('vmId')
    resource = data.get('resource', 'https://management.azure.com/')
    
    if not vm_id:
        return jsonify({'success': False, 'error': 'vmId required'}), 400
    
    try:
        service = ARMService(access_token)
        result = service.extract_vm_managed_identity_token(vm_id, resource)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/import-mi-token', methods=['POST'])
def import_vm_managed_identity_token():
    """Import extracted Managed Identity token to database"""
    data = request.get_json()
    
    access_token = data.get('access_token')
    resource = data.get('resource')
    expires_on = data.get('expires_on')
    claims = data.get('claims', {})
    identity = data.get('identity', {})
    vm_id = data.get('vm_id')
    
    if not access_token:
        return jsonify({'success': False, 'error': 'access_token required'}), 400
    
    try:
        from datetime import datetime, timezone
        
        # Extract identity info
        oid = claims.get('oid') or claims.get('sub')
        
        # UPN: Try displayName first, then construct meaningful name from oid
        if identity.get('displayName'):
            upn = identity.get('displayName')
        elif oid:
            upn = f"MI-{oid[:8]}"  # "MI-35051fd1" - short prefix instead of full GUID
        else:
            upn = 'Managed Identity'
        
        # Client ID: Use appId if available, otherwise clearly mark as Object ID
        if identity.get('appId'):
            client_id = identity.get('appId')
        elif oid:
            client_id = f"OID-{oid}"  # Prefix shows it's Object ID, not Client ID
        else:
            client_id = 'Unknown'
        
        # Convert expires_on timestamp to datetime
        expires_at = None
        if expires_on:
            try:
                expires_at = datetime.fromtimestamp(int(expires_on), tz=timezone.utc)
            except:
                pass
        
        # Create token entry with required fields
        new_token = Token(
            client_id=client_id,
            upn=upn,
            scope='user_impersonation',  # Default scope for MI tokens
            audience=claims.get('aud', resource),
            access_token=access_token,
            expires_at=expires_at,
            token_type='Managed Identity',
            source=f'MI Token from {vm_id.split("/")[-1] if vm_id else "VM"}',
            is_active=False  # CRITICAL: Must be False - user decides when to activate
        )
        
        db.session.add(new_token)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Token imported successfully',
            'token_id': new_token.id,
            'upn': upn
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STORAGE ACCOUNTS ====================

@arm_bp.route('/subscriptions/<subscription_id>/storage', methods=['GET'])
def get_storage_accounts(subscription_id):
    """Get storage accounts in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = StorageService(access_token)
        result = service.get_storage_accounts(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== KEY VAULTS ====================

@arm_bp.route('/subscriptions/<subscription_id>/keyvaults', methods=['GET'])
def get_key_vaults(subscription_id):
    """Get Key Vaults in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = KeyVaultService(access_token)
        result = service.get_key_vaults(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SQL SERVERS ====================

@arm_bp.route('/subscriptions/<subscription_id>/sql', methods=['GET'])
def get_sql_servers(subscription_id):
    """Get SQL servers in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_sql_servers(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== APP SERVICES ====================

@arm_bp.route('/subscriptions/<subscription_id>/appservices', methods=['GET'])
def get_app_services(subscription_id):
    """Get App Services in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_app_services(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AUTOMATION ACCOUNTS ====================

@arm_bp.route('/subscriptions/<subscription_id>/automation', methods=['GET'])
def get_automation_accounts(subscription_id):
    """Get Automation Accounts in subscription"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_automation_accounts(subscription_id)
        
        # Add auto-activation notification if present
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== RUNBOOKS ====================

@arm_bp.route('/automation/<path:automation_account_id>/runbooks', methods=['GET'])
def get_runbooks(automation_account_id):
    """Get all runbooks in Automation Account"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_runbooks(automation_account_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/runbook/<path:runbook_id>/content', methods=['GET'])
def get_runbook_content(runbook_id):
    """Get runbook script content"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_runbook_content(runbook_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] get_runbook_content exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/runbook/<path:runbook_id>', methods=['GET'])
def get_runbook_details(runbook_id):
    """Get single runbook details"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_runbook(runbook_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/<path:automation_account_id>/runbooks/create', methods=['POST'])
def create_runbook(automation_account_id):
    """Create a new runbook"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        data = request.get_json()
        runbook_name = data.get('runbook_name')
        runbook_type = data.get('runbook_type', 'PowerShell')
        description = data.get('description')
        script_content = data.get('script_content')
        tags = data.get('tags')
        
        if not runbook_name:
            return jsonify({'success': False, 'error': 'runbook_name is required'}), 400
        
        service = ARMService(access_token)
        
        # Step 1: Create runbook
        result = service.create_runbook(
            automation_account_id,
            runbook_name,
            runbook_type,
            description,
            tags
        )
        
        if not result.get('success'):
            return jsonify(result), 500
        
        # Get runbook ID from response
        runbook_data = result.get('runbook', {})
        runbook_id = runbook_data.get('id')
        
        if not runbook_id:
            return jsonify({'success': False, 'error': 'Failed to get runbook ID'}), 500
        
        # Step 2: Upload content if provided
        if script_content:
            content_result = service.update_runbook_content(runbook_id, script_content)
            if not content_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': 'Runbook created but failed to upload content',
                    'details': content_result.get('error')
                }), 500
            
            # Step 3: Publish runbook
            publish_result = service.publish_runbook(runbook_id)
            if not publish_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': 'Runbook created and content uploaded but failed to publish',
                    'details': publish_result.get('error')
                }), 500
        
        return jsonify({
            'success': True,
            'message': 'Runbook created successfully',
            'runbook_id': runbook_id,
            'runbook': runbook_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/<path:automation_account_id>/runbooks/<runbook_name>/start', methods=['POST'])
def start_runbook(automation_account_id, runbook_name):
    """Start a runbook job"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        data = request.get_json() or {}
        parameters = data.get('parameters')
        run_on = data.get('run_on')  # Hybrid worker group name (optional)
        
        service = ARMService(access_token)
        result = service.start_runbook(
            automation_account_id,
            runbook_name,
            parameters,
            run_on
        )
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/runbook/<path:runbook_id>/publish', methods=['POST'])
def publish_runbook(runbook_id):
    """Publish runbook (Draft → Published)"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.publish_runbook(runbook_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/runbook/<path:runbook_id>', methods=['DELETE'])
def delete_runbook(runbook_id):
    """Delete runbook"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.delete_runbook(runbook_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AUTOMATION ACCOUNTS - DETAILED ====================
# NOTA: Questa route DEVE stare DOPO le route runbook perché è più generica!

@arm_bp.route('/automation/<path:automation_account_id>', methods=['GET'])
def get_automation_account_details(automation_account_id):
    """Get single Automation Account details"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_automation_account(automation_account_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== RUNBOOK JOBS ====================

@arm_bp.route('/automation/job/<path:job_id>/output', methods=['GET'])
def get_job_output(job_id):
    """Get runbook job output"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_job_output(job_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/job/<path:job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get runbook job status"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_job_status(job_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AUTOMATION VARIABLES ====================

@arm_bp.route('/automation/<path:automation_account_id>/variables', methods=['GET'])
def get_automation_variables(automation_account_id):
    """Get automation variables (credential theft target)"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_automation_variables(automation_account_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== HYBRID WORKER GROUPS ====================

@arm_bp.route('/automation/<path:automation_account_id>/hybridworkers', methods=['GET'])
def get_hybrid_worker_groups(automation_account_id):
    """Get Hybrid Runbook Worker Groups"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_hybrid_worker_groups(automation_account_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/automation/<path:automation_account_id>/hybridworkers/<group_name>', methods=['GET'])
def get_hybrid_workers(automation_account_id, group_name):
    """Get Hybrid Workers in a specific group"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = ARMService(access_token)
        result = service.get_hybrid_workers(automation_account_id, group_name)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ==================== MANAGED IDENTITY SECURITY ====================

@arm_bp.route('/automation/<path:automation_account_id>/managed-identity', methods=['GET'])
def check_automation_managed_identity(automation_account_id):
    """
    Check Automation Account Managed Identity and permissions
    
    Path parameter:
        automation_account_id: URL-encoded full resource ID
        Format: subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Automation/automationAccounts/{name}
        
    Returns:
        JSON with identity status, role assignments, and risk score
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        from services.automation_service import AutomationService
        
        # Reconstruct full resource ID (add leading slash)
        full_id = f"/{automation_account_id}"
        
        print(f"[ARM->AUTOMATION] Checking MI for: {full_id}")
        
        service = AutomationService(access_token)
        result = service.check_managed_identity(full_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        print(f"[ARM->AUTOMATION] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/vms/scan-managed-identities', methods=['POST'])
def scan_vm_managed_identities():
    """
    Scan all VMs in a subscription for Managed Identity security risks
    
    Request body:
        {
            "subscriptionId": "subscription-id"
        }
        
    Returns:
        JSON with scan results including risk scores and recommendations
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    data = request.get_json()
    subscription_id = data.get('subscriptionId')
    
    if not subscription_id:
        return jsonify({'success': False, 'error': 'subscriptionId required'}), 400
    
    try:
        from services.vm_service import VMService
        
        print(f"[ARM->VM] Starting security scan for subscription: {subscription_id}")
        
        service = VMService(access_token)
        result = service.scan_vms_managed_identities(subscription_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        print(f"[ARM->VM] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== PERMISSIONS CHECK ====================

@arm_bp.route('/permissions/check', methods=['GET'])
def check_permissions():
    """Check user permissions on a resource"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        resource_id = request.args.get('resource_id')
        if not resource_id:
            return jsonify({'success': False, 'error': 'resource_id parameter is required'}), 400
        
        service = ARMService(access_token)
        result = service.check_permissions(resource_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/permissions/roleassignments', methods=['GET'])
def get_role_assignments():
    """Get role assignments for a resource"""
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        resource_id = request.args.get('resource_id')
        if not resource_id:
            return jsonify({'success': False, 'error': 'resource_id parameter is required'}), 400
        
        service = ARMService(access_token)
        result = service.get_role_assignments(resource_id)
        
        if error_or_notification and error_or_notification.get('auto_activated'):
            result['auto_activated_token'] = error_or_notification
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STORAGE SECURITY AUDIT ====================

@arm_bp.route('/storage/<path:storage_id>/properties', methods=['GET'])
def get_storage_properties(storage_id):
    """
    PHASE 1: Get detailed storage account properties
    Returns: network rules, firewall, public access, encryption
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = StorageService(access_token)
        result = service.get_storage_account_properties(storage_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/storage/<path:storage_id>/containers', methods=['GET'])
def get_storage_containers(storage_id):
    """
    PHASE 2: List containers in storage account
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = StorageService(access_token)
        result = service.list_containers(storage_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/storage/<path:storage_id>/keys', methods=['GET'])
def get_storage_account_keys(storage_id):
    """
    PHASE 3: Attempt to get storage account keys
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = StorageService(access_token)
        result = service.get_storage_keys(storage_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/storage/<path:storage_id>/security-audit', methods=['GET'])
def storage_security_audit(storage_id):
    """
    Comprehensive security audit (Phases 1+2+3 combined)
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    try:
        service = StorageService(access_token)
        result = service.security_audit(storage_id)
        
        if result.get('permission_denied'):
            return jsonify(result), 403
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@arm_bp.route('/storage/<storage_account_name>/container/<container_name>/blobs', methods=['GET'])
def list_container_blobs(storage_account_name, container_name):
    """
    List blobs in a public container (server-side to bypass CORS)
    Query param: blob_endpoint (e.g., https://account.blob.core.windows.net/)
    """
    token_id, access_token, error_or_notification = get_active_token()
    if not token_id:
        return jsonify(error_or_notification), 401
    
    blob_endpoint = request.args.get('blob_endpoint')
    if not blob_endpoint:
        return jsonify({'success': False, 'error': 'blob_endpoint query parameter required'}), 400
    
    try:
        service = StorageService(access_token)
        result = service.list_blobs(storage_account_name, container_name, blob_endpoint)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
