"""
CAP Service - Conditional Access Policy Enumeration
Uses Azure AD Graph API 1.61-internal (ROADrecon technique)
WITH NAME RESOLUTION: Resolves GUIDs to readable names
WITH LOCATION RESOLUTION: Pre-fetch Named Locations like ROADrecon
NOW USES: EntityCacheService for centralized entity resolution (no more duplicate prefetch!)
"""
import requests
import json
import base64
import zlib
import time
from datetime import datetime, timedelta
from services.entity_cache_service import EntityCacheService


class CAPService:
    """Service for enumerating Conditional Access Policies via Azure AD Graph API"""
    
    # Azure AD Graph API (legacy) - NOT MS Graph!
    AZURE_AD_GRAPH_URL = "https://graph.windows.net"
    MS_GRAPH_URL = "https://graph.microsoft.com/v1.0"
    API_VERSION = "1.61-internal"
    
    # FOCI Client ID for token exchange
    FOCI_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"  # Microsoft Office
    
    # Cache storage
    _cache = {}
    _cache_ttl = timedelta(minutes=10)
    _named_locations_cache = {}  # Cache for Named Locations (pre-fetched)
    _cap_policies_cache = {}  # Cache for CAP policies (for reverse lookup)
    
    # Warnings/Banners
    _warnings = []
    
    # Common Location names
    LOCATION_MAP = {
        'All': 'All Locations',
        'AllTrusted': 'All Trusted Locations',
        '00000000-0000-0000-0000-000000000000': 'All Locations',
    }
    
    def __init__(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.tenant_id = self._extract_tenant_id(access_token)
        self.aad_token = None
        self.ms_graph_token = None
        self._warnings = []
        self._entity_cache = None  # EntityCacheService instance
    
    def _get_entity_cache(self):
        """Get or create EntityCacheService with MS Graph token"""
        if not self._entity_cache:
            # Make sure we have MS Graph token
            if not self.ms_graph_token:
                self._get_ms_graph_token()
            
            if self.ms_graph_token:
                self._entity_cache = EntityCacheService(
                    access_token=self.ms_graph_token,
                    tenant_id=self.tenant_id
                )
        return self._entity_cache
    
    def _get_cache_key(self, endpoint):
        return f"{self.tenant_id}:{endpoint}"
    
    def _get_cached(self, endpoint):
        key = self._get_cache_key(endpoint)
        if key in CAPService._cache:
            cached_data, cached_time = CAPService._cache[key]
            if datetime.utcnow() - cached_time < CAPService._cache_ttl:
                return cached_data
            else:
                del CAPService._cache[key]
        return None
    
    def _set_cache(self, endpoint, data):
        key = self._get_cache_key(endpoint)
        CAPService._cache[key] = (data, datetime.utcnow())
    
    def _request_with_retry(self, url, headers, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait_time = int(retry_after) if retry_after else (2 ** attempt) * 5
                    print(f"[!] Rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"[!] Request error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        return response
        
    def _extract_tenant_id(self, token):
        try:
            parts = token.split('.')
            if len(parts) < 2:
                return None
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data.get('tid')
        except:
            return None
    
    def _extract_audience(self, token):
        try:
            parts = token.split('.')
            if len(parts) < 2:
                return None
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data.get('aud')
        except:
            return None
    
    def _decompress_cidr_ranges(self, compressed_data):
        """
        Decompress CompressedCidrIpRanges from Azure AD Graph
        Format: base64(zlib(ip_ranges))
        Returns list of CIDR strings
        """
        if not compressed_data:
            return []
        
        try:
            # Decode base64
            decoded = base64.b64decode(compressed_data)
            
            # Decompress with zlib (raw deflate, no header)
            # Try different window bits for compatibility
            for wbits in [-15, -zlib.MAX_WBITS, 15, zlib.MAX_WBITS]:
                try:
                    decompressed = zlib.decompress(decoded, wbits)
                    # Parse the decompressed data
                    text = decompressed.decode('utf-8', errors='ignore')
                    
                    # Split by common delimiters
                    if '\n' in text:
                        ranges = [r.strip() for r in text.split('\n') if r.strip()]
                    elif '\r' in text:
                        ranges = [r.strip() for r in text.split('\r') if r.strip()]
                    elif ',' in text:
                        ranges = [r.strip() for r in text.split(',') if r.strip()]
                    else:
                        # Single IP or unknown format
                        ranges = [text.strip()] if text.strip() else []
                    
                    # Filter valid CIDR-like strings
                    valid_ranges = []
                    for r in ranges:
                        if r and ('.' in r or ':' in r):  # IPv4 or IPv6
                            valid_ranges.append(r)
                    
                    if valid_ranges:
                        return valid_ranges
                        
                except zlib.error:
                    continue
            
            # If all decompression attempts fail, return empty
            print(f"[!] Could not decompress CIDR ranges: {compressed_data[:50]}...")
            return []
            
        except Exception as e:
            print(f"[!] Error decompressing CIDR ranges: {e}")
            return []
    
    def _get_aad_graph_token(self):
        current_audience = self._extract_audience(self.access_token)
        
        if current_audience and 'graph.windows.net' in current_audience:
            self.aad_token = self.access_token
            return True
        
        if not self.refresh_token:
            return False
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.FOCI_CLIENT_ID,
            'resource': self.AZURE_AD_GRAPH_URL
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code == 200:
                self.aad_token = response.json().get('access_token')
                return True
            else:
                print(f"[!] AAD Graph token exchange failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[!] AAD Graph token exchange error: {e}")
            return False
    
    def _get_ms_graph_token(self):
        current_audience = self._extract_audience(self.access_token)
        
        if current_audience and 'graph.microsoft.com' in current_audience:
            self.ms_graph_token = self.access_token
            return True
        
        if not self.refresh_token:
            print("[!] No refresh token available for MS Graph")
            return False
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.FOCI_CLIENT_ID,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code == 200:
                self.ms_graph_token = response.json().get('access_token')
                print("[+] MS Graph token obtained successfully")
                return True
            else:
                print(f"[!] MS Graph token exchange failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[!] MS Graph token exchange error: {e}")
            return False
    
    def _prefetch_named_locations(self, all_policies):
        """
        Pre-fetch Named Locations from the policies list (ROADrecon style)
        Named Locations are policies with policyType == 6
        Enhanced: Now extracts all details including countriesAndRegions, decompresses IP ranges
        """
        cache_key = self._get_cache_key('named_locations')
        
        # Check if already cached
        if cache_key in CAPService._named_locations_cache:
            cached_data, cached_time = CAPService._named_locations_cache[cache_key]
            if datetime.utcnow() - cached_time < CAPService._cache_ttl:
                print(f"[+] Using cached Named Locations ({len(cached_data)} locations)")
                return cached_data
        
        locations = {}
        
        for policy in all_policies:
            policy_type = policy.get('policyType')
            
            # policyType == 6 = Named Location
            if policy_type == 6:
                object_id = policy.get('objectId')
                policy_identifier = policy.get('policyIdentifier')
                display_name = policy.get('displayName', 'Unknown Location')
                
                # Skip dummy/placeholder policies
                if 'DummyKnownNetworkPolicy' in str(policy.get('policyDetail', '')):
                    continue
                
                # Parse policy detail for additional info
                policy_detail_raw = policy.get('policyDetail', [])
                
                location_data = {
                    'id': policy_identifier or object_id,
                    'objectId': object_id,
                    'displayName': display_name,
                    'isTrusted': False,
                    'applyToUnknownCountry': False,
                    'ipRanges': [],
                    'countriesAndRegions': [],
                    'categories': [],
                    'locationType': 'unknown'  # 'ip' or 'country'
                }
                
                if isinstance(policy_detail_raw, list) and len(policy_detail_raw) > 0:
                    try:
                        detail = json.loads(policy_detail_raw[0]) if isinstance(policy_detail_raw[0], str) else policy_detail_raw[0]
                        
                        # Extract categories
                        categories = detail.get('Categories', [])
                        if isinstance(categories, str):
                            categories = [categories]
                        
                        # Check for compressed IP ranges
                        compressed_ranges = detail.get('CompressedCidrIpRanges')
                        ip_ranges = []
                        if compressed_ranges:
                            ip_ranges = self._decompress_cidr_ranges(compressed_ranges)
                        
                        # Also check for uncompressed CidrIpRanges
                        if not ip_ranges:
                            ip_ranges = detail.get('CidrIpRanges', [])
                        
                        # Extract country codes
                        country_codes = detail.get('CountryIsoCodes', [])
                        
                        # Determine location type
                        if country_codes:
                            loc_type = 'country'
                        elif ip_ranges:
                            loc_type = 'ip'
                        else:
                            loc_type = 'unknown'
                        
                        location_data = {
                            'id': policy_identifier or object_id,
                            'objectId': object_id,
                            'displayName': display_name,
                            'isTrusted': 'trusted' in str(categories).lower(),
                            'applyToUnknownCountry': detail.get('ApplyToUnknownCountry', False),
                            'ipRanges': ip_ranges,
                            'countriesAndRegions': country_codes,
                            'categories': categories if isinstance(categories, list) else [categories] if categories else [],
                            'locationType': loc_type
                        }
                                
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"[!] Error parsing Named Location {display_name}: {e}")
                
                # Store by policyIdentifier (the ID used in CAP policies)
                loc_id = policy_identifier or object_id
                if loc_id:
                    locations[loc_id] = location_data
                    print(f"    [+] Named Location: {display_name} (ID: {loc_id[:8]}...) - {len(location_data['ipRanges'])} IPs, {len(location_data['countriesAndRegions'])} countries")
        
        # Cache the locations
        CAPService._named_locations_cache[cache_key] = (locations, datetime.utcnow())
        print(f"[+] Pre-fetched {len(locations)} Named Locations from Azure AD Graph")
        
        return locations
    
    def _compute_associated_policies(self, locations, cap_policies_raw):
        """
        Compute which CAP policies use each Named Location (reverse lookup)
        NOW INCLUDES: Policies that use "All" locations
        """
        # Initialize associated policies for each location
        for loc_id in locations:
            locations[loc_id]['associatedPolicies'] = []
        
        for policy in cap_policies_raw:
            policy_name = policy.get('displayName', 'Unknown')
            policy_id = policy.get('objectId')
            
            try:
                policy_detail_raw = policy.get('policyDetail', [])
                
                if isinstance(policy_detail_raw, list) and len(policy_detail_raw) > 0:
                    policy_detail = policy_detail_raw[0]
                else:
                    continue
                
                if isinstance(policy_detail, str):
                    detail = json.loads(policy_detail)
                elif isinstance(policy_detail, dict):
                    detail = policy_detail
                else:
                    continue
                
                conditions = detail.get('Conditions', {})
                if not isinstance(conditions, dict):
                    continue
                
                # Get locations from this policy
                policy_locations = conditions.get('Locations', {})
                if not isinstance(policy_locations, dict):
                    continue
                
                # Track if this policy uses "All" locations
                uses_all_include = False
                excluded_locations = set()
                
                # First pass: collect excluded locations and check for "All"
                for direction in ['Include', 'Exclude']:
                    items = policy_locations.get(direction, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                loc_ids = item.get('Locations', [])
                                if isinstance(loc_ids, list):
                                    for loc_id in loc_ids:
                                        if direction == 'Include' and loc_id == 'All':
                                            uses_all_include = True
                                        elif direction == 'Exclude':
                                            excluded_locations.add(loc_id)
                
                # Second pass: add associations
                for direction in ['Include', 'Exclude']:
                    items = policy_locations.get(direction, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                loc_ids = item.get('Locations', [])
                                if isinstance(loc_ids, list):
                                    for loc_id in loc_ids:
                                        if loc_id in locations and loc_id != 'All':
                                            # Direct reference
                                            assoc = {
                                                'id': policy_id,
                                                'name': policy_name,
                                                'direction': direction.lower()
                                            }
                                            if assoc not in locations[loc_id]['associatedPolicies']:
                                                locations[loc_id]['associatedPolicies'].append(assoc)
                
                # If policy uses "All" include, add to all locations (except excluded ones)
                if uses_all_include:
                    for loc_id in locations:
                        if loc_id not in excluded_locations:
                            assoc = {
                                'id': policy_id,
                                'name': policy_name,
                                'direction': 'include (all)'
                            }
                            if assoc not in locations[loc_id]['associatedPolicies']:
                                locations[loc_id]['associatedPolicies'].append(assoc)
                
            except Exception as e:
                print(f"[!] Error computing associated policies for {policy_name}: {e}")
                continue
        
        return locations
    
    def _resolve_location_name(self, location_id):
        """Resolve Named Location ID to displayName using pre-fetched data"""
        # Check static map first
        if location_id in self.LOCATION_MAP:
            return {
                'id': location_id,
                'displayName': self.LOCATION_MAP[location_id]
            }
        
        # Check pre-fetched locations cache
        cache_key = self._get_cache_key('named_locations')
        if cache_key in CAPService._named_locations_cache:
            locations, _ = CAPService._named_locations_cache[cache_key]
            if location_id in locations:
                return locations[location_id]
        
        # Fallback: return GUID with indicator
        return {
            'id': location_id,
            'displayName': f"📍 {location_id[:8]}...",
            'resolved': False
        }
    
    def _resolve_user_name(self, user_id):
        """Resolve user ID using EntityCacheService (local lookup, no API call)"""
        cache = self._get_entity_cache()
        if cache:
            return cache.resolve_user(user_id)
        
        # Fallback if no cache available
        if user_id == 'All':
            return {'id': user_id, 'displayName': 'All Users', 'userPrincipalName': None}
        if user_id == 'GuestsOrExternalUsers':
            return {'id': user_id, 'displayName': 'All Guest/External Users', 'userPrincipalName': None}
        if user_id == 'None':
            return {'id': user_id, 'displayName': 'None', 'userPrincipalName': None}
        
        return {'id': user_id, 'displayName': f'👤 {user_id[:8]}...', 'userPrincipalName': None}
    
    def _resolve_group_name(self, group_id):
        """Resolve group ID using EntityCacheService (local lookup, no API call)"""
        cache = self._get_entity_cache()
        if cache:
            return cache.resolve_group(group_id)
        
        return {'id': group_id, 'displayName': f'👥 {group_id[:8]}...'}
    
    def _resolve_role_name(self, role_template_id):
        """Resolve role template ID using EntityCacheService"""
        cache = self._get_entity_cache()
        if cache:
            return cache.resolve_role(role_template_id)
        
        return {'id': role_template_id, 'displayName': f'🔐 {role_template_id[:8]}...'}
    
    def get_conditional_access_policies(self):
        """Get all Conditional Access Policies"""
        
        if not self.tenant_id:
            return {
                'success': False,
                'error': 'Could not extract tenant ID from token'
            }
        
        cached = self._get_cached('policies')
        if cached:
            print("[+] Returning cached policies")
            return cached
        
        if not self.aad_token:
            if not self._get_aad_graph_token():
                return {
                    'success': False,
                    'error': 'Could not obtain Azure AD Graph token. Refresh token required for FOCI exchange.',
                    'hint': 'Select a token that has a refresh token available'
                }
        
        # Pre-fetch MS Graph token for name resolution
        if not self.ms_graph_token:
            self._get_ms_graph_token()
        
        url = f"{self.AZURE_AD_GRAPH_URL}/{self.tenant_id}/policies?api-version={self.API_VERSION}"
        
        headers = {
            'Authorization': f'Bearer {self.aad_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = self._request_with_retry(url, headers)
            
            if response.status_code == 200:
                data = response.json()
                all_policies = data.get('value', [])
                
                # Filter CAP policies first (for reverse lookup)
                cap_policies_raw = [p for p in all_policies if p.get('policyType') == 18]
                
                # Pre-fetch Named Locations (ROADrecon style) with enhanced details
                locations = self._prefetch_named_locations(all_policies)
                
                # Compute associated policies (reverse lookup) - NOW includes "All" locations
                self._compute_associated_policies(locations, cap_policies_raw)
                
                # Use EntityCacheService for batch prefetch (centralized, no duplication!)
                entity_cache = self._get_entity_cache()
                if entity_cache:
                    print("[*] Pre-fetching all users from tenant...")
                    entity_cache.prefetch_users()
                    
                    print("[*] Pre-fetching all groups from tenant...")
                    entity_cache.prefetch_groups()
                else:
                    print("[!] EntityCacheService not available - names may not be resolved")
                
                print(f"[*] Found {len(cap_policies_raw)} CAP policies")
                
                # Now parse policies (will use cached names)
                cap_policies = []
                for i, policy in enumerate(cap_policies_raw):
                    print(f"[*] Parsing policy {i+1}/{len(cap_policies_raw)}: {policy.get('displayName', 'Unknown')}")
                    parsed = self._parse_cap_policy(policy)
                    if parsed:
                        cap_policies.append(parsed)
                
                result = {
                    'success': True,
                    'policies': cap_policies,
                    'total_count': len(cap_policies),
                    'tenant_id': self.tenant_id,
                    'warnings': self._warnings
                }
                
                self._set_cache('policies', result)
                
                return result
            
            elif response.status_code == 401:
                return {'success': False, 'error': 'Unauthorized - Token may be expired or invalid', 'status_code': 401}
            elif response.status_code == 403:
                return {'success': False, 'error': 'Forbidden - Insufficient permissions', 'status_code': 403}
            elif response.status_code == 429:
                return {'success': False, 'error': 'Rate limited - Too many requests. Wait 1-2 minutes and try again.', 'status_code': 429}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}', 'details': response.text}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}
    
    def get_named_locations(self):
        """
        Get all Named Locations with full details and associated policies
        Returns the pre-fetched and enhanced locations data
        """
        # First ensure we have fetched policies (which populates locations)
        if not self._get_cached('policies'):
            result = self.get_conditional_access_policies()
            if not result.get('success'):
                return result
        
        # Get locations from cache
        cache_key = self._get_cache_key('named_locations')
        if cache_key in CAPService._named_locations_cache:
            locations, _ = CAPService._named_locations_cache[cache_key]
            
            # Convert to list for frontend
            locations_list = list(locations.values())
            
            return {
                'success': True,
                'locations': locations_list,
                'total_count': len(locations_list),
                'tenant_id': self.tenant_id
            }
        
        return {
            'success': False,
            'error': 'Named Locations not available. Fetch policies first.'
        }
    
    def _extract_ids_from_policy(self, policy):
        """Extract all user and group IDs from a policy for batch resolution"""
        user_ids = set()
        group_ids = set()
        policy_name = policy.get('displayName', 'Unknown')
        
        try:
            policy_detail_raw = policy.get('policyDetail', [])
            
            if isinstance(policy_detail_raw, list) and len(policy_detail_raw) > 0:
                policy_detail = policy_detail_raw[0]
            else:
                return user_ids, group_ids
            
            if isinstance(policy_detail, str):
                detail = json.loads(policy_detail)
            elif isinstance(policy_detail, dict):
                detail = policy_detail
            else:
                return user_ids, group_ids
            
            conditions = detail.get('Conditions', {})
            if not isinstance(conditions, dict):
                return user_ids, group_ids
            
            # Extract from Users
            users = conditions.get('Users', {})
            if isinstance(users, dict):
                for direction in ['Include', 'Exclude']:
                    items = users.get(direction, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                # Extract users
                                item_users = item.get('Users', [])
                                if isinstance(item_users, list):
                                    for uid in item_users:
                                        if uid and isinstance(uid, str):
                                            user_ids.add(uid)
                                
                                # Extract groups
                                item_groups = item.get('Groups', [])
                                if isinstance(item_groups, list):
                                    for gid in item_groups:
                                        if gid and isinstance(gid, str):
                                            group_ids.add(gid)
            
            if user_ids or group_ids:
                print(f"    [*] {policy_name}: extracted {len(user_ids)} users, {len(group_ids)} groups")
            
        except Exception as e:
            print(f"[!] Error extracting IDs from {policy_name}: {e}")
        
        return user_ids, group_ids
    
    def _safe_get(self, obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default
    
    def _extract_from_list_of_dicts(self, list_of_dicts, key):
        result = []
        if not isinstance(list_of_dicts, list):
            return result
        
        for item in list_of_dicts:
            if isinstance(item, dict) and key in item:
                value = item[key]
                if isinstance(value, list):
                    result.extend(value)
                else:
                    result.append(value)
        
        return result
    
    def _parse_cap_policy(self, policy):
        """Parse a Conditional Access Policy into readable format"""
        try:
            policy_detail_raw = policy.get('policyDetail', [])
            
            if isinstance(policy_detail_raw, list):
                if len(policy_detail_raw) == 0:
                    return None
                policy_detail = policy_detail_raw[0]
            elif isinstance(policy_detail_raw, dict):
                policy_detail = policy_detail_raw
            elif isinstance(policy_detail_raw, str):
                policy_detail = policy_detail_raw
            else:
                return None
            
            if isinstance(policy_detail, str):
                try:
                    detail = json.loads(policy_detail)
                except json.JSONDecodeError:
                    return None
            elif isinstance(policy_detail, dict):
                detail = policy_detail
            else:
                return None
            
            conditions = self._safe_get(detail, 'Conditions', {})
            if not isinstance(conditions, dict):
                conditions = {}
            
            # Extract grant controls
            controls_raw = detail.get('Controls', [])
            grant_controls = []
            controls_operator = 'OR'
            
            if isinstance(controls_raw, list):
                for control_item in controls_raw:
                    if isinstance(control_item, dict):
                        ctrl = control_item.get('Control', [])
                        if isinstance(ctrl, list):
                            grant_controls.extend(ctrl)
                        else:
                            grant_controls.append(ctrl)
                        if 'Operator' in control_item:
                            controls_operator = control_item.get('Operator', 'OR')
                    elif isinstance(control_item, str):
                        grant_controls.append(control_item)
            elif isinstance(controls_raw, dict):
                grant_controls = controls_raw.get('Control', [])
                controls_operator = controls_raw.get('Operator', 'OR')
            
            # Parse applications
            apps = self._safe_get(conditions, 'Applications', {})
            if isinstance(apps, dict):
                include_list = apps.get('Include', [])
                exclude_list = apps.get('Exclude', [])
                include_apps = self._extract_from_list_of_dicts(include_list, 'Applications')
                exclude_apps = self._extract_from_list_of_dicts(exclude_list, 'Applications')
            else:
                include_apps = []
                exclude_apps = []
            
            # Parse users
            users = self._safe_get(conditions, 'Users', {})
            if isinstance(users, dict):
                include_list = users.get('Include', [])
                exclude_list = users.get('Exclude', [])
                
                include_users_ids = self._extract_from_list_of_dicts(include_list, 'Users')
                include_groups = self._extract_from_list_of_dicts(include_list, 'Groups')
                include_roles = self._extract_from_list_of_dicts(include_list, 'Roles')
                
                exclude_users_ids = self._extract_from_list_of_dicts(exclude_list, 'Users')
                exclude_groups = self._extract_from_list_of_dicts(exclude_list, 'Groups')
                exclude_roles = self._extract_from_list_of_dicts(exclude_list, 'Roles')
            else:
                include_users_ids = []
                include_groups = []
                include_roles = []
                exclude_users_ids = []
                exclude_groups = []
                exclude_roles = []
            
            # Resolve names from EntityCacheService (already pre-fetched)
            include_users_resolved = [self._resolve_user_name(uid) for uid in include_users_ids]
            include_groups_resolved = [self._resolve_group_name(gid) for gid in include_groups]
            include_roles_resolved = [self._resolve_role_name(rid) for rid in include_roles]
            
            exclude_users_resolved = [self._resolve_user_name(uid) for uid in exclude_users_ids]
            exclude_groups_resolved = [self._resolve_group_name(gid) for gid in exclude_groups]
            exclude_roles_resolved = [self._resolve_role_name(rid) for rid in exclude_roles]
            
            # Parse locations
            locations = self._safe_get(conditions, 'Locations', {})
            if isinstance(locations, dict):
                include_list = locations.get('Include', [])
                exclude_list = locations.get('Exclude', [])
                include_location_ids = self._extract_from_list_of_dicts(include_list, 'Locations')
                exclude_location_ids = self._extract_from_list_of_dicts(exclude_list, 'Locations')
            else:
                include_location_ids = []
                exclude_location_ids = []
            
            # Resolve location names (from pre-fetched cache)
            include_locations_resolved = [self._resolve_location_name(lid) for lid in include_location_ids]
            exclude_locations_resolved = [self._resolve_location_name(lid) for lid in exclude_location_ids]
            
            # Parse platforms
            platforms = self._safe_get(conditions, 'Platforms', {})
            device_platforms = self._safe_get(conditions, 'DevicePlatforms', {})
            
            if isinstance(device_platforms, dict):
                include_list = device_platforms.get('Include', [])
                exclude_list = device_platforms.get('Exclude', [])
                include_platforms = self._extract_from_list_of_dicts(include_list, 'DevicePlatforms')
                exclude_platforms = self._extract_from_list_of_dicts(exclude_list, 'DevicePlatforms')
            elif isinstance(platforms, dict):
                include_list = platforms.get('Include', [])
                exclude_list = platforms.get('Exclude', [])
                include_platforms = self._extract_from_list_of_dicts(include_list, 'Platforms')
                exclude_platforms = self._extract_from_list_of_dicts(exclude_list, 'Platforms')
            else:
                include_platforms = []
                exclude_platforms = []
            
            # Parse client app types
            client_apps = self._safe_get(conditions, 'ClientApps', {})
            client_types = self._safe_get(conditions, 'ClientTypes', {})
            
            if isinstance(client_types, dict):
                client_app_types = client_types.get('ClientAppTypes', [])
            elif isinstance(client_apps, dict):
                client_app_types = client_apps.get('ClientAppTypes', [])
            else:
                client_app_types = []
            
            # Parse risk levels
            sign_in_risk = self._safe_get(conditions, 'SignInRisk', {})
            user_risk = self._safe_get(conditions, 'UserRisk', {})
            
            parsed = {
                'id': policy.get('objectId'),
                'displayName': policy.get('displayName', 'Unnamed Policy'),
                'state': detail.get('State', 'unknown'),
                'createdDateTime': policy.get('createdDateTime'),
                'modifiedDateTime': policy.get('modifiedDateTime'),
                
                'conditions': {
                    'applications': {
                        'includeApplications': self._resolve_app_ids(include_apps),
                        'excludeApplications': self._resolve_app_ids(exclude_apps),
                        'includeAllApps': 'All' in include_apps
                    },
                    'users': {
                        'includeUsers': {
                            'users': include_users_resolved,
                            'groups': include_groups_resolved,
                            'roles': include_roles_resolved,
                            'allUsers': 'All' in include_users_ids,
                            'allGuestUsers': 'GuestsOrExternalUsers' in include_users_ids
                        },
                        'excludeUsers': {
                            'users': exclude_users_resolved,
                            'groups': exclude_groups_resolved,
                            'roles': exclude_roles_resolved,
                            'allUsers': False,
                            'allGuestUsers': False
                        }
                    },
                    'locations': {
                        'includeLocations': include_locations_resolved,
                        'excludeLocations': exclude_locations_resolved
                    },
                    'platforms': {
                        'includePlatforms': include_platforms,
                        'excludePlatforms': exclude_platforms
                    },
                    'clientAppTypes': client_app_types if isinstance(client_app_types, list) else [],
                    'signInRiskLevels': self._safe_get(sign_in_risk, 'RiskLevels', []) if isinstance(sign_in_risk, dict) else [],
                    'userRiskLevels': self._safe_get(user_risk, 'RiskLevels', []) if isinstance(user_risk, dict) else []
                },
                
                'grantControls': {
                    'operator': controls_operator,
                    'builtInControls': self._parse_grant_controls(grant_controls),
                    'customControls': []
                },
                
                'sessionControls': self._parse_session_controls(controls_raw),
                'analysis': self._analyze_policy(detail, grant_controls)
            }
            
            return parsed
            
        except Exception as e:
            print(f"[!] Error parsing policy: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _resolve_app_ids(self, app_ids):
        app_map = {
            'All': 'All Applications',
            'Office365': 'Office 365',
            'MicrosoftAdminPortals': 'Microsoft Admin Portals',
            '00000002-0000-0ff1-ce00-000000000000': 'Office 365 Exchange Online',
            '00000003-0000-0ff1-ce00-000000000000': 'Office 365 SharePoint Online',
            '00000004-0000-0ff1-ce00-000000000000': 'Microsoft Skype for Business',
            '0000000c-0000-0000-c000-000000000000': 'Microsoft App Access Panel',
            '00000002-0000-0000-c000-000000000000': 'Microsoft Graph (Legacy)',
            '00000003-0000-0000-c000-000000000000': 'Microsoft Graph',
            '797f4846-ba00-4fd7-ba43-dac1f8f63013': 'Azure Service Management API',
            'd4ebce55-015a-49b5-a083-c84d1797ae8c': 'Microsoft Intune Enrollment',
            '0000000a-0000-0000-c000-000000000000': 'Microsoft Intune',
            'cc15fd57-2c6c-4117-a88c-83b1d56b4bbe': 'Microsoft Teams Services',
            '1fec8e78-bce4-4aaf-ab1b-5451cc387264': 'Microsoft Teams',
            '5e3ce6c0-2b1f-4285-8d4b-75ee78787346': 'Microsoft Teams Web Client',
            '8c59ead7-d703-4a27-9e55-c96a0054c8d2': 'Microsoft Office',
        }
        
        resolved = []
        for app_id in app_ids:
            if app_id in app_map:
                resolved.append({'id': app_id, 'name': app_map[app_id]})
            else:
                resolved.append({'id': app_id, 'name': app_id})
        
        return resolved
    
    def _parse_grant_controls(self, controls):
        control_map = {
            'Mfa': 'Require MFA',
            'CompliantDevice': 'Require Compliant Device',
            'DomainJoinedDevice': 'Require Hybrid Azure AD Joined Device',
            'ApprovedApplication': 'Require Approved Client App',
            'CompliantApplication': 'Require App Protection Policy',
            'PasswordChange': 'Require Password Change',
            'Block': 'Block Access'
        }
        
        parsed = []
        for control in controls:
            if control in control_map:
                parsed.append(control_map[control])
            else:
                parsed.append(control)
        
        return parsed
    
    def _parse_session_controls(self, controls_raw):
        session = {}
        
        if isinstance(controls_raw, list):
            for control_item in controls_raw:
                if isinstance(control_item, dict) and 'Session' in control_item:
                    session = self._extract_session_details(control_item['Session'])
                    break
        elif isinstance(controls_raw, dict) and 'Session' in controls_raw:
            session = self._extract_session_details(controls_raw['Session'])
        
        return session
    
    def _extract_session_details(self, session_controls):
        session = {}
        
        if 'SignInFrequency' in session_controls:
            sif = session_controls['SignInFrequency']
            session['signInFrequency'] = {
                'value': sif.get('Value'),
                'type': sif.get('Type'),
                'isEnabled': sif.get('IsEnabled', False)
            }
        
        if 'PersistentBrowser' in session_controls:
            pb = session_controls['PersistentBrowser']
            session['persistentBrowser'] = {
                'mode': pb.get('Mode'),
                'isEnabled': pb.get('IsEnabled', False)
            }
        
        if 'CloudAppSecurity' in session_controls:
            cas = session_controls['CloudAppSecurity']
            session['cloudAppSecurity'] = {
                'cloudAppSecurityType': cas.get('CloudAppSecurityType'),
                'isEnabled': cas.get('IsEnabled', False)
            }
        
        return session
    
    def _analyze_policy(self, detail, grant_controls):
        analysis = {
            'severity': 'info',
            'findings': [],
            'bypass_opportunities': []
        }
        
        conditions = self._safe_get(detail, 'Conditions', {})
        if not isinstance(conditions, dict):
            conditions = {}
        
        state = self._safe_get(detail, 'State', '')
        
        if isinstance(state, str) and state.lower() in ['disabled', 'enabledforreportingbutnotenforced']:
            analysis['findings'].append({
                'type': 'warning',
                'message': f'Policy is {state} - not actively enforcing'
            })
            analysis['severity'] = 'low'
        
        # Check legacy auth
        client_apps = self._safe_get(conditions, 'ClientApps', {})
        client_types = self._safe_get(conditions, 'ClientTypes', {})
        
        if isinstance(client_types, dict):
            client_app_types = client_types.get('ClientAppTypes', [])
        elif isinstance(client_apps, dict):
            client_app_types = client_apps.get('ClientAppTypes', [])
        else:
            client_app_types = []
        
        if not isinstance(client_app_types, list):
            client_app_types = []
        
        if 'ExchangeActiveSync' not in client_app_types and 'Other' not in client_app_types:
            analysis['bypass_opportunities'].append({
                'type': 'legacy_auth',
                'message': 'Policy may not block legacy authentication protocols',
                'technique': 'Use legacy auth clients (IMAP, POP3, SMTP AUTH)'
            })
        
        # Check location exclusions
        locations = self._safe_get(conditions, 'Locations', {})
        if isinstance(locations, dict):
            exclude_list = locations.get('Exclude', [])
            exclude_locations = self._extract_from_list_of_dicts(exclude_list, 'Locations')
        else:
            exclude_locations = []
        
        if exclude_locations:
            analysis['findings'].append({
                'type': 'info',
                'message': f'Policy excludes {len(exclude_locations)} location(s)'
            })
            analysis['bypass_opportunities'].append({
                'type': 'location_bypass',
                'message': 'Traffic from excluded locations bypasses this policy',
                'technique': 'Route traffic through excluded locations/VPNs'
            })
        
        # Check platform gaps
        platforms = self._safe_get(conditions, 'Platforms', {})
        device_platforms = self._safe_get(conditions, 'DevicePlatforms', {})
        
        if isinstance(device_platforms, dict):
            include_list = device_platforms.get('Include', [])
            include_platforms = self._extract_from_list_of_dicts(include_list, 'DevicePlatforms')
        elif isinstance(platforms, dict):
            include_list = platforms.get('Include', [])
            include_platforms = self._extract_from_list_of_dicts(include_list, 'Platforms')
        else:
            include_platforms = []
        
        if include_platforms and 'All' not in include_platforms:
            missing = set(['Android', 'iOS', 'Windows', 'macOS', 'Linux']) - set(include_platforms)
            if missing:
                analysis['bypass_opportunities'].append({
                    'type': 'platform_bypass',
                    'message': f'Policy does not cover: {", ".join(missing)}',
                    'technique': f'Access from {list(missing)[0]} device'
                })
        
        # Check app exclusions
        apps = self._safe_get(conditions, 'Applications', {})
        if isinstance(apps, dict):
            exclude_list = apps.get('Exclude', [])
            exclude_apps = self._extract_from_list_of_dicts(exclude_list, 'Applications')
        else:
            exclude_apps = []
        
        if exclude_apps:
            analysis['findings'].append({
                'type': 'info',
                'message': f'Policy excludes {len(exclude_apps)} application(s)'
            })
        
        # Check grant controls
        if 'Mfa' not in grant_controls and 'Block' not in grant_controls:
            analysis['findings'].append({
                'type': 'warning',
                'message': 'Policy does not require MFA or block access'
            })
        
        # Check user exclusions
        users = self._safe_get(conditions, 'Users', {})
        if isinstance(users, dict):
            exclude_list = users.get('Exclude', [])
            exclude_users = self._extract_from_list_of_dicts(exclude_list, 'Users')
            exclude_groups = self._extract_from_list_of_dicts(exclude_list, 'Groups')
            exclude_roles = self._extract_from_list_of_dicts(exclude_list, 'Roles')
        else:
            exclude_users = []
            exclude_groups = []
            exclude_roles = []
        
        if exclude_users or exclude_groups or exclude_roles:
            analysis['findings'].append({
                'type': 'info',
                'message': 'Policy has user/group/role exclusions'
            })
            analysis['bypass_opportunities'].append({
                'type': 'user_bypass',
                'message': 'Excluded users/groups bypass this policy',
                'technique': 'Compromise excluded accounts'
            })
        
        # Severity
        if len(analysis['bypass_opportunities']) >= 3:
            analysis['severity'] = 'high'
        elif len(analysis['bypass_opportunities']) >= 1:
            analysis['severity'] = 'medium'
        elif len(analysis['findings']) >= 2:
            analysis['severity'] = 'low'
        
        return analysis
    
    def get_authorization_policy(self):
        if not self.aad_token:
            if not self._get_aad_graph_token():
                return {'success': False, 'error': 'Could not obtain Azure AD Graph token'}
        
        url = f"{self.AZURE_AD_GRAPH_URL}/{self.tenant_id}/policies/authorizationPolicy?api-version={self.API_VERSION}"
        headers = {'Authorization': f'Bearer {self.aad_token}', 'Content-Type': 'application/json'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return {'success': True, 'policy': response.json()}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}', 'details': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_policies_raw(self):
        if not self.aad_token:
            if not self._get_aad_graph_token():
                return {'success': False, 'error': 'Could not obtain Azure AD Graph token'}
        
        url = f"{self.AZURE_AD_GRAPH_URL}/{self.tenant_id}/policies?api-version={self.API_VERSION}"
        headers = {'Authorization': f'Bearer {self.aad_token}', 'Content-Type': 'application/json'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return {'success': True, 'policies': response.json().get('value', [])}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_named_locations_via_msgraph(self):
        """
        Get Named Locations via MS Graph API (requires Policy.Read.All)
        Use this for additional details or as fallback
        """
        if not self.ms_graph_token:
            if not self._get_ms_graph_token():
                return {
                    'success': False, 
                    'error': 'Could not obtain MS Graph token',
                    'requires_scope': 'Policy.Read.All'
                }
        
        url = f"{self.MS_GRAPH_URL}/identity/conditionalAccess/namedLocations"
        headers = {
            'Authorization': f'Bearer {self.ms_graph_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'locations': data.get('value', [])
                }
            elif response.status_code == 403:
                self._warnings.append({
                    'type': 'scope_missing',
                    'message': 'MS Graph Named Locations requires Policy.Read.All scope',
                    'hint': 'Generate a token with Policy.Read.All scope for full location details'
                })
                return {
                    'success': False,
                    'error': 'Forbidden - requires Policy.Read.All scope',
                    'status_code': 403,
                    'requires_scope': 'Policy.Read.All'
                }
            else:
                return {
                    'success': False,
                    'error': f'API Error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
