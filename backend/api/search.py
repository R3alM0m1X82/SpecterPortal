"""
Search API endpoints
Microsoft Search + Sensitive Data Discovery
Teams Secrets Scanner with Skype API integration
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.search_service import SearchService
from services.teams_secrets_scanner_service import TeamsScanManager

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


def _get_active_token_or_error():
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    if not token.get('access_token_full') or token['access_token_full'].endswith('...'):
        return None, (jsonify({
            'success': False,
            'error': 'Active token is truncated or invalid'
        }), 401)

    return token, None


@search_bp.route('/microsoft', methods=['POST'])
def microsoft_search():
    """
    Microsoft Search - Search across M365 apps
    
    NOTE: Teams chat search moved to /teams/scan endpoints (uses Skype API)
    This endpoint now supports: Files, Emails, SharePoint
    
    Request body:
    {
        "query": "search terms",
        "entity_types": ["driveItem", "message", "site"],  // SharePoint instead of chatMessage
        "size": 25
    }
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data or not data.get('query'):
        return jsonify({
            'success': False,
            'error': 'Missing query parameter'
        }), 400
    
    query = data.get('query')
    entity_types = data.get('entity_types')
    size = data.get('size', 25)
    
    try:
        print(f"[DEBUG] Microsoft Search - Query: {query}")
        print(f"[DEBUG] Entity types: {entity_types}")
        print(f"[DEBUG] Size: {size}")
        
        search_service = SearchService(token['access_token_full'])
        result = search_service.microsoft_search(query, entity_types, size)
        
        print(f"[DEBUG] Result success: {result.get('success')}")
        
        if result['success']:
            return jsonify(result)
        else:
            print(f"[DEBUG] Result error: {result.get('error')}")
            print(f"[DEBUG] Result details: {result.get('details')}")
            return jsonify(result), 500
            
    except Exception as e:
        print(f"[ERROR] Microsoft Search Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/patterns', methods=['GET'])
def get_patterns():
    """Get all available sensitive data patterns"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    search_service = SearchService(token['access_token_full'])
    result = search_service.get_patterns()
    
    return jsonify(result)


@search_bp.route('/scan/text', methods=['POST'])
def scan_text():
    """
    Scan text content for sensitive patterns
    
    Request body:
    {
        "content": "text to scan",
        "enabled_patterns": ["aws_access_key", "password_assignment", ...]
    }
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({
            'success': False,
            'error': 'Missing content parameter'
        }), 400
    
    content = data.get('content')
    enabled_patterns = data.get('enabled_patterns')
    
    search_service = SearchService(token['access_token_full'])
    findings = search_service.scan_for_patterns(content, enabled_patterns)
    
    return jsonify({
        'success': True,
        'findings': findings,
        'total_count': len(findings)
    })


@search_bp.route('/scan/onedrive', methods=['POST'])
def scan_onedrive():
    """
    Scan OneDrive files for sensitive patterns
    
    Request body:
    {
        "enabled_patterns": ["aws_access_key", "password_assignment", ...],
        "max_files": 100
    }
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json() or {}
    
    enabled_patterns = data.get('enabled_patterns')
    max_files = data.get('max_files', 100)
    
    search_service = SearchService(token['access_token_full'])
    result = search_service.scan_onedrive_files(enabled_patterns, max_files)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# TEAMS SECRETS SCANNER ENDPOINTS (NEW)
# Uses Skype API for direct message access + advanced pattern detection
# ============================================================================

@search_bp.route('/teams/scan/start', methods=['POST'])
def teams_scan_start():
    """
    Start Teams Secrets Scanner
    
    POST /api/search/teams/scan/start
    
    Request body:
    {
        "max_conversations": 100,          // Max conversations to scan
        "skip_empty": true,                // Skip empty conversations
        "enabled_patterns": [...]          // Optional: specific patterns to check
    }
    
    Returns:
        {
            "success": true,
            "scan_id": "abc12345",
            "message": "Scan started"
        }
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json() or {}
    
    # Scan options
    options = {
        'max_conversations': data.get('max_conversations', 100),
        'skip_empty': data.get('skip_empty', True),
        'enabled_patterns': data.get('enabled_patterns')
    }
    
    try:
        # Create scan
        create_result = TeamsScanManager.create_scan(
            token_id=token['id'],
            options=options
        )
        
        if not create_result['success']:
            return jsonify(create_result), 400
        
        scan_id = create_result['scan_id']
        
        # Start scan in background
        start_result = TeamsScanManager.start_scan(scan_id)
        
        if not start_result['success']:
            return jsonify(start_result), 400
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'message': 'Teams scan started'
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Teams scan start error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/progress/<scan_id>', methods=['GET'])
def teams_scan_progress(scan_id):
    """
    Get Teams scan progress
    
    GET /api/search/teams/scan/progress/{scan_id}
    
    Returns:
        {
            "success": true,
            "scan_id": "abc12345",
            "status": "running",  // initializing/running/completed/stopped/error
            "progress": {
                "total_conversations": 150,
                "scanned_conversations": 45,
                "total_messages": 1234,
                "secrets_found": 12,
                "current_conversation_name": "Project Alpha",
                "percent": 30
            },
            "start_time": 1234567890,
            "end_time": null
        }
    """
    try:
        result = TeamsScanManager.get_scan_progress(scan_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"[ERROR] Teams scan progress error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/results/<scan_id>', methods=['GET'])
def teams_scan_results(scan_id):
    """
    Get Teams scan results with optional filtering
    
    GET /api/search/teams/scan/results/{scan_id}?severity=critical&limit=100
    
    Query parameters:
        - severity: Filter by severity (critical/high/medium/low)
        - secret_type: Filter by secret type
        - limit: Max results to return (default 500)
    
    Returns:
        {
            "success": true,
            "scan_id": "abc12345",
            "status": "completed",
            "progress": {...},
            "secrets": [
                {
                    "id": "secret_1",
                    "secret_type": "AWS Access Key",
                    "redacted_value": "AKIA****",
                    "confidence": 0.95,
                    "severity": "critical",
                    "conversation_name": "DevOps Team",
                    "sender": "john@company.com",
                    "timestamp": "2025-01-11T10:30:00Z",
                    "context_before": "...",
                    "context_after": "..."
                }
            ],
            "total_secrets": 12,
            "filtered_count": 5
        }
    """
    try:
        # Get filters from query params
        filters = {
            'severity': request.args.get('severity'),
            'secret_type': request.args.get('secret_type'),
            'limit': request.args.get('limit', 500, type=int)
        }
        
        result = TeamsScanManager.get_scan_results(scan_id, filters)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"[ERROR] Teams scan results error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/stop/<scan_id>', methods=['POST'])
def teams_scan_stop(scan_id):
    """
    Stop a running Teams scan
    
    POST /api/search/teams/scan/stop/{scan_id}
    
    Returns:
        {
            "success": true,
            "message": "Scan stopped"
        }
    """
    try:
        result = TeamsScanManager.stop_scan(scan_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"[ERROR] Teams scan stop error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/delete/<scan_id>', methods=['DELETE'])
def teams_scan_delete(scan_id):
    """
    Delete a scan from memory
    
    DELETE /api/search/teams/scan/delete/{scan_id}
    
    Returns:
        {
            "success": true,
            "message": "Scan deleted"
        }
    """
    try:
        result = TeamsScanManager.delete_scan(scan_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"[ERROR] Teams scan delete error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/list', methods=['GET'])
def teams_scan_list():
    """
    List all active scans
    
    GET /api/search/teams/scan/list
    
    Returns:
        {
            "success": true,
            "scans": [
                {
                    "scan_id": "abc12345",
                    "status": "running",
                    "user_email": "user@company.com",
                    "start_time": 1234567890,
                    "progress": {...}
                }
            ],
            "count": 2
        }
    """
    try:
        result = TeamsScanManager.list_scans()
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[ERROR] Teams scan list error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/context/<scan_id>/<message_id>', methods=['GET'])
def teams_scan_context(scan_id, message_id):
    """
    Get message context (surrounding messages)
    
    GET /api/search/teams/scan/context/{scan_id}/{message_id}
    
    Returns:
        {
            "success": true,
            "message_id": "msg_123",
            "context": {
                "before": "text before secret",
                "message": "full message content",
                "after": "text after secret",
                "conversation_name": "DevOps Team",
                "sender": "john@company.com",
                "timestamp": "2025-01-11T10:30:00Z"
            }
        }
    """
    try:
        result = TeamsScanManager.get_message_context(scan_id, message_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"[ERROR] Teams scan context error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@search_bp.route('/teams/scan/export/<scan_id>', methods=['GET'])
def teams_scan_export(scan_id):
    """
    Export scan results (TruffleHog-compatible format)
    
    GET /api/search/teams/scan/export/{scan_id}
    
    Returns:
        {
            "success": true,
            "export": {
                "scan_info": {...},
                "results": [...]
            }
        }
    """
    try:
        result = TeamsScanManager.export_results(scan_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"[ERROR] Teams scan export error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
