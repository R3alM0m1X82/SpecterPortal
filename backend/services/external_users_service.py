"""
External Users Service - Guest/External user enumeration
Identifies guest users and maps their access for red team assessment
"""
import requests
import time
from datetime import datetime, timedelta
from flask import current_app


class ExternalUsersService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
    
    def _make_request(self, endpoint, method='GET', params=None):
        """Make request to Graph API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'ConsistencyLevel': 'eventual'  # Required for advanced queries
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"[429 Rate Limit] Waiting {retry_after}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'data': response.json()
                    }
                else:
                    error_detail = response.text
                    error_code = None
                    try:
                        error_json = response.json()
                        if 'error' in error_json:
                            error_detail = error_json['error'].get('message', response.text)
                            error_code = error_json['error'].get('code', None)
                    except:
                        pass
                    
                    return {
                        'success': False,
                        'error': f'API returned {response.status_code}',
                        'details': error_detail,
                        'error_code': error_code
                    }
                    
            except requests.exceptions.Timeout:
                return {'success': False, 'error': 'Request timeout'}
            except requests.exceptions.RequestException as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Rate limit exceeded - Max retries reached'}
    
    def _paginate_request(self, endpoint, params=None):
        """Make paginated request to Graph API"""
        all_items = []
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'ConsistencyLevel': 'eventual'
        }
        
        while url:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    time.sleep(retry_after)
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    all_items.extend(data.get('value', []))
                    url = data.get('@odata.nextLink')
                    params = None  # nextLink already has params
                else:
                    break
                    
            except Exception as e:
                print(f"[Pagination Error] {e}")
                break
        
        return all_items
    
    def get_external_users(self, include_details=False):
        """
        Get all guest/external users in the tenant
        
        Args:
            include_details: If True, fetch additional details (memberships, sign-in activity)
        """
        # Base select fields
        select_fields = [
            'id', 'displayName', 'userPrincipalName', 'mail', 'otherMails',
            'createdDateTime', 'userType', 'accountEnabled', 'externalUserState',
            'externalUserStateChangeDateTime', 'creationType', 'identities'
        ]
        
        # signInActivity requires AuditLog.Read.All or Directory.Read.All
        # We'll try with it, fallback without if permission denied
        select_with_signin = select_fields + ['signInActivity']
        
        params = {
            '$filter': "userType eq 'Guest'",
            '$select': ','.join(select_with_signin),
            '$top': 100,
            '$count': 'true'
        }
        
        # Try with signInActivity first
        guests = self._paginate_request('users', params)
        
        # If no results, try without signInActivity (permission issue)
        if not guests:
            params['$select'] = ','.join(select_fields)
            guests = self._paginate_request('users', params)
        
        # Format results
        formatted_guests = []
        for guest in guests:
            formatted = self._format_guest(guest)
            formatted_guests.append(formatted)
        
        # If include_details, fetch memberships for each guest
        if include_details and formatted_guests:
            for guest in formatted_guests:
                memberships = self.get_user_memberships(guest['id'])
                if memberships['success']:
                    guest['memberships'] = memberships['memberships']
                    guest['groupCount'] = len([m for m in memberships['memberships'] if m['type'] == 'group'])
                else:
                    guest['memberships'] = []
                    guest['groupCount'] = 0
        
        # Calculate statistics
        stats = self._calculate_stats(formatted_guests)
        
        return {
            'success': True,
            'guests': formatted_guests,
            'count': len(formatted_guests),
            'stats': stats
        }
    
    def get_user_memberships(self, user_id):
        """Get group memberships for a user"""
        result = self._make_request(
            f'users/{user_id}/memberOf',
            params={'$select': 'id,displayName,description,groupTypes,securityEnabled,mail'}
        )
        
        if result['success']:
            memberships = []
            for item in result['data'].get('value', []):
                odata_type = item.get('@odata.type', '')
                
                membership = {
                    'id': item.get('id'),
                    'displayName': item.get('displayName'),
                    'description': item.get('description'),
                    'type': 'group' if 'group' in odata_type.lower() else 'role' if 'role' in odata_type.lower() else 'other'
                }
                
                if membership['type'] == 'group':
                    membership['securityEnabled'] = item.get('securityEnabled', False)
                    membership['groupTypes'] = item.get('groupTypes', [])
                    membership['mail'] = item.get('mail')
                
                memberships.append(membership)
            
            return {
                'success': True,
                'memberships': memberships
            }
        
        return result
    
    def get_guest_details(self, user_id):
        """Get detailed information for a specific guest user"""
        # Get basic info with signInActivity
        select = 'id,displayName,userPrincipalName,mail,otherMails,createdDateTime,userType,accountEnabled,externalUserState,externalUserStateChangeDateTime,creationType,identities,signInActivity,jobTitle,department,companyName'
        
        result = self._make_request(f'users/{user_id}', params={'$select': select})
        
        if not result['success']:
            # Retry without signInActivity
            select_fallback = 'id,displayName,userPrincipalName,mail,otherMails,createdDateTime,userType,accountEnabled,externalUserState,externalUserStateChangeDateTime,creationType,identities,jobTitle,department,companyName'
            result = self._make_request(f'users/{user_id}', params={'$select': select_fallback})
        
        if result['success']:
            guest = self._format_guest(result['data'])
            
            # Get memberships
            memberships = self.get_user_memberships(user_id)
            if memberships['success']:
                guest['memberships'] = memberships['memberships']
                guest['groupCount'] = len([m for m in memberships['memberships'] if m['type'] == 'group'])
            
            # Try to get invited by info (createdBy)
            created_by = self._get_invited_by(user_id)
            if created_by:
                guest['invitedBy'] = created_by
            
            return {
                'success': True,
                'guest': guest
            }
        
        return result
    
    def _get_invited_by(self, user_id):
        """Try to get who invited this guest user"""
        # This requires Directory.Read.All and may not always be available
        try:
            # Check audit logs for invitation
            result = self._make_request(
                'auditLogs/directoryAudits',
                params={
                    '$filter': f"targetResources/any(t: t/id eq '{user_id}') and activityDisplayName eq 'Invite external user'",
                    '$top': 1,
                    '$select': 'initiatedBy,activityDateTime'
                }
            )
            
            if result['success'] and result['data'].get('value'):
                audit = result['data']['value'][0]
                initiated_by = audit.get('initiatedBy', {})
                user_info = initiated_by.get('user', {})
                
                if user_info:
                    return {
                        'displayName': user_info.get('displayName'),
                        'userPrincipalName': user_info.get('userPrincipalName'),
                        'id': user_info.get('id'),
                        'invitedOn': audit.get('activityDateTime')
                    }
        except Exception as e:
            print(f"[InvitedBy Error] {e}")
        
        return None
    
    def get_inactive_guests(self, days=90):
        """Get guests who haven't signed in for X days"""
        result = self.get_external_users(include_details=False)
        
        if not result['success']:
            return result
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        inactive_guests = []
        
        for guest in result['guests']:
            last_signin = guest.get('lastSignIn')
            
            if last_signin:
                try:
                    signin_date = datetime.fromisoformat(last_signin.replace('Z', '+00:00'))
                    if signin_date.replace(tzinfo=None) < cutoff_date:
                        guest['daysSinceLastSignIn'] = (datetime.utcnow() - signin_date.replace(tzinfo=None)).days
                        inactive_guests.append(guest)
                except:
                    # Can't parse date, consider as potentially inactive
                    guest['daysSinceLastSignIn'] = None
                    inactive_guests.append(guest)
            else:
                # No sign-in recorded, could be never signed in
                guest['daysSinceLastSignIn'] = None
                guest['neverSignedIn'] = True
                inactive_guests.append(guest)
        
        return {
            'success': True,
            'guests': inactive_guests,
            'count': len(inactive_guests),
            'threshold_days': days
        }
    
    def _format_guest(self, guest):
        """Format guest user data"""
        # Extract source tenant from identities or UPN
        source_tenant = None
        identities = guest.get('identities', [])
        
        for identity in identities:
            issuer = identity.get('issuer', '')
            if issuer and issuer != 'ExternalAzureAD':
                source_tenant = issuer
                break
        
        # Try to extract from UPN if not found
        if not source_tenant:
            upn = guest.get('userPrincipalName', '')
            if '#EXT#' in upn:
                # Format: user_domain.com#EXT#@tenant.onmicrosoft.com
                parts = upn.split('#EXT#')
                if parts:
                    original_email = parts[0].replace('_', '@', 1)
                    if '@' in original_email:
                        source_tenant = original_email.split('@')[1]
        
        # Parse sign-in activity
        sign_in_activity = guest.get('signInActivity', {})
        last_signin = sign_in_activity.get('lastSignInDateTime') if sign_in_activity else None
        last_non_interactive = sign_in_activity.get('lastNonInteractiveSignInDateTime') if sign_in_activity else None
        
        # Calculate days since creation
        created_dt = guest.get('createdDateTime')
        days_since_creation = None
        if created_dt:
            try:
                created = datetime.fromisoformat(created_dt.replace('Z', '+00:00'))
                days_since_creation = (datetime.utcnow() - created.replace(tzinfo=None)).days
            except:
                pass
        
        return {
            'id': guest.get('id'),
            'displayName': guest.get('displayName'),
            'userPrincipalName': guest.get('userPrincipalName'),
            'mail': guest.get('mail'),
            'otherMails': guest.get('otherMails', []),
            'createdDateTime': created_dt,
            'daysSinceCreation': days_since_creation,
            'accountEnabled': guest.get('accountEnabled', True),
            'externalUserState': guest.get('externalUserState'),  # PendingAcceptance, Accepted
            'externalUserStateChangeDateTime': guest.get('externalUserStateChangeDateTime'),
            'creationType': guest.get('creationType'),  # Invitation, etc.
            'sourceTenant': source_tenant,
            'lastSignIn': last_signin,
            'lastNonInteractiveSignIn': last_non_interactive,
            'jobTitle': guest.get('jobTitle'),
            'department': guest.get('department'),
            'companyName': guest.get('companyName'),
            'identities': identities
        }
    
    def _calculate_stats(self, guests):
        """Calculate statistics for guest users"""
        total = len(guests)
        
        if total == 0:
            return {
                'total': 0,
                'pending': 0,
                'accepted': 0,
                'disabled': 0,
                'neverSignedIn': 0,
                'recentlyCreated': 0,
                'sourceTenants': []
            }
        
        pending = sum(1 for g in guests if g.get('externalUserState') == 'PendingAcceptance')
        accepted = sum(1 for g in guests if g.get('externalUserState') == 'Accepted')
        disabled = sum(1 for g in guests if not g.get('accountEnabled', True))
        never_signed_in = sum(1 for g in guests if not g.get('lastSignIn'))
        
        # Recently created (last 30 days)
        recently_created = sum(1 for g in guests if g.get('daysSinceCreation') is not None and g['daysSinceCreation'] <= 30)
        
        # Source tenants breakdown
        source_tenants = {}
        for g in guests:
            tenant = g.get('sourceTenant') or 'Unknown'
            source_tenants[tenant] = source_tenants.get(tenant, 0) + 1
        
        # Sort by count
        sorted_tenants = sorted(source_tenants.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total': total,
            'pending': pending,
            'accepted': accepted,
            'disabled': disabled,
            'neverSignedIn': never_signed_in,
            'recentlyCreated': recently_created,
            'sourceTenants': [{'tenant': t[0], 'count': t[1]} for t in sorted_tenants[:10]]
        }
    
    def export_guests(self, format='json'):
        """Export guest users data"""
        result = self.get_external_users(include_details=True)
        
        if not result['success']:
            return result
        
        if format == 'csv':
            return self._export_csv(result['guests'])
        else:
            return {
                'success': True,
                'data': result['guests'],
                'format': 'json'
            }
    
    def _export_csv(self, guests):
        """Convert guests to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        fieldnames = [
            'id', 'displayName', 'userPrincipalName', 'mail', 'createdDateTime',
            'accountEnabled', 'externalUserState', 'sourceTenant', 'lastSignIn',
            'daysSinceCreation', 'groupCount', 'companyName', 'jobTitle'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for guest in guests:
            row = {k: guest.get(k, '') for k in fieldnames}
            writer.writerow(row)
        
        return {
            'success': True,
            'data': output.getvalue(),
            'format': 'csv'
        }
