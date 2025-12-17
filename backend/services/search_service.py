"""
Search service - Microsoft Search API + Sensitive Data Discovery
Cross-app search and pattern detection for red team intelligence
"""
import requests
import re
from flask import current_app


class SearchService:
    
    PATTERNS = {
        'aws_access_key': {
            'regex': r'AKIA[0-9A-Z]{16}',
            'severity': 'critical',
            'description': 'AWS Access Key ID'
        },
        'aws_secret_key': {
            'regex': r'aws_secret_access_key\s*=\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
            'severity': 'critical',
            'description': 'AWS Secret Access Key'
        },
        'azure_storage_connection': {
            'regex': r'DefaultEndpointsProtocol=https;AccountName=([^;]+);AccountKey=([^;]+)',
            'severity': 'critical',
            'description': 'Azure Storage Connection String'
        },
        'azure_storage_key': {
            'regex': r'AccountKey=([A-Za-z0-9+/=]{88})',
            'severity': 'critical',
            'description': 'Azure Storage Account Key'
        },
        'private_key_rsa': {
            'regex': r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----',
            'severity': 'critical',
            'description': 'Private Key (RSA/EC/OpenSSH)'
        },
        'private_key_pkcs': {
            'regex': r'-----BEGIN PRIVATE KEY-----',
            'severity': 'critical',
            'description': 'Private Key (PKCS#8)'
        },
        'jwt_token': {
            'regex': r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
            'severity': 'high',
            'description': 'JWT Token'
        },
        'password_assignment': {
            'regex': r'(?:password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
            'severity': 'high',
            'description': 'Hardcoded Password'
        },
        'api_key_generic': {
            'regex': r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-]{20,})["\']',
            'severity': 'high',
            'description': 'API Key'
        },
        'slack_token': {
            'regex': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24,}',
            'severity': 'high',
            'description': 'Slack Token'
        },
        'github_token': {
            'regex': r'ghp_[A-Za-z0-9]{36}',
            'severity': 'high',
            'description': 'GitHub Personal Access Token'
        },
        'stripe_api_key': {
            'regex': r'sk_live_[0-9a-zA-Z]{24,}',
            'severity': 'high',
            'description': 'Stripe Live API Key'
        },
        'database_connection': {
            'regex': r'(?:mysql|postgresql|mongodb|redis)://[^:]+:[^@]+@[^/]+/[^\s]+',
            'severity': 'high',
            'description': 'Database Connection String'
        },
        'ssn_us': {
            'regex': r'\b\d{3}-\d{2}-\d{4}\b',
            'severity': 'medium',
            'description': 'US Social Security Number'
        },
        'credit_card': {
            'regex': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'severity': 'medium',
            'description': 'Credit Card Number'
        },
        'email_address': {
            'regex': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'severity': 'low',
            'description': 'Email Address'
        },
        'ipv4_address': {
            'regex': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'severity': 'low',
            'description': 'IPv4 Address'
        },
        # PowerShell Credentials Patterns (Multi-line)
        'powershell_credentials_block': {
            'regex': r'(?:\$\w*[Uu]ser(?:\w*name)?\s*=\s*["\']([^"\']+)["\'])[\s\S]{0,200}(?:\$\w*[Pp](?:ass)?[Ww](?:or)?d\w*\s*=\s*(?:ConvertTo-SecureString|ConvertFrom-SecureString|\$\w+|["\'][^"\']+["\']))',
            'severity': 'high',
            'description': 'PowerShell Credentials Block (Username + Password)'
        },
        'convertto_securestring': {
            'regex': r'ConvertTo-SecureString\s+-String\s+["\']([^"\']{6,})["\']',
            'severity': 'high',
            'description': 'PowerShell ConvertTo-SecureString with Password'
        },
        'pscredential_object': {
            'regex': r'New-Object\s+(?:System\.Management\.Automation\.)?PSCredential\s*\(\s*["\']?([^"\'(),]+)["\']?\s*,\s*([^\)]+)\)',
            'severity': 'high',
            'description': 'PowerShell PSCredential Object'
        }
    }
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = current_app.config['GRAPH_API_BASE']
        self.beta_url = 'https://graph.microsoft.com/beta'
        self.timeout = current_app.config['GRAPH_API_TIMEOUT']
    
    def _make_request(self, endpoint, method='GET', use_beta=False, **kwargs):
        base = self.beta_url if use_beta else self.base_url
        url = f"{base}/{endpoint}"
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
                            'data': response.json()
                        }
                    except:
                        return {
                            'success': True,
                            'data': {}
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
    
    def microsoft_search(self, query, entity_types=None, size=25):
        """
        Microsoft Search API - Search across M365 apps
        
        Args:
            query: Search keywords
            entity_types: List of types to search ['driveItem', 'message', 'chatMessage', 'site', 'list']
            size: Number of results per entity type (max 25)
        
        Returns:
            Dict with results grouped by entity type
        """
        if not entity_types:
            entity_types = ['driveItem', 'message', 'chatMessage']
        
        all_results = {
            'files': [],
            'emails': [],
            'teams': [],
            'sites': []
        }
        
        for entity_type in entity_types:
            search_request = {
                'requests': [{
                    'entityTypes': [entity_type],
                    'query': {
                        'queryString': query
                    },
                    'size': min(size, 25)
                }]
            }
            
            result = self._make_request('search/query', method='POST', use_beta=True, json=search_request)
            
            if result['success']:
                formatted = self._format_search_results(result['data'])
                
                all_results['files'].extend(formatted.get('files', []))
                all_results['emails'].extend(formatted.get('emails', []))
                all_results['teams'].extend(formatted.get('teams', []))
                all_results['sites'].extend(formatted.get('sites', []))
        
        return {
            'success': True,
            'results': all_results,
            'total_count': sum(len(v) for v in all_results.values())
        }
    
    def _format_search_results(self, data):
        """Format Microsoft Search results by entity type"""
        formatted = {
            'files': [],
            'emails': [],
            'teams': [],
            'sites': []
        }
        
        for response in data.get('value', []):
            hits_container = response.get('hitsContainers', [])
            
            for container in hits_container:
                hits = container.get('hits', [])
                
                for hit in hits:
                    resource = hit.get('resource', {})
                    hit_resource_type = resource.get('@odata.type', '')
                    
                    # Debug logging
                    if hit_resource_type:
                        print(f"[SEARCH DEBUG] Resource type: {hit_resource_type}")
                        if 'site' in hit_resource_type.lower() or 'list' in hit_resource_type.lower():
                            print(f"[SEARCH DEBUG] SharePoint resource found: {resource.get('name') or resource.get('displayName')}")
                    
                    if 'driveItem' in hit_resource_type:
                        formatted['files'].append({
                            'id': resource.get('id'),
                            'name': resource.get('name'),
                            'webUrl': resource.get('webUrl'),
                            'size': resource.get('size', 0),
                            'lastModifiedDateTime': resource.get('lastModifiedDateTime'),
                            'createdBy': resource.get('createdBy', {}).get('user', {}).get('displayName', 'Unknown'),
                            'type': 'file'
                        })
                    
                    elif 'message' in hit_resource_type:
                        formatted['emails'].append({
                            'id': resource.get('id'),
                            'subject': resource.get('subject', 'No Subject'),
                            'from': resource.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                            'receivedDateTime': resource.get('receivedDateTime'),
                            'webUrl': resource.get('webLink'),
                            'bodyPreview': resource.get('bodyPreview', '')[:200],
                            'type': 'email'
                        })
                    
                    elif 'chatMessage' in hit_resource_type:
                        formatted['teams'].append({
                            'id': resource.get('id'),
                            'message': resource.get('body', {}).get('content', '')[:200],
                            'from': resource.get('from', {}).get('user', {}).get('displayName', 'Unknown'),
                            'createdDateTime': resource.get('createdDateTime'),
                            'webUrl': resource.get('webUrl'),
                            'type': 'teams'
                        })
                    
                    # SharePoint sites and lists
                    elif 'site' in hit_resource_type or 'list' in hit_resource_type:
                        formatted['sites'].append({
                            'id': resource.get('id'),
                            'name': resource.get('name') or resource.get('displayName', 'Unnamed Site'),
                            'webUrl': resource.get('webUrl'),
                            'description': resource.get('description', ''),
                            'lastModifiedDateTime': resource.get('lastModifiedDateTime'),
                            'createdDateTime': resource.get('createdDateTime'),
                            'type': 'site'
                        })
        
        return formatted
    
    def _extract_smart_context(self, content, match_start, match_end, window_chars=300):
        """
        Extract context around match with complete lines
        
        Args:
            content: Full content
            match_start: Match start position
            match_end: Match end position  
            window_chars: Character window size (default 300)
        
        Returns:
            Context string with complete lines
        """
        # Expand window
        start = max(0, match_start - window_chars)
        end = min(len(content), match_end + window_chars)
        
        # Find line boundaries to avoid truncation
        while start > 0 and content[start] not in ('\n', '\r'):
            start -= 1
        while end < len(content) and content[end] not in ('\n', '\r'):
            end += 1
        
        # Extract context with complete lines
        context = content[start:end].strip()
        
        # Limit to max 10 lines to avoid huge context
        lines = context.split('\n')
        if len(lines) > 10:
            # Keep 5 lines before and 5 lines after match
            match_line_idx = None
            for i, line in enumerate(lines):
                if match_start >= start and match_start <= end:
                    if content[start:].find(line) <= match_start - start <= content[start:].find(line) + len(line):
                        match_line_idx = i
                        break
            
            if match_line_idx:
                start_line = max(0, match_line_idx - 5)
                end_line = min(len(lines), match_line_idx + 6)
                context = '\n'.join(lines[start_line:end_line])
        
        return context
    
    def _escalate_severity(self, finding, context):
        """
        Smart severity escalation based on context
        
        Args:
            finding: Finding dict with pattern, severity, etc.
            context: Context string around finding
        
        Returns:
            Escalated severity if applicable
        """
        severity = finding['severity']
        description = finding['description']
        pattern_name = finding['pattern']
        context_lower = context.lower()
        
        # Escalate email to HIGH if password/credentials in context
        if severity == 'low' and pattern_name == 'email_address':
            credential_keywords = [
                'password', 'passwd', 'pwd', '$pwd', '$pw', '$pword',
                'convertto-securestring', 'securestring', 'credential',
                'pscredential', 'new-object', 'api-key', 'api_key',
                'secret', 'token', 'authorization', 'bearer'
            ]
            
            if any(keyword in context_lower for keyword in credential_keywords):
                severity = 'high'
                finding['description'] += ' (with associated credentials)'
        
        # Escalate API key mentions to HIGH if in auth context
        if 'api' in pattern_name and severity != 'critical':
            auth_keywords = ['authorization', 'bearer', 'x-api-key', 'apikey']
            if any(keyword in context_lower for keyword in auth_keywords):
                severity = 'high'
        
        return severity
    
    def _group_related_findings(self, findings, proximity_threshold=200):
        """
        Group related findings that are close together
        
        Args:
            findings: List of findings
            proximity_threshold: Max distance to consider related (chars)
        
        Returns:
            Grouped findings with combined context
        """
        if len(findings) <= 1:
            return findings
        
        # Sort by position
        sorted_findings = sorted(findings, key=lambda f: f['position'])
        
        grouped = []
        skip_indices = set()
        
        for i, finding in enumerate(sorted_findings):
            if i in skip_indices:
                continue
            
            # Find related findings within threshold
            related = []
            for j, other in enumerate(sorted_findings[i+1:], start=i+1):
                if j in skip_indices:
                    continue
                
                distance = abs(other['position'] - finding['position'])
                if distance <= proximity_threshold:
                    related.append(other)
                    skip_indices.add(j)
                else:
                    break  # Sorted, so no need to check further
            
            if related:
                # Combine into high-severity grouped finding
                all_descriptions = [finding['description']] + [r['description'] for r in related]
                combined_description = f"{finding['description']} + {len(related)} related finding(s)"
                
                # Use highest severity
                all_severities = [finding['severity']] + [r['severity'] for r in related]
                severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                highest_severity = max(all_severities, key=lambda s: severity_order.get(s, 0))
                
                # Expand context to cover all findings
                min_pos = min([finding['position']] + [r['position'] for r in related])
                max_pos = max([finding['position'] + len(finding['match'])] + 
                             [r['position'] + len(r['match']) for r in related])
                
                grouped.append({
                    'pattern': 'grouped_credentials',
                    'description': combined_description,
                    'severity': highest_severity,
                    'match': finding['match'],  # Keep first match
                    'context': finding['context'],  # Already expanded
                    'position': finding['position'],
                    'grouped_count': len(related) + 1,
                    'grouped_items': all_descriptions
                })
            else:
                grouped.append(finding)
        
        return grouped
    
    def scan_for_patterns(self, content, enabled_patterns=None):
        """
        Scan text content for sensitive data patterns
        
        Args:
            content: Text content to scan
            enabled_patterns: List of pattern names to check (None = all)
        
        Returns:
            List of findings with severity and context
        """
        if enabled_patterns is None:
            patterns_to_check = self.PATTERNS
        else:
            patterns_to_check = {k: v for k, v in self.PATTERNS.items() if k in enabled_patterns}
        
        findings = []
        
        for pattern_name, pattern_info in patterns_to_check.items():
            # Use MULTILINE and DOTALL for multi-line patterns
            flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
            matches = re.finditer(pattern_info['regex'], content, flags)
            
            for match in matches:
                # Extract smart context with complete lines
                context = self._extract_smart_context(content, match.start(), match.end())
                
                finding = {
                    'pattern': pattern_name,
                    'description': pattern_info['description'],
                    'severity': pattern_info['severity'],
                    'match': match.group(0),
                    'context': context,
                    'position': match.start()
                }
                
                # Apply severity escalation
                finding['severity'] = self._escalate_severity(finding, context)
                
                findings.append(finding)
        
        # Group related findings
        findings = self._group_related_findings(findings)
        
        return findings
    
    def scan_onedrive_files(self, enabled_patterns=None, max_files=100):
        """
        Scan OneDrive files for sensitive patterns
        
        Args:
            enabled_patterns: List of pattern names to check
            max_files: Maximum number of files to scan
        
        Returns:
            Dict with findings grouped by file
        """
        result = self._make_request('me/drive/root/children')
        
        if not result['success']:
            return result
        
        items = result['data'].get('value', [])
        files_to_scan = [item for item in items if not item.get('folder')][:max_files]
        
        all_findings = []
        scanned_count = 0
        
        for file_item in files_to_scan:
            file_id = file_item.get('id')
            file_name = file_item.get('name', 'Unknown')
            
            if file_item.get('size', 0) > 5 * 1024 * 1024:
                continue
            
            download_result = self._make_request(f'me/drive/items/{file_id}')
            if not download_result['success']:
                continue
            
            download_url = download_result['data'].get('@microsoft.graph.downloadUrl')
            if not download_url:
                continue
            
            try:
                content_response = requests.get(download_url, timeout=10)
                if content_response.status_code != 200:
                    continue
                
                try:
                    content = content_response.text
                except:
                    continue
                
                findings = self.scan_for_patterns(content, enabled_patterns)
                
                if findings:
                    all_findings.append({
                        'file_id': file_id,
                        'file_name': file_name,
                        'file_size': file_item.get('size', 0),
                        'web_url': file_item.get('webUrl'),
                        'findings': findings,
                        'findings_count': len(findings)
                    })
                
                scanned_count += 1
                
            except Exception:
                continue
        
        return {
            'success': True,
            'files_scanned': scanned_count,
            'files_with_findings': len(all_findings),
            'results': all_findings,
            'total_findings': sum(f['findings_count'] for f in all_findings)
        }
    
    def get_patterns(self):
        """Get all available patterns with metadata"""
        return {
            'success': True,
            'patterns': [
                {
                    'name': name,
                    'description': info['description'],
                    'severity': info['severity'],
                    'regex': info['regex']
                }
                for name, info in self.PATTERNS.items()
            ]
        }
