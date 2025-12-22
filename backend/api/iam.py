"""
IAM Management API
Generic endpoints for managing Azure RBAC role assignments on any resource
Works for: VMs, Storage Accounts, Key Vaults, SQL Databases, App Services, etc.
"""
from flask import Blueprint, jsonify, request
from models.token import Token
import requests
import traceback
import jwt

iam_bp = Blueprint('iam', __name__, url_prefix='/api/iam')

def get_arm_token():
    """
    Find ARM token for current user or any available ARM token
    Returns (token_string, error_message)
    """
    # Try to get active token first
    active_token = Token.query.filter_by(is_active=True, token_type='access_token').first()
    
    if active_token and active_token.audience and 'management.azure.com' in active_token.audience.lower():
        return active_token.access_token, None
    
    # Fallback: find any ARM token
    all_tokens = Token.query.filter_by(token_type='access_token').all()
    
    for token in all_tokens:
        if token.audience and 'management.azure.com' in token.audience.lower():
            return token.access_token, None
    
    return None, 'No ARM token available. Please authenticate with Azure PowerShell or Azure CLI.'

def get_current_user_from_token(token_string):
    """
    Extract user info from ARM token
    Returns dict with objectId and upn
    """
    try:
        # Ensure token is string for jwt.decode
        if isinstance(token_string, bytes):
            token_string = token_string.decode('utf-8')
        elif not isinstance(token_string, str):
            return {'objectId': None, 'upn': 'Unknown'}
        
        decoded = jwt.decode(token_string, options={"verify_signature": False})
        return {
            'objectId': decoded.get('oid'),
            'upn': decoded.get('upn', 'Unknown')
        }
    except Exception as e:
        print(f'[IAM] Warning: Failed to decode token: {str(e)}')
        return {'objectId': None, 'upn': 'Unknown'}

