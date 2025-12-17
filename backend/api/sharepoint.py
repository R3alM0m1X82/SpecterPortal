"""
SharePoint API endpoints
"""
from flask import Blueprint, request, jsonify
from services.token_service import TokenService
from services.sharepoint_service import SharePointService
import logging

# Setup logging
logger = logging.getLogger(__name__)

sharepoint_bp = Blueprint('sharepoint', __name__, url_prefix='/api/sharepoint')


def _get_active_token_or_error():
    """Get active token or return error response"""
    token = TokenService.get_active_token()
    
    if not token:
        return None, (jsonify({
            'success': False,
            'error': 'No active token'
        }), 401)
        
    if not token.get('access_token_full') or token['access_token_full'].endswith('...'):
        return None, (jsonify({
            'success': False,
            'error': 'Active token is truncated or invalid'
        }), 401)

    return token, None


@sharepoint_bp.route('/sites', methods=['GET'])
def get_all_sites():
    """Get all accessible SharePoint sites"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    search_query = request.args.get('search', '*')
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_all_sites(search_query)
    
    if result['success']:
        return jsonify(result)
    else:
        # Log the error for debugging
        logger.error(f"SharePoint sites error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/sites/<path:site_id>', methods=['GET'])
def get_site_details(site_id):
    """Get details of a specific SharePoint site"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_site_details(site_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint site details error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/sites/<path:site_id>/drives', methods=['GET'])
def get_site_drives(site_id):
    """Get document libraries (drives) for a site"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_site_drives(site_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint drives error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/sites/<path:site_id>/lists', methods=['GET'])
def get_site_lists(site_id):
    """Get lists for a site"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_site_lists(site_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint lists error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/sites/<path:site_id>/permissions', methods=['GET'])
def get_site_permissions(site_id):
    """Get permissions for a site"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_site_permissions(site_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint permissions error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/drives/<drive_id>/root', methods=['GET'])
def get_drive_root(drive_id):
    """Get root items of a specific drive"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_drive_items(drive_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint drive root error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/drives/<drive_id>/items/<item_id>/children', methods=['GET'])
def get_drive_folder_items(drive_id, item_id):
    """Get items in a specific folder of a drive"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_drive_folder_items(drive_id, item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint folder items error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/drives/<drive_id>/items/<item_id>/content', methods=['GET'])
def get_item_download_url(drive_id, item_id):
    """Get download URL for an item"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_item_download_url(drive_id, item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint download URL error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/search', methods=['GET'])
def search_sharepoint():
    """Search across all SharePoint sites"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Missing query parameter: q'
        }), 400
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.search_sharepoint(query)
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint search error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/recent', methods=['GET'])
def get_recent_sites():
    """Get recently accessed sites"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_recent_sites()
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint recent sites error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500


@sharepoint_bp.route('/followed', methods=['GET'])
def get_followed_sites():
    """Get sites followed by the user"""
    token, error = _get_active_token_or_error()
    if error:
        return error
    
    sharepoint_service = SharePointService(token['access_token_full'])
    result = sharepoint_service.get_followed_sites()
    
    if result['success']:
        return jsonify(result)
    else:
        logger.error(f"SharePoint followed sites error: {result.get('error', 'Unknown error')}")
        print(f"[SharePoint Error] {result.get('error', 'Unknown error')}")
        return jsonify(result), 500
