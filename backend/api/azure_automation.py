"""
Azure Automation API endpoints
Handles Automation Account operations including Managed Identity analysis
"""
from flask import Blueprint, jsonify, request
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.automation_service import AutomationService
from services.token_service import TokenService

# Create Blueprint
azure_automation_bp = Blueprint('azure_automation', __name__)

# Token service instance
token_service = TokenService()


def find_token_for_audience(required_audience):
    """
    Find appropriate token for Azure Management API
    
    Args:
        required_audience: Required audience (e.g., 'https://management.azure.com')
        
    Returns:
        tuple: (token_string, error_msg)
    """
    print(f"[AUTOMATION-API] Searching for audience: {required_audience}")
    
    # Get all tokens - TokenService.get_all_tokens() returns LIST, not dict!
    all_tokens = token_service.get_all_tokens()
    
    if not all_tokens:
        return None, 'No tokens available in database. Please import tokens first.'
    
    print(f"[AUTOMATION-API] Total tokens in DB: {len(all_tokens)}")
    
    # Filter for access tokens only
    access_tokens = [t for t in all_tokens if t.get('token_type') in ['access_token', 'Managed Identity']]
    print(f"[AUTOMATION-API] Access tokens: {len(access_tokens)}")
    
    if not access_tokens:
        return None, 'No access tokens available. Please authenticate first.'
    
    # Check for active token first - get_active_token() returns dict or None
    active_token = token_service.get_active_token()
    if active_token:
        print(f"[AUTOMATION-API] Found ACTIVE token #{active_token.get('id')}")
        
        # Check if active token has correct audience
        if active_token.get('audience') == required_audience:
            print(f"[AUTOMATION-API] ✓ Using ACTIVE token #{active_token.get('id')} (correct audience)")
            
            # Check if expired
            if active_token.get('is_expired', False):
                print(f"[AUTOMATION-API] ⚠️ ACTIVE token is expired, searching for alternative...")
            else:
                # Return token string, not dict
                return active_token.get('access_token'), None
        else:
            print(f"[AUTOMATION-API] Active token #{active_token.get('id')} has wrong audience: {active_token.get('audience')}")
    
    # Search all access tokens for matching audience
    matching_tokens = []
    for token in access_tokens:
        if token.get('audience') == required_audience:
            matching_tokens.append(token)
    
    print(f"[AUTOMATION-API] Found {len(matching_tokens)} matching tokens after audience check")
    
    if not matching_tokens:
        return None, f'No token found with audience {required_audience}. Please authenticate with Azure PowerShell.'
    
    # Return first valid (non-expired) token
    for token in matching_tokens:
        if not token.get('is_expired', False):
            print(f"[AUTOMATION-API] Using token #{token.get('id')}")
            return token.get('access_token'), None
    
    return None, 'All matching tokens have expired. Please re-authenticate.'


@azure_automation_bp.route('/automation/<path:automation_account_id>/managed-identity', methods=['GET'])
def check_automation_managed_identity(automation_account_id):
    """
    Check Automation Account Managed Identity and permissions
    
    Path parameter:
        automation_account_id: URL-encoded full resource ID
        Format: subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Automation/automationAccounts/{name}
        
    Returns:
        JSON with identity status, role assignments, and risk score
    """
    try:
        # Reconstruct full resource ID (add leading slash)
        full_id = f"/{automation_account_id}"
        
        print(f"[AUTOMATION-API] Checking Managed Identity for: {full_id}")
        
        # Find ARM token
        required_audience = 'https://management.azure.com'
        token_string, error_msg = find_token_for_audience(required_audience)
        
        if not token_string:
            return jsonify({
                'success': False,
                'error': error_msg,
                'requiresAudience': 'https://management.azure.com/.default',
                'suggestion': 'Authenticate with Azure PowerShell to get ARM token'
            }), 200
        
        print(f"[AUTOMATION-API] Using token for ARM API")
        
        # Initialize automation service with token string
        automation_service = AutomationService(token_string)
        
        # Check Managed Identity
        result = automation_service.check_managed_identity(full_id)
        
        if result['success']:
            print(f"[AUTOMATION-API] Success - Risk Score: {result['riskScore']}")
            return jsonify({
                'success': True,
                'identity': result['identity'],
                'roleAssignments': result['roleAssignments'],
                'riskScore': result['riskScore'],
                'recommendations': result['recommendations']
            }), 200
        else:
            print(f"[AUTOMATION-API] Error: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 200
            
    except Exception as e:
        print(f"[AUTOMATION-API] Exception: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
