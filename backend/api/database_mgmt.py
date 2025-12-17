"""
SpecterPortal - Database Management API
Endpoints for database operations: create, reset, backup, switch
"""
from flask import Blueprint, jsonify, request, send_file
from database import db
from config import Config, DATA_DIR
from pathlib import Path
import shutil
import os
from datetime import datetime

database_mgmt_bp = Blueprint('database_mgmt', __name__, url_prefix='/api/database')


def get_db_info(db_path: Path) -> dict:
    """Get information about a database file"""
    if not db_path.exists():
        return {
            'exists': False,
            'path': str(db_path),
            'name': db_path.name,
            'size': 0,
            'size_human': '0 B',
            'modified': None
        }
    
    stats = db_path.stat()
    size = stats.st_size
    
    # Human readable size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            size_human = f"{size:.1f} {unit}"
            break
        size /= 1024
    else:
        size_human = f"{size:.1f} TB"
    
    return {
        'exists': True,
        'path': str(db_path),
        'name': db_path.name,
        'size': stats.st_size,
        'size_human': size_human,
        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
    }


def get_table_counts() -> dict:
    """Get row counts for all tables in current database"""
    counts = {}
    try:
        # Get all table names
        result = db.session.execute(db.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ))
        tables = [row[0] for row in result]
        
        for table in tables:
            try:
                count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = count_result.scalar()
            except Exception:
                counts[table] = -1  # Error getting count
                
    except Exception as e:
        print(f"[!] Error getting table counts: {e}")
    
    return counts


@database_mgmt_bp.route('/info', methods=['GET'])
def get_database_info():
    """Get current database information"""
    try:
        db_path = Config.DATABASE_PATH
        info = get_db_info(db_path)
        
        # Add table counts if database exists
        if info['exists']:
            info['tables'] = get_table_counts()
            info['total_records'] = sum(c for c in info['tables'].values() if c > 0)
        
        return jsonify({
            'success': True,
            'database': info,
            'data_directory': str(DATA_DIR)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/list', methods=['GET'])
def list_databases():
    """List all database files in data directory"""
    try:
        data_dir = DATA_DIR
        databases = []
        
        # Find all .db files
        for db_file in data_dir.glob('*.db'):
            info = get_db_info(db_file)
            info['is_active'] = (db_file == Config.DATABASE_PATH)
            databases.append(info)
        
        # Sort by modified date, newest first
        databases.sort(key=lambda x: x.get('modified') or '', reverse=True)
        
        return jsonify({
            'success': True,
            'databases': databases,
            'active_database': str(Config.DATABASE_PATH),
            'data_directory': str(data_dir)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/reset', methods=['POST'])
def reset_database():
    """Reset current database - drop all tables and recreate"""
    try:
        # Get confirmation from request
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Confirmation required. Send {"confirm": true} to proceed.'
            }), 400
        
        # Drop all tables
        db.drop_all()
        
        # Recreate all tables
        db.create_all()
        
        # Get new info
        info = get_db_info(Config.DATABASE_PATH)
        info['tables'] = get_table_counts()
        
        return jsonify({
            'success': True,
            'message': 'Database reset successfully. All tables recreated.',
            'database': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/backup', methods=['POST'])
def backup_database():
    """Create a backup of current database"""
    try:
        db_path = Config.DATABASE_PATH
        
        if not db_path.exists():
            return jsonify({
                'success': False,
                'error': 'No database file to backup'
            }), 404
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"specterportal_backup_{timestamp}.db"
        backup_path = DATA_DIR / backup_name
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        return jsonify({
            'success': True,
            'message': f'Backup created: {backup_name}',
            'backup': get_db_info(backup_path)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/create', methods=['POST'])
def create_new_database():
    """Create a new empty database with a custom name"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        
        if not name:
            # Generate default name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"specterportal_{timestamp}"
        
        # Sanitize name
        name = ''.join(c for c in name if c.isalnum() or c in '_-')
        
        if not name.endswith('.db'):
            name += '.db'
        
        new_db_path = DATA_DIR / name
        
        if new_db_path.exists():
            return jsonify({
                'success': False,
                'error': f'Database {name} already exists'
            }), 400
        
        # Create empty database by touching the file
        # SQLite will create it when first accessed
        new_db_path.touch()
        
        return jsonify({
            'success': True,
            'message': f'Database created: {name}',
            'database': get_db_info(new_db_path),
            'note': 'Use /api/database/switch to activate this database'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/delete', methods=['POST'])
def delete_database():
    """Delete a database file (not the active one)"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        confirm = data.get('confirm', False)
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Database name required'
            }), 400
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Confirmation required. Send {"confirm": true} to proceed.'
            }), 400
        
        db_path = DATA_DIR / name
        
        if not db_path.exists():
            return jsonify({
                'success': False,
                'error': f'Database {name} not found'
            }), 404
        
        # Prevent deleting active database
        if db_path == Config.DATABASE_PATH:
            return jsonify({
                'success': False,
                'error': 'Cannot delete active database. Switch to another database first.'
            }), 400
        
        # Delete the file
        db_path.unlink()
        
        return jsonify({
            'success': True,
            'message': f'Database {name} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/download', methods=['GET'])
def download_database():
    """Download current database file"""
    try:
        db_path = Config.DATABASE_PATH
        
        if not db_path.exists():
            return jsonify({
                'success': False,
                'error': 'No database file to download'
            }), 404
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"specterportal_export_{datetime.now().strftime('%Y%m%d')}.db"
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@database_mgmt_bp.route('/vacuum', methods=['POST'])
def vacuum_database():
    """Optimize database by running VACUUM"""
    try:
        # Get size before
        size_before = Config.DATABASE_PATH.stat().st_size if Config.DATABASE_PATH.exists() else 0
        
        # Run VACUUM
        db.session.execute(db.text('VACUUM'))
        db.session.commit()
        
        # Get size after
        size_after = Config.DATABASE_PATH.stat().st_size if Config.DATABASE_PATH.exists() else 0
        
        saved = size_before - size_after
        
        return jsonify({
            'success': True,
            'message': 'Database optimized',
            'size_before': size_before,
            'size_after': size_after,
            'space_saved': saved,
            'space_saved_human': f"{saved / 1024:.1f} KB" if saved > 0 else "0 B"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
