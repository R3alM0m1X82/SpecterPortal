"""
CAP API endpoints - Conditional Access Policy Enumeration
WITH CACHE OPTIMIZATION - TTL 15 min to prevent 429 rate limiting
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.cap_service import CAPService
from services.cache_service import graph_cache

cap_bp = Blueprint('cap', __name__, url_prefix='/api/cap')


def _get_active_token_or_error():
    """Get active token or return error response"""
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token',
            'hint': 'Please activate a token first'
        }), 401)
        
    if not token.get('access_token_full') or token['access_token_full'].endswith('...'):
        return None, (jsonify({
            'success': False,
            'error': 'Active token is truncated or invalid'
        }), 401)

    return token, None


@cap_bp.route('/policies', methods=['GET'])
def get_policies():
    """
    Get all Conditional Access Policies - CACHED 15 min
    
    Uses Azure AD Graph API 1.61-internal (ROADrecon technique)
    Requires refresh token for FOCI exchange if current token 
    doesn't have graph.windows.net audience
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    token_id = token.get('id')
    
    # Check cache first
    cached = graph_cache.get(token_id, 'cap_policies')
    if cached:
        return jsonify(cached)
    
    # Get refresh token if available
    refresh_token = token.get('refresh_token_full')
    
    cap_service = CAPService(
        token['access_token_full'],
        refresh_token
    )
    
    result = cap_service.get_conditional_access_policies()
    
    if result['success']:
        # Cache for 15 minutes
        graph_cache.set(token_id, 'cap_policies', result, ttl_seconds=900)
        return jsonify(result)
    else:
        status_code = result.get('status_code', 500)
        return jsonify(result), status_code


@cap_bp.route('/named-locations', methods=['GET'])
def get_named_locations():
    """
    Get Named Locations with full details and associated policies - CACHED 15 min
    
    Returns all Named Locations with:
    - Trusted status
    - IP ranges / Country codes
    - Associated CAP policies (reverse lookup)
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    token_id = token.get('id')
    
    # Check cache first
    cached = graph_cache.get(token_id, 'cap_named_locations')
    if cached:
        return jsonify(cached)
    
    refresh_token = token.get('refresh_token_full')
    
    cap_service = CAPService(
        token['access_token_full'],
        refresh_token
    )
    
    result = cap_service.get_named_locations()
    
    if result['success']:
        # Cache for 15 minutes
        graph_cache.set(token_id, 'cap_named_locations', result, ttl_seconds=900)
        return jsonify(result)
    else:
        status_code = result.get('status_code', 500)
        return jsonify(result), status_code


@cap_bp.route('/policies/<policy_id>', methods=['GET'])
def get_policy_detail(policy_id):
    """Get details of a specific Conditional Access Policy - uses cached policies"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    token_id = token.get('id')
    
    # Check cache first
    cached = graph_cache.get(token_id, 'cap_policies')
    if cached:
        result = cached
    else:
        # Fetch if not cached
        refresh_token = token.get('refresh_token_full')
        
        cap_service = CAPService(
            token['access_token_full'],
            refresh_token
        )
        
        result = cap_service.get_conditional_access_policies()
        
        if not result['success']:
            return jsonify(result), 500
        
        # Cache for next time
        graph_cache.set(token_id, 'cap_policies', result, ttl_seconds=900)
    
    # Find specific policy
    policy = None
    for p in result['policies']:
        if p['id'] == policy_id:
            policy = p
            break
    
    if not policy:
        return jsonify({
            'success': False,
            'error': f'Policy {policy_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'policy': policy
    })


@cap_bp.route('/authorization-policy', methods=['GET'])
def get_authorization_policy():
    """Get tenant authorization policy settings - CACHED 15 min"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    token_id = token.get('id')
    
    # Check cache first
    cached = graph_cache.get(token_id, 'cap_authorization_policy')
    if cached:
        return jsonify(cached)
    
    refresh_token = token.get('refresh_token_full')
    
    cap_service = CAPService(
        token['access_token_full'],
        refresh_token
    )
    
    result = cap_service.get_authorization_policy()
    
    if result['success']:
        # Cache for 15 minutes
        graph_cache.set(token_id, 'cap_authorization_policy', result, ttl_seconds=900)
        return jsonify(result)
    else:
        return jsonify(result), 500


@cap_bp.route('/raw', methods=['GET'])
def get_raw_policies():
    """
    Get all policies in raw format (for debugging/analysis)
    NOT CACHED - debug endpoint
    
    Returns all policy types, not just CAPs
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    refresh_token = token.get('refresh_token_full')
    
    cap_service = CAPService(
        token['access_token_full'],
        refresh_token
    )
    
    result = cap_service.get_all_policies_raw()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@cap_bp.route('/summary', methods=['GET'])
