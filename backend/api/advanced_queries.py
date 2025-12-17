"""
Advanced Queries API endpoint
Execute custom queries against Microsoft Graph, ARM, Key Vault, and Storage APIs
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
import requests

advanced_queries_bp = Blueprint('advanced_queries', __name__, url_prefix='/api/advanced-queries')


def _get_active_token_or_error():
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    return token, None


@advanced_queries_bp.route('/execute', methods=['POST'])
def execute_query():
    """Execute custom API query"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    endpoint_type = data.get('endpoint')
    method = data.get('method', 'GET')
    path = data.get('path', '')
    custom_base = data.get('baseUrl')
    resource_name = data.get('resourceName')
    body = data.get('body')
    
    if not path:
        return jsonify({
            'success': False,
            'error': 'Missing required field: path'
        }), 400
    
    # Determine base URL
    if endpoint_type == 'graph-v1':
        base_url = 'https://graph.microsoft.com/v1.0'
    elif endpoint_type == 'graph-beta':
        base_url = 'https://graph.microsoft.com/beta'
    elif endpoint_type == 'arm':
        base_url = 'https://management.azure.com'
    elif endpoint_type == 'keyvault':
        # Use resourceName if provided, otherwise use custom base or fail
        if resource_name:
            base_url = f'https://{resource_name}.vault.azure.net'
        elif custom_base:
            base_url = custom_base
        else:
            return jsonify({
                'success': False,
                'error': 'Vault name required for Key Vault endpoint'
            }), 400
    elif endpoint_type == 'storage':
        # Use resourceName if provided, otherwise use custom base or fail
        if resource_name:
            base_url = f'https://{resource_name}.blob.core.windows.net'
        elif custom_base:
            base_url = custom_base
        else:
            return jsonify({
                'success': False,
                'error': 'Storage account name required for Storage endpoint'
            }), 400
    elif endpoint_type == 'custom':
        base_url = custom_base
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid endpoint type'
        }), 400
    
    # Remove leading slash from path if present
    if path.startswith('/'):
        path = path[1:]
    
    # Build full URL
    url = f"{base_url}/{path}"
    
    # Prepare headers
    headers = {
        'Authorization': f'Bearer {token["access_token_full"]}',
        'Content-Type': 'application/json'
    }
    
    # Execute request
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=body, timeout=30)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=body, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=body, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported HTTP method: {method}'
            }), 400
        
        # Return response
        try:
            response_data = response.json() if response.content else {}
        except:
            response_data = response.text
        
        return jsonify({
            'success': True,
            'status': response.status_code,
            'statusText': response.reason,
            'data': response_data
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timeout'
        }), 408
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
