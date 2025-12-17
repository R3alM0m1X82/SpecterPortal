"""
Authentication API endpoints
- Portal Login (API Key authentication)
- Device Code Flow & ROPC (Azure AD authentication)
- Service Principal (Client Credentials)
"""
from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from services.token_service import TokenService
from models.user import User
from database import db
from functools import wraps
import requests
import time

# Optional PyJWT for token decoding
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("[WARNING] PyJWT not installed - Service Principal token metadata will be limited")

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Device Code Flow timeout tracking (5 minutes)
# Format: {device_code: start_timestamp}
device_code_sessions = {}
DEVICE_CODE_TIMEOUT = 300  # 5 minutes in seconds


# =====================
# PORTAL AUTHENTICATION
# =====================

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Portal login with API key
    Creates session on success
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    username = data.get('username', 'admin')  # Default to admin
    api_key = data.get('api_key') or data.get('password')  # Accept both field names
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key is required'
        }), 400
    
    # Find user
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.is_active:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401
    
    # Verify API key
    if not user.verify_api_key(api_key):
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401
    
    # Create session
    session['authenticated'] = True
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = data.get('remember', False)
    
    # Update last login
    user.update_last_login()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': user.to_dict()
    })


@auth_bp.route('/verify', methods=['GET'])
def verify():
    """
    Verify if current session is authenticated
    """
    if session.get('authenticated'):
        user = User.query.get(session.get('user_id'))
        if user and user.is_active:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': user.to_dict()
            })
    
    return jsonify({
        'success': True,
        'authenticated': False
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout and destroy session
    """
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


# =====================
# CLIENT IDS & SCOPES
# =====================

@auth_bp.route('/client-ids', methods=['GET'])
def get_client_ids():
    """Get available client IDs"""
    return jsonify({
        'success': True,
        'client_ids': AuthService.get_client_ids()
    })


@auth_bp.route('/scopes', methods=['GET'])
def get_scopes():
    """Get available scope presets"""
    return jsonify({
        'success': True,
        'scopes': AuthService.get_scopes()
    })


# =====================
# DEVICE CODE FLOW
# =====================

@auth_bp.route('/device-code/start', methods=['POST'])
def start_device_code():
    """
    Start Device Code Flow
    Returns device code and user instructions
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    client_id = data.get('client_id')
    scope = data.get('scope', 'https://graph.microsoft.com/.default offline_access')
    
    if not client_id:
        return jsonify({
            'success': False,
            'error': 'client_id is required'
        }), 400
    
    result = AuthService.start_device_code_flow(client_id, scope)
    
    if result['success']:
        # Save timestamp for timeout tracking (5 minutes)
        device_code = result.get('device_code')
        if device_code:
            device_code_sessions[device_code] = time.time()
            print(f"[DEVICE-CODE] Started session for device_code (expires in {DEVICE_CODE_TIMEOUT}s)")
        
        return jsonify(result)
    else:
        return jsonify(result), 400


@auth_bp.route('/device-code/poll', methods=['POST'])
def poll_device_code():
    """
    Poll for token after user authenticates
    Returns token or pending status
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    client_id = data.get('client_id')
    device_code = data.get('device_code')
    
    if not client_id or not device_code:
        return jsonify({
            'success': False,
            'error': 'client_id and device_code are required'
        }), 400
    
    # Check timeout (5 minutes)
    if device_code in device_code_sessions:
        elapsed_time = time.time() - device_code_sessions[device_code]
        
        if elapsed_time > DEVICE_CODE_TIMEOUT:
            # Timeout expired - cleanup and return error
            del device_code_sessions[device_code]
            print(f"[DEVICE-CODE] ❌ Session expired after {int(elapsed_time)}s (timeout: {DEVICE_CODE_TIMEOUT}s)")
            
            return jsonify({
                'success': False,
                'status': 'expired',
                'error': 'Device code authentication timeout (5 minutes). Please restart the authentication process.'
            }), 200  # Return 200 so frontend handles it gracefully
        else:
            print(f"[DEVICE-CODE] Polling... ({int(elapsed_time)}s / {DEVICE_CODE_TIMEOUT}s)")
    
    result = AuthService.poll_device_code(client_id, device_code)
    
    print(f"[DEBUG API] Poll result: {result}")
    
    if result['success']:
        # Success - cleanup session
        if device_code in device_code_sessions:
            del device_code_sessions[device_code]
            print(f"[DEVICE-CODE] ✓ Session completed and cleaned up")
        
        return jsonify(result)
    elif result.get('status') in ['pending', 'slow_down']:
        # Not an error, just waiting - return 200
        return jsonify(result), 200
    else:
        # Error - cleanup session
        if device_code in device_code_sessions:
            del device_code_sessions[device_code]
            print(f"[DEVICE-CODE] ❌ Session failed and cleaned up")
        
        return jsonify(result), 400


# =====================
# ROPC FLOW
# =====================

@auth_bp.route('/ropc', methods=['POST'])
def authenticate_ropc():
    """
    Resource Owner Password Credentials (ROPC) Flow
    WARNING: Only for lab environments without MFA!
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    username = data.get('username')
    password = data.get('password')
    client_id = data.get('client_id')
    scope = data.get('scope', 'https://graph.microsoft.com/.default offline_access')
    tenant_id = data.get('tenant_id')  # Optional tenant ID
    
    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'username and password are required'
        }), 400
    
    if not client_id:
        return jsonify({
            'success': False,
            'error': 'client_id is required'
        }), 400
    
    result = AuthService.authenticate_ropc(username, password, client_id, scope, tenant_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 401


# =====================
# SERVICE PRINCIPAL
# =====================

@auth_bp.route('/service-principal', methods=['POST'])
def authenticate_service_principal():
    """
    Authenticate as Service Principal using Client Credentials flow
    POST body:
    {
        "client_id": "xxx-xxx-xxx-xxx",
        "client_secret": "secret",
        "tenant_id": "xxx-xxx-xxx-xxx",
        "scope": "https://graph.microsoft.com/.default"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    tenant_id = data.get('tenant_id')
    scope = data.get('scope', 'https://graph.microsoft.com/.default')
    
    if not client_id or not client_secret or not tenant_id:
        return jsonify({
            'success': False,
            'error': 'client_id, client_secret and tenant_id are required'
        }), 400
    
    # OAuth 2.0 Client Credentials flow
    token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope,
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(token_url, data=payload, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            
            # Default metadata
            app_id = client_id
            app_name = 'Service Principal'
            tenant_id_from_token = tenant_id
            roles = []
            aud = scope.replace('/.default', '')
            
            # Decode token to get app info (if PyJWT available)
            if JWT_AVAILABLE:
                try:
                    decoded = jwt.decode(access_token, options={"verify_signature": False})
                    app_id = decoded.get('appid', client_id)
                    app_name = decoded.get('app_displayname', 'Service Principal')
                    tenant_id_from_token = decoded.get('tid', tenant_id)
                    roles = decoded.get('roles', [])
                    aud = decoded.get('aud', scope.replace('/.default', ''))
                    
                    print(f"[SP AUTH] Decoded token - App: {app_name}, Roles: {roles}")
                except Exception as e:
                    print(f"[SP AUTH] Failed to decode token: {e}")
            
            # Store token in database
            token_id = TokenService.add_token(
                access_token=access_token,
                refresh_token=None,  # SP tokens don't have refresh tokens
                scope=scope,
                upn=f"{app_name} (SP)",
                source='service_principal',
                client_id=client_id,
                expires_in=expires_in
            )
            
            print(f"[SP AUTH] Token stored with ID: {token_id}")
            
            return jsonify({
                'success': True,
                'token_id': token_id,
                'app_name': app_name,
                'app_id': app_id,
                'tenant_id': tenant_id_from_token,
                'scope': scope,
                'roles': roles,
                'audience': aud,
                'expires_in': expires_in,
                'message': f'Service Principal authenticated successfully'
            })
        else:
            error_data = response.json()
            error_desc = error_data.get('error_description', 'Authentication failed')
            error_code = error_data.get('error', 'unknown_error')
            
            print(f"[SP AUTH ERROR] {error_code}: {error_desc}")
            
            return jsonify({
                'success': False,
                'error': error_desc,
                'error_code': error_code
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timeout - Azure AD may be unreachable'
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        print(f"[SP AUTH EXCEPTION] {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


# =====================
# REFRESH TOKEN
# =====================

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Use refresh token to get new access token
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    refresh_token = data.get('refresh_token')
    client_id = data.get('client_id')
    scope = data.get('scope')
    
    if not refresh_token or not client_id:
        return jsonify({
            'success': False,
            'error': 'refresh_token and client_id are required'
        }), 400
    
    result = AuthService.refresh_access_token(refresh_token, client_id, scope)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# =====================
# UTILITY
# =====================

@auth_bp.route('/validate-client', methods=['POST'])
def validate_client():
    """
    Validate and get info about a client ID
    """
    data = request.get_json()
    
    if not data or not data.get('client_id'):
        return jsonify({
            'success': False,
            'error': 'client_id is required'
        }), 400
    
    result = AuthService.validate_client_id(data['client_id'])
    
    return jsonify({
        'success': True,
        **result
    })
