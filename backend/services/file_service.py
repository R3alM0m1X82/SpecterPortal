"""
File service - Microsoft Graph API OneDrive operations
"""
import requests
from flask import current_app


class FileService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
    
    def _make_request(self, endpoint, method='GET', **kwargs):
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code in [200, 201, 202, 204]:
                if response.content:
                    try:
                        return {
                            'success': True,
                            'data': response.json(),
                            'raw': response.content
                        }
                    except:
                        return {
                            'success': True,
                            'data': {},
                            'raw': response.content
                        }
                else:
                    return {'success': True, 'data': {}}
            else:
                return {
                    'success': False,
                    'error': f'API returned {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_root_items(self):
        """Get items in root folder"""
        result = self._make_request('me/drive/root/children')
        
        if result['success']:
            items = result['data'].get('value', [])
            return {
                'success': True,
                'items': [self._format_item(item) for item in items]
            }
        
        return result
    
    def get_folder_items(self, item_id):
        """Get items in specific folder"""
        result = self._make_request(f'me/drive/items/{item_id}/children')
        
        if result['success']:
            items = result['data'].get('value', [])
            return {
                'success': True,
                'items': [self._format_item(item) for item in items]
            }
        
        return result
    
    def get_item_metadata(self, item_id):
        """Get item metadata"""
        result = self._make_request(f'me/drive/items/{item_id}')
        
        if result['success']:
            return {
                'success': True,
                'item': self._format_item(result['data'])
            }
        
        return result
    
    def download_file(self, item_id):
        """Get download URL for file"""
        result = self._make_request(f'me/drive/items/{item_id}')
        
        if result['success']:
            download_url = result['data'].get('@microsoft.graph.downloadUrl')
            
            if download_url:
                return {
                    'success': True,
                    'download_url': download_url,
                    'name': result['data'].get('name'),
                    'size': result['data'].get('size', 0)
                }
            else:
                return {
                    'success': False,
                    'error': 'No download URL available'
                }
        
        return result
    
    def upload_file(self, filename, file_content, folder_id=None):
        """Upload file to OneDrive"""
        if folder_id:
            endpoint = f'me/drive/items/{folder_id}:/{filename}:/content'
        else:
            endpoint = f'me/drive/root:/{filename}:/content'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/octet-stream'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.put(
                url,
                headers=headers,
                data=file_content,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'item': self._format_item(response.json()),
                    'message': 'File uploaded successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Upload failed: {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def search_files(self, query):
        """Search files in OneDrive"""
        result = self._make_request(f'me/drive/root/search(q=\'{query}\')')
        
        if result['success']:
            items = result['data'].get('value', [])
            return {
                'success': True,
                'items': [self._format_item(item) for item in items]
            }
        
        return result
    
    def delete_item(self, item_id):
        """Delete file or folder"""
        result = self._make_request(f'me/drive/items/{item_id}', method='DELETE')
        
        if result['success']:
            return {
                'success': True,
                'message': 'Item deleted successfully'
            }
        
        return result
    
    def create_folder(self, folder_name, parent_id=None):
        """Create new folder"""
        if parent_id:
            endpoint = f'me/drive/items/{parent_id}/children'
        else:
            endpoint = 'me/drive/root/children'
        
        folder_data = {
            'name': folder_name,
            'folder': {},
            '@microsoft.graph.conflictBehavior': 'rename'
        }
        
        result = self._make_request(endpoint, method='POST', json=folder_data)
        
        if result['success']:
            return {
                'success': True,
                'item': self._format_item(result['data']),
                'message': 'Folder created successfully'
            }
        
        return result
    
    def _format_item(self, item):
        """Format OneDrive item"""
        is_folder = 'folder' in item
        
        formatted = {
            'id': item.get('id'),
            'name': item.get('name'),
            'size': item.get('size', 0),
            'isFolder': is_folder,
            'createdDateTime': item.get('createdDateTime'),
            'lastModifiedDateTime': item.get('lastModifiedDateTime'),
            'webUrl': item.get('webUrl')
        }
        
        if is_folder:
            formatted['childCount'] = item.get('folder', {}).get('childCount', 0)
        else:
            formatted['mimeType'] = item.get('file', {}).get('mimeType', 'unknown')
        
        return formatted
    
    def rename_item(self, item_id, new_name):
        """Rename file or folder"""
        update_data = {'name': new_name}
        
        result = self._make_request(
            f'me/drive/items/{item_id}',
            method='PATCH',
            json=update_data
        )
        
        if result['success']:
            return {
                'success': True,
                'item': self._format_item(result['data']),
                'message': 'Item renamed successfully'
            }
        
        return result
    
    def bulk_download_zip(self, item_ids):
        """Download multiple files as ZIP"""
        import io
        import zipfile
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for item_id in item_ids:
                try:
                    download_result = self.download_file(item_id)
                    
                    if download_result['success']:
                        download_url = download_result['download_url']
                        file_name = download_result['name']
                        
                        file_response = requests.get(download_url, timeout=self.timeout)
                        
                        if file_response.status_code == 200:
                            zip_file.writestr(file_name, file_response.content)
                        
                except Exception as e:
                    continue
        
        zip_buffer.seek(0)
        
        return {
            'success': True,
            'zip_content': zip_buffer.getvalue(),
            'filename': 'onedrive_files.zip'
        }
