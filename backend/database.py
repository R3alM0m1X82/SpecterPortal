"""
SpecterPortal - Database initialization and setup
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        import models.token
        import models.extraction
        import models.user  # Import User model
        
        db.create_all()
        
        # Create default admin user if none exists
        from models.user import User
        User.create_default_user()
        
        print(f"[+] SpecterPortal database initialized: {app.config['DATABASE_PATH']}")
