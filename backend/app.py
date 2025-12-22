"""
SpecterPortal Flask Application
Azure & Entra ID Token Management & Enumeration Platform
WITH AUTHENTICATION SYSTEM
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import init_db, db
from api import tokens_bp, graph_bp
from api.emails import emails_bp
from api.teams import teams_bp
from api.teams_skype import teams_skype_bp
from api.sharepoint import sharepoint_bp
from api.cap import cap_bp
from api.roles import roles_bp
from api.files import files_bp
from api.tenant import tenant_bp
from api.refresh import refresh_bp
from api.auth import auth_bp
from api.arm import arm_bp
from api.scheduler import scheduler_bp
from api.database_mgmt import database_mgmt_bp
from api.app_management import app_mgmt_bp
from api.permissions import permissions_bp
from api.admin_actions import admin_bp
from api.azure_perms import azure_perms_bp
from api.key_vaults import key_vaults_bp
from api.external_users import external_users_bp
from api.oauth_consent import oauth_consent_bp
from api.azure_vms import azure_vms_bp
from api.search import search_bp
from api.advanced_queries import advanced_queries_bp
from api.utils import utils_bp
from services.token_service import TokenService
from api.iam import iam_bp



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # CORS with credentials support for sessions
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True  # Enable session cookies
        }
    })
    
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)  # Auth MUST be first (no protection)
    app.register_blueprint(tokens_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(teams_skype_bp)
    app.register_blueprint(sharepoint_bp)
    app.register_blueprint(cap_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(arm_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(refresh_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(database_mgmt_bp)
    app.register_blueprint(app_mgmt_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(key_vaults_bp, url_prefix='/api/azure/keyvaults')
    app.register_blueprint(azure_perms_bp)
    app.register_blueprint(external_users_bp)
    app.register_blueprint(oauth_consent_bp)
    app.register_blueprint(azure_vms_bp, url_prefix='/api/azure')
    app.register_blueprint(search_bp)
    app.register_blueprint(advanced_queries_bp)
    app.register_blueprint(utils_bp)
    app.register_blueprint(iam_bp)

    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint - for backend, database e API"""
        health_status = {
            'backend': True,
            'database': False,
            'api': False
        }
        
        # Test database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            health_status['database'] = True
        except Exception as e:
            print(f"[!] Database health check failed: {e}")
            health_status['database'] = False
        
        # API It is ready if the database is connected
        health_status['api'] = health_status['database']
        
        return jsonify({
            'success': True,
            'status': 'healthy' if all(health_status.values()) else 'degraded',
            'message': 'SpecterPortal backend is running',
            'version': '2.0',
            **health_status
        })
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        stats = TokenService.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    return app


def main():
    app = create_app()
    
    # Print banner only once (avoid duplicate in debug mode)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Banner ASCII
        banner = """
\033[38;5;93m  ██████╗██████╗ ███████╗ ██████╗████████╗███████╗██████╗ 
  ██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗
  ███████╗██████╔╝█████╗  ██║        ██║   █████╗  ██████╔╝
  ╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══╝  ██╔══██╗
  ███████║██║     ███████╗╚██████╗   ██║   ███████╗██║  ██║
  ╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
\033[0m                                                            
\033[97m  ██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗            
  ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║            
  ██████╔╝██║   ██║██████╔╝   ██║   ███████║██║            
  ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║            
  ██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗       
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝       
\033[0m
\033[96m                        v.2.0\033[0m
                                                            
\033[96m  ═══════════════════════════════════════════════════════════
        Post-Exploitation Framework for Azure/EntraID
                by r3alm0m1x82 | safebreach.it
  ═══════════════════════════════════════════════════════════\033[0m
"""
        print(banner)
        
        print("=" * 70)
        print(f"  Database: {app.config['DATABASE_PATH']}")
        print(f"  Server:   http://127.0.0.1:5000")
        print(f"  CORS:     {', '.join(app.config['CORS_ORIGINS'])}")
        print("=" * 70)
        print("\n[*] Server starting...\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )


if __name__ == '__main__':
    main()
