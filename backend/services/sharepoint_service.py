"""
SharePoint Service for Microsoft Graph API interactions
"""
import requests
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)


class SharePointService:
    """Service for SharePoint operations via Microsoft Graph API"""
    
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to Microsoft Graph API"""
        url = f"{self.GRAPH_BASE_URL}{endpoint}"
        
        try:
            logger.debug(f"SharePoint API Request: {method} {url}")
            
            response = requests.request(
                method,
                url,
                headers=self.headers,
                **kwargs
            )
            
            logger.debug(f"SharePoint API Response: {response.status_code}")
            
            if response.status_code == 204:
                return {'success': True}
            
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('error', {}).get('code', 'Unknown')
                
                logger.error(f"SharePoint API Error: {error_code} - {error_message}")
                
                return {
                    'success': False,
                    'error': error_message,
                    'error_code': error_code,
                    'status_code': response.status_code
                }
            
            return {
                'success': True,
                'data': response.json() if response.text else {}
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SharePoint API Request Exception: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"SharePoint API Unexpected Exception: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def get_all_sites(self, search_query='*'):
        """
        Get all accessible SharePoint sites
        
        Args:
            search_query: Search query to filter sites (default '*' for all)
        
        Returns:
            dict with success status and list of sites
        """
        try:
            # Use search to find all sites
            endpoint = f"/sites?search={search_query}"
            result = self._make_request('GET', endpoint)
            
            if not result['success']:
                logger.error(f"Failed to get sites: {result.get('error', 'Unknown error')}")
                return result
            
            sites = result['data'].get('value', [])
            logger.info(f"Retrieved {len(sites)} SharePoint sites")
            
            # Process and enrich site data
            processed_sites = []
            for site in sites:
                try:
                    processed_site = {
                        'id': site.get('id', ''),
                        'name': site.get('displayName', site.get('name', 'Unnamed Site')),
                        'description': site.get('description', ''),
                        'web_url': site.get('webUrl', ''),
                        'created': site.get('createdDateTime', ''),
                        'last_modified': site.get('lastModifiedDateTime', ''),
                        'site_collection': site.get('siteCollection', {}),
                        'root': site.get('root', {}),
                        # Determine site type from template or URL
                        'site_type': self._determine_site_type(site)
                    }
                    processed_sites.append(processed_site)
                except Exception as e:
                    logger.warning(f"Error processing site {site.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Sort by name
            processed_sites.sort(key=lambda x: x['name'].lower())
            
            return {
                'success': True,
                'sites': processed_sites,
                'count': len(processed_sites)
            }
            
        except Exception as e:
            logger.error(f"Exception in get_all_sites: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to retrieve sites: {str(e)}"
            }
    
    def _determine_site_type(self, site):
        """Determine the type of SharePoint site"""
        web_url = site.get('webUrl', '').lower()
        
        if '/teams/' in web_url:
            return 'Team Site'
        elif '/sites/' in web_url:
            # Could be Communication or Team site
            if site.get('root', {}).get('createdByUser'):
                return 'Communication Site'
            return 'Site'
        elif '/personal/' in web_url:
            return 'OneDrive'
        else:
            return 'Site Collection'
    
    def get_site_details(self, site_id):
        """
        Get detailed information about a specific site
        
        Args:
            site_id: The site ID (can be site-id or hostname,site-path format)
        
        Returns:
            dict with success status and site details
        """
        endpoint = f"/sites/{site_id}"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        site = result['data']
        
        return {
            'success': True,
            'site': {
                'id': site.get('id', ''),
                'name': site.get('displayName', site.get('name', '')),
                'description': site.get('description', ''),
                'web_url': site.get('webUrl', ''),
                'created': site.get('createdDateTime', ''),
                'last_modified': site.get('lastModifiedDateTime', ''),
                'site_collection': site.get('siteCollection', {}),
                'root': site.get('root', {}),
                'site_type': self._determine_site_type(site)
            }
        }
    
    def get_site_drives(self, site_id):
        """
        Get all document libraries (drives) for a site
        
        Args:
            site_id: The site ID
        
        Returns:
            dict with success status and list of drives
        """
        endpoint = f"/sites/{site_id}/drives"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        drives = result['data'].get('value', [])
        
        processed_drives = []
        for drive in drives:
            processed_drive = {
                'id': drive.get('id', ''),
                'name': drive.get('name', ''),
                'description': drive.get('description', ''),
                'drive_type': drive.get('driveType', ''),
                'web_url': drive.get('webUrl', ''),
                'created': drive.get('createdDateTime', ''),
                'last_modified': drive.get('lastModifiedDateTime', ''),
                'quota': {
                    'total': drive.get('quota', {}).get('total', 0),
                    'used': drive.get('quota', {}).get('used', 0),
                    'remaining': drive.get('quota', {}).get('remaining', 0),
                    'state': drive.get('quota', {}).get('state', 'normal')
                },
                'owner': drive.get('owner', {})
            }
            processed_drives.append(processed_drive)
        
        return {
            'success': True,
            'drives': processed_drives,
            'count': len(processed_drives)
        }
    
    def get_site_lists(self, site_id):
        """
        Get all lists for a site
        
        Args:
            site_id: The site ID
        
        Returns:
            dict with success status and list of lists
        """
        endpoint = f"/sites/{site_id}/lists"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        lists = result['data'].get('value', [])
        
        processed_lists = []
        for lst in lists:
            processed_list = {
                'id': lst.get('id', ''),
                'name': lst.get('displayName', lst.get('name', '')),
                'description': lst.get('description', ''),
                'web_url': lst.get('webUrl', ''),
                'created': lst.get('createdDateTime', ''),
                'last_modified': lst.get('lastModifiedDateTime', ''),
                'list_info': {
                    'template': lst.get('list', {}).get('template', ''),
                    'hidden': lst.get('list', {}).get('hidden', False),
                    'content_types_enabled': lst.get('list', {}).get('contentTypesEnabled', False)
                }
            }
            processed_lists.append(processed_list)
        
        # Filter out hidden lists by default
        visible_lists = [l for l in processed_lists if not l['list_info']['hidden']]
        
        return {
            'success': True,
            'lists': visible_lists,
            'count': len(visible_lists),
            'total_count': len(processed_lists)
        }
    
    def get_site_permissions(self, site_id):
        """
        Get permissions for a site
        
        Args:
            site_id: The site ID
        
        Returns:
            dict with success status and list of permissions
        """
        endpoint = f"/sites/{site_id}/permissions"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        permissions = result['data'].get('value', [])
        
        processed_permissions = []
        for perm in permissions:
            processed_perm = {
                'id': perm.get('id', ''),
                'roles': perm.get('roles', []),
                'granted_to': perm.get('grantedTo', {}),
                'granted_to_identities': perm.get('grantedToIdentities', []),
                'invitation': perm.get('invitation', {}),
                'inherited_from': perm.get('inheritedFrom', {})
            }
            processed_permissions.append(processed_perm)
        
        return {
            'success': True,
            'permissions': processed_permissions,
            'count': len(processed_permissions)
        }
    
    def get_drive_items(self, drive_id, folder_id=None):
        """
        Get items in a drive's root or specific folder
        
        Args:
            drive_id: The drive ID
            folder_id: Optional folder ID (None for root)
        
        Returns:
            dict with success status and list of items
        """
        if folder_id:
            endpoint = f"/drives/{drive_id}/items/{folder_id}/children"
        else:
            endpoint = f"/drives/{drive_id}/root/children"
        
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        items = result['data'].get('value', [])
        
        processed_items = []
        for item in items:
            processed_item = {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'size': item.get('size', 0),
                'created': item.get('createdDateTime', ''),
                'last_modified': item.get('lastModifiedDateTime', ''),
                'web_url': item.get('webUrl', ''),
                'is_folder': 'folder' in item,
                'folder_info': item.get('folder', {}),
                'file_info': item.get('file', {}),
                'created_by': item.get('createdBy', {}).get('user', {}),
                'last_modified_by': item.get('lastModifiedBy', {}).get('user', {})
            }
            processed_items.append(processed_item)
        
        # Sort: folders first, then files
        processed_items.sort(key=lambda x: (not x['is_folder'], x['name'].lower()))
        
        return {
            'success': True,
            'items': processed_items,
            'count': len(processed_items)
        }
    
    def get_drive_folder_items(self, drive_id, item_id):
        """
        Get items in a specific folder of a drive
        
        Args:
            drive_id: The drive ID
            item_id: The folder item ID
        
        Returns:
            dict with success status and list of items
        """
        return self.get_drive_items(drive_id, item_id)
    
    def get_item_download_url(self, drive_id, item_id):
        """
        Get download URL for a specific item
        
        Args:
            drive_id: The drive ID
            item_id: The item ID
        
        Returns:
            dict with success status and download URL
        """
        endpoint = f"/drives/{drive_id}/items/{item_id}"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        item = result['data']
        download_url = item.get('@microsoft.graph.downloadUrl', '')
        
        if not download_url:
            return {
                'success': False,
                'error': 'No download URL available for this item'
            }
        
        return {
            'success': True,
            'download_url': download_url,
            'filename': item.get('name', 'download'),
            'size': item.get('size', 0)
        }
    
    def search_sharepoint(self, query):
        """
        Search across all SharePoint sites
        
        Args:
            query: Search query string
        
        Returns:
            dict with success status and search results
        """
        # Use the search API
        endpoint = f"/search/query"
        
        search_request = {
            "requests": [
                {
                    "entityTypes": ["driveItem", "listItem", "site"],
                    "query": {
                        "queryString": query
                    },
                    "from": 0,
                    "size": 100
                }
            ]
        }
        
        result = self._make_request('POST', endpoint, json=search_request)
        
        if not result['success']:
            # Fallback to simpler search if advanced search fails
            return self._simple_search(query)
        
        # Process search results
        hits = []
        for response in result['data'].get('value', []):
            for hit_container in response.get('hitsContainers', []):
                for hit in hit_container.get('hits', []):
                    resource = hit.get('resource', {})
                    hits.append({
                        'id': resource.get('id', ''),
                        'name': resource.get('name', ''),
                        'web_url': resource.get('webUrl', ''),
                        'type': resource.get('@odata.type', '').replace('#microsoft.graph.', ''),
                        'summary': hit.get('summary', ''),
                        'rank': hit.get('rank', 0)
                    })
        
        return {
            'success': True,
            'results': hits,
            'count': len(hits)
        }
    
    def _simple_search(self, query):
        """
        Fallback simple search using drive search
        
        Args:
            query: Search query string
        
        Returns:
            dict with success status and search results
        """
        endpoint = f"/me/drive/root/search(q='{query}')"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        items = result['data'].get('value', [])
        
        results = []
        for item in items:
            results.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'web_url': item.get('webUrl', ''),
                'type': 'driveItem',
                'summary': '',
                'size': item.get('size', 0)
            })
        
        return {
            'success': True,
            'results': results,
            'count': len(results)
        }
    
    def get_recent_sites(self):
        """
        Get recently accessed sites
        Note: Uses user's recent activity
        
        Returns:
            dict with success status and list of recent sites
        """
        # Get followed sites as proxy for recent
        return self.get_followed_sites()
    
    def get_followed_sites(self):
        """
        Get sites followed by the user
        
        Returns:
            dict with success status and list of followed sites
        """
        endpoint = "/me/followedSites"
        result = self._make_request('GET', endpoint)
        
        if not result['success']:
            return result
        
        sites = result['data'].get('value', [])
        
        processed_sites = []
        for site in sites:
            processed_site = {
                'id': site.get('id', ''),
                'name': site.get('displayName', site.get('name', '')),
                'web_url': site.get('webUrl', ''),
                'site_type': self._determine_site_type(site)
            }
            processed_sites.append(processed_site)
        
        return {
            'success': True,
            'sites': processed_sites,
            'count': len(processed_sites)
        }
