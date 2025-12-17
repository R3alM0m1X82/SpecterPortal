"""
Files API endpoints
"""
from flask import Blueprint, request, jsonify, redirect
from services.token_service import TokenService
from services.file_service import FileService

files_bp = Blueprint('files', __name__, url_prefix='/api/files')


def _get_active_token_or_error():
    #
    # Gets the complete dictionary of the token (with access_token_full)
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    # Validate that the complete token exists
    if not token.get('access_token_full') or token['access_token_full'].endswith('...'):
        return None, (jsonify({
            'success': False,
            'error': 'Active token is truncated or invalid'
        }), 401)

    return token, None


@files_bp.route('', methods=['GET'])
@files_bp.route('/root', methods=['GET'])
def get_root_items():
    """Get items in root folder"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.get_root_items()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/folder/<item_id>', methods=['GET'])
def get_folder_items(item_id):
    """Get items in specific folder"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.get_folder_items(item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/item/<item_id>', methods=['GET'])
def get_item_metadata(item_id):
    """Get item metadata"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.get_item_metadata(item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/download/<item_id>', methods=['GET'])
def download_file(item_id):
    """Get download URL and redirect"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.download_file(item_id)
    
    if result['success']:
        return redirect(result['download_url'])
    else:
        return jsonify(result), 500


@files_bp.route('/download/<item_id>/url', methods=['GET'])
def get_download_url(item_id):
    """Get download URL without redirect"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.download_file(item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload file to OneDrive"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['file']
    folder_id = request.form.get('folder_id')
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Empty filename'
        }), 400
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.upload_file(
        file.filename,
        file.read(),
        folder_id
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@files_bp.route('/search', methods=['GET'])
def search_files():
    """Search files in OneDrive"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Missing query parameter: q'
        }), 400
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.search_files(query)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/item/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete file or folder"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    
    file_service = FileService(token['access_token_full'])
    result = file_service.delete_item(item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/folder', methods=['POST'])
def create_folder():
    """Create new folder"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'error': 'Missing folder name'
        }), 400
    
    folder_name = data.get('name')
    parent_id = data.get('parent_id')
    
    file_service = FileService(token['access_token_full'])
    result = file_service.create_folder(folder_name, parent_id)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@files_bp.route('/item/<item_id>/rename', methods=['PATCH'])
def rename_item(item_id):
    """Rename file or folder"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'error': 'Missing new name'
        }), 400
    
    new_name = data.get('name')
    
    file_service = FileService(token['access_token_full'])
    result = file_service.rename_item(item_id, new_name)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@files_bp.route('/bulk-download', methods=['POST'])
def bulk_download():
    """Download multiple files as ZIP"""
    from flask import send_file
    from io import BytesIO
    
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    data = request.get_json()
    
    if not data or not data.get('item_ids'):
        return jsonify({
            'success': False,
            'error': 'Missing item_ids array'
        }), 400
    
    item_ids = data.get('item_ids')
    
    if not isinstance(item_ids, list) or len(item_ids) == 0:
        return jsonify({
            'success': False,
            'error': 'item_ids must be a non-empty array'
        }), 400
    
    file_service = FileService(token['access_token_full'])
    result = file_service.bulk_download_zip(item_ids)
    
    if result['success']:
        return send_file(
            BytesIO(result['zip_content']),
            mimetype='application/zip',
            as_attachment=True,
            download_name=result['filename']
        )
    else:
        return jsonify(result), 500