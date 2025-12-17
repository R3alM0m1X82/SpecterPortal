"""
Admin Actions Service
Handles write operations: Create User, Reset Password, TAP, MFA Management
Uses Microsoft Graph API with proper permission validation

IMPORTANT: Uses FOCI exchange to get Azure PowerShell token for pre-consented permissions
"""
import requests
from datetime import datetime, timedelta
from services.permission_service import PermissionService

# Import FOCI check function
try:
    from models.client_ids import is_foci_app
except ImportError:
    # Fallback if client_ids not available
    def is_foci_app(client_id):
        # Known FOCI clients
        FOCI_CLIENTS = {
            '1950a258-227b-4e31-a9cf-717495945fc2',  # Azure PowerShell
            '29d9ed98-a469-4536-ade2-f981bc1d605e',  # Microsoft Authenticator
            '04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Microsoft Azure CLI
            'd3590ed6-52b3-4102-aeff-aad2292ab01c',  # Office (common)
        }
        return client_id in FOCI_CLIENTS


class AdminActionsService:
    """Service for administrative write operations on Azure AD"""
    
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    GRAPH_BETA_URL = "https://graph.microsoft.com/beta"
    
    # Azure PowerShell Client ID - has pre-consent for admin operations
    AZURE_POWERSHELL_CLIENT_ID = "1950a258-227b-4e31-a9cf-717495945fc2"
    
    # Token endpoint
    TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    
    # Required admin roles (wids claim) - Azure AD Role Template IDs
    ADMIN_ROLES = {
        '62e90394-69f5-4237-9190-012177145e10': 'Global Administrator',
        'fe930be7-5e62-47db-91af-98c3a49a38b1': 'User Administrator',
        '966707d0-3269-4727-9be2-8c3a10f19b9d': 'Password Administrator',
        '729827e3-9c14-49f7-bb1b-9608f156bbb8': 'Helpdesk Administrator',
        'c4e39bd9-1100-46d3-8c65-fb160da0071f': 'Authentication Administrator',
        '7be44c8a-adaf-4e2a-84d6-ab2649e08a13': 'Privileged Authentication Administrator',
    }
    
    # Required scopes for admin actions
    REQUIRED_SCOPES = [
        'Directory.AccessAsUser.All',
        'UserAuthenticationMethod.ReadWrite.All',
        'User.ReadWrite.All',  # For password reset via Azure PowerShell
    ]
    
    # Scope requirements per action type
    PASSWORD_RESET_SCOPES = ['Directory.AccessAsUser.All']  # Sufficiente per password reset
    TAP_MFA_SCOPES = ['UserAuthenticationMethod.ReadWrite.All']
    
    # ========================================
    # CAPABILITY CHECK
    # ========================================
    
    @staticmethod
    def _check_au_scoped_roles(access_token):
        """
        Check for AU-scoped admin roles via Microsoft Graph API.
        AU-scoped roles are NOT in the JWT wids claim, must query API.
        
        Uses /roleManagement/directory/roleAssignments to find all role assignments
        for the current user, including AU-scoped ones.
        
        Returns:
            list of detected role names from AU assignments
        """
        print("\n[CapCheck-AU] ===== Starting AU-scoped role check =====")
        try:
            # First, get current user's ID
            print("[CapCheck-AU] Step 1: Getting user ID from /me...")
            me_response = requests.get(
                f"{AdminActionsService.GRAPH_API_URL}/me",
                headers=AdminActionsService._get_headers(access_token),
                params={'$select': 'id'},
                timeout=30
            )
            
            print(f"[CapCheck-AU] /me response: HTTP {me_response.status_code}")
            
            if me_response.status_code != 200:
                error_data = me_response.json() if me_response.text else {}
                print(f"[CapCheck-AU] ❌ Failed to get user ID: {error_data}")
                return []
            
            user_id = me_response.json().get('id')
            if not user_id:
                print(f"[CapCheck-AU] ❌ Could not extract user ID from response")
                return []
            
            print(f"[CapCheck-AU] ✓ User ID: {user_id[:8]}...")
            print(f"[CapCheck-AU] Step 2: Querying role assignments...")
            
            # Query roleAssignments filtered by principalId
            assignments_url = f"{AdminActionsService.GRAPH_API_URL}/roleManagement/directory/roleAssignments"
            filter_query = f"principalId eq '{user_id}'"
            
            print(f"[CapCheck-AU] URL: {assignments_url}")
            print(f"[CapCheck-AU] Filter: {filter_query}")
            
            assignments_response = requests.get(
                assignments_url,
                headers=AdminActionsService._get_headers(access_token),
                params={
                    '$filter': filter_query,
                    '$expand': 'roleDefinition'
                },
                timeout=30
            )
            
            print(f"[CapCheck-AU] /roleAssignments response: HTTP {assignments_response.status_code}")
            
            if assignments_response.status_code != 200:
                error_data = assignments_response.json() if assignments_response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'unknown error')
                print(f"[CapCheck-AU] ❌ Failed to get role assignments")
                print(f"[CapCheck-AU] Error message: {error_msg}")
                print(f"[CapCheck-AU] Full error: {error_data}")
                return []
            
            data = assignments_response.json()
            assignments = data.get('value', [])
            
            print(f"[CapCheck-AU] ✓ Found {len(assignments)} total role assignment(s)")
            
            detected_au_roles = []
            for idx, assignment in enumerate(assignments):
                # Check if this is an AU-scoped assignment
                directory_scope_id = assignment.get('directoryScopeId', '/')
                
                print(f"[CapCheck-AU]   Assignment #{idx+1}: directoryScopeId={directory_scope_id}")
                
                # '/' means tenant-wide (not AU-scoped), skip those as they're already in JWT
                if directory_scope_id == '/':
                    print(f"[CapCheck-AU]     → Tenant-wide (skipping, already in JWT wids)")
                    continue
                
                # AU-scoped assignments have directoryScopeId like "/administrativeUnits/{AU-ID}"
                role_definition = assignment.get('roleDefinition', {})
                role_template_id = role_definition.get('templateId')
                role_display_name = role_definition.get('displayName', 'Unknown Role')
                
                print(f"[CapCheck-AU]     → Role: {role_display_name}")
                print(f"[CapCheck-AU]     → Template ID: {role_template_id}")
                
                if role_template_id and role_template_id in AdminActionsService.ADMIN_ROLES:
                    role_name = AdminActionsService.ADMIN_ROLES[role_template_id]
                    
                    # Extract AU ID from directoryScopeId
                    au_id = 'unknown'
                    if '/administrativeUnits/' in directory_scope_id:
                        au_id = directory_scope_id.split('/')[-1]
                    
                    detected_au_roles.append(f"{role_name} (AU: {au_id[:8]}...)")
                    print(f"[CapCheck-AU]     ✓ MATCHED! {role_name} on AU {au_id[:8]}...")
                else:
                    print(f"[CapCheck-AU]     ✗ Not an admin role (not in ADMIN_ROLES dict)")
            
            if not detected_au_roles:
                print(f"[CapCheck-AU] No AU-scoped admin roles found among assignments")
            else:
                print(f"[CapCheck-AU] ===== Total AU-scoped roles detected: {len(detected_au_roles)} =====")
            
            return detected_au_roles
            
        except requests.exceptions.RequestException as e:
            print(f"[CapCheck-AU] ❌ Network error: {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"[CapCheck-AU] ❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def check_capabilities(access_token, action_type=None):
        """
        Check if current token has admin capabilities for admin actions.
        Checks BOTH directory-level roles (JWT wids) AND AU-scoped roles (API call).
        
        AUTO-FOCI FROM REFRESH TOKEN
        If has_admin_role=True but has_required_scope=False and action_type='password_reset',
        automatically attempts FOCI exchange from RT in DB to acquire required token.
        
        Args:
            access_token: JWT access token
            action_type: Optional action type filter ('password_reset' | 'tap_mfa')
        
        Returns:
            dict with:
            - has_admin_role: bool
            - has_required_scope: bool
            - can_perform_actions: bool (both role AND scope)
            - detected_roles: list of role names
            - detected_scopes: list of scopes
            - missing_scopes: list of missing required scopes
            - foci_available: bool (has refresh token for FOCI exchange)
            - recommendation: string with action to take
            - role_source: 'directory' | 'au' | 'both' | 'none'
            - action_type: specific action type checked (if provided)
            - auto_acquired_token: new token if auto-FOCI was successful
            - auto_foci_success: bool indicating if auto-FOCI was attempted and succeeded
        """
        result = {
            'success': True,
            'has_admin_role': False,
            'has_required_scope': False,
            'can_perform_actions': False,
            'detected_roles': [],
            'detected_scopes': [],
            'missing_scopes': [],
            'foci_available': False,
            'recommendation': None,
            'role_source': 'none',
            'action_type': action_type,
            'auto_acquired_token': None,
            'auto_foci_success': False
        }
        
        # Decode token
        token_info = PermissionService.decode_jwt(access_token)
        if not token_info:
            result['success'] = False
            result['error'] = 'Failed to decode token'
            return result
        
        upn = token_info.get('upn') or token_info.get('unique_name')
        result['upn'] = upn
        
        # ===== CHECK 1: Directory-level roles from JWT (wids claim) =====
        wids = token_info.get('wids', [])
        if isinstance(wids, str):
            wids = [wids]
        
        directory_roles_found = False
        for wid in wids:
            if wid in AdminActionsService.ADMIN_ROLES:
                result['detected_roles'].append(f"{AdminActionsService.ADMIN_ROLES[wid]} (Directory)")
                result['has_admin_role'] = True
                directory_roles_found = True
                print(f"[CapCheck] Directory role found: {AdminActionsService.ADMIN_ROLES[wid]}")
        
        # ===== CHECK 2: AU-scoped roles via API call =====
        au_roles = AdminActionsService._check_au_scoped_roles(access_token)
        if au_roles:
            result['detected_roles'].extend(au_roles)
            result['has_admin_role'] = True
            print(f"[CapCheck] AU-scoped roles found: {len(au_roles)}")
        
        # Set role source
        if directory_roles_found and au_roles:
            result['role_source'] = 'both'
        elif directory_roles_found:
            result['role_source'] = 'directory'
        elif au_roles:
            result['role_source'] = 'au'
        else:
            result['role_source'] = 'none'
        
        # Extract scp (scopes)
        scp = token_info.get('scp', '')
        if isinstance(scp, str):
            scopes = scp.split(' ')
        else:
            scopes = scp if scp else []
        
        result['detected_scopes'] = scopes
        
        # Check required scopes based on action_type
        if action_type == 'password_reset':
            required_scopes = AdminActionsService.PASSWORD_RESET_SCOPES
        elif action_type == 'tap_mfa':
            required_scopes = AdminActionsService.TAP_MFA_SCOPES
        else:
            # Default: ALL scopes
            required_scopes = AdminActionsService.REQUIRED_SCOPES
        
        missing_scopes = []
        for req_scope in required_scopes:
            if req_scope not in scopes:
                missing_scopes.append(req_scope)
        
        result['missing_scopes'] = missing_scopes
        result['has_required_scope'] = len(missing_scopes) == 0  # True only if ALL scopes present
        result['can_perform_actions'] = result['has_admin_role'] and result['has_required_scope']
        
        # Check if FOCI exchange is available
        result['foci_available'] = AdminActionsService._check_foci_available(upn)
        
        # ===== AUTO-FOCI FROM RT =====
        # Automatically acquire token via FOCI if:
        # 1. Has admin role (tenant-level or AU)
        # 2. Missing required scopes
        # 3. FOCI RT available in DB
        # 4. Action type is 'password_reset'
        if (result['has_admin_role'] and 
            not result['has_required_scope'] and 
            result['foci_available'] and 
            action_type == 'password_reset'):
            
            print(f"[CapCheck-AutoFOCI] Attempting auto-FOCI exchange for password_reset...")
            print(f"[CapCheck-AutoFOCI] Has admin role: {result['has_admin_role']}, Missing scopes: {result['missing_scopes']}")
            
            try:
                # Attempt FOCI exchange from RT in DB
                foci_result = AdminActionsService.foci_exchange_for_admin(access_token)
                
                if foci_result.get('success'):
                    print(f"[CapCheck-AutoFOCI] ✅ Auto-FOCI exchange successful!")
                    
                    # Update result with new token info
                    new_token = foci_result.get('access_token')
                    new_capabilities = foci_result.get('capabilities', {})
                    
                    result['auto_acquired_token'] = new_token
                    result['auto_foci_success'] = True
                    result['token_id'] = foci_result.get('token_id')
                    
                    # Update capabilities from new token
                    result['has_required_scope'] = new_capabilities.get('has_required_scope', False)
                    result['can_perform_actions'] = new_capabilities.get('can_perform_actions', False)
                    result['detected_scopes'] = new_capabilities.get('detected_scopes', [])
                    result['missing_scopes'] = new_capabilities.get('missing_scopes', [])
                    result['scopes'] = result['detected_scopes']  # Add for frontend compatibility
                    
                    # Update recommendation
                    if result['can_perform_actions']:
                        if result['role_source'] == 'au':
                            result['recommendation'] = 'au_scoped_warning'
                        else:
                            result['recommendation'] = None
                    else:
                        result['recommendation'] = 'device_code_required'
                    
                    print(f"[CapCheck-AutoFOCI] New token capabilities: can_perform={result['can_perform_actions']}")
                    
                else:
                    print(f"[CapCheck-AutoFOCI] ❌ Auto-FOCI failed: {foci_result.get('error')}")
                    result['auto_foci_error'] = foci_result.get('error')
                    
            except Exception as e:
                print(f"[CapCheck-AutoFOCI] ❌ Exception during auto-FOCI: {e}")
                import traceback
                traceback.print_exc()
                result['auto_foci_error'] = str(e)
        
        # Generate recommendation based on action_type (if auto-FOCI not attempted or failed)
        if not result['auto_foci_success']:
            if result['can_perform_actions']:
                # All good, but add warning if only AU-scoped
                if result['role_source'] == 'au':
                    result['recommendation'] = 'au_scoped_warning'
                else:
                    result['recommendation'] = None
            elif not result['has_admin_role']:
                result['recommendation'] = 'no_role'
            elif not result['has_required_scope']:
                if result['foci_available']:
                    if action_type == 'tap_mfa':
                        # FOCI won't help for TAP/MFA - need device code
                        result['recommendation'] = 'device_code_required'
                    else:
                        # Password reset can use FOCI auto-exchange
                        result['recommendation'] = 'foci_auto_exchange'
                else:
                    result['recommendation'] = 'no_scope_no_foci'
        
        # Log final result for debugging
        print(f"[CapCheck] Final result for action_type='{action_type}': "
              f"has_admin_role={result['has_admin_role']}, "
              f"has_required_scope={result['has_required_scope']}, "
              f"can_perform_actions={result['can_perform_actions']}, "
              f"auto_foci_success={result['auto_foci_success']}, "
              f"recommendation='{result['recommendation']}'")
        
        return result
    
    @staticmethod
    def _check_foci_available(upn):
        """
        Check if a FOCI-enabled refresh token is available for exchange.
        
        FOCI (Family of Client IDs) allows using a RT from one Microsoft app
        to get tokens for another app in the same family.
        
        FIX: Query filters for FOCI clients FIRST to avoid finding non-FOCI RTs
        
        Args:
            upn: User principal name
            
        Returns:
            bool: True if FOCI RT available, False otherwise
        """
        if not upn:
            return False
        
        try:
            from models.token import Token
            
            # CRITICAL FIX: Get list of FOCI client IDs to filter query
            FOCI_CLIENTS = [
                '1950a258-227b-4e31-a9cf-717495945fc2',  # Azure PowerShell
                '29d9ed98-a469-4536-ade2-f981bc1d605e',  # Microsoft Authenticator
                '04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Microsoft Azure CLI
                'd3590ed6-52b3-4102-aeff-aad2292ab01c',  # Office Master
                '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa',  # Azure Mobile App
                '872cd9fa-d31f-45e0-9eab-6e460a02d1f1',  # Visual Studio
                '1fec8e78-bce4-4aaf-ab1b-5451cc387264',  # Microsoft Teams
                '4813382a-8fa7-425e-ab75-3b753aab3abb',  # Microsoft Authenticator
                '27922004-5251-4030-b22d-91ecd9a37ea4',  # Outlook Mobile
            ]
            
            # Method 1: Check for RT in refresh_token field with FOCI filter
            rt = Token.query.filter(
                Token.upn == upn,
                Token.refresh_token.isnot(None),
                Token.refresh_token != '',
                Token.client_id.in_(FOCI_CLIENTS)  # ✅ FIX: Filter ONLY FOCI clients
            ).first()
            
            if rt:
                print(f"[CapCheck-FOCI] ✅ Found FOCI RT (method 1): client_id={rt.client_id}")
                return True
            
            # Method 2: Check for token_type = 'refresh_token' with FOCI filter
            rt2 = Token.query.filter(
                Token.upn == upn,
                Token.token_type == 'refresh_token',
                Token.client_id.in_(FOCI_CLIENTS)  # ✅ FIX: Filter ONLY FOCI clients
            ).first()
            
            if rt2:
                print(f"[CapCheck-FOCI] ✅ Found FOCI RT (method 2): client_id={rt2.client_id}")
                return True
            
            # Check if ANY RT exists (for logging)
            any_rt = Token.query.filter(
                Token.upn == upn,
                Token.refresh_token.isnot(None),
                Token.refresh_token != ''
            ).first()
            
            if any_rt:
                print(f"[CapCheck-FOCI] ❌ RT found but NOT FOCI: client_id={any_rt.client_id}")
            else:
                print(f"[CapCheck-FOCI] ❌ No RT found for UPN: {upn}")
            
            return False
            
        except Exception as e:
            print(f"[CapCheck-FOCI] Error checking FOCI availability: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def foci_exchange_for_admin(current_access_token):
        """
        Perform FOCI exchange to get Azure PowerShell token with admin scopes.
        This is the MANUAL version triggered by user button click.
        
        Returns:
            dict with:
            - success: bool
            - access_token: new token (if success)
            - error: error message (if failed)
            - capabilities: new capability check result
        """
        try:
            from models.token import Token
            from database import db
            
            # Decode current token to get UPN
            token_info = PermissionService.decode_jwt(current_access_token)
            if not token_info:
                return {'success': False, 'error': 'Failed to decode current token'}
            
            upn = token_info.get('upn') or token_info.get('unique_name')
            tenant_id = token_info.get('tid')
            
            if not upn or not tenant_id:
                return {'success': False, 'error': 'Token missing upn or tid'}
            
            print(f"[FOCI-Admin] Looking for FOCI-enabled refresh token for {upn}")
            
            # CRITICAL: List of FOCI client IDs
            FOCI_CLIENTS = [
                '1950a258-227b-4e31-a9cf-717495945fc2',  # Azure PowerShell
                '29d9ed98-a469-4536-ade2-f981bc1d605e',  # Microsoft Authenticator
                '04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Microsoft Azure CLI
                'd3590ed6-52b3-4102-aeff-aad2292ab01c',  # Office Master
                '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa',  # Azure Mobile App
                '872cd9fa-d31f-45e0-9eab-6e460a02d1f1',  # Visual Studio
                '1fec8e78-bce4-4aaf-ab1b-5451cc387264',  # Microsoft Teams
                '4813382a-8fa7-425e-ab75-3b753aab3abb',  # Microsoft Authenticator
                '27922004-5251-4030-b22d-91ecd9a37ea4',  # Outlook Mobile
            ]
            
            # Find FOCI-enabled refresh token (method 1: RT in refresh_token field)
            # Filter for FOCI clients ONLY to avoid picking non-FOCI RTs
            refresh_token_record = Token.query.filter(
                Token.upn == upn,
                Token.refresh_token.isnot(None),
                Token.refresh_token != '',
                Token.client_id.in_(FOCI_CLIENTS)  # ✅ FIX: Filter ONLY FOCI clients
            ).first()
            
            if not refresh_token_record:
                # Try token_type = 'refresh_token' (method 2: RT as token_type)
                refresh_token_record = Token.query.filter(
                    Token.upn == upn,
                    Token.token_type == 'refresh_token',
                    Token.client_id.in_(FOCI_CLIENTS)  # ✅ FIX: Filter ONLY FOCI clients
                ).first()
            
            if not refresh_token_record:
                return {
                    'success': False, 
                    'error': f'No FOCI refresh token found for {upn}. Authenticate with Azure PowerShell or Microsoft Authenticator using Device Code Flow first.'
                }
            
            # Verify the RT is FOCI-enabled (should always be true now due to filter)
            if not is_foci_app(refresh_token_record.client_id):
                return {
                    'success': False,
                    'error': f'Refresh token found but NOT FOCI-enabled (client: {refresh_token_record.client_id}). This should not happen due to query filter.'
                }
            
            refresh_token = refresh_token_record.refresh_token or refresh_token_record.access_token
            print(f"[FOCI-Admin] Found FOCI RT from client: {refresh_token_record.client_id}, length: {len(refresh_token)}")
            
            # Perform FOCI exchange with Azure PowerShell client
            token_url = AdminActionsService.TOKEN_ENDPOINT.format(tenant=tenant_id)
            
            payload = {
                'client_id': AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            print(f"[FOCI-Admin] Exchanging with Azure PowerShell client...")
            response = requests.post(token_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', error_data.get('error', f'HTTP {response.status_code}'))
                print(f"[FOCI-Admin] ❌ Exchange failed: {error_msg}")
                return {'success': False, 'error': f'FOCI exchange failed: {error_msg}'}
            
            data = response.json()
            new_access_token = data.get('access_token')
            new_refresh_token = data.get('refresh_token')
            
            print(f"[FOCI-Admin] ✅ Got new token, length: {len(new_access_token)}")
            
            # Store new tokens - update existing or create new
            new_token_info = PermissionService.decode_jwt(new_access_token)
            expires_at = None
            if new_token_info and new_token_info.get('exp'):
                expires_at = datetime.utcfromtimestamp(new_token_info['exp'])
            
            # Extract scope from new token
            new_scope = new_token_info.get('scp', '') if new_token_info else ''
            audience = new_token_info.get('aud', 'https://graph.microsoft.com') if new_token_info else 'https://graph.microsoft.com'
            
            # Deactivate all current tokens for this UPN
            Token.query.filter_by(upn=upn, is_active=True).update({'is_active': False})
            
            # Create new token entry with Azure PowerShell client
            new_token_record = Token(
                client_id=AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,
                upn=upn,
                scope=new_scope,
                audience=audience,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at,
                is_active=True,
                imported_from='FOCI Exchange',
                token_type='access_token',
                source='foci_exchange'
            )
            
            db.session.add(new_token_record)
            db.session.commit()
            
            print(f"[FOCI-Admin] ✅ Saved new token to database (ID: {new_token_record.id}) and activated")
            
            # Check capabilities of new token for password_reset actions
            # CRITICAL: Must pass action_type='password_reset' to check only password reset scopes
            # Without this, it checks ALL scopes (including TAP/MFA) and fails!
            capabilities = AdminActionsService.check_capabilities(new_access_token, action_type='password_reset')
            
            return {
                'success': True,
                'access_token': new_access_token,
                'capabilities': capabilities,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'client_id': AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,
                'token_id': new_token_record.id
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[FOCI-Admin] Network error: {e}")
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            print(f"[FOCI-Admin] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def foci_exchange_for_vault():
        """
        FOCI Exchange for Azure Key Vault data plane (vault.azure.net)
        
        Automatically exchanges FOCI Refresh Token for Key Vault data plane access token.
        This enables accessing Key Vault secrets without manual Device Code Flow.
        
        Auto-FOCI for vault.azure.net
        
        Returns:
            dict with success, access_token, token_id, error
        """
        from models.token import Token
        from database import db
        
        print(f"[FOCI-Vault] Starting FOCI exchange for vault.azure.net...")
        
        # Define FOCI clients list
        FOCI_CLIENTS = [
            '1950a258-227b-4e31-a9cf-717495945fc2',  # Azure PowerShell
            '29d9ed98-a469-4536-ade2-f981bc1d605e',  # Microsoft Authenticator
            '04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Microsoft Azure CLI
            'd3590ed6-52b3-4102-aeff-aad2292ab01c',  # Office Master
            '0c1307d4-29d6-4389-a11c-5cbe7f65d7fa',  # Azure Mobile App
            '872cd9fa-d31f-45e0-9eab-6e460a02d1f1',  # Visual Studio
            '1fec8e78-bce4-4aaf-ab1b-5451cc387264',  # Microsoft Teams
            '4813382a-8fa7-425e-ab75-3b753aab3abb',  # Microsoft Authenticator
            '27922004-5251-4030-b22d-91ecd9a37ea4',  # Outlook Mobile
        ]
        
        # Find ANY FOCI RT in database (any user with FOCI token)
        foci_rt = Token.query.filter(
            Token.refresh_token.isnot(None),
            Token.refresh_token != '',
            Token.client_id.in_(FOCI_CLIENTS)
        ).order_by(Token.last_used_at.desc()).first()
        
        if not foci_rt:
            print(f"[FOCI-Vault] No FOCI refresh token found in database")
            return {'success': False, 'error': 'No FOCI refresh token available'}
        
        print(f"[FOCI-Vault] Found FOCI RT from client: {foci_rt.client_id} (UPN: {foci_rt.upn})")
        
        # Exchange for vault.azure.net token
        # Use "common" tenant endpoint (works for all tenants)
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        payload = {
            'client_id': AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,  # Azure PowerShell
            'grant_type': 'refresh_token',
            'refresh_token': foci_rt.refresh_token,
            'scope': 'https://vault.azure.net/.default offline_access'
        }
        
        try:
            print(f"[FOCI-Vault] Requesting vault token...")
            response = requests.post(token_url, data=payload, timeout=15)
            
            if response.status_code != 200:
                error_data = response.json()
                print(f"[FOCI-Vault] ❌ Token exchange failed: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('error_description', 'Token exchange failed'),
                    'error_code': error_data.get('error')
                }
            
            token_data = response.json()
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 3600)
            
            print(f"[FOCI-Vault] ✅ Got vault token, length: {len(new_access_token)}")
            
            # Decode token to get metadata
            import jwt
            decoded = jwt.decode(new_access_token, options={"verify_signature": False})
            
            upn = decoded.get('upn') or decoded.get('unique_name') or foci_rt.upn
            tenant_id = decoded.get('tid')  # Extract from new token
            audience = decoded.get('aud', 'https://vault.azure.net')
            
            print(f"[FOCI-Vault] Token metadata: upn={upn}, audience={audience}, tid={tenant_id}")
            
            # Calculate expiration
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Save to database
            new_token_record = Token(
                upn=upn,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                client_id=AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,
                scope='https://vault.azure.net/.default',
                audience=audience,
                expires_at=expires_at,
                is_active=True,
                imported_from='FOCI Exchange (Vault)',
                token_type='access_token',
                source='foci_vault_exchange'
            )
            
            db.session.add(new_token_record)
            db.session.commit()
            
            print(f"[FOCI-Vault] ✅ Saved vault token to database (ID: {new_token_record.id})")
            
            return {
                'success': True,
                'access_token': new_access_token,
                'token_id': new_token_record.id,
                'upn': upn,
                'expires_at': expires_at.isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[FOCI-Vault] Network error: {e}")
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            print(f"[FOCI-Vault] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def auto_foci_exchange_password_reset(current_access_token):
        """
        AUTO-EXCHANGE FOCI for Password Reset tab (background operation).
        Similar to foci_exchange_for_admin but called automatically.
        
        Returns:
            dict with success, access_token (if success), token_id, error
        """
        print(f"[Auto-FOCI-Password] Starting auto FOCI exchange for Password Reset...")
        return AdminActionsService.foci_exchange_for_admin(current_access_token)
    
    @staticmethod
    def save_device_code_token(access_token, refresh_token=None, client_id=None, source_method='device_code'):
        """
        Save token obtained via Device Code Flow to database and activate it.
        
        Args:
            access_token: JWT access token
            refresh_token: Optional refresh token
            client_id: Client ID used for authentication
            source_method: Source method (default: 'device_code')
        
        Returns:
            dict with:
            - success: bool
            - token_id: database token ID
            - capabilities: capability check result
            - error: error message (if failed)
        """
        try:
            from models.token import Token
            from database import db
            
            print(f"[DeviceCode-Save] Saving device code token to database...")
            
            # Decode token to extract info
            token_info = PermissionService.decode_jwt(access_token)
            if not token_info:
                return {'success': False, 'error': 'Failed to decode access token'}
            
            upn = token_info.get('upn') or token_info.get('unique_name')
            audience = token_info.get('aud', 'https://graph.microsoft.com')
            scope = token_info.get('scp', '')
            
            # Calculate expiration
            expires_at = None
            if token_info.get('exp'):
                expires_at = datetime.utcfromtimestamp(token_info['exp'])
            
            print(f"[DeviceCode-Save] Token UPN: {upn}, Client: {client_id}, Expires: {expires_at}")
            
            # Deactivate all current tokens for this UPN
            Token.query.filter_by(upn=upn, is_active=True).update({'is_active': False})
            
            # Create new token entry
            new_token = Token(
                client_id=client_id or 'unknown',
                upn=upn,
                scope=scope,
                audience=audience,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                is_active=True,
                imported_from=f'Auth:{source_method}',
                token_type='access_token',
                source='auth'
            )
            
            db.session.add(new_token)
            
            # Also save refresh token as separate entry if present
            if refresh_token:
                rt_token = Token(
                    client_id=client_id or 'unknown',
                    upn=upn,
                    scope=scope,
                    audience=audience,
                    access_token=refresh_token,
                    refresh_token=refresh_token,
                    expires_at=None,
                    imported_from=f'Auth:{source_method}',
                    token_type='refresh_token',
                    source='auth'
                )
                db.session.add(rt_token)
            
            db.session.commit()
            
            print(f"[DeviceCode-Save] ✅ Saved token to database (ID: {new_token.id}) and activated")
            
            # Check capabilities of new token
            capabilities = AdminActionsService.check_capabilities(access_token)
            
            return {
                'success': True,
                'token_id': new_token.id,
                'access_token': access_token,
                'capabilities': capabilities,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
        except Exception as e:
            print(f"[DeviceCode-Save] Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    @staticmethod
    def _get_headers(access_token):
        """Build authorization headers for Graph API calls"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _get_admin_token_via_foci(current_access_token):
        """
        Use FOCI exchange to get an Access Token from Azure PowerShell app
        which has pre-consented permissions for admin operations.
        
        This is critical because Microsoft Graph PowerShell client may not have
        admin consent for password operations in all tenants.
        
        Returns: (success, access_token_or_error)
        """
        # First, we need a refresh token. Get it from the active token in DB
        try:
            from models.token import Token
            from database import db
            
            # Decode current token to get UPN
            token_info = PermissionService.decode_jwt(current_access_token)
            if not token_info:
                return False, "Failed to decode current token"
            
            upn = token_info.get('upn') or token_info.get('unique_name')
            tenant_id = token_info.get('tid')
            
            if not upn or not tenant_id:
                print(f"[FOCI] Missing upn or tenant_id in token")
                return False, "Token missing required claims (upn, tid)"
            
            print(f"[FOCI] Looking for refresh token for {upn}")
            
            # Find a refresh token for this user
            refresh_token_record = Token.query.filter(
                Token.upn == upn,
                Token.refresh_token.isnot(None),
                Token.refresh_token != ''
            ).first()
            
            if not refresh_token_record or not refresh_token_record.refresh_token:
                print(f"[FOCI] No refresh token found for {upn}")
                # Fallback: try to find any token with refresh_token for this user
                refresh_token_record = Token.query.filter(
                    Token.upn == upn,
                    Token.token_type == 'refresh_token'
                ).first()
                
                if not refresh_token_record:
                    return False, f"No refresh token available for {upn}. Import a token with refresh_token or use Device Code Flow."
            
            refresh_token = refresh_token_record.refresh_token or refresh_token_record.access_token
            print(f"[FOCI] Found refresh token, length: {len(refresh_token)}")
            
            # Perform FOCI exchange with Azure PowerShell client ID
            token_url = AdminActionsService.TOKEN_ENDPOINT.format(tenant=tenant_id)
            
            payload = {
                "client_id": AdminActionsService.AZURE_POWERSHELL_CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "https://graph.microsoft.com/.default offline_access"
            }
            
            print(f"[FOCI] Exchanging token with Azure PowerShell client...")
            response = requests.post(token_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get('access_token')
                print(f"[FOCI] ✅ Got new token, length: {len(new_access_token)}")
                
                # Debug: show new token scopes
                new_token_info = PermissionService.decode_jwt(new_access_token)
                if new_token_info:
                    new_scopes = new_token_info.get('scp', '')
                    print(f"[FOCI] New token scopes: {new_scopes}")
                
                return True, new_access_token
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error_description', error_data.get('error', f'HTTP {response.status_code}'))
                print(f"[FOCI] ❌ Exchange failed: {error_msg}")
                return False, f"FOCI exchange failed: {error_msg}"
                
        except Exception as e:
            print(f"[FOCI] ❌ Exception: {str(e)}")
            return False, f"FOCI exchange error: {str(e)}"
    
    @staticmethod
    def _check_permission(access_token, action_id):
        """
        Verify token has required permissions for action.
        Returns (success, error_msg, capability_details)
        """
        result = PermissionService.check_specific_action(access_token, action_id)
        
        if not result.get('success'):
            return False, result.get('error', 'Permission check failed'), None
        
        if not result.get('available'):
            details = result.get('details', {})
            missing = []
            if not details.get('has_required_role'):
                missing.append(f"roles: {details.get('required_roles', [])}")
            if not details.get('has_required_scope'):
                missing.append(f"scopes: {details.get('required_scopes', [])}")
            return False, f"Insufficient permissions. Missing: {', '.join(missing)}", details
        
        return True, None, result.get('details')
    
    @staticmethod
    def _log_action(action, target, actor, success, details=None):
        """
        Log admin action for audit trail.
        In production, this would write to a database or SIEM.
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "target": target,
            "actor": actor,
            "success": success,
            "details": details
        }
        # Print for now - in production, save to DB
        status = "✅" if success else "❌"
        print(f"[AUDIT] {status} {timestamp} | {action} | Target: {target} | Actor: {actor}")
        return log_entry
    
    # ========================================
    # CREATE USER
    # ========================================
    
    @staticmethod
    def create_user(access_token, user_data):
        """
        Create a new user in Azure AD.
        
        Required user_data fields:
        - displayName: str
        - userPrincipalName: str (must include domain, e.g. user@domain.com)
        - mailNickname: str
        - accountEnabled: bool
        - passwordProfile: dict with password and forceChangePasswordNextSignIn
        
        Optional fields:
        - givenName, surname, jobTitle, department, officeLocation, etc.
        
        Returns: dict with success status and user data or error
        """
        # Validate required fields
        required_fields = ['displayName', 'userPrincipalName', 'mailNickname', 'accountEnabled', 'passwordProfile']
        missing = [f for f in required_fields if f not in user_data]
        if missing:
            return {"success": False, "error": f"Missing required fields: {missing}"}
        
        # Get actor for audit
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        try:
            response = requests.post(
                f"{AdminActionsService.GRAPH_API_URL}/users",
                headers=AdminActionsService._get_headers(access_token),
                json=user_data,
                timeout=30
            )
            
            if response.status_code == 201:
                created_user = response.json()
                AdminActionsService._log_action(
                    "CREATE_USER",
                    created_user.get('userPrincipalName'),
                    actor,
                    True,
                    {"userId": created_user.get('id')}
                )
                return {
                    "success": True,
                    "message": "User created successfully",
                    "user": {
                        "id": created_user.get('id'),
                        "displayName": created_user.get('displayName'),
                        "userPrincipalName": created_user.get('userPrincipalName'),
                        "mail": created_user.get('mail')
                    }
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                AdminActionsService._log_action(
                    "CREATE_USER",
                    user_data.get('userPrincipalName'),
                    actor,
                    False,
                    {"error": error_msg}
                )
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("CREATE_USER", user_data.get('userPrincipalName'), actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    # ========================================
    # PASSWORD RESET
    # ========================================
    
    @staticmethod
    def reset_password(access_token, user_id, new_password, force_change=True):
        """
        Reset a user's password.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - new_password: The new password to set
        - force_change: If True, user must change password at next sign-in
        
        Returns: dict with success status
        
        Note: Requires User.ReadWrite.All or Directory.AccessAsUser.All scope
        Note: Cannot reset password for users with higher privilege (GA cannot reset another GA)
        """
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        payload = {
            "passwordProfile": {
                "password": new_password,
                "forceChangePasswordNextSignIn": force_change
            }
        }
        
        try:
            response = requests.patch(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}",
                headers=AdminActionsService._get_headers(access_token),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 204:
                AdminActionsService._log_action(
                    "RESET_PASSWORD",
                    user_id,
                    actor,
                    True,
                    {"forceChange": force_change}
                )
                return {
                    "success": True,
                    "message": "Password reset successfully",
                    "forceChange": force_change
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                AdminActionsService._log_action(
                    "RESET_PASSWORD",
                    user_id,
                    actor,
                    False,
                    {"error": error_msg}
                )
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("RESET_PASSWORD", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    # ========================================
    # TEMPORARY ACCESS PASS (TAP)
    # ========================================
    
    @staticmethod
    def create_tap(access_token, user_id, lifetime_minutes=60, is_usable_once=False, start_time=None):
        """
        Create a Temporary Access Pass for a user.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - lifetime_minutes: How long the TAP is valid (10-43200, default 60)
        - is_usable_once: If True, TAP can only be used once
        - start_time: When TAP becomes active (ISO format, default now)
        
        Returns: dict with TAP details including the pass itself
        
        Red Team Note: TAP allows authentication without knowing the password!
        """
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        # DEBUG: Log token info
        print(f"\n[CREATE_TAP DEBUG]")
        print(f"  User ID: {user_id}")
        print(f"  Actor: {actor}")
        if token_info:
            print(f"  Token client_id (appid): {token_info.get('appid', 'N/A')}")
            print(f"  Token scopes (scp): {token_info.get('scp', 'N/A')}")
            print(f"  Token roles (wids): {token_info.get('wids', 'N/A')}")
        print(f"  Token length: {len(access_token)}")
        print()
        
        # Clamp lifetime
        lifetime_minutes = max(10, min(43200, lifetime_minutes))
        
        payload = {
            "lifetimeInMinutes": lifetime_minutes,
            "isUsableOnce": is_usable_once
        }
        
        if start_time:
            payload["startDateTime"] = start_time
        
        try:
            response = requests.post(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/temporaryAccessPassMethods",
                headers=AdminActionsService._get_headers(access_token),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                tap_data = response.json()
                AdminActionsService._log_action(
                    "CREATE_TAP",
                    user_id,
                    actor,
                    True,
                    {"lifetimeMinutes": lifetime_minutes, "isUsableOnce": is_usable_once}
                )
                return {
                    "success": True,
                    "message": "TAP created successfully",
                    "tap": {
                        "id": tap_data.get('id'),
                        "temporaryAccessPass": tap_data.get('temporaryAccessPass'),
                        "lifetimeInMinutes": tap_data.get('lifetimeInMinutes'),
                        "isUsableOnce": tap_data.get('isUsableOnce'),
                        "isUsable": tap_data.get('isUsable'),
                        "startDateTime": tap_data.get('startDateTime'),
                        "methodUsabilityReason": tap_data.get('methodUsabilityReason')
                    }
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('error', {}).get('code', 'Unknown')
                
                # DETAILED ERROR LOGGING
                print(f"\n[TAP CREATE FAILED]")
                print(f"  HTTP Status: {response.status_code}")
                print(f"  Error Code: {error_code}")
                print(f"  Error Message: {error_msg}")
                print(f"  Full Response: {error_data}")
                print(f"  User ID: {user_id}")
                print(f"  Actor: {actor}\n")
                
                AdminActionsService._log_action(
                    "CREATE_TAP",
                    user_id,
                    actor,
                    False,
                    {"error": error_msg, "code": error_code}
                )
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("CREATE_TAP", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    @staticmethod
    def list_tap(access_token, user_id):
        """
        List all Temporary Access Passes for a user.
        
        Returns: dict with list of TAPs (without the actual pass values)
        """
        try:
            response = requests.get(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/temporaryAccessPassMethods",
                headers=AdminActionsService._get_headers(access_token),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                taps = data.get('value', [])
                return {
                    "success": True,
                    "taps": [{
                        "id": tap.get('id'),
                        "lifetimeInMinutes": tap.get('lifetimeInMinutes'),
                        "isUsableOnce": tap.get('isUsableOnce'),
                        "isUsable": tap.get('isUsable'),
                        "startDateTime": tap.get('startDateTime'),
                        "methodUsabilityReason": tap.get('methodUsabilityReason')
                    } for tap in taps]
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    @staticmethod
    def delete_tap(access_token, user_id, tap_id):
        """
        Delete a Temporary Access Pass.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - tap_id: ID of the TAP to delete
        
        Returns: dict with success status
        """
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        try:
            response = requests.delete(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/temporaryAccessPassMethods/{tap_id}",
                headers=AdminActionsService._get_headers(access_token),
                timeout=30
            )
            
            if response.status_code == 204:
                AdminActionsService._log_action(
                    "DELETE_TAP",
                    user_id,
                    actor,
                    True,
                    {"tapId": tap_id}
                )
                return {"success": True, "message": "TAP deleted successfully"}
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                AdminActionsService._log_action(
                    "DELETE_TAP",
                    user_id,
                    actor,
                    False,
                    {"tapId": tap_id, "error": error_msg}
                )
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("DELETE_TAP", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    # ========================================
    # MFA MANAGEMENT
    # ========================================
    
    @staticmethod
    def list_auth_methods(access_token, user_id):
        """
        List all authentication methods for a user.
        
        Returns: dict with categorized auth methods
        
        Method types:
        - password: The password (always exists)
        - phone: SMS/Voice authentication
        - email: Email OTP
        - fido2: Security keys
        - microsoftAuthenticator: Authenticator app
        - softwareOath: TOTP tokens
        - windowsHelloForBusiness: Windows Hello
        - temporaryAccessPass: TAP
        """
        # DEBUG: Log token info
        token_info = PermissionService.decode_jwt(access_token)
        print(f"\n[LIST_AUTH_METHODS DEBUG]")
        print(f"  User ID: {user_id}")
        if token_info:
            actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown'
            print(f"  Actor: {actor}")
            print(f"  Token client_id (appid): {token_info.get('appid', 'N/A')}")
            print(f"  Token scopes (scp): {token_info.get('scp', 'N/A')}")
            print(f"  Token roles (wids): {token_info.get('wids', 'N/A')}")
        print(f"  Token length: {len(access_token)}")
        print()
        
        try:
            response = requests.get(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/methods",
                headers=AdminActionsService._get_headers(access_token),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                methods = data.get('value', [])
                
                # Categorize methods
                categorized = {
                    'phone': [],
                    'email': [],
                    'fido2': [],
                    'microsoftAuthenticator': [],
                    'softwareOath': [],
                    'windowsHello': [],
                    'password': [],
                    'temporaryAccessPass': []
                }
                
                for method in methods:
                    odata_type = method.get('@odata.type', '')
                    
                    if 'phoneAuthenticationMethod' in odata_type:
                        categorized['phone'].append({
                            'id': method.get('id'),
                            'phoneNumber': method.get('phoneNumber'),
                            'phoneType': method.get('phoneType'),
                            'smsSignInState': method.get('smsSignInState')
                        })
                    elif 'emailAuthenticationMethod' in odata_type:
                        categorized['email'].append({
                            'id': method.get('id'),
                            'emailAddress': method.get('emailAddress')
                        })
                    elif 'fido2AuthenticationMethod' in odata_type:
                        categorized['fido2'].append({
                            'id': method.get('id'),
                            'displayName': method.get('displayName'),
                            'model': method.get('model'),
                            'createdDateTime': method.get('createdDateTime')
                        })
                    elif 'microsoftAuthenticatorAuthenticationMethod' in odata_type:
                        categorized['microsoftAuthenticator'].append({
                            'id': method.get('id'),
                            'displayName': method.get('displayName'),
                            'deviceTag': method.get('deviceTag'),
                            'phoneAppVersion': method.get('phoneAppVersion')
                        })
                    elif 'softwareOathAuthenticationMethod' in odata_type:
                        categorized['softwareOath'].append({
                            'id': method.get('id'),
                            'secretKey': '***'  # Never expose
                        })
                    elif 'windowsHelloForBusinessAuthenticationMethod' in odata_type:
                        categorized['windowsHello'].append({
                            'id': method.get('id'),
                            'displayName': method.get('displayName'),
                            'createdDateTime': method.get('createdDateTime')
                        })
                    elif 'passwordAuthenticationMethod' in odata_type:
                        categorized['password'].append({
                            'id': method.get('id')
                        })
                    elif 'temporaryAccessPassAuthenticationMethod' in odata_type:
                        categorized['temporaryAccessPass'].append({
                            'id': method.get('id'),
                            'isUsable': method.get('isUsable'),
                            'isUsableOnce': method.get('isUsableOnce')
                        })
                
                # Calculate MFA status
                mfa_methods = (
                    len(categorized['phone']) +
                    len(categorized['fido2']) +
                    len(categorized['microsoftAuthenticator']) +
                    len(categorized['softwareOath']) +
                    len(categorized['windowsHello'])
                )
                
                return {
                    "success": True,
                    "methods": categorized,
                    "hasMfa": mfa_methods > 0,
                    "mfaMethodCount": mfa_methods,
                    "totalMethods": len(methods)
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('error', {}).get('code', 'Unknown')
                
                # DETAILED ERROR LOGGING
                print(f"\n[LIST AUTH METHODS FAILED]")
                print(f"  HTTP Status: {response.status_code}")
                print(f"  Error Code: {error_code}")
                print(f"  Error Message: {error_msg}")
                print(f"  Full Response: {error_data}")
                print(f"  User ID: {user_id}\n")
                
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    @staticmethod
    def delete_auth_method(access_token, user_id, method_type, method_id):
        """
        Delete a specific authentication method.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - method_type: Type of method (phone, email, fido2, microsoftAuthenticator, softwareOath)
        - method_id: ID of the method to delete
        
        Returns: dict with success status
        
        Warning: Cannot delete password method. Cannot delete last MFA method if required.
        
        Red Team Note: Removing MFA can enable password-only attacks
        """
        # Map method type to API path
        method_paths = {
            "phone": "phoneMethods",
            "email": "emailMethods",
            "fido2": "fido2Methods",
            "microsoftAuthenticator": "microsoftAuthenticatorMethods",
            "softwareOath": "softwareOathMethods",
            "temporaryAccessPass": "temporaryAccessPassMethods",
            "windowsHello": "windowsHelloForBusinessMethods"
        }
        
        if method_type not in method_paths:
            return {
                "success": False, 
                "error": f"Invalid method_type. Must be one of: {list(method_paths.keys())}"
            }
        
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown'
        
        try:
            response = requests.delete(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/{method_paths[method_type]}/{method_id}",
                headers=AdminActionsService._get_headers(access_token),
                timeout=30
            )
            
            if response.status_code == 204:
                AdminActionsService._log_action(
                    "DELETE_AUTH_METHOD",
                    user_id,
                    actor,
                    True,
                    {"methodType": method_type, "methodId": method_id}
                )
                return {
                    "success": True,
                    "message": f"{method_type} authentication method deleted successfully"
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                AdminActionsService._log_action(
                    "DELETE_AUTH_METHOD",
                    user_id,
                    actor,
                    False,
                    {"methodType": method_type, "methodId": method_id, "error": error_msg}
                )
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("DELETE_AUTH_METHOD", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    @staticmethod
    def add_phone_method(access_token, user_id, phone_number, phone_type="mobile"):
        """
        Add a phone authentication method.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - phone_number: Phone number in E.164 format (e.g., +1 5555551234)
        - phone_type: "mobile", "alternateMobile", or "office"
        
        Returns: dict with created method details
        """
        valid_types = ["mobile", "alternateMobile", "office"]
        if phone_type not in valid_types:
            return {"success": False, "error": f"phone_type must be one of: {valid_types}"}
        
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        payload = {
            "phoneNumber": phone_number,
            "phoneType": phone_type
        }
        
        try:
            response = requests.post(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/phoneMethods",
                headers=AdminActionsService._get_headers(access_token),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                method_data = response.json()
                AdminActionsService._log_action(
                    "ADD_PHONE_METHOD",
                    user_id,
                    actor,
                    True,
                    {"phoneType": phone_type}
                )
                return {
                    "success": True,
                    "message": "Phone method added successfully",
                    "method": {
                        "id": method_data.get('id'),
                        "phoneNumber": method_data.get('phoneNumber'),
                        "phoneType": method_data.get('phoneType'),
                        "smsSignInState": method_data.get('smsSignInState')
                    }
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                AdminActionsService._log_action("ADD_PHONE_METHOD", user_id, actor, False, {"error": error_msg})
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("ADD_PHONE_METHOD", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    @staticmethod
    def add_email_method(access_token, user_id, email_address):
        """
        Add an email authentication method.
        
        Parameters:
        - user_id: User's object ID or userPrincipalName
        - email_address: Email address for authentication
        
        Returns: dict with created method details
        """
        token_info = PermissionService.decode_jwt(access_token)
        actor = token_info.get('upn') or token_info.get('unique_name') or 'unknown' if token_info else 'unknown'
        
        payload = {
            "emailAddress": email_address
        }
        
        try:
            response = requests.post(
                f"{AdminActionsService.GRAPH_API_URL}/users/{user_id}/authentication/emailMethods",
                headers=AdminActionsService._get_headers(access_token),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                method_data = response.json()
                AdminActionsService._log_action(
                    "ADD_EMAIL_METHOD",
                    user_id,
                    actor,
                    True,
                    {"email": email_address}
                )
                return {
                    "success": True,
                    "message": "Email method added successfully",
                    "method": {
                        "id": method_data.get('id'),
                        "emailAddress": method_data.get('emailAddress')
                    }
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                AdminActionsService._log_action("ADD_EMAIL_METHOD", user_id, actor, False, {"error": error_msg})
                return {"success": False, "error": error_msg, "details": error_data}
                
        except requests.exceptions.RequestException as e:
            AdminActionsService._log_action("ADD_EMAIL_METHOD", user_id, actor, False, {"error": str(e)})
            return {"success": False, "error": f"Request failed: {str(e)}"}
