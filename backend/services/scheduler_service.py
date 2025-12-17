"""
Token Refresh Scheduler Service
Automatically refreshes expiring access tokens using available refresh tokens
"""
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import db
from models.token import Token
from services.auth_service import AuthService


class SchedulerService:
    """Service for managing automatic token refresh"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one scheduler instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.scheduler = BackgroundScheduler()
        self.job_id = 'token_refresh_job'
        self.is_running = False
        
        # Default configuration
        self.config = {
            'interval_minutes': 5,          # Check every 5 minutes
            'expiry_threshold_minutes': 10, # Refresh if < 10 min to expiry
            'enabled': False
        }
        
        # History of refresh operations
        self.history = []
        self.max_history = 100
        
        self._initialized = True
        print("[Scheduler] Token Refresh Scheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            return {'success': False, 'error': 'Scheduler already running'}
        
        try:
            # Add job if not exists
            if not self.scheduler.get_job(self.job_id):
                self.scheduler.add_job(
                    self._refresh_job,
                    trigger=IntervalTrigger(minutes=self.config['interval_minutes']),
                    id=self.job_id,
                    name='Token Refresh Job',
                    replace_existing=True
                )
            
            if not self.scheduler.running:
                self.scheduler.start()
            
            self.is_running = True
            self.config['enabled'] = True
            
            self._log_event('scheduler_started', 'Scheduler started')
            print(f"[Scheduler] Started - checking every {self.config['interval_minutes']} minutes")
            
            return {
                'success': True,
                'message': f"Scheduler started (interval: {self.config['interval_minutes']}min, threshold: {self.config['expiry_threshold_minutes']}min)"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return {'success': False, 'error': 'Scheduler not running'}
        
        try:
            if self.scheduler.get_job(self.job_id):
                self.scheduler.remove_job(self.job_id)
            
            self.is_running = False
            self.config['enabled'] = False
            
            self._log_event('scheduler_stopped', 'Scheduler stopped')
            print("[Scheduler] Stopped")
            
            return {'success': True, 'message': 'Scheduler stopped'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def trigger_now(self):
        """Manually trigger a refresh check"""
        self._log_event('manual_trigger', 'Manual refresh triggered')
        return self._refresh_job()
    
    def update_config(self, interval_minutes=None, expiry_threshold_minutes=None):
        """Update scheduler configuration"""
        updated = []
        
        if interval_minutes is not None and interval_minutes > 0:
            self.config['interval_minutes'] = interval_minutes
            updated.append(f"interval={interval_minutes}min")
        
        if expiry_threshold_minutes is not None and expiry_threshold_minutes > 0:
            self.config['expiry_threshold_minutes'] = expiry_threshold_minutes
            updated.append(f"threshold={expiry_threshold_minutes}min")
        
        # Reschedule job if running
        if self.is_running and interval_minutes is not None:
            self.scheduler.reschedule_job(
                self.job_id,
                trigger=IntervalTrigger(minutes=self.config['interval_minutes'])
            )
        
        if updated:
            self._log_event('config_updated', f"Config updated: {', '.join(updated)}")
        
        return {
            'success': True,
            'config': self.config,
            'message': f"Updated: {', '.join(updated)}" if updated else "No changes"
        }
    
    def get_status(self):
        """Get current scheduler status"""
        next_run = None
        if self.is_running:
            job = self.scheduler.get_job(self.job_id)
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        
        return {
            'success': True,
            'status': {
                'is_running': self.is_running,
                'config': self.config,
                'next_run': next_run,
                'history_count': len(self.history)
            }
        }
    
    def get_history(self, limit=20):
        """Get recent refresh history"""
        return {
            'success': True,
            'history': self.history[-limit:][::-1]  # Most recent first
        }
    
    def _refresh_job(self):
        """Main job that checks and refreshes expiring tokens"""
        from flask import current_app
        
        # Need app context for database operations
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            # No app context, try to get it from scheduler
            print("[Scheduler] No app context available")
            return {'success': False, 'error': 'No app context'}
        
        with app.app_context():
            return self._do_refresh()
    
    def _do_refresh(self):
        """Perform the actual refresh operation"""
        threshold = datetime.utcnow() + timedelta(minutes=self.config['expiry_threshold_minutes'])
        
        # Find expiring access tokens
        expiring_tokens = Token.query.filter(
            Token.token_type == 'access_token',
            Token.expires_at.isnot(None),
            Token.expires_at < threshold,
            Token.expires_at > datetime.utcnow()  # Not already expired
        ).all()
        
        if not expiring_tokens:
            self._log_event('check_complete', 'No expiring tokens found')
            return {
                'success': True,
                'message': 'No expiring tokens',
                'refreshed': 0,
                'failed': 0
            }
        
        print(f"[Scheduler] Found {len(expiring_tokens)} expiring token(s)")
        
        refreshed = 0
        failed = 0
        results = []
        
        for token in expiring_tokens:
            result = self._refresh_single_token(token)
            results.append(result)
            
            if result['success']:
                refreshed += 1
            else:
                failed += 1
        
        message = f"Refreshed {refreshed}, failed {failed}"
        self._log_event('refresh_complete', message, {
            'refreshed': refreshed,
            'failed': failed,
            'results': results
        })
        
        return {
            'success': True,
            'message': message,
            'refreshed': refreshed,
            'failed': failed,
            'results': results
        }
    
    def _refresh_single_token(self, token):
        """Refresh a single access token using its refresh token"""
        # STEP 1: Find matching refresh token with SAME client_id
        refresh_token = Token.query.filter(
            Token.token_type == 'refresh_token',
            Token.client_id == token.client_id,
            Token.upn == token.upn,
            Token.refresh_token.isnot(None)
        ).first()
        
        rt_value = None
        rt_source = None
        
        if refresh_token:
            rt_value = refresh_token.refresh_token
            rt_source = f'RT record (client_id={token.client_id})'
        
        # STEP 2: Try RT embedded in the access token record
        if not rt_value and token.refresh_token:
            rt_value = token.refresh_token
            rt_source = 'RT embedded in AT record'
        
        # STEP 3: FOCI fallback - try ANY refresh token for same UPN
        # (FOCI = Family of Client IDs allows token exchange)
        if not rt_value:
            any_rt = Token.query.filter(
                Token.token_type == 'refresh_token',
                Token.upn == token.upn,
                Token.refresh_token.isnot(None)
            ).first()
            
            if any_rt:
                rt_value = any_rt.refresh_token
                rt_source = f'FOCI RT (client_id={any_rt.client_id})'
                print(f"[Scheduler] Using FOCI RT from {any_rt.client_id} to refresh {token.client_id}")
        
        # STEP 4: No RT found at all
        if not rt_value:
            return {
                'success': False,
                'token_id': token.id,
                'upn': token.upn,
                'client_id': token.client_id,
                'error': 'No refresh token found (checked same client_id, embedded, and FOCI)'
            }
        
        # Perform refresh
        print(f"[Scheduler] Refreshing token {token.id} (client_id={token.client_id}) using {rt_source}")
        result = AuthService.refresh_access_token(
            rt_value,
            token.client_id,
            scope=token.scope
        )
        
        if result['success']:
            # Optionally deactivate old token or delete it
            # For now, just log success
            return {
                'success': True,
                'token_id': token.id,
                'upn': token.upn,
                'client_id': token.client_id,
                'rt_source': rt_source,
                'new_token_id': result.get('token', {}).get('id'),
                'expires_in': result.get('expires_in')
            }
        else:
            return {
                'success': False,
                'token_id': token.id,
                'upn': token.upn,
                'client_id': token.client_id,
                'rt_source': rt_source,
                'error': result.get('error', 'Refresh failed')
            }
    
    def _log_event(self, event_type, message, data=None):
        """Log an event to history"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'message': message
        }
        if data:
            event['data'] = data
        
        self.history.append(event)
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        print(f"[Scheduler] {event_type}: {message}")


# Global instance
scheduler_service = SchedulerService()
