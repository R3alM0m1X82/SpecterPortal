"""
Email API endpoints
WITH CALENDAR IMAGES SUPPORT (cid: attachments proxy)
"""
from flask import Blueprint, request, jsonify, send_file, Response
from io import BytesIO
from services.token_service import TokenService
from services.email_service import EmailService
from services.calendar_attachments_helper import process_event_body, get_event_attachment

emails_bp = Blueprint('emails', __name__, url_prefix='/api/emails')


def _get_active_token_or_error():
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    return token, None


@emails_bp.route('/folders', methods=['GET'])
def get_folders():
    """Get all mail folders"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_folders()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/folders/recursive', methods=['GET'])
def get_folders_recursive():
    """Get all mail folders including subfolders recursively"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_all_folders_recursive()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('', methods=['GET'])
def get_emails():
    """Get inbox messages"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    top = request.args.get('top', 20, type=int)
    skip = request.args.get('skip', 0, type=int)
    folder = request.args.get('folder', 'inbox', type=str)
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_messages(top=top, skip=skip, folder=folder)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/<message_id>', methods=['GET'])
def get_email(message_id):
    """Get single email by ID"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_message_by_id(message_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/<message_id>/attachments', methods=['GET'])
def get_attachments(message_id):
    """Get email attachments list"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_attachments(message_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/<message_id>/attachments/<attachment_id>/download', methods=['GET'])
def download_attachment(message_id, attachment_id):
    """Download attachment"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.download_attachment(message_id, attachment_id)
    
    if result['success']:
        return send_file(
            BytesIO(result['content']),
            mimetype=result.get('contentType', 'application/octet-stream'),
            as_attachment=True,
            download_name=result['name']
        )
    else:
        return jsonify(result), 500


@emails_bp.route('/send', methods=['POST'])
def send_email():
    """Send email"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    to = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    body_type = data.get('bodyType', 'HTML')
    
    if not to or not subject or not body:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: to, subject, body'
        }), 400
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.send_message(to, subject, body, body_type)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@emails_bp.route('/search', methods=['GET'])
def search_emails():
    """Search emails"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    query = request.args.get('q', '')
    top = request.args.get('top', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Missing query parameter: q'
        }), 400
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.search_messages(query, top)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# PERSISTENCE TECHNIQUES - Mailbox Rules & Calendar Injection
# ============================================================================

@emails_bp.route('/rules', methods=['GET'])
def get_mailbox_rules():
    """Get all mailbox rules"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_mailbox_rules()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/rules', methods=['POST'])
def create_mailbox_rule():
    """Create mailbox rule"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    rule_type = data.get('ruleType')
    if not rule_type or rule_type not in ['forward', 'delete', 'move']:
        return jsonify({
            'success': False,
            'error': 'Invalid or missing ruleType. Must be: forward, delete, or move'
        }), 400
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.create_mailbox_rule(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@emails_bp.route('/rules/<rule_id>', methods=['DELETE'])
def delete_mailbox_rule(rule_id):
    """Delete mailbox rule"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.delete_mailbox_rule(rule_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    """Get calendar events with cid: images support"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    days_ahead = request.args.get('days', 30, type=int)
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.get_calendar_events(days_ahead)
    
    if result['success']:
        # ✅ NEW: Process event bodies to replace cid: with proxy URLs
        # This is NON-DESTRUCTIVE: if processing fails, original body is preserved
        events = result.get('events', [])
        for event in events:
            event_id = event.get('id')
            body = event.get('body', '')
            
            if body and event_id:
                try:
                    # Process body to replace cid: image references
                    processed_body = process_event_body(body, event_id, token['access_token_full'])
                    event['body'] = processed_body
                except Exception as e:
                    # If processing fails, keep original body (non-destructive)
                    print(f"[ERROR] Failed to process body for event {event_id}: {e}")
                    pass
        
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/calendar/events', methods=['POST'])
def create_calendar_event():
    """Create calendar event"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    required_fields = ['subject', 'start', 'end']
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.create_calendar_event(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@emails_bp.route('/calendar/events/<event_id>', methods=['PATCH'])
def update_calendar_event(event_id):
    """Update calendar event"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.update_calendar_event(event_id, data)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@emails_bp.route('/calendar/events/<event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    """Delete calendar event"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    email_service = EmailService(token['access_token_full'])
    result = email_service.delete_calendar_event(event_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# NEW: CALENDAR ATTACHMENTS PROXY
# Support for cid: images in calendar events
# ============================================================================

@emails_bp.route('/calendar/events/<event_id>/attachment/<path:attachment_cid>', methods=['GET'])
def proxy_calendar_attachment(event_id, attachment_cid):
    """
    Proxy endpoint to fetch and return event attachment images.
    
    This allows the frontend to display cid: images that are embedded
    as attachments in calendar events.
    
    Example:
        GET /api/emails/calendar/events/ABC123/attachment/image001.png@01DC683C.4D6FC7D0
        
    Returns:
        Image bytes with appropriate Content-Type header
    """
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    try:
        # Fetch the attachment using helper
        result = get_event_attachment(event_id, attachment_cid, token['access_token_full'])
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Attachment not found'
            }), 404
        
        # Return image bytes with proper Content-Type
        return Response(
            result['content_bytes'],
            mimetype=result['content_type'],
            headers={
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        print(f"[ERROR] proxy_calendar_attachment: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch attachment'
        }), 500
