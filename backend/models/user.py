"""
User model for SpecterPortal authentication
"""
from datetime import datetime
from database import db
import hashlib
import secrets


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    api_key_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @staticmethod
    def hash_api_key(api_key):
        """Hash API key with SHA256"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key():
        """Generate secure random API key"""
        return secrets.token_urlsafe(32)
    
    def verify_api_key(self, api_key):
        """Verify API key against stored hash"""
        return self.api_key_hash == User.hash_api_key(api_key)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def create_default_user():
        """Create default admin user if no users exist"""
        if User.query.count() == 0:
            api_key = User.generate_api_key()
            user = User(
                username='admin',
                api_key_hash=User.hash_api_key(api_key)
            )
            db.session.add(user)
            db.session.commit()
            
            print("=" * 70)
            print("  🔐 DEFAULT ADMIN USER CREATED")
            print("=" * 70)
            print(f"  Username: admin")
            print(f"  API Key:  {api_key}")
            print("=" * 70)
            print("  ⚠️  SAVE THIS API KEY - IT WILL NOT BE SHOWN AGAIN!")
            print("=" * 70)
            
            return user, api_key
        
        return None, None
