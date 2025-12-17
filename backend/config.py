"""
Configuration for SpecterPortal Backend
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

DATA_DIR.mkdir(exist_ok=True)


class Config:
    DATABASE_PATH = DATA_DIR / 'specterportal.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173'
    ]
    
    # CORS supports credentials for session cookies
    CORS_SUPPORTS_CREDENTIALS = True
    
    GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'
    GRAPH_API_TIMEOUT = 30
    
    # Redis Cache Configuration (persistent cache for Graph API)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'True').lower() == 'true'
    
    # Azure Resource Manager API (for SpecterPortal)
    ARM_API_BASE = 'https://management.azure.com'
    ARM_API_VERSION = '2022-12-01'
