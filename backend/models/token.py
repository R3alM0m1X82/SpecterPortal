"""
Token model for storing Microsoft OAuth tokens
Enhanced with BrokerDecrypt support + SpecterBroker fields
"""
from datetime import datetime
from database import db
import json
import sys
import os

# Import client_ids module
sys.path.insert(0, os.path.dirname(__file__))
try:
    from client_ids import get_app_name, is_foci_app
except:
    def get_app_name(cid): return cid
    def is_foci_app(cid): return False


class Token(db.Model):
    __tablename__ = 'tokens'
    
    # Original fields
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.String(255), nullable=False, index=True)
    upn = db.Column(db.String(255), nullable=True, index=True)
    scope = db.Column(db.Text, nullable=True)
    audience = db.Column(db.String(255), nullable=True, index=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    imported_from = db.Column(db.String(255), nullable=True)
    
    # BrokerDecrypt fields
    token_type = db.Column(db.String(20), default='access_token', index=True)
    source = db.Column(db.String(20), default='tbres', index=True)
    broker_cache_path = db.Column(db.Text, nullable=True)
    parent_token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=True, index=True)
    metadata_json = db.Column(db.Text, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # NEW: SpecterBroker v1.2 fields
    source_type = db.Column(db.String(20), nullable=True, index=True)  # AUTHORITY_FILE/PRT_FILE/UNKNOWN
    is_prt_bound = db.Column(db.Boolean, default=False, index=True)    # PRT-bound refresh token flag
    display_name = db.Column(db.String(255), nullable=True, index=True)  # Full user display name
    classification = db.Column(db.String(20), nullable=True, index=True)  # FOCI/STANDALONE/PRT_BOUND
    
    # Relationships
    children = db.relationship('Token', backref=db.backref('parent', remote_side=[id]))
    
    def __repr__(self):
        return f'<Token {self.id}: {self.token_type} - {self.upn or self.client_id}>'
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'client_app_name': get_app_name(self.client_id),
            'is_foci': is_foci_app(self.client_id),
            'upn': self.upn,
            'scope': self.scope,
            'audience': self.audience,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'imported_from': self.imported_from,
            'token_type': self.token_type,
            'source': self.source,
            'broker_cache_path': self.broker_cache_path,
            'parent_token_id': self.parent_token_id,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'has_refresh_token': self.token_type == 'refresh_token',
            'is_expired': self.is_expired,
            'is_office_master': self.is_office_master,
            # NEW: SpecterBroker v1.2 fields
            'source_type': self.source_type,
            'is_prt_bound': self.is_prt_bound,
            'display_name': self.display_name,
            'classification': self.classification,
        }
        
        # Return full token when include_sensitive=True
        if include_sensitive:
            # Full tokens for sensitive operations
            data['access_token'] = self.access_token
            data['refresh_token'] = self.refresh_token
            # Keep _full variants for backward compatibility
            data['access_token_full'] = self.access_token
            data['refresh_token_full'] = self.refresh_token
        else:
            # Truncated tokens for list views (security)
            if self.token_type == 'access_token':
                data['access_token'] = self.access_token[:50] + '...' if self.access_token else None
            elif self.token_type == 'refresh_token':
                data['refresh_token'] = self.access_token[:50] + '...' if self.access_token else None
            elif self.token_type == 'ngc_token':
                data['ngc_token'] = self.access_token[:50] + '...' if self.access_token else None
        
        if self.metadata_json:
            try:
                data['metadata'] = json.loads(self.metadata_json)
            except:
                data['metadata'] = None
        else:
            data['metadata'] = None
        
        return data
    
    def to_dict_full(self):
        return self.to_dict(include_sensitive=True)
    
    @property
    def is_office_master(self):
        return self.client_id == 'd3590ed6-52b3-4102-aeff-aad2292ab01c'
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_refresh_token(self):
        return self.token_type == 'refresh_token'
    
    @property
    def is_ngc_token(self):
        return self.token_type == 'ngc_token'
    
    @property
    def is_broker_token(self):
        return self.source == 'broker'
    
    def get_metadata(self):
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except:
            return {}
    
    def set_metadata(self, metadata_dict):
        if metadata_dict:
            self.metadata_json = json.dumps(metadata_dict)
        else:
            self.metadata_json = None
    
    def mark_used(self):
        self.last_used_at = datetime.utcnow()
    
    @staticmethod
    def from_broker_data(broker_token_data, cache_file_path=None):
        """Create Token from BrokerDecrypt JSON with SpecterBroker v1.2 fields"""
        token_type = broker_token_data.get('type', 'access_token')
        
        # Map type
        if token_type == 'refresh_token':
            db_token_type = 'refresh_token'
            token_value = broker_token_data.get('token', '')
        elif token_type == 'ngc_token':
            db_token_type = 'ngc_token'
            token_value = broker_token_data.get('token', '')
        else:
            db_token_type = 'access_token'
            token_value = broker_token_data.get('access_token', '')
        
        # Extract fields
        client_id = broker_token_data.get('client_id') or 'unknown'
        upn = broker_token_data.get('email') or broker_token_data.get('upn')
        scope = broker_token_data.get('scope')
        
        # For Access Tokens: extract audience from claims
        audience = None
        if db_token_type == 'access_token' and broker_token_data.get('claims'):
            audience = broker_token_data['claims'].get('aud')
        # For RT/NGC: try to get from metadata
        elif broker_token_data.get('metadata', {}).get('audience'):
            audience = broker_token_data['metadata']['audience']
        
        # Parse expires_at from JWT 'exp' claim, not response 'expires_at'
        expires_at = None
        try:
            claims = broker_token_data.get('claims')
            if claims and claims.get('exp'):
                expires_at = datetime.utcfromtimestamp(int(claims['exp']))
        except:
            pass
        
        # Fallback if 'claims' not avaiable
        if not expires_at and broker_token_data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(broker_token_data['expires_at'].replace('Z', '+00:00'))
            except:
                pass
        
        # NEW: Extract SpecterBroker v1.2 fields
        source_type = broker_token_data.get('source_type')  # AUTHORITY_FILE/PRT_FILE/UNKNOWN
        is_prt_bound = broker_token_data.get('is_prt_bound', False)  # boolean
        display_name = broker_token_data.get('display_name')  # Full user name
        
        # Calculate classification for Refresh Tokens
        classification = None
        if db_token_type == 'refresh_token':
            # Classification logic:
            # 1. PRT_BOUND if is_prt_bound=True
            # 2. FOCI if client_id is FOCI-enabled (from client_ids.py)
            # 3. STANDALONE otherwise
            if is_prt_bound:
                classification = 'PRT_BOUND'
            elif is_foci_app(client_id):
                classification = 'FOCI'
            else:
                classification = 'STANDALONE'
        
        # Metadata
        metadata = {
            'login_url': broker_token_data.get('login_url'),
            'tenant_id': broker_token_data.get('tenant_id'),
            'user_oid': broker_token_data.get('user_oid'),
            'session_key': broker_token_data.get('session_key'),
            'redirect_uri': broker_token_data.get('redirect_uri'),
        }
        metadata = {k: v for k, v in metadata.items() if v}
        
        return Token(
            client_id=client_id,
            upn=upn,
            scope=scope,
            audience=audience,
            access_token=token_value,
            expires_at=expires_at,
            token_type=db_token_type,
            source='broker',
            broker_cache_path=cache_file_path or broker_token_data.get('cache_path'),
            imported_from='BrokerDecrypt',
            metadata_json=json.dumps(metadata) if metadata else None,
            # NEW: SpecterBroker v1.2 fields
            source_type=source_type,
            is_prt_bound=is_prt_bound,
            display_name=display_name,
            classification=classification
        )