def get_policies_summary():
    """
    Get summary/analysis of all CAPs - uses cached policies
    
    Returns aggregated findings and bypass opportunities
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    token_id = token.get('id')
    
    # Try to use cached policies
    cached = graph_cache.get(token_id, 'cap_policies')
    if cached:
        result = cached
    else:
        # Fetch if not cached
        refresh_token = token.get('refresh_token_full')
        
        cap_service = CAPService(
            token['access_token_full'],
            refresh_token
        )
        
        result = cap_service.get_conditional_access_policies()
        
        if not result['success']:
            return jsonify(result), 500
        
        # Cache for next time
        graph_cache.set(token_id, 'cap_policies', result, ttl_seconds=900)
    
    policies = result['policies']
    
    # Aggregate analysis
    summary = {
        'total_policies': len(policies),
        'enabled_policies': 0,
        'disabled_policies': 0,
        'report_only_policies': 0,
        'mfa_required_policies': 0,
        'block_policies': 0,
        'device_compliance_policies': 0,
        'all_bypass_opportunities': [],
        'severity_counts': {
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        },
        'coverage_gaps': []
    }
    
    apps_covered = set()
    platforms_covered = set()
    
    for policy in policies:
        # Count by state
        state = policy.get('state', '').lower()
        if state == 'enabled':
            summary['enabled_policies'] += 1
        elif state == 'disabled':
            summary['disabled_policies'] += 1
        elif 'report' in state:
            summary['report_only_policies'] += 1
        
        # Count by controls
        controls = policy.get('grantControls', {}).get('builtInControls', [])
        if 'Require MFA' in controls:
            summary['mfa_required_policies'] += 1
        if 'Block Access' in controls:
            summary['block_policies'] += 1
        if 'Require Compliant Device' in controls or 'Require Hybrid Azure AD Joined Device' in controls:
            summary['device_compliance_policies'] += 1
        
        # Collect bypass opportunities
        analysis = policy.get('analysis', {})
        severity = analysis.get('severity', 'info')
        summary['severity_counts'][severity] += 1
        
        for bypass in analysis.get('bypass_opportunities', []):
            bypass['policy_name'] = policy['displayName']
            summary['all_bypass_opportunities'].append(bypass)
        
        # Track coverage
        conditions = policy.get('conditions', {})
        
        # Apps
        apps = conditions.get('applications', {})
        if apps.get('includeAllApps'):
            apps_covered.add('All')
        for app in apps.get('includeApplications', []):
            apps_covered.add(app.get('name', app.get('id')))
        
        # Platforms
        platforms = conditions.get('platforms', {})
        for platform in platforms.get('includePlatforms', []):
            platforms_covered.add(platform)
    
    # Identify coverage gaps
    if 'All' not in apps_covered:
        summary['coverage_gaps'].append({
            'type': 'applications',
            'message': 'Not all applications are covered by CAP',
            'covered': list(apps_covered)
        })
    
    all_platforms = {'Android', 'iOS', 'Windows', 'macOS', 'Linux'}
    missing_platforms = all_platforms - platforms_covered
    if missing_platforms and 'All' not in platforms_covered:
        summary['coverage_gaps'].append({
            'type': 'platforms',
            'message': f'Some platforms not covered: {", ".join(missing_platforms)}',
            'missing': list(missing_platforms)
        })
    
    # Check for common security gaps
    if summary['mfa_required_policies'] == 0:
        summary['coverage_gaps'].append({
            'type': 'mfa',
            'message': 'No policies require MFA',
            'severity': 'high'
        })
    
    if summary['enabled_policies'] == 0:
        summary['coverage_gaps'].append({
            'type': 'enforcement',
            'message': 'No CAPs are actively enforced',
            'severity': 'critical'
        })
    
    return jsonify({
        'success': True,
        'summary': summary,
        'tenant_id': result.get('tenant_id')
    })
