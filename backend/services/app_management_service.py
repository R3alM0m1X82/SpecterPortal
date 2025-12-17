"""
App Management Service - Create, Delete, Manage App Registrations
Works with standard user permissions when "Users can register applications" = Yes
"""
import requests
from datetime import datetime, timedelta


class AppManagementService:
    """Service for managing App Registrations via Microsoft Graph API"""
    
    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint, method='GET', json_data=None):
        """Make a request to Microsoft Graph API"""
        url = f"{self.GRAPH_URL}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=json_data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=json_data, timeout=30)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            # DELETE returns 204 No Content on success
            if method == 'DELETE' and response.status_code == 204:
                return {'success': True}
            
            if response.status_code in [200, 201]:
                return {'success': True, 'data': response.json()}
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return {'success': False, 'error': error_msg, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def check_app_registration_allowed(self):
        """
        Check if users can register applications (authorization policy)
        Returns the policy status
        """
        result = self._make_request('policies/authorizationPolicy')
        
        if result['success']:
            policy = result['data']
            default_perms = policy.get('defaultUserRolePermissions', {})
            
            return {
                'success': True,
                'allowedToCreateApps': default_perms.get('allowedToCreateApps', True),
                'allowedToCreateSecurityGroups': default_perms.get('allowedToCreateSecurityGroups', False),
                'allowedToReadOtherUsers': default_perms.get('allowedToReadOtherUsers', True),
                'policy': {
                    'allowedToCreateApps': default_perms.get('allowedToCreateApps', True),
                    'allowedToCreateSecurityGroups': default_perms.get('allowedToCreateSecurityGroups', False),
                    'allowedToReadOtherUsers': default_perms.get('allowedToReadOtherUsers', True)
                }
            }
        
        # If we can't read policy, assume allowed (default Azure AD behavior)
        return {
            'success': True,
            'allowedToCreateApps': True,
            'note': 'Could not read policy, assuming default (allowed)'
        }
    
    def get_my_applications(self):
        """
        Get applications owned by the current user
        Uses /me/ownedObjects filtered to applications
        """
        # Get owned objects and filter to applications
        result = self._make_request('me/ownedObjects/microsoft.graph.application?$top=100')
        
        if result['success']:
            apps = result['data'].get('value', [])
            
            # Enrich with credential info
            enriched_apps = []
            for app in apps:
                app_info = {
                    'id': app.get('id'),
                    'appId': app.get('appId'),
                    'displayName': app.get('displayName'),
                    'signInAudience': app.get('signInAudience'),
                    'createdDateTime': app.get('createdDateTime'),
                    'publisherDomain': app.get('publisherDomain'),
                    'credentials': self._analyze_credentials(app)
                }
                enriched_apps.append(app_info)
            
            return {
                'success': True,
                'applications': enriched_apps,
                'count': len(enriched_apps)
            }
        
        return result
    
    def _analyze_credentials(self, app):
        """Analyze password and key credentials for an application"""
        secrets = app.get('passwordCredentials', [])
        certs = app.get('keyCredentials', [])
        
        secret_count = len(secrets)
        cert_count = len(certs)
        
        # Determine credential type
        if secret_count > 0 and cert_count > 0:
            cred_type = 'both'
        elif secret_count > 0:
            cred_type = 'secret'
        elif cert_count > 0:
            cred_type = 'certificate'
        else:
            cred_type = 'none'
        
        # Find earliest expiry
        all_expiries = []
        for s in secrets:
            if s.get('endDateTime'):
                all_expiries.append(s['endDateTime'])
        for c in certs:
            if c.get('endDateTime'):
                all_expiries.append(c['endDateTime'])
        
        earliest_expiry = min(all_expiries) if all_expiries else None
        
        return {
            'credentialType': cred_type,
            'secretCount': secret_count,
            'certificateCount': cert_count,
            'earliestExpiry': earliest_expiry,
            'secrets': [
                {
                    'keyId': s.get('keyId'),
                    'displayName': s.get('displayName', 'Unnamed'),
                    'startDateTime': s.get('startDateTime'),
                    'endDateTime': s.get('endDateTime')
                }
                for s in secrets
            ]
        }
    
    def create_application(self, display_name, sign_in_audience='AzureADMyOrg', redirect_uris=None, description=None):
        """
        Create a new App Registration
        
        Args:
            display_name: Name of the application
            sign_in_audience: Who can sign in
                - AzureADMyOrg (single tenant - default)
                - AzureADMultipleOrgs (multi-tenant)
                - AzureADandPersonalMicrosoftAccount
                - PersonalMicrosoftAccount
            redirect_uris: List of redirect URIs (optional)
            description: Application description (optional)
        """
        app_data = {
            'displayName': display_name,
            'signInAudience': sign_in_audience
        }
        
        # Add description if provided
        if description:
            app_data['description'] = description
        
        # Add redirect URIs if provided
        if redirect_uris and len(redirect_uris) > 0:
            app_data['web'] = {
                'redirectUris': redirect_uris
            }
        
        result = self._make_request('applications', method='POST', json_data=app_data)
        
        if result['success']:
            app = result['data']
            return {
                'success': True,
                'message': f'Application "{display_name}" created successfully',
                'application': {
                    'id': app.get('id'),  # Object ID (needed for secret/delete operations)
                    'appId': app.get('appId'),  # Application (client) ID
                    'displayName': app.get('displayName'),
                    'signInAudience': app.get('signInAudience'),
                    'createdDateTime': app.get('createdDateTime'),
                    'publisherDomain': app.get('publisherDomain')
                }
            }
        
        return result
    
    def delete_application(self, app_object_id):
        """
        Delete an App Registration
        
        Args:
            app_object_id: The Object ID of the application (not appId!)
        
        Note: User must be owner of the application to delete it
        """
        result = self._make_request(f'applications/{app_object_id}', method='DELETE')
        
        if result['success']:
            return {
                'success': True,
                'message': 'Application deleted successfully'
            }
        
        return result
    
    def add_client_secret(self, app_object_id, description='SpecterPortal Secret', expiry_months=12):
        """
        Add a client secret to an application
        
        Args:
            app_object_id: The Object ID of the application (not appId!)
            description: Description for the secret
            expiry_months: Months until expiration (1, 6, 12, or 24)
        
        Returns:
            The secret value (only available at creation time!)
        """
        # Calculate expiry date
        expiry_date = datetime.utcnow() + timedelta(days=expiry_months * 30)
        
        secret_data = {
            'passwordCredential': {
                'displayName': description,
                'endDateTime': expiry_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        }
        
        result = self._make_request(
            f'applications/{app_object_id}/addPassword',
            method='POST',
            json_data=secret_data
        )
        
        if result['success']:
            cred = result['data']
            return {
                'success': True,
                'message': 'Client secret created successfully',
                'credential': {
                    'keyId': cred.get('keyId'),
                    'displayName': cred.get('displayName'),
                    'secretText': cred.get('secretText'),  # Only available NOW!
                    'startDateTime': cred.get('startDateTime'),
                    'endDateTime': cred.get('endDateTime')
                },
                'warning': 'Save this secret now! It will not be shown again.'
            }
        
        return result
    
    def remove_client_secret(self, app_object_id, key_id):
        """
        Remove a client secret from an application
        
        Args:
            app_object_id: The Object ID of the application
            key_id: The keyId of the secret to remove
        """
        result = self._make_request(
            f'applications/{app_object_id}/removePassword',
            method='POST',
            json_data={'keyId': key_id}
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Client secret removed successfully'
            }
        
        return result
    
    def get_application_details(self, app_object_id):
        """
        Get full details of an application including credentials metadata
        
        Args:
            app_object_id: The Object ID of the application
        """
        result = self._make_request(f'applications/{app_object_id}')
        
        if result['success']:
            app = result['data']
            return {
                'success': True,
                'application': {
                    'id': app.get('id'),
                    'appId': app.get('appId'),
                    'displayName': app.get('displayName'),
                    'description': app.get('description'),
                    'signInAudience': app.get('signInAudience'),
                    'createdDateTime': app.get('createdDateTime'),
                    'publisherDomain': app.get('publisherDomain'),
                    'credentials': self._analyze_credentials(app)
                }
            }
        
        return result
