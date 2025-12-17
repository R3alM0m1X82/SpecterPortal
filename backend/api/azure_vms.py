"""
Azure Virtual Machines API endpoints
Handles VM operations including Managed Identity security scanning
"""
from flask import Blueprint, jsonify, request
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vm_service import VMService
from services.token_service import TokenService

# Create Blueprint
azure_vms_bp = Blueprint('azure_vms', __name__)

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
    print(f"[VM-API] Searching for audience: {required_audience}")
    
    # Get all tokens - TokenService.get_all_tokens() returns LIST, not dict!
    all_tokens = token_service.get_all_tokens()
    
    if not all_tokens:
        return None, 'No tokens available in database. Please import tokens first.'
    
    print(f"[VM-API] Total tokens in DB: {len(all_tokens)}")
    
    # Filter for access tokens only
    access_tokens = [t for t in all_tokens if t.get('token_type') in ['access_token', 'Managed Identity']]
    print(f"[VM-API] Access tokens: {len(access_tokens)}")
    
    if not access_tokens:
        return None, 'No access tokens available. Please authenticate first.'
    
    # Check for active token first - get_active_token() returns dict or None
    active_token = token_service.get_active_token()
    if active_token:
        print(f"[VM-API] Found ACTIVE token #{active_token.get('id')}")
        
        # Check if active token has correct audience
        if active_token.get('audience') == required_audience:
            print(f"[VM-API] ✓ Using ACTIVE token #{active_token.get('id')} (correct audience)")
            
            # Check if expired
            if active_token.get('is_expired', False):
                print(f"[VM-API] ⚠️ ACTIVE token is expired, searching for alternative...")
            else:
                # Return token string, not dict
                return active_token.get('access_token'), None
        else:
            print(f"[VM-API] Active token #{active_token.get('id')} has wrong audience: {active_token.get('audience')}")
    
    # Search all access tokens for matching audience
    matching_tokens = []
    for token in access_tokens:
        if token.get('audience') == required_audience:
            matching_tokens.append(token)
    
    print(f"[VM-API] Found {len(matching_tokens)} matching tokens after audience check")
    
    if not matching_tokens:
        return None, f'No token found with audience {required_audience}. Please authenticate with Azure PowerShell.'
    
    # Return first valid (non-expired) token
    for token in matching_tokens:
        if not token.get('is_expired', False):
            print(f"[VM-API] Using token #{token.get('id')}")
            return token.get('access_token'), None
    
    return None, 'All matching tokens have expired. Please re-authenticate.'


@azure_vms_bp.route('/vms/scan-managed-identities', methods=['POST'])
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
    try:
        data = request.get_json()
        subscription_id = data.get('subscriptionId')
        
        if not subscription_id:
            return jsonify({
                'success': False,
                'error': 'subscriptionId is required'
            }), 400
        
        print(f"[VM-API] Starting security scan for subscription: {subscription_id}")
        
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
        
        print(f"[VM-API] Using token for ARM API")
        
        # Initialize VM service
        vm_service = VMService(token_string)
        
        # Perform security scan
        result = vm_service.scan_vms_managed_identities(subscription_id)
        
        if result['success']:
            print(f"[VM-API] Scan complete: {result['summary']}")
            return jsonify({
                'success': True,
                'vms': result['vms'],
                'summary': result['summary'],
                'criticalVMs': result['criticalVMs']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 200
            
    except Exception as e:
        print(f"[VM-API] Exception: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
