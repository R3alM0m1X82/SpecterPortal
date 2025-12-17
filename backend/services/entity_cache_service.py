"""
EntityCacheService - Centralized Entity Resolution Cache
ROADrecon-style batch prefetch for ALL Azure AD entities
Prevents 429 errors by pre-fetching all entities once and resolving locally
Complete service with Users, Groups, Devices, Service Principals, 
Applications, Directory Roles (with members), and Licenses
"""
import requests
import time
import json
import base64
from datetime import datetime, timedelta


class EntityCacheService:
    """
    Centralized cache for Azure AD entity resolution.
    Pre-fetches all entities once, then resolves GUIDs locally without API calls.
    """
    
    # Class-level cache (shared across instances)
    _cache = {}
    _cache_ttl = timedelta(minutes=10)
    
    # MS Graph base URL
    MS_GRAPH_URL = "https://graph.microsoft.com/v1.0"
    
    # Common Directory Role Template IDs (static, no need to fetch)
    ROLE_TEMPLATE_MAP = {
        '62e90394-69f5-4237-9190-012177145e10': 'Global Administrator',
        '194ae4cb-b126-40b2-bd5b-6091b380977d': 'Security Administrator',
        'f28a1f50-f6e7-4571-818b-6a12f2af6b6c': 'SharePoint Administrator',
        '29232cdf-9323-42fd-ade2-1d097af3e4de': 'Exchange Administrator',
        'b1be1c3e-b65d-4f19-8427-f6fa0d97feb9': 'Cloud Application Administrator',
        '729827e3-9c14-49f7-bb1b-9608f156bbb8': 'Helpdesk Administrator',
        'b0f54661-2d74-4c50-afa3-1ec803f12efe': 'Billing Administrator',
        'fe930be7-5e62-47db-91af-98c3a49a38b1': 'User Administrator',
        'c4e39bd9-1100-46d3-8c65-fb160da0071f': 'Password Administrator',
        '158c047a-c907-4556-b7ef-446551a6b5f7': 'Cloud Device Administrator',
        '966707d0-3269-4727-9be2-8c3a10f19b9d': 'Global Reader',
        '7be44c8a-adaf-4e2a-84d6-ab2649e08a13': 'Application Administrator',
        'e8611ab8-c189-46e8-94e1-60213ab1f814': 'Privileged Role Administrator',
        '8ac3fc64-6eca-42ea-9e69-59f4c7b60eb2': 'Compliance Administrator',
        '7698a772-787b-4ac8-901f-60d6b08affd2': 'Conditional Access Administrator',
        'fdd7a751-b60b-444a-984c-02652fe8fa1c': 'Groups Administrator',
        '9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3': 'Application Developer',
        '38a96431-2bdf-4b4c-8b6e-5d3d8abac1a4': 'Desktop Analytics Administrator',
        '4a5d8f65-41da-4de4-8968-e035b65339cf': 'Insights Administrator',
        '44367163-eba1-44c3-98af-f5787879f96a': 'Dynamics 365 Administrator',
        '11648597-926c-4cf3-9c36-bcebb0ba8dcc': 'Power Platform Administrator',
        '69091246-20e8-4a56-aa4d-066075b2a7a8': 'Teams Administrator',
        'baf37b3a-610e-45da-9e62-d9d1e5e8914b': 'Teams Communications Administrator',
        'f70938a0-fc10-4177-9e90-2178f8765737': 'Teams Communications Support Engineer',
        'fcf91098-03e3-41a9-b5ba-6f0ec8188a12': 'Teams Communications Support Specialist',
        '3a2c62db-5318-420d-8d74-23affee5d9d5': 'Intune Administrator',
        '74ef975b-6605-40af-a5d2-b9539d836353': 'Kaizala Administrator',
        'eb1f4a8d-243a-41f0-9fbd-c7cdf6c5ef7c': 'Insights Analyst',
        'ac16e43d-7b2d-40e0-ac05-243ff356ab5b': 'Message Center Privacy Reader',
        '790c1fb9-7f7d-4f88-86a1-ef1f95c05c1b': 'Message Center Reader',
        '4d6ac14f-3453-41d0-bef9-a3e0c569773a': 'Network Administrator',
        '2b745bdf-0803-4d80-aa65-822c4493daac': 'Office Apps Administrator',
        '644ef478-e28f-4e28-b9dc-3fdde9aa0b1f': 'Printer Administrator',
        'e00e864a-17c5-4a4b-9c06-f5b95a8d5bd8': 'Printer Technician',
        '0964bb5e-9bdb-4d7b-ac29-58e794862a40': 'Search Administrator',
        '8835291a-918c-4fd7-a9ce-faa49f0cf7d9': 'Search Editor',
        '17315797-102d-40b4-93e0-432062caca18': 'Compliance Data Administrator',
        'd37c8bed-0711-4417-ba38-b4abe66ce4c2': 'Network Administrator',
        '31e939ad-9672-4796-9c2e-873181342d2d': 'External Identity Provider Administrator',
        'e6d1a23a-da11-4be4-9570-befc86d067a7': 'Compliance Manager Administrator',
        '5f2222b1-57c3-48ba-8ad5-d4759f1fde6f': 'Security Operator',
        '5d6b6bb7-de71-4623-b4af-96380a352509': 'Security Reader',
        'f2ef992c-3afb-46b9-b7cf-a126ee74c451': 'Global Secure Access Administrator',
        '9c6df0f2-1e7c-4dc3-b195-66dfbd24aa8f': 'Knowledge Administrator',
        '744ec460-397e-42ad-a462-8b3f9747a02c': 'Knowledge Manager',
        '8329153b-31d0-4727-b945-745eb3bc5f31': 'Domain Name Administrator',
        '31392ffb-586c-42d1-9346-e59415a2cc4e': 'Exchange Recipient Administrator',
        '45d8d3c5-c802-45c6-b32a-1d70b5e1e86e': 'Identity Governance Administrator',
        '892c5842-a9a6-463a-8041-72aa08ca3cf6': 'Cloud App Security Administrator',
        '7495fdc4-34c4-4d15-a289-98788ce399fd': 'Azure AD Joined Device Local Administrator',
        'a9ea8996-122f-4c74-9520-8edcd192826c': 'Attack Payload Author',
        'c430b396-e693-46cc-96f3-db01bf8bb62a': 'Attack Simulation Administrator',
        '580d12a8-7a70-4d03-bbc9-af5ccfcbbe1b': 'Attribute Assignment Administrator',
        '58a13ea3-c632-46ae-9ee0-9c0d43cd7f3d': 'Attribute Assignment Reader',
        '8424c6f0-a189-499e-bbd0-26c1753c96d4': 'Attribute Definition Administrator',
        '1d336d2c-4ae8-42ef-9711-b3604ce3fc2c': 'Attribute Definition Reader',
        'be2f45a1-457d-42af-a067-6ec1fa63bc45': 'Authentication Administrator',
        '0526716b-113d-4c15-b2c8-68e3c22b9f80': 'Authentication Policy Administrator',
        '25a516ed-2fa0-40ea-a2d0-12923a21473a': 'Lifecycle Workflows Administrator',
    }
    
    # Common SKU Part Numbers to friendly names
    SKU_NAME_MAP = {
        'ENTERPRISEPACK': 'Office 365 E3',
        'ENTERPRISEPREMIUM': 'Office 365 E5',
        'SPE_E3': 'Microsoft 365 E3',
        'SPE_E5': 'Microsoft 365 E5',
        'SPE_F1': 'Microsoft 365 F3',
        'FLOW_FREE': 'Power Automate Free',
        'POWER_BI_STANDARD': 'Power BI Free',
        'POWER_BI_PRO': 'Power BI Pro',
        'EXCHANGESTANDARD': 'Exchange Online Plan 1',
        'EXCHANGEENTERPRISE': 'Exchange Online Plan 2',
        'AAD_PREMIUM': 'Azure AD Premium P1',
        'AAD_PREMIUM_P2': 'Azure AD Premium P2',
        'EMS': 'Enterprise Mobility + Security E3',
        'EMSPREMIUM': 'Enterprise Mobility + Security E5',
        'PROJECTPREMIUM': 'Project Plan 5',
        'VISIOCLIENT': 'Visio Plan 2',
        'WINDOWS_STORE': 'Windows Store for Business',
        'STREAM': 'Microsoft Stream',
        'TEAMS_EXPLORATORY': 'Teams Exploratory',
        'MICROSOFT_BUSINESS_CENTER': 'Microsoft Business Center',
        'DYN365_ENTERPRISE_SALES': 'Dynamics 365 Sales Enterprise',
        'DYN365_ENTERPRISE_CUSTOMER_SERVICE': 'Dynamics 365 Customer Service Enterprise',
        'INTUNE_A': 'Intune',
        'ATP_ENTERPRISE': 'Microsoft Defender for Office 365 Plan 1',
        'THREAT_INTELLIGENCE': 'Microsoft Defender for Office 365 Plan 2',
        'IDENTITY_THREAT_PROTECTION': 'Microsoft 365 E5 Security',
        'INFORMATION_PROTECTION_COMPLIANCE': 'Microsoft 365 E5 Compliance',
    }
    
    def __init__(self, access_token, tenant_id=None):
        """
        Initialize with MS Graph access token.
        
        Args:
            access_token: MS Graph token (audience https://graph.microsoft.com)
            tenant_id: Optional tenant ID (extracted from token if not provided)
        """
        self.access_token = access_token
        self.tenant_id = tenant_id or self._extract_tenant_id(access_token)
        self.timeout = 30
    
    def _extract_tenant_id(self, token):
        """Extract tenant ID from JWT token"""
        try:
            parts = token.split('.')
            if len(parts) < 2:
                return 'unknown'
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data.get('tid', 'unknown')
        except:
            return 'unknown'
    
    def _get_cache_key(self, entity_type):
        """Generate cache key for entity type"""
        return f"{self.tenant_id}:{entity_type}"
    
    def _is_cache_valid(self, entity_type):
        """Check if cache exists and is still valid"""
        key = self._get_cache_key(entity_type)
        if key in EntityCacheService._cache:
            _, cached_time = EntityCacheService._cache[key]
            if datetime.utcnow() - cached_time < EntityCacheService._cache_ttl:
                return True
        return False
    
    def _get_from_cache(self, entity_type):
        """Get cached data if valid"""
        key = self._get_cache_key(entity_type)
        if key in EntityCacheService._cache:
            cached_data, cached_time = EntityCacheService._cache[key]
            if datetime.utcnow() - cached_time < EntityCacheService._cache_ttl:
                return cached_data
        return None
    
    def _set_cache(self, entity_type, data):
        """Store data in cache"""
        key = self._get_cache_key(entity_type)
        EntityCacheService._cache[key] = (data, datetime.utcnow())
    
    def _paginated_fetch(self, endpoint, select_fields, entity_name, page_size=999):
        """
        Generic paginated fetch with rate limit handling.
        
        Args:
            endpoint: MS Graph endpoint (e.g., 'users', 'groups')
            select_fields: Comma-separated fields to select
            entity_name: Human-readable name for logging
            page_size: Number of items per page (max 999)
        
        Returns:
            dict: {entity_id: entity_data, ...}
        """
        entities = {}
        
        # Build URL with or without select
        if select_fields:
            url = f"{self.MS_GRAPH_URL}/{endpoint}?$select={select_fields}&$top={page_size}"
        else:
            url = f"{self.MS_GRAPH_URL}/{endpoint}?$top={page_size}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        page_count = 0
        max_retries = 3
        
        while url:
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for entity in data.get('value', []):
                            entity_id = entity.get('id')
                            if entity_id:
                                entities[entity_id] = entity
                        
                        # Get next page
                        url = data.get('@odata.nextLink')
                        page_count += 1
                        
                        if url:
                            print(f"    [*] Fetched page {page_count} ({len(entities)} {entity_name} so far)...")
                            time.sleep(0.1)  # Small delay between pages to be polite
                        
                        break  # Success, exit retry loop
                    
                    elif response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', 10))
                        print(f"[!] Rate limited on {entity_name} page {page_count}. Waiting {retry_after}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_after)
                        continue  # Retry
                    
                    elif response.status_code == 403:
                        print(f"[!] Forbidden: Insufficient permissions for {endpoint}")
                        return entities  # Return what we have
                    
                    else:
                        print(f"[!] Failed to fetch {entity_name}: {response.status_code} - {response.text[:200]}")
                        return entities
                        
                except requests.exceptions.Timeout:
                    print(f"[!] Timeout fetching {entity_name} page {page_count}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return entities
                    
                except requests.exceptions.RequestException as e:
                    print(f"[!] Error fetching {entity_name}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return entities
            else:
                # Max retries exceeded
                print(f"[!] Max retries exceeded for {entity_name}")
                break
        
        return entities
    
    def _simple_fetch(self, endpoint, entity_name):
        """
        Simple fetch without pagination (for small collections like licenses).
        
        Args:
            endpoint: MS Graph endpoint
            entity_name: Human-readable name for logging
        
        Returns:
            list: List of entities
        """
        url = f"{self.MS_GRAPH_URL}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('value', [])
                
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 10))
                    print(f"[!] Rate limited on {entity_name}. Waiting {retry_after}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 403:
                    print(f"[!] Forbidden: Insufficient permissions for {endpoint}")
                    return []
                
                else:
                    print(f"[!] Failed to fetch {entity_name}: {response.status_code}")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"[!] Error fetching {entity_name}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []
        
        return []
    
    # ==================== PREFETCH METHODS ====================
    
    def prefetch_users(self, force=False):
        """
        Pre-fetch ALL users from tenant.
        
        Args:
            force: Force refresh even if cached
        
        Returns:
            dict: {user_id: {'id', 'displayName', 'userPrincipalName'}, ...}
        """
        if not force:
            cached = self._get_from_cache('users')
            if cached:
                print(f"[+] Using cached users ({len(cached)} users)")
                return cached
        
        print("[*] Pre-fetching all users from tenant...")
        users = self._paginated_fetch(
            endpoint='users',
            select_fields='id,displayName,userPrincipalName,mail,jobTitle,department,accountEnabled',
            entity_name='users'
        )
        
        # Format for easy lookup
        formatted = {}
        for user_id, user in users.items():
            formatted[user_id] = {
                'id': user_id,
                'displayName': user.get('displayName', f'{user_id[:8]}...'),
                'userPrincipalName': user.get('userPrincipalName'),
                'mail': user.get('mail'),
                'jobTitle': user.get('jobTitle'),
                'department': user.get('department'),
                'accountEnabled': user.get('accountEnabled', True)
            }
        
        self._set_cache('users', formatted)
        print(f"[+] Pre-fetched {len(formatted)} users from tenant")
        return formatted
    
    def prefetch_groups(self, force=False):
        """
        Pre-fetch ALL groups from tenant.
        
        Returns:
            dict: {group_id: {'id', 'displayName', 'mail'}, ...}
        """
        if not force:
            cached = self._get_from_cache('groups')
            if cached:
                print(f"[+] Using cached groups ({len(cached)} groups)")
                return cached
        
        print("[*] Pre-fetching all groups from tenant...")
        groups = self._paginated_fetch(
            endpoint='groups',
            select_fields='id,displayName,mail,groupTypes,securityEnabled,description',
            entity_name='groups'
        )
        
        # Format for easy lookup
        formatted = {}
        for group_id, group in groups.items():
            formatted[group_id] = {
                'id': group_id,
                'displayName': group.get('displayName', f'{group_id[:8]}...'),
                'mail': group.get('mail'),
                'groupTypes': group.get('groupTypes', []),
                'securityEnabled': group.get('securityEnabled', False),
                'description': group.get('description')
            }
        
        self._set_cache('groups', formatted)
        print(f"[+] Pre-fetched {len(formatted)} groups from tenant")
        return formatted
    
    def prefetch_devices(self, force=False):
        """
        Pre-fetch ALL devices from tenant.
        
        Returns:
            dict: {device_id: {'id', 'displayName', 'operatingSystem', ...}, ...}
        """
        if not force:
            cached = self._get_from_cache('devices')
            if cached:
                print(f"[+] Using cached devices ({len(cached)} devices)")
                return cached
        
        print("[*] Pre-fetching all devices from tenant...")
        devices = self._paginated_fetch(
            endpoint='devices',
            select_fields='id,displayName,deviceId,operatingSystem,operatingSystemVersion,trustType,isCompliant,isManaged,accountEnabled',
            entity_name='devices'
        )
        
        # Format for easy lookup
        formatted = {}
        for device_id, device in devices.items():
            formatted[device_id] = {
                'id': device_id,
                'displayName': device.get('displayName', f'{device_id[:8]}...'),
                'deviceId': device.get('deviceId'),
                'operatingSystem': device.get('operatingSystem'),
                'operatingSystemVersion': device.get('operatingSystemVersion'),
                'trustType': device.get('trustType'),
                'isCompliant': device.get('isCompliant'),
                'isManaged': device.get('isManaged'),
                'accountEnabled': device.get('accountEnabled')
            }
        
        self._set_cache('devices', formatted)
        print(f"[+] Pre-fetched {len(formatted)} devices from tenant")
        return formatted
    
    def prefetch_service_principals(self, force=False):
        """
        Pre-fetch ALL service principals from tenant.
        
        Returns:
            dict: {sp_id: {'id', 'displayName', 'appId', ...}, ...}
        """
        if not force:
            cached = self._get_from_cache('service_principals')
            if cached:
                print(f"[+] Using cached service principals ({len(cached)} SPs)")
                return cached
        
        print("[*] Pre-fetching all service principals from tenant...")
        sps = self._paginated_fetch(
            endpoint='servicePrincipals',
            select_fields='id,displayName,appId,appDisplayName,servicePrincipalType,accountEnabled',
            entity_name='service principals'
        )
        
        # Format for easy lookup
        formatted = {}
        for sp_id, sp in sps.items():
            formatted[sp_id] = {
                'id': sp_id,
                'displayName': sp.get('displayName', f'{sp_id[:8]}...'),
                'appId': sp.get('appId'),
                'appDisplayName': sp.get('appDisplayName'),
                'servicePrincipalType': sp.get('servicePrincipalType'),
                'accountEnabled': sp.get('accountEnabled', True)
            }
        
        self._set_cache('service_principals', formatted)
        print(f"[+] Pre-fetched {len(formatted)} service principals from tenant")
        return formatted
    
    def prefetch_applications(self, force=False):
        """
        Pre-fetch ALL app registrations from tenant.
        
        Returns:
            dict: {app_id: {'id', 'displayName', 'appId', ...}, ...}
        """
        if not force:
            cached = self._get_from_cache('applications')
            if cached:
                print(f"[+] Using cached applications ({len(cached)} apps)")
                return cached
        
        print("[*] Pre-fetching all applications from tenant...")
        apps = self._paginated_fetch(
            endpoint='applications',
            select_fields='id,displayName,appId,createdDateTime,publisherDomain',
            entity_name='applications'
        )
        
        # Format for easy lookup
        formatted = {}
        for app_id, app in apps.items():
            formatted[app_id] = {
                'id': app_id,
                'displayName': app.get('displayName', f'{app_id[:8]}...'),
                'appId': app.get('appId'),
                'createdDateTime': app.get('createdDateTime'),
                'publisherDomain': app.get('publisherDomain')
            }
        
        self._set_cache('applications', formatted)
        print(f"[+] Pre-fetched {len(formatted)} applications from tenant")
        return formatted
    
    def prefetch_directory_roles(self, force=False):
        """
        Pre-fetch ALL directory roles with their members.
        This is critical for Roles & Licenses drill-down!
        
        Returns:
            dict: {role_id: {'id', 'displayName', 'description', 'members': [...]}, ...}
        """
        if not force:
            cached = self._get_from_cache('directory_roles')
            if cached:
                print(f"[+] Using cached directory roles ({len(cached)} roles)")
                return cached
        
        print("[*] Pre-fetching all directory roles from tenant...")
        
        # First fetch all roles
        roles_raw = self._simple_fetch('directoryRoles', 'directory roles')
        
        formatted = {}
        
        for role in roles_raw:
            role_id = role.get('id')
            if not role_id:
                continue
            
            role_template_id = role.get('roleTemplateId')
            display_name = role.get('displayName', f'{role_id[:8]}...')
            
            # Try to get friendly name from static map
            if role_template_id and role_template_id in self.ROLE_TEMPLATE_MAP:
                display_name = self.ROLE_TEMPLATE_MAP[role_template_id]
            
            formatted[role_id] = {
                'id': role_id,
                'displayName': display_name,
                'description': role.get('description'),
                'roleTemplateId': role_template_id,
                'members': [],
                'memberCount': 0
            }
        
        print(f"    [*] Found {len(formatted)} activated directory roles")
        
        # Now fetch members for each role
        print("[*] Pre-fetching members for each role...")
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        for i, (role_id, role_data) in enumerate(formatted.items()):
            try:
                url = f"{self.MS_GRAPH_URL}/directoryRoles/{role_id}/members?$select=id,displayName,userPrincipalName"
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    members_data = response.json().get('value', [])
                    members = []
                    
                    for member in members_data:
                        member_type = member.get('@odata.type', '').replace('#microsoft.graph.', '')
                        members.append({
                            'id': member.get('id'),
                            'displayName': member.get('displayName'),
                            'userPrincipalName': member.get('userPrincipalName'),
                            'type': member_type
                        })
                    
                    formatted[role_id]['members'] = members
                    formatted[role_id]['memberCount'] = len(members)
                    
                    if (i + 1) % 10 == 0:
                        print(f"    [*] Processed {i + 1}/{len(formatted)} roles...")
                
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"[!] Rate limited on role members. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    # Retry this role
                    i -= 1
                    continue
                
                # Small delay between requests
                time.sleep(0.05)
                
            except Exception as e:
                print(f"[!] Error fetching members for role {role_data['displayName']}: {e}")
                continue
        
        self._set_cache('directory_roles', formatted)
        
        total_members = sum(r['memberCount'] for r in formatted.values())
        print(f"[+] Pre-fetched {len(formatted)} directory roles with {total_members} total members")
        return formatted
    
    def prefetch_licenses(self, force=False):
        """
        Pre-fetch ALL subscribed SKUs (licenses) from tenant.
        
        Returns:
            dict: {sku_id: {'id', 'skuPartNumber', 'displayName', 'consumedUnits', ...}, ...}
        """
        if not force:
            cached = self._get_from_cache('licenses')
            if cached:
                print(f"[+] Using cached licenses ({len(cached)} SKUs)")
                return cached
        
        print("[*] Pre-fetching all licenses from tenant...")
        
        skus = self._simple_fetch('subscribedSkus', 'subscribed SKUs')
        
        formatted = {}
        for sku in skus:
            sku_id = sku.get('skuId')
            if not sku_id:
                continue
            
            sku_part_number = sku.get('skuPartNumber', '')
            
            # Get friendly name from map or use part number
            display_name = self.SKU_NAME_MAP.get(sku_part_number, sku_part_number)
            
            # Calculate available licenses
            prepaid = sku.get('prepaidUnits', {})
            enabled = prepaid.get('enabled', 0)
            consumed = sku.get('consumedUnits', 0)
            available = enabled - consumed if enabled else 0
            
            formatted[sku_id] = {
                'id': sku_id,
                'skuPartNumber': sku_part_number,
                'displayName': display_name,
                'consumedUnits': consumed,
                'prepaidUnits': {
                    'enabled': enabled,
                    'suspended': prepaid.get('suspended', 0),
                    'warning': prepaid.get('warning', 0)
                },
                'availableUnits': available,
                'capabilityStatus': sku.get('capabilityStatus'),
                'appliesTo': sku.get('appliesTo'),
                'servicePlans': sku.get('servicePlans', [])
            }
        
        self._set_cache('licenses', formatted)
        print(f"[+] Pre-fetched {len(formatted)} licenses (subscribed SKUs)")
        return formatted
    
    def prefetch_all(self, force=False):
        """
        Pre-fetch ALL entity types at once.
        
        Returns:
            dict: Statistics about what was fetched
        """
        stats = {
            'users': len(self.prefetch_users(force)),
            'groups': len(self.prefetch_groups(force)),
            'devices': len(self.prefetch_devices(force)),
            'service_principals': len(self.prefetch_service_principals(force)),
            'applications': len(self.prefetch_applications(force)),
            'directory_roles': len(self.prefetch_directory_roles(force)),
            'licenses': len(self.prefetch_licenses(force))
        }
        
        total = sum(stats.values())
        print(f"[+] Total entities cached: {total}")
        return stats
    
    # ==================== RESOLVE METHODS (Local Lookup) ====================
    
    def resolve_user(self, user_id):
        """
        Resolve user ID to display name (local cache lookup, NO API call).
        
        Args:
            user_id: User GUID or special value
        
        Returns:
            dict: {'id', 'displayName', 'userPrincipalName'} or indicator if not found
        """
        # Handle special values
        if user_id == 'All':
            return {'id': user_id, 'displayName': 'All Users', 'userPrincipalName': None}
        if user_id == 'GuestsOrExternalUsers':
            return {'id': user_id, 'displayName': 'All Guest/External Users', 'userPrincipalName': None}
        if user_id == 'None':
            return {'id': user_id, 'displayName': 'None', 'userPrincipalName': None}
        
        # Ensure cache is populated
        cached = self._get_from_cache('users')
        if not cached:
            cached = self.prefetch_users()
        
        # Lookup
        if user_id in cached:
            return cached[user_id]
        
        # Not found - return GUID indicator
        return {'id': user_id, 'displayName': f'👤 {user_id[:8]}...', 'userPrincipalName': None}
    
    def resolve_group(self, group_id):
        """
        Resolve group ID to display name (local cache lookup, NO API call).
        """
        # Ensure cache is populated
        cached = self._get_from_cache('groups')
        if not cached:
            cached = self.prefetch_groups()
        
        # Lookup
        if group_id in cached:
            return cached[group_id]
        
        # Not found
        return {'id': group_id, 'displayName': f'👥 {group_id[:8]}...'}
    
    def resolve_device(self, device_id):
        """
        Resolve device ID to display name (local cache lookup, NO API call).
        """
        # Ensure cache is populated
        cached = self._get_from_cache('devices')
        if not cached:
            cached = self.prefetch_devices()
        
        # Lookup
        if device_id in cached:
            return cached[device_id]
        
        # Not found
        return {'id': device_id, 'displayName': f'💻 {device_id[:8]}...'}
    
    def resolve_role(self, role_id_or_template_id):
        """
        Resolve role ID or template ID to display name.
        Checks both static map and cached directory roles.
        """
        # Check static map first (for template IDs)
        if role_id_or_template_id in self.ROLE_TEMPLATE_MAP:
            return {
                'id': role_id_or_template_id,
                'displayName': self.ROLE_TEMPLATE_MAP[role_id_or_template_id]
            }
        
        # Check cached directory roles (for role IDs)
        cached = self._get_from_cache('directory_roles')
        if cached and role_id_or_template_id in cached:
            return cached[role_id_or_template_id]
        
        # Not found - return GUID indicator
        return {'id': role_id_or_template_id, 'displayName': f'🔐 {role_id_or_template_id[:8]}...'}
    
    def resolve_service_principal(self, sp_id):
        """
        Resolve service principal ID (local cache lookup, NO API call).
        """
        # Ensure cache is populated
        cached = self._get_from_cache('service_principals')
        if not cached:
            cached = self.prefetch_service_principals()
        
        # Lookup
        if sp_id in cached:
            return cached[sp_id]
        
        # Not found
        return {'id': sp_id, 'displayName': f'⚙️ {sp_id[:8]}...'}
    
    def resolve_application(self, app_id):
        """
        Resolve application ID (local cache lookup, NO API call).
        """
        # Ensure cache is populated
        cached = self._get_from_cache('applications')
        if not cached:
            cached = self.prefetch_applications()
        
        # Lookup
        if app_id in cached:
            return cached[app_id]
        
        # Not found
        return {'id': app_id, 'displayName': f'📱 {app_id[:8]}...'}
    
    def resolve_license(self, sku_id):
        """
        Resolve license SKU ID to friendly name (local cache lookup, NO API call).
        """
        # Ensure cache is populated
        cached = self._get_from_cache('licenses')
        if not cached:
            cached = self.prefetch_licenses()
        
        # Lookup
        if sku_id in cached:
            return cached[sku_id]
        
        # Not found
        return {'id': sku_id, 'displayName': f'📄 {sku_id[:8]}...'}
    
    # ==================== BULK RESOLVE ====================
    
    def resolve_users_bulk(self, user_ids):
        """
        Resolve multiple user IDs at once.
        
        Args:
            user_ids: List of user GUIDs
        
        Returns:
            list: List of resolved user dicts
        """
        return [self.resolve_user(uid) for uid in user_ids]
    
    def resolve_groups_bulk(self, group_ids):
        """Resolve multiple group IDs at once."""
        return [self.resolve_group(gid) for gid in group_ids]
    
    # ==================== DRILL-DOWN METHODS ====================
    
    def get_role_members(self, role_id):
        """
        Get members of a specific role from cache.
        
        Args:
            role_id: Directory role ID
        
        Returns:
            list: List of member dicts
        """
        cached = self._get_from_cache('directory_roles')
        if not cached:
            cached = self.prefetch_directory_roles()
        
        if role_id in cached:
            return cached[role_id].get('members', [])
        
        return []
    
    def get_roles_for_user(self, user_id):
        """
        Get all roles assigned to a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            list: List of role dicts
        """
        cached = self._get_from_cache('directory_roles')
        if not cached:
            cached = self.prefetch_directory_roles()
        
        user_roles = []
        for role_id, role_data in cached.items():
            for member in role_data.get('members', []):
                if member.get('id') == user_id:
                    user_roles.append({
                        'id': role_id,
                        'displayName': role_data.get('displayName'),
                        'roleTemplateId': role_data.get('roleTemplateId')
                    })
                    break
        
        return user_roles
    
    def get_license_service_plans(self, sku_id):
        """
        Get service plans included in a license.
        
        Args:
            sku_id: License SKU ID
        
        Returns:
            list: List of service plan dicts
        """
        cached = self._get_from_cache('licenses')
        if not cached:
            cached = self.prefetch_licenses()
        
        if sku_id in cached:
            return cached[sku_id].get('servicePlans', [])
        
        return []
    
    # ==================== UTILITY ====================
    
    def get_cache_stats(self):
        """Get statistics about current cache state."""
        stats = {}
        entity_types = ['users', 'groups', 'devices', 'service_principals', 
                        'applications', 'directory_roles', 'licenses']
        
        for entity_type in entity_types:
            key = self._get_cache_key(entity_type)
            if key in EntityCacheService._cache:
                data, cached_time = EntityCacheService._cache[key]
                age = datetime.utcnow() - cached_time
                stats[entity_type] = {
                    'count': len(data),
                    'cached_at': cached_time.isoformat(),
                    'age_seconds': int(age.total_seconds()),
                    'valid': age < EntityCacheService._cache_ttl
                }
            else:
                stats[entity_type] = {
                    'count': 0,
                    'cached_at': None,
                    'valid': False
                }
        return stats
    
    def clear_cache(self, entity_type=None):
        """
        Clear cache for specific entity type or all.
        
        Args:
            entity_type: 'users', 'groups', etc. or None for all
        """
        if entity_type:
            key = self._get_cache_key(entity_type)
            if key in EntityCacheService._cache:
                del EntityCacheService._cache[key]
                print(f"[+] Cleared cache for {entity_type}")
        else:
            # Clear all caches for this tenant
            keys_to_delete = [k for k in EntityCacheService._cache.keys() if k.startswith(f"{self.tenant_id}:")]
            for key in keys_to_delete:
                del EntityCacheService._cache[key]
            print(f"[+] Cleared all caches for tenant {self.tenant_id}")
    
    @classmethod
    def get_all_cached_tenants(cls):
        """Get list of all tenants with cached data."""
        tenants = set()
        for key in cls._cache.keys():
            if ':' in key:
                tenant_id = key.split(':')[0]
                tenants.add(tenant_id)
        return list(tenants)
