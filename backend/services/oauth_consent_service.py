"""
OAuth Consent Service - Application Consent Auditor
Added Owner analysis for consent apps
Identifies OAuth apps with consent and risky permissions.
Calculates risk scores based on permission combinations.
"""
import requests
from datetime import datetime, timedelta
from services.cache_service import graph_cache


class OAuthConsentService:
    """Service for auditing OAuth application consents and permissions"""
    
    # High-risk permission patterns
    HIGH_RISK_PERMISSIONS = [
        'Mail.ReadWrite',
        'Mail.ReadWrite.All',
        'Mail.Send',
        'Mail.Send.All',
        'Files.ReadWrite.All',
        'Sites.ReadWrite.All',
        'Directory.ReadWrite.All',
        'RoleManagement.ReadWrite.Directory',
        'Application.ReadWrite.All',
        'AppRoleAssignment.ReadWrite.All',
        'User.ReadWrite.All',
        'Group.ReadWrite.All',
        'full_access_as_app',
    ]
    
    # Critical permission combinations (high risk when together)
    CRITICAL_COMBINATIONS = [
        ('Mail.ReadWrite', 'Files.ReadWrite.All'),
        ('Mail.Send', 'User.Read.All'),
        ('Directory.ReadWrite.All', 'Application.ReadWrite.All'),
        ('Mail.ReadWrite.All', 'Mail.Send.All'),
    ]
    
    # Known Microsoft publisher domains
    MICROSOFT_PUBLISHERS = [
        'microsoft.com',
        'microsoft.onmicrosoft.com',
        'azure.com',
        'office.com',
        'windows.net',
    ]
    
    def __init__(self, access_token, token_id=None):
        self.access_token = access_token
        self.token_id = token_id
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self.graph_url = 'https://graph.microsoft.com/v1.0'
    
    def _make_request(self, url, params=None):
        """Make Graph API request with error handling"""
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                return {'error': 'Insufficient permissions', 'status': 403}
            elif response.status_code == 429:
                return {'error': 'Rate limited', 'status': 429}
            else:
                return {'error': f'API error: {response.status_code}', 'status': response.status_code}
        except Exception as e:
            return {'error': str(e)}
    
    def _paginate_request(self, url, params=None, max_items=500):
        """Handle pagination for Graph API requests"""
        all_items = []
        
        while url and len(all_items) < max_items:
            data = self._make_request(url, params)
            
            if 'error' in data:
                return data
            
            all_items.extend(data.get('value', []))
            url = data.get('@odata.nextLink')
            params = None  # nextLink includes params
        
        return {'value': all_items}
    
    # ==================== OWNER ANALYSIS ====================
    
    def _get_owners(self, sp_id):
        """
        Get owners for a specific service principal
        
        Args:
            sp_id: Service Principal object ID
        
        Returns:
            List of owner objects with displayName and userPrincipalName
        """
        url = f'{self.graph_url}/servicePrincipals/{sp_id}/owners'
        result = self._make_request(url)
        
        if 'error' not in result:
            owners = result.get('value', [])
            return [
                {
                    'id': o.get('id'),
                    'displayName': o.get('displayName'),
                    'userPrincipalName': o.get('userPrincipalName'),
                    'mail': o.get('mail')
                }
                for o in owners
            ]
        
        return []
    
    def _get_owners_batch(self, service_principals, max_batch=30):
        """
        Get owners for multiple service principals in batch with caching
        
        Args:
            service_principals: List of SP dicts with 'id' field
            max_batch: Maximum number of SPs to fetch owners for (default 30)
        
        Returns:
            Dict mapping sp_id -> list of owners
        """
        owners_map = {}
        
        # Only fetch for first N entities to avoid rate limiting
        batch_sps = service_principals[:max_batch]
        
        for sp in batch_sps:
            sp_id = sp.get('id')
            if not sp_id:
                continue
            
            # Check cache first (20 min TTL)
            if self.token_id:
                cache_key = f'sp_owners_{sp_id}'
                cached_owners = graph_cache.get(self.token_id, cache_key)
                
                if cached_owners is not None:
                    owners_map[sp_id] = cached_owners
                    continue
            
            # Fetch owners
            owners = self._get_owners(sp_id)
            owners_map[sp_id] = owners
            
            # Cache result (20 min = 1200 seconds)
            if self.token_id:
                graph_cache.set(self.token_id, cache_key, owners, ttl_seconds=1200)
        
        return owners_map
    
    def _format_owner_display(self, owners):
        """
        Format owner(s) for display
        
        Args:
            owners: List of owner dicts
        
        Returns:
            String representation: "John Doe", "John Doe +1", or None
        """
        if not owners or len(owners) == 0:
            return None
        
        if len(owners) == 1:
            return owners[0].get('displayName', owners[0].get('userPrincipalName', 'Unknown'))
        
        # Multiple owners: show first + count
        first_owner = owners[0].get('displayName', owners[0].get('userPrincipalName', 'Unknown'))
        return f"{first_owner} +{len(owners) - 1}"
    
    # ==================== CONSENT AUDITING ====================
    
    def get_oauth_permission_grants(self):
        """
        Get all OAuth2 permission grants (delegated permissions)
        These represent user/admin consent to applications
        """
        url = f'{self.graph_url}/oauth2PermissionGrants'
        params = {
            '$top': 100
        }
        
        return self._paginate_request(url, params)
    
    def get_service_principals(self):
        """Get all service principals with app role assignments"""
        url = f'{self.graph_url}/servicePrincipals'
        params = {
            '$select': 'id,appId,displayName,appDisplayName,servicePrincipalType,accountEnabled,publisherName,verifiedPublisher,appOwnerOrganizationId,createdDateTime,tags',
            '$top': 100
        }
        
        return self._paginate_request(url, params)
    
    def get_app_role_assignments(self, sp_id):
        """Get application role assignments for a service principal"""
        url = f'{self.graph_url}/servicePrincipals/{sp_id}/appRoleAssignments'
        return self._make_request(url)
    
    def get_delegated_permission_grants_for_sp(self, sp_id):
        """Get delegated permission grants for a specific service principal"""
        url = f'{self.graph_url}/oauth2PermissionGrants'
        params = {
            '$filter': f"clientId eq '{sp_id}'"
        }
        return self._make_request(url, params)
    
    def _is_microsoft_app(self, sp):
        """Check if app is from Microsoft"""
        publisher = sp.get('publisherName', '') or ''
        verified = sp.get('verifiedPublisher', {})
        
        if verified and verified.get('verifiedPublisherId'):
            # Has verified publisher
            publisher_domain = verified.get('displayName', '').lower()
            if any(ms in publisher_domain for ms in self.MICROSOFT_PUBLISHERS):
                return True
        
        # Check publisher name
        if 'microsoft' in publisher.lower():
            return True
        
        # Check app owner organization (Microsoft tenant ID)
        ms_tenant_id = 'f8cdef31-a31e-4b4a-93e4-5f571e91255a'  # Microsoft tenant
        if sp.get('appOwnerOrganizationId') == ms_tenant_id:
            return True
        
        return False
    
    def _calculate_risk_score(self, permissions, sp, consent_type):
        """
        Calculate risk score for an application based on permissions
        
        Risk levels:
        - 0-2: Low (green)
        - 3-5: Medium (yellow)
        - 6-8: High (orange)
        - 9+: Critical (red)
        """
        score = 0
        risk_factors = []
        
        # Parse permissions
        perm_list = [p.strip() for p in permissions.split() if p.strip()] if permissions else []
        
        # 1. Check for high-risk individual permissions
        for perm in perm_list:
            if any(hr.lower() in perm.lower() for hr in self.HIGH_RISK_PERMISSIONS):
                score += 2
                risk_factors.append(f"High-risk permission: {perm}")
        
        # 2. Check for *.All scope pattern
        all_perms = [p for p in perm_list if '.All' in p or p.endswith('.All')]
        if all_perms:
            score += len(all_perms)
            if len(all_perms) > 3:
                risk_factors.append(f"Multiple .All permissions ({len(all_perms)})")
        
        # 3. Check for critical combinations
        for combo in self.CRITICAL_COMBINATIONS:
            if all(any(c.lower() in p.lower() for p in perm_list) for c in combo):
                score += 3
                risk_factors.append(f"Critical combination: {combo[0]} + {combo[1]}")
        
        # 4. Non-Microsoft app with sensitive permissions
        if not self._is_microsoft_app(sp) and score > 0:
            score += 2
            risk_factors.append("Non-Microsoft app with sensitive permissions")
        
        # 5. Admin consent on delegated permissions
        if consent_type == 'AllPrincipals':
            score += 1
            risk_factors.append("Admin consent (affects all users)")
        
        # 6. App is disabled but has permissions
        if not sp.get('accountEnabled', True) and perm_list:
            score += 1
            risk_factors.append("Disabled app with active permissions")
        
        # Determine risk level
        if score >= 9:
            risk_level = 'Critical'
        elif score >= 6:
            risk_level = 'High'
        elif score >= 3:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        return {
            'score': min(score, 10),  # Cap at 10
            'level': risk_level,
            'factors': risk_factors
        }
    
    def get_consent_audit(self):
        """
        Main method: Get comprehensive OAuth consent audit
        Returns list of apps with consent, risk assessment, and owners
        """
        # Get all service principals
        sp_result = self.get_service_principals()
        if 'error' in sp_result:
            return sp_result
        
        service_principals = sp_result.get('value', [])
        
        # Get all OAuth permission grants
        grants_result = self.get_oauth_permission_grants()
        if 'error' in grants_result:
            # Continue without grants, just show apps
            grants = []
        else:
            grants = grants_result.get('value', [])
        
        # Build lookup: SP ID -> grants
        grants_by_client = {}
        for grant in grants:
            client_id = grant.get('clientId')
            if client_id not in grants_by_client:
                grants_by_client[client_id] = []
            grants_by_client[client_id].append(grant)
        
        # Process each service principal
        consent_apps = []
        
        for sp in service_principals:
            sp_id = sp.get('id')
            sp_grants = grants_by_client.get(sp_id, [])
            
            # Skip if no consent grants
            if not sp_grants:
                continue
            
            # Aggregate permissions
            all_scopes = []
            consent_types = set()
            resource_ids = set()
            
            for grant in sp_grants:
                scopes = grant.get('scope', '').split()
                all_scopes.extend(scopes)
                consent_types.add(grant.get('consentType', 'Unknown'))
                resource_ids.add(grant.get('resourceId'))
            
            # Deduplicate scopes
            unique_scopes = list(set(all_scopes))
            scopes_str = ' '.join(unique_scopes)
            
            # Determine consent type
            consent_type = 'Admin' if 'AllPrincipals' in consent_types else 'User'
            
            # Calculate risk
            risk = self._calculate_risk_score(
                scopes_str, 
                sp, 
                'AllPrincipals' if consent_type == 'Admin' else 'Principal'
            )
            
            # Build app info
            app_info = {
                'id': sp_id,
                'appId': sp.get('appId'),
                'displayName': sp.get('displayName') or sp.get('appDisplayName'),
                'publisherName': sp.get('publisherName') or 'Unknown',
                'verifiedPublisher': sp.get('verifiedPublisher'),
                'servicePrincipalType': sp.get('servicePrincipalType'),
                'accountEnabled': sp.get('accountEnabled', True),
                'createdDateTime': sp.get('createdDateTime'),
                'isMicrosoftApp': self._is_microsoft_app(sp),
                'consentType': consent_type,
                'permissions': unique_scopes,
                'permissionCount': len(unique_scopes),
                'risk': risk,
                'tags': sp.get('tags', [])
            }
            
            consent_apps.append(app_info)
        
        # Sort by risk score (highest first)
        consent_apps.sort(key=lambda x: x['risk']['score'], reverse=True)
        
        # Calculate summary stats
        stats = {
            'total': len(consent_apps),
            'critical': sum(1 for a in consent_apps if a['risk']['level'] == 'Critical'),
            'high': sum(1 for a in consent_apps if a['risk']['level'] == 'High'),
            'medium': sum(1 for a in consent_apps if a['risk']['level'] == 'Medium'),
            'low': sum(1 for a in consent_apps if a['risk']['level'] == 'Low'),
            'adminConsent': sum(1 for a in consent_apps if a['consentType'] == 'Admin'),
            'userConsent': sum(1 for a in consent_apps if a['consentType'] == 'User'),
            'nonMicrosoft': sum(1 for a in consent_apps if not a['isMicrosoftApp']),
        }
        
        return {
            'success': True,
            'consentApps': consent_apps,
            'stats': stats
        }
    

    def get_owners_for_consent_apps(self, app_ids):
        """
        Get owners for specific consent apps on-demand
        Lazy loading owners
        
        Args:
            app_ids: List of service principal IDs
        
        Returns:
            Dict mapping app_id -> owner info
        """
        apps = [{'id': aid} for aid in app_ids]
        owners_map = self._get_owners_batch(apps, max_batch=len(app_ids))
        
        # Format for frontend
        result = {}
        for app_id, owners in owners_map.items():
            result[app_id] = {
                'owner': self._format_owner_display(owners),
                'owners': owners,
                'ownerCount': len(owners)
            }
        
        return {
            'success': True,
            'owners': result,
            'count': len(result)
        }

    def get_risky_apps_only(self, min_risk_level='Medium'):
        """Get only apps above a certain risk threshold"""
        result = self.get_consent_audit()
        
        if 'error' in result:
            return result
        
        level_order = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
        min_level = level_order.get(min_risk_level, 1)
        
        filtered = [
            app for app in result.get('consentApps', [])
            if level_order.get(app['risk']['level'], 0) >= min_level
        ]
        
        return {
            'success': True,
            'consentApps': filtered,
            'stats': result.get('stats')
        }