def get_graph_token():
    """
    Find Graph token for current user or generate one from refresh token
    Returns (token_string, error_message)
    
    Strategy:
    1. Check if active token is Graph token
    2. Search for any Graph token with same UPN as active token
    3. Try to use refresh token to generate new Graph token
    """
    from database import db
    
    # Get active token to find current user UPN
    active_token = Token.query.filter_by(is_active=True, token_type='access_token').first()
    if not active_token:
        return None, 'No active token found'
    
    current_upn = active_token.upn
    
    # 1. Check if active token is already Graph token
    if active_token.audience and 'graph.microsoft.com' in active_token.audience.lower():
        print(f'[GRAPH] Using active Graph token for {current_upn}')
        return active_token.access_token, None
    
    # 2. Search for existing Graph token with same UPN
    print(f'[GRAPH] Searching for Graph token with UPN: {current_upn}')
    all_tokens = Token.query.filter_by(upn=current_upn, token_type='access_token').all()
    
    for token in all_tokens:
        if token.audience and 'graph.microsoft.com' in token.audience.lower():
            print(f'[GRAPH] Found existing Graph token (ID: {token.id})')
            return token.access_token, None
    
    # 3. Try to generate Graph token from refresh token
    print(f'[GRAPH] No Graph token found, attempting to generate from refresh token')
    
    # Get ALL refresh tokens for this user
    all_refresh_tokens = Token.query.filter_by(upn=current_upn, token_type='refresh_token').all()
    
    if not all_refresh_tokens:
        return None, f'No refresh tokens available for {current_upn}'
    
    print(f'[GRAPH] Found {len(all_refresh_tokens)} refresh token(s) for {current_upn}')
    
    # Filter for AUTHORITY tokens only (exclude PRT/PRT-Bound)
    authority_tokens = []
    for token in all_refresh_tokens:
        # Try multiple possible field names for tags
        tags = (getattr(token, 'classification', None) or 
                getattr(token, 'tags', None) or 
                getattr(token, 'tag', None) or 
                getattr(token, 'source_type', None) or '')
        
        tags_upper = str(tags).upper()
        
        print(f'[GRAPH] Token ID {token.id}: classification="{getattr(token, "classification", None)}", source_type="{getattr(token, "source_type", None)}", is_prt_bound={getattr(token, "is_prt_bound", None)}')
        
        # Skip PRT-Bound tokens using is_prt_bound flag
        if getattr(token, 'is_prt_bound', False):
            print(f'[GRAPH] ❌ Skipping token ID {token.id}: PRT-Bound flag set (cannot exchange)')
            continue
        
        # Skip tokens with PRT in classification/tags
        if 'PRT' in tags_upper:
            print(f'[GRAPH] ❌ Skipping token ID {token.id}: PRT tag "{tags}" (cannot exchange)')
            continue
        
        # Accept this token
        authority_tokens.append(token)
        print(f'[GRAPH] ✅ Token ID {token.id}: Usable for exchange')
    
    if not authority_tokens:
        return None, f'No AUTHORITY refresh tokens available for {current_upn} (only found PRT/PRT-Bound tokens which cannot be exchanged)'
    
    print(f'[GRAPH] Will try {len(authority_tokens)} AUTHORITY token(s)')
    
    # Try each AUTHORITY token until one works
    last_error = None
    
    for refresh_token_obj in authority_tokens:
        print(f'[GRAPH] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print(f'[GRAPH] Trying refresh token ID: {refresh_token_obj.id}')
        print(f'[GRAPH] App: {getattr(refresh_token_obj, "display_name", "Unknown")}')
        print(f'[GRAPH] Tags: {getattr(refresh_token_obj, "tags", None) or getattr(refresh_token_obj, "tag", "None")}')
        
        # Exchange refresh token for Graph access token
        try:
            # Get refresh token value - try multiple field names
            refresh_token_value = None
            
            if hasattr(refresh_token_obj, 'refresh_token') and refresh_token_obj.refresh_token:
                refresh_token_value = refresh_token_obj.refresh_token
                print(f'[GRAPH] Using refresh_token field (length: {len(refresh_token_value)})')
            elif hasattr(refresh_token_obj, 'access_token') and refresh_token_obj.access_token:
                refresh_token_value = refresh_token_obj.access_token
                print(f'[GRAPH] Using access_token field as fallback (length: {len(refresh_token_value)})')
            else:
                print(f'[GRAPH] ❌ Could not find token value in any field')
                continue
            
            # Validate token exists
            if not refresh_token_value:
                print(f'[GRAPH] ❌ Refresh token is empty')
                continue
            
            # Ensure token is a string (jwt.decode in newer versions may require specific type)
            if isinstance(refresh_token_value, bytes):
                refresh_token_value = refresh_token_value.decode('utf-8')
            elif not isinstance(refresh_token_value, str):
                print(f'[GRAPH] ❌ Invalid refresh token type: {type(refresh_token_value).__name__}')
                continue
            
            # Get tenant ID from ARM token instead of decoding refresh token
            # Refresh tokens may be encrypted or in non-JWT format
            print(f'[GRAPH] Extracting tenant ID from ARM token')
            
            # Get ARM token to extract tenant ID
            arm_token, _ = get_arm_token()
            if not arm_token:
                print(f'[GRAPH] ❌ Cannot get ARM token for tenant ID extraction')
                continue
            
            try:
                # Decode ARM token to get tenant ID
                if isinstance(arm_token, bytes):
                    arm_token = arm_token.decode('utf-8')
                
                decoded_arm = jwt.decode(arm_token, options={"verify_signature": False})
                tenant_id = decoded_arm.get('tid')
                
                if not tenant_id:
                    print(f'[GRAPH] ❌ Could not extract tenant ID from ARM token')
                    continue
                
                print(f'[GRAPH] Extracted tenant ID: {tenant_id}')
                
            except Exception as e:
                print(f'[GRAPH] ❌ Failed to extract tenant ID: {str(e)}')
                continue
            
            # Token endpoint
            token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
            
            # Request body for refresh token grant
            data = {
                'client_id': '04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Azure CLI
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token_value,  # Use validated string
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            print(f'[GRAPH] Exchanging refresh token for Graph token...')
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code == 200:
                print(f'[GRAPH] ✅ Exchange successful!')
                token_data = response.json()
                new_graph_token = token_data.get('access_token')
                
                # Save new Graph token to database
                new_token = Token(
                    client_id='04b07795-8ddb-461a-bbee-02f9e1bf7b46',  # Azure CLI client_id
                    access_token=new_graph_token,
                    token_type='access_token',
                    audience='https://graph.microsoft.com',
                    upn=current_upn,
                    display_name='Microsoft Graph',
                    is_active=False  # Don't activate it
                )
                
                # Decode to get expiry and other claims
                try:
                    # Ensure token is string for jwt.decode
                    token_to_decode = new_graph_token
                    if isinstance(token_to_decode, bytes):
                        token_to_decode = token_to_decode.decode('utf-8')
                    
                    decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
                    from datetime import datetime
                    
                    # Set expiry
                    if 'exp' in decoded:
                        new_token.expires_at = datetime.fromtimestamp(decoded.get('exp'))
                        
                except Exception as decode_err:
                    print(f'[GRAPH] Warning: Could not decode new Graph token: {decode_err}')
                    pass
                
                try:
                    db.session.add(new_token)
                    db.session.commit()
                    print(f'[GRAPH] ✅ Successfully generated and saved new Graph token (ID: {new_token.id})')
                    return new_graph_token, None  # SUCCESS - Return immediately
                except Exception as db_err:
                    print(f'[GRAPH] ❌ Database error saving token: {str(db_err)}')
                    db.session.rollback()  # Rollback to continue loop
                    last_error = str(db_err)
                    continue
                
            else:
                # Exchange failed
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error_description', f'HTTP {response.status_code}')
                error_code = error_data.get('error', 'unknown')
                
                print(f'[GRAPH] ❌ Exchange failed with error:')
                print(f'[GRAPH]    Code: {error_code}')
                print(f'[GRAPH]    Message: {error_msg}')
                
                last_error = error_msg
                
                # Continue to next token
                continue
                
        except Exception as e:
            print(f'[GRAPH] ❌ Exception during exchange: {str(e)}')
            print(traceback.format_exc())
            last_error = str(e)
            continue
    
    # If we get here, all tokens failed
    print(f'[GRAPH] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'[GRAPH] ❌ All {len(authority_tokens)} AUTHORITY token(s) failed')
    return None, f'Failed to generate Graph token: {last_error}'

def resolve_principals_via_graph(principal_ids, current_user_info):
    """
    Resolve principal IDs to display names using Graph API
    
    Args:
        principal_ids: List of principal object IDs
        current_user_info: Dict with current user's objectId and upn
    
    Returns:
        Dict mapping {principalId: displayName}
    """
    resolved = {}
    
    # Current user is already known
    current_oid = current_user_info.get('objectId')
    current_upn = current_user_info.get('upn')
    
    if current_oid:
        resolved[current_oid] = current_upn
    
    # Get remaining principal IDs to resolve
    to_resolve = [pid for pid in principal_ids if pid not in resolved and pid]
    
    if not to_resolve:
        return resolved
    
    # Get Graph token
    graph_token, error_msg = get_graph_token()
    
    if not graph_token:
        print(f'[GRAPH] Cannot resolve principals: {error_msg}')
        # Fallback: return truncated GUIDs
        for pid in to_resolve:
            resolved[pid] = f'{pid[:8]}... (Unknown)'
        return resolved
    
    # Resolve each principal via Graph API
    headers = {
        'Authorization': f'Bearer {graph_token}',
        'Content-Type': 'application/json'
    }
    
    print(f'[GRAPH] Resolving {len(to_resolve)} principals via Graph API')
    print(f'[GRAPH] Principals to resolve: {to_resolve}')
    
    for principal_id in to_resolve:
        print(f'[GRAPH] Processing principal: {principal_id}')
        
        try:
            # Try user endpoint first
            url = f'https://graph.microsoft.com/v1.0/users/{principal_id}'
            print(f'[GRAPH] Calling: {url}')
            response = requests.get(url, headers=headers, timeout=5)
            
            print(f'[GRAPH] User API response: {response.status_code}')
            
            if response.status_code == 200:
                user_data = response.json()
                display_name = user_data.get('userPrincipalName') or user_data.get('displayName') or user_data.get('mail')
                resolved[principal_id] = display_name
                print(f'[GRAPH] ✅ Resolved user: {principal_id} → {display_name}')
            elif response.status_code == 404:
                # Not a user, try service principal
                sp_url = f'https://graph.microsoft.com/v1.0/servicePrincipals/{principal_id}'
                print(f'[GRAPH] User not found, trying SP: {sp_url}')
                sp_response = requests.get(sp_url, headers=headers, timeout=5)
                
                print(f'[GRAPH] SP API response: {sp_response.status_code}')
                
                if sp_response.status_code == 200:
                    sp_data = sp_response.json()
                    display_name = sp_data.get('displayName') or sp_data.get('appDisplayName')
                    resolved[principal_id] = f'{display_name} (Service Principal)'
                    print(f'[GRAPH] ✅ Resolved SP: {principal_id} → {display_name}')
                elif sp_response.status_code == 404:
                    # Not a SP, try group
                    group_url = f'https://graph.microsoft.com/v1.0/groups/{principal_id}'
                    print(f'[GRAPH] SP not found, trying Group: {group_url}')
                    group_response = requests.get(group_url, headers=headers, timeout=5)
                    
                    print(f'[GRAPH] Group API response: {group_response.status_code}')
                    
                    if group_response.status_code == 200:
                        group_data = group_response.json()
                        display_name = group_data.get('displayName') or group_data.get('mailNickname')
                        resolved[principal_id] = f'{display_name} (Group)'
                        print(f'[GRAPH] ✅ Resolved Group: {principal_id} → {display_name}')
                    else:
                        # Could not resolve as user, SP, or group
                        resolved[principal_id] = f'{principal_id[:8]}... (Unknown)'
                        print(f'[GRAPH] ❌ Could not resolve: {principal_id} (Group returned {group_response.status_code})')
                else:
                    # SP query failed with error other than 404
                    resolved[principal_id] = f'{principal_id[:8]}... (Unknown)'
                    print(f'[GRAPH] ❌ Could not resolve: {principal_id} (SP returned {sp_response.status_code})')
            else:
                error_body = response.text[:200] if response.text else 'No error body'
                resolved[principal_id] = f'{principal_id[:8]}... (Unknown)'
                print(f'[GRAPH] ❌ User API failed with {response.status_code}: {error_body}')
                
        except Exception as e:
            print(f'[GRAPH ERROR] ❌ Failed to resolve {principal_id}: {str(e)}')
            print(traceback.format_exc())
            resolved[principal_id] = f'{principal_id[:8]}... (Error)'
    
    print(f'[GRAPH] Resolution complete. Resolved {len(resolved)} principals total')
    return resolved

@iam_bp.route('/current-user', methods=['GET'])
def get_current_user():
    """
    Get current user info from active ARM token
    
    Returns:
        {
            "success": true,
            "user": {
                "objectId": "xxx-xxx-xxx",
                "upn": "user@domain.com"
            }
        }
    """
    try:
        # Get ARM token
        token, error_msg = get_arm_token()
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Extract user info
        user_info = get_current_user_from_token(token)
        
        return jsonify({
            'success': True,
            'user': user_info
        })
        
    except Exception as e:
        print('[IAM ERROR] get_current_user:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@iam_bp.route('/resource-roles', methods=['GET'])
def get_resource_roles():
    """
    Get all role assignments for a specific resource
    
    Query params:
        resourceId: Full Azure resource ID (e.g., /subscriptions/.../virtualMachines/vm-name)
    
    Returns:
        {
            "success": true,
            "roles": [
                {
                    "assignmentId": "...",
                    "roleName": "Contributor",
                    "principalId": "...",
                    "principalName": "user@domain.com",
                    "scope": "/subscriptions/...",
                    "inherited": true/false,
                    "canDelete": true/false
                }
            ]
        }
    """
    try:
        resource_id = request.args.get('resourceId')
        
        if not resource_id:
            return jsonify({
                'success': False,
                'error': 'resourceId parameter is required'
            }), 400
        
        # Get ARM token
        token, error_msg = get_arm_token()
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Get current user
        current_user = get_current_user_from_token(token)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Extract subscription ID from resource ID
        parts = resource_id.split('/')
        if len(parts) < 3 or parts[1] != 'subscriptions':
            return jsonify({
                'success': False,
                'error': 'Invalid resource ID format'
            }), 400
        
        subscription_id = parts[2]
        
        # Query at ROOT level to capture ALL inherited roles
        # This includes:
        # - Root scope (/) assignments (e.g., User Access Administrator elevated from GA)
        # - Subscription scope
        # - Resource group scope
        # - Direct resource assignments
        
        print(f'[IAM] Fetching role assignments for resource: {resource_id}')
        print(f'[IAM] Current user: {current_user}')
        
        all_assignments = []
        
        # 1. Query ROOT scope assignments with filter
        # This captures elevated roles like User Access Administrator at "/"
        try:
            root_url = f'https://management.azure.com/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=atScope()'
            print(f'[IAM] Querying ROOT scope...')
            root_response = requests.get(root_url, headers=headers, timeout=30)
            
            if root_response.status_code == 200:
                root_assignments = root_response.json().get('value', [])
                all_assignments.extend(root_assignments)
                print(f'[IAM] Found {len(root_assignments)} assignments at ROOT scope')
            else:
                print(f'[IAM] Root query failed: {root_response.status_code}')
        except Exception as e:
            print(f'[IAM] Root query error: {e}')
        
        # 2. Query SUBSCRIPTION scope (fallback/additional)
        sub_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01'
        print(f'[IAM] Querying SUBSCRIPTION scope...')
        sub_response = requests.get(sub_url, headers=headers, timeout=30)
        
        if sub_response.status_code != 200:
            # If subscription query fails but we have root data, continue
            if not all_assignments:
                return jsonify({
                    'success': False,
                    'error': f'Failed to fetch role assignments: HTTP {sub_response.status_code}'
                }), 200
        else:
            sub_assignments = sub_response.json().get('value', [])
            print(f'[IAM] Found {len(sub_assignments)} assignments at SUBSCRIPTION scope')
            
            # Add subscription assignments (avoiding duplicates)
            existing_ids = {a.get('name') for a in all_assignments}
            for assignment in sub_assignments:
                if assignment.get('name') not in existing_ids:
                    all_assignments.append(assignment)
        
        print(f'[IAM] Total assignments to process: {len(all_assignments)}')
        
        # Filter assignments relevant to this resource
        relevant_roles = []
        
        for assignment in all_assignments:
            props = assignment.get('properties', {})
            scope = props.get('scope', '')
            principal_id = props.get('principalId')
            role_def_id = props.get('roleDefinitionId')
            
            # Check if scope applies to this resource
            # Scope can be: root (/), subscription, resource group, or specific resource
            is_relevant = (
                scope == resource_id or  # Direct assignment
                resource_id.startswith(scope + '/') or  # Inherited from parent scope
                scope == '/'  # Root scope applies to EVERYTHING
            )
            
            if not is_relevant:
                continue
            
            print(f'[IAM] Relevant role: {scope} (principalId: {principal_id})')
            
            # Get role name
            role_name = 'Unknown'
            try:
                role_response = requests.get(
                    f'https://management.azure.com{role_def_id}?api-version=2022-04-01',
                    headers=headers,
                    timeout=10
                )
                if role_response.status_code == 200:
                    role_name = role_response.json().get('properties', {}).get('roleName', 'Unknown')
            except:
                pass
            
            # Determine if inherited
            inherited = scope != resource_id
            
            # Can delete if: not inherited AND current user can manage (has Owner/UAA role)
            # For simplicity, allow delete only for direct assignments
            can_delete = not inherited
            
            relevant_roles.append({
                'assignmentId': assignment.get('name'),  # This is the GUID
                'roleName': role_name,
                'principalId': principal_id,
                'principalName': None,  # Will be resolved below via Graph API
                'scope': scope,
                'inherited': inherited,
                'canDelete': can_delete
            })
        
        print(f'[IAM] Total relevant roles found: {len(relevant_roles)}')
        
        # Resolve all principal IDs via Graph API in batch
        if relevant_roles:
            print(f'[IAM] Resolving principal names via Graph API...')
            
            # Collect unique principal IDs
            principal_ids = list(set(role['principalId'] for role in relevant_roles if role['principalId']))
            
            # Resolve via Graph
            principal_names = resolve_principals_via_graph(principal_ids, current_user)
            
            # Populate principal names
            for role in relevant_roles:
                pid = role['principalId']
                role['principalName'] = principal_names.get(pid, f'{pid[:8]}... (Unknown)')
        
        # Debug: Count roles for current user
        current_user_oid = current_user.get('objectId')
        user_roles = [r for r in relevant_roles if r['principalId'] == current_user_oid]
        other_roles = [r for r in relevant_roles if r['principalId'] != current_user_oid]
        
        print(f'[IAM] Current user ({current_user_oid}) roles: {len(user_roles)}')
        print(f'[IAM] Other principals roles: {len(other_roles)}')
        
        if user_roles:
            print(f'[IAM] Your roles:')
            for role in user_roles:
                print(f'  - {role["roleName"]} (scope: {role["scope"]}, inherited: {role["inherited"]})')
        
        return jsonify({
            'success': True,
            'roles': relevant_roles
        })
        
    except Exception as e:
        print('[IAM ERROR] get_resource_roles:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@iam_bp.route('/available-roles', methods=['GET'])
def get_available_roles():
    """
    Get available roles for a resource type
    
    Query params:
        resourceType: Azure resource type (e.g., Microsoft.Compute/virtualMachines)
    
    Returns:
        {
            "success": true,
            "roles": [
                {
                    "id": "/subscriptions/.../roleDefinitions/xxx",
                    "name": "Virtual Machine Contributor",
                    "description": "Lets you manage virtual machines..."
                }
            ]
        }
    """
    try:
        resource_type = request.args.get('resourceType', '')
        
        # Get ARM token
        token, error_msg = get_arm_token()
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        # Extract subscription from token or use first available
        active_token_obj = Token.query.filter_by(is_active=True).first()
        if not active_token_obj:
            return jsonify({
                'success': False,
                'error': 'No active token found'
            }), 200
        
        # For now, we'll return a curated list of common roles based on resource type
        # In production, you'd query: GET /subscriptions/{subscriptionId}/providers/Microsoft.Authorization/roleDefinitions
        
        common_roles = {
            'Microsoft.Compute/virtualMachines': [
                {'name': 'Virtual Machine Contributor', 'id': '9980e02c-c2be-4d73-94e8-173b1dc7cf3c', 'description': 'Lets you manage virtual machines, but not access to them'},
                {'name': 'Virtual Machine Administrator Login', 'id': '1c0163c0-47e6-4577-8991-ea5c82e286e4', 'description': 'View Virtual Machines in the portal and login as administrator'},
                {'name': 'Owner', 'id': '8e3af657-a8ff-443c-a75c-2fe8c4bcb635', 'description': 'Grants full access to manage all resources, including the ability to assign roles'},
                {'name': 'Contributor', 'id': 'b24988ac-6180-42a0-ab88-20f7382dd24c', 'description': 'Grants full access to manage all resources'},
                {'name': 'Reader', 'id': 'acdd72a7-3385-48ef-bd42-f606fba81ae7', 'description': 'View all resources, but does not allow you to make any changes'},
            ],
            'Microsoft.Storage/storageAccounts': [
                {'name': 'Storage Blob Data Owner', 'id': 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b', 'description': 'Provides full access to Azure Storage blob containers and data'},
                {'name': 'Storage Blob Data Contributor', 'id': 'ba92f5b4-2d11-453d-a403-e96b0029c9fe', 'description': 'Read, write, and delete Azure Storage containers and blobs'},
                {'name': 'Storage Blob Data Reader', 'id': '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1', 'description': 'Read and list Azure Storage containers and blobs'},
                {'name': 'Storage Account Contributor', 'id': '17d1049b-9a84-46fb-8f53-869881c3d3ab', 'description': 'Lets you manage storage accounts'},
                {'name': 'Owner', 'id': '8e3af657-a8ff-443c-a75c-2fe8c4bcb635', 'description': 'Grants full access to manage all resources, including the ability to assign roles'},
                {'name': 'Contributor', 'id': 'b24988ac-6180-42a0-ab88-20f7382dd24c', 'description': 'Grants full access to manage all resources'},
                {'name': 'Reader', 'id': 'acdd72a7-3385-48ef-bd42-f606fba81ae7', 'description': 'View all resources'},
            ],
            'Microsoft.KeyVault/vaults': [
                {'name': 'Key Vault Administrator', 'id': '00482a5a-887f-4fb3-b363-3b7fe8e74483', 'description': 'Perform all data plane operations on a key vault'},
                {'name': 'Key Vault Secrets Officer', 'id': 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7', 'description': 'Perform any action on the secrets of a key vault'},
                {'name': 'Key Vault Secrets User', 'id': '4633458b-17de-408a-b874-0445c86b69e6', 'description': 'Read secret contents'},
                {'name': 'Key Vault Contributor', 'id': 'f25e0fa2-a7c8-4377-a976-54943a77a395', 'description': 'Manage key vaults, but not access to data'},
                {'name': 'Owner', 'id': '8e3af657-a8ff-443c-a75c-2fe8c4bcb635', 'description': 'Grants full access to manage all resources, including the ability to assign roles'},
                {'name': 'Contributor', 'id': 'b24988ac-6180-42a0-ab88-20f7382dd24c', 'description': 'Grants full access to manage all resources'},
                {'name': 'Reader', 'id': 'acdd72a7-3385-48ef-bd42-f606fba81ae7', 'description': 'View all resources'},
            ],
            'default': [
                {'name': 'Contributor', 'id': 'b24988ac-6180-42a0-ab88-20f7382dd24c', 'description': 'Grants full access to manage all resources'},
                {'name': 'Reader', 'id': 'acdd72a7-3385-48ef-bd42-f606fba81ae7', 'description': 'View all resources'},
                {'name': 'Owner', 'id': '8e3af657-a8ff-443c-a75c-2fe8c4bcb635', 'description': 'Grants full access to manage all resources, including the ability to assign roles'},
            ]
        }
        
        # Get roles for this resource type or default
        roles = common_roles.get(resource_type, common_roles['default'])
        
        # Format roles with full definition IDs (using built-in role IDs)
        formatted_roles = []
        for role in roles:
            formatted_roles.append({
                'id': f"/providers/Microsoft.Authorization/roleDefinitions/{role['id']}",
                'name': role['name'],
                'description': role['description']
            })
        
        return jsonify({
            'success': True,
            'roles': formatted_roles
        })
        
    except Exception as e:
        print('[IAM ERROR] get_available_roles:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@iam_bp.route('/assign-role', methods=['POST'])
def assign_role():
    """
    Assign a role to a principal on a resource
    
    Request body:
        {
            "resourceId": "/subscriptions/.../virtualMachines/vm-name",
            "roleDefinitionId": "/providers/Microsoft.Authorization/roleDefinitions/xxx",
            "principalId": "user-object-id"
        }
    
    Returns:
        {
            "success": true,
            "assignmentId": "..."
        }
    """
    try:
        data = request.get_json()
        
        resource_id = data.get('resourceId')
        role_def_id = data.get('roleDefinitionId')
        principal_id = data.get('principalId')
        
        if not all([resource_id, role_def_id, principal_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: resourceId, roleDefinitionId, principalId'
            }), 400
        
        # Get ARM token
        token, error_msg = get_arm_token()
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Generate unique assignment ID (GUID)
        import uuid
        assignment_id = str(uuid.uuid4())
        
        # Create role assignment
        url = f'https://management.azure.com{resource_id}/providers/Microsoft.Authorization/roleAssignments/{assignment_id}?api-version=2022-04-01'
        
        payload = {
            'properties': {
                'roleDefinitionId': role_def_id,
                'principalId': principal_id
            }
        }
        
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'assignmentId': assignment_id,
                'message': 'Role assigned successfully'
            })
        else:
            error_detail = response.json() if response.content else {}
            error_msg = error_detail.get('error', {}).get('message', f'HTTP {response.status_code}')
            
            return jsonify({
                'success': False,
                'error': f'Failed to assign role: {error_msg}'
            }), 200
        
    except Exception as e:
        print('[IAM ERROR] assign_role:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@iam_bp.route('/remove-role/<assignment_id>', methods=['DELETE'])
def remove_role(assignment_id):
    """
    Remove a role assignment
    
    Path params:
        assignment_id: The role assignment GUID
    
    Query params:
        resourceId: Full Azure resource ID (required to construct the delete URL)
    
    Returns:
        {
            "success": true,
            "message": "Role removed successfully"
        }
    """
    try:
        resource_id = request.args.get('resourceId')
        
        if not resource_id:
            # Try to find assignment via subscription-wide search
            # For now, require resourceId
            return jsonify({
                'success': False,
                'error': 'resourceId parameter is required'
            }), 400
        
        # Get ARM token
        token, error_msg = get_arm_token()
        if not token:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 200
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Delete role assignment
        url = f'https://management.azure.com{resource_id}/providers/Microsoft.Authorization/roleAssignments/{assignment_id}?api-version=2022-04-01'
        
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Role removed successfully'
            })
        else:
            error_detail = response.json() if response.content else {}
            error_msg = error_detail.get('error', {}).get('message', f'HTTP {response.status_code}')
            
            return jsonify({
                'success': False,
                'error': f'Failed to remove role: {error_msg}'
            }), 200
        
    except Exception as e:
        print('[IAM ERROR] remove_role:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
