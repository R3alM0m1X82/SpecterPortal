"""
Skype Token Model
Stores Skype tokens obtained from Teams authsvc endpoint
"""
from database import db
from datetime import datetime


class SkypeToken(db.Model):
    __tablename__ = 'skype_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id', ondelete='CASCADE'), nullable=False)
    skype_token = db.Column(db.Text, nullable=False)
    skype_id = db.Column(db.String(255), nullable=False)
    chat_service_url = db.Column(db.String(500), nullable=False)
    issued_at = db.Column(db.Integer, nullable=False)  # Unix timestamp
    expires_at = db.Column(db.Integer, nullable=False)  # Unix timestamp
    settings_raw = db.Column(db.Text, nullable=False)  # Full JSON response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'token_id': self.token_id,
            'skype_token': self.skype_token,
            'skype_id': self.skype_id,
            'chat_service_url': self.chat_service_url,
            'issued_at': self.issued_at,
            'expires_at': self.expires_at,
            'is_expired': datetime.utcnow().timestamp() >= self.expires_at,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
