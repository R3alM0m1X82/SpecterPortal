"""
Generate new API key for SpecterPortal admin user
Use this script if you lost your API key
"""
from models.user import User
from database import db
from app import create_app

def generate_new_api_key(username='admin'):
    """Generate new API key for specified user"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"[!] User '{username}' not found")
            print("[*] Available users:")
            for u in User.query.all():
                print(f"    - {u.username}")
            return
        
        # Generate new API key
        new_key = User.generate_api_key()
        user.api_key_hash = User.hash_api_key(new_key)
        db.session.commit()
        
        print("=" * 70)
        print("  🔐 NEW API KEY GENERATED")
        print("=" * 70)
        print(f"  Username: {username}")
        print(f"  API Key:  {new_key}")
        print("=" * 70)
        print("  ⚠️  SAVE THIS API KEY - IT WILL NOT BE SHOWN AGAIN!")
        print("=" * 70)


if __name__ == '__main__':
    import sys
    
    username = sys.argv[1] if len(sys.argv) > 1 else 'admin'
    generate_new_api_key(username)
