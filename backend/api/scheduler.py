"""
Scheduler API endpoints - Token Refresh Auto-Scheduler
"""
from flask import Blueprint, request, jsonify
from services.scheduler_service import scheduler_service

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')


@scheduler_bp.route('/status', methods=['GET'])
def get_status():
    """Get scheduler status"""
    result = scheduler_service.get_status()
    return jsonify(result)


@scheduler_bp.route('/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler"""
    result = scheduler_service.start()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@scheduler_bp.route('/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler"""
    result = scheduler_service.stop()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@scheduler_bp.route('/trigger', methods=['POST'])
def trigger_refresh():
    """Manually trigger a refresh check"""
    result = scheduler_service.trigger_now()
    return jsonify(result)


@scheduler_bp.route('/config', methods=['PUT'])
def update_config():
    """Update scheduler configuration"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    interval = data.get('interval_minutes')
    threshold = data.get('expiry_threshold_minutes')
    
    result = scheduler_service.update_config(
        interval_minutes=interval,
        expiry_threshold_minutes=threshold
    )
    
    return jsonify(result)


@scheduler_bp.route('/history', methods=['GET'])
def get_history():
    """Get refresh history"""
    limit = request.args.get('limit', 20, type=int)
    result = scheduler_service.get_history(limit=limit)
    return jsonify(result)


@scheduler_bp.route('/expiring', methods=['GET'])
def get_expiring_tokens():
    """Get tokens that will be refreshed soon"""
    from datetime import datetime, timedelta
    from models.token import Token
    
    threshold_minutes = request.args.get('threshold', 
        scheduler_service.config['expiry_threshold_minutes'], 
        type=int
    )
    
    threshold = datetime.utcnow() + timedelta(minutes=threshold_minutes)
    
    expiring = Token.query.filter(
        Token.token_type == 'access_token',
        Token.expires_at.isnot(None),
        Token.expires_at < threshold,
        Token.expires_at > datetime.utcnow()
    ).all()
    
    tokens = []
    for token in expiring:
        # Check if refresh token available
        has_rt = bool(token.refresh_token)
        if not has_rt:
            # Check for separate RT record
            from models.token import Token as TokenModel
            rt = TokenModel.query.filter(
                TokenModel.token_type == 'refresh_token',
                TokenModel.client_id == token.client_id,
                TokenModel.upn == token.upn
            ).first()
            has_rt = bool(rt)
        
        tokens.append({
            'id': token.id,
            'upn': token.upn,
            'client_id': token.client_id,
            'expires_at': token.expires_at.isoformat() if token.expires_at else None,
            'minutes_until_expiry': int((token.expires_at - datetime.utcnow()).total_seconds() / 60) if token.expires_at else None,
            'has_refresh_token': has_rt,
            'can_refresh': has_rt
        })
    
    return jsonify({
        'success': True,
        'expiring_tokens': tokens,
        'count': len(tokens),
        'threshold_minutes': threshold_minutes
    })
