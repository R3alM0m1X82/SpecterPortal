<template>
  <div :class="['p-8 min-h-screen', bgContainer]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 :class="['text-3xl font-bold', textPrimary]">Virtual Machines</h1>
        <p :class="['text-sm mt-1', textSecondary]">Azure VM enumeration and control</p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Subscription Selector -->
        <select 
          v-model="selectedSubscription" 
          @change="loadVMs"
          :class="[
            'px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:outline-none',
            isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
          ]"
        >
          <option value="">Select Subscription</option>
          <option v-for="sub in subscriptions" :key="sub.id" :value="sub.id">
            {{ sub.displayName }}
          </option>
        </select>
        <!-- Refresh Button -->
        <button 
          @click="forceRefresh" 
          :disabled="loading || !selectedSubscription"
          class="refresh-btn"
        >
          <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ loading ? 'Loading...' : 'Refresh' }}</span>
        </button>
      </div>
    </div>

    <!-- Cross-User Token Banner -->
    <div 
      v-if="showCrossUserBanner && !bannerDismissed" 
      class="mb-6 bg-gradient-to-r from-amber-900/30 to-orange-900/30 border-l-4 border-amber-500 rounded-lg overflow-hidden shadow-xl"
    >
      <div class="p-5">
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-4 flex-1">
            <div class="flex-shrink-0 mt-0.5">
              <div class="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
                <svg class="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            
            <div class="flex-1">
              <div class="flex items-center space-x-2 mb-2">
                <h3 class="text-lg font-semibold text-amber-200">No ARM Token Available</h3>
                <span class="px-2 py-0.5 text-xs font-medium bg-amber-500/30 text-amber-300 rounded-full">
                  Cross-User Token Available
                </span>
              </div>
              
              <p class="text-sm text-gray-300 mb-3">
                No ARM token found for <span class="font-mono text-cyan-400">{{ currentUserUPN }}</span>
              </p>
              
              <div class="text-sm text-gray-400 mb-4">
                However, ARM tokens from other users are available. You can activate one to access Azure resources:
              </div>
              
              <div class="space-y-2">
                <div 
                  v-for="token in crossUserTokens.slice(0, 3)" 
                  :key="token.token_id"
                  class="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 hover:border-amber-500/50 transition-all"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center space-x-2 mb-1">
                        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span class="font-mono text-sm text-blue-400">{{ token.upn }}</span>
                      </div>
                      <div class="flex items-center space-x-3 text-xs text-gray-500">
                        <span>Token ID: <span class="font-mono text-gray-400">#{{ token.token_id }}</span></span>
                        <span v-if="token.expires_at">Expires: {{ formatTokenExpiry(token.expires_at) }}</span>
                      </div>
                    </div>
                    
                    <button
                      @click="activateCrossUserToken(token.token_id)"
                      class="ml-4 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center space-x-2 shadow-lg hover:shadow-xl"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Use This Token</span>
                    </button>
                  </div>
                </div>
              </div>
              
              <div v-if="crossUserTokens.length > 3" class="text-xs text-gray-500 mt-2">
                + {{ crossUserTokens.length - 3 }} more token(s) available
              </div>
            </div>
          </div>
          
          <button 
            @click="dismissCrossUserBanner"
            class="flex-shrink-0 ml-4 text-gray-400 hover:text-gray-200 transition-colors"
            title="Dismiss"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" :class="[isDark ? 'bg-red-900/50 border-red-700 text-red-200' : 'bg-red-100 border-red-300 text-red-800', 'border px-4 py-3 rounded-lg mb-4']">
      <div class="flex items-center">
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- No Subscription Selected -->
    <div v-if="!selectedSubscription" class="text-center py-12">
      <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 :class="['text-lg font-semibold mb-2', textTertiary]">Select a Subscription</h3>
      <p :class="[textPlaceholder]">Choose a subscription from the dropdown to view Virtual Machines</p>
    </div>

    <!-- Content with Tabs -->
    <div v-else-if="!loading && vms.length > 0">
      <!-- Tabs Navigation -->
      <div :class="[bgPrimary, borderPrimary, 'rounded-t-lg border-t border-l border-r']">
        <div class="flex border-b" :class="[isDark ? 'border-gray-700' : 'border-gray-300']">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="[
              'px-6 py-3 font-medium transition-colors relative',
              currentTab === tab.id
                ? (isDark ? 'text-blue-400 bg-gray-750' : 'text-blue-600 bg-gray-50')
                : (isDark ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-750' : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50')
            ]"
          >
            {{ tab.name }}
            <div 
              v-if="currentTab === tab.id" 
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"
            ></div>
          </button>
        </div>
      </div>

      <!-- Tab Content -->
      <div :class="[bgPrimary, borderPrimary, 'rounded-b-lg border-b border-l border-r']">
        <!-- Overview Tab -->
        <div v-if="currentTab === 'overview'" class="overflow-x-auto">
          <table class="w-full">
            <thead :class="[bgSecondary]">
              <tr>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Name</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Subscription</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Resource Group</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Location</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Status</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Operating System</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Size</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Public IP Address</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Disks</th>
                <th :class="['px-6 py-3 text-right text-xs font-medium uppercase tracking-wider', textTertiary]">Actions</th>
              </tr>
            </thead>
            <tbody :class="['divide-y', isDark ? 'divide-gray-700' : 'divide-gray-300']">
              <tr 
                v-for="vm in vms" 
                :key="vm.id" 
                @click="selectVM(vm)"
                :class="[
                  isDark ? 'hover:bg-gray-750' : 'hover:bg-gray-100',
                  selectedVM?.id === vm.id ? 'ring-2 ring-blue-500' : '',
                  'transition-all cursor-pointer'
                ]"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10">
                      <svg viewBox="0 0 18 18" class="h-10 w-10">
                        <defs>
                          <linearGradient id="vmGradient1" x1="8.86" y1="13.02" x2="8.86" y2="1.02" gradientUnits="userSpaceOnUse">
                            <stop offset="0" stop-color="#0078d4"/>
                            <stop offset="0.82" stop-color="#5ea0ef"/>
                          </linearGradient>
                          <linearGradient id="vmGradient2" x1="8.86" y1="17.65" x2="8.86" y2="13.02" gradientUnits="userSpaceOnUse">
                            <stop offset="0" stop-color="#1490df"/>
                            <stop offset="0.98" stop-color="#1f56a3"/>
                          </linearGradient>
                        </defs>
                        <rect x="-0.14" y="1.02" width="18" height="12" rx="0.6" fill="url(#vmGradient1)"/>
                        <rect x="0.86" y="2.02" width="16" height="10" rx="0.33" fill="#fff"/>
                        <polygon points="11.86 5.27 11.86 8.76 8.86 10.52 8.86 7.02 11.86 5.27" fill="#0078d4"/>
                        <polygon points="11.86 5.27 8.86 7.03 5.86 5.27 8.86 3.52 11.86 5.27" fill="#83b9f9"/>
                        <polygon points="8.86 7.03 8.86 10.52 5.86 8.76 5.86 5.27 8.86 7.03" fill="#5ea0ef"/>
                        <polygon points="5.86 8.76 8.86 7.02 8.86 10.52 5.86 8.76" fill="#83b9f9" opacity="0.2"/>
                        <polygon points="11.86 8.76 8.86 7.02 8.86 10.52 11.86 8.76" fill="#5ea0ef" opacity="0.2"/>
                        <path d="M12.46,16.65c-1.77-.28-1.84-1.57-1.84-3.63H7.09c0,2.06-.07,3.35-1.84,3.63a1,1,0,0,0-.89,1h9A1,1,0,0,0,12.46,16.65Z" fill="url(#vmGradient2)"/>
                      </svg>
                    </div>
                    <div class="ml-3">
                      <div :class="['text-sm font-medium', textPrimary]">{{ vm.name }}</div>
                      <div :class="['text-xs', textSecondary]">{{ vm.vmId }}</div>
                    </div>
                  </div>
                </td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.subscription || 'N/A' }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.resourceGroup }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.location }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="[getStatusClass(vm.powerState), 'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full']">
                    {{ vm.powerState || 'Unknown' }}
                  </span>
                </td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.osType || 'Unknown' }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.vmSize || 'Unknown' }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.publicIpAddress || '-' }}</td>
                <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ vm.disksCount || 'N/A' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium" @click.stop>
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      v-if="vm.powerState === 'running'"
                      @click="stopVM(vm)"
                      :disabled="actionLoading[vm.id]"
                      class="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                    >
                      Stop
                    </button>
                    <button
                      v-else-if="vm.powerState === 'deallocated' || vm.powerState === 'stopped'"
                      @click="startVM(vm)"
                      :disabled="actionLoading[vm.id]"
                      class="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                    >
                      Start
                    </button>
                    <button
                      @click="restartVM(vm)"
                      :disabled="actionLoading[vm.id] || vm.powerState !== 'running'"
                      class="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                    >
                      Restart
                    </button>
                    <button
                      @click="deallocateVM(vm)"
                      :disabled="actionLoading[vm.id] || vm.powerState === 'deallocated'"
                      class="px-3 py-1 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                    >
                      Deallocate
                    </button>
                    <button
                      @click="goToRunCommand(vm)"
                      class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                    >
                      Run Command
                    </button>
                    <button
                      @click="extractManagedIdentityToken(vm)"
                      class="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded transition-colors"
                    >
                      Extract MI Token
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Run Command Tab -->
        <div v-if="currentTab === 'run-command'" class="p-6">
          <div v-if="!selectedVM" :class="['text-center py-12', textSecondary]">
            <p>Please select a VM from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="mb-4">
              <h3 :class="['text-lg font-semibold', textPrimary]">Run Command on {{ selectedVM.name }}</h3>
              <p :class="['text-sm', textSecondary]">Execute remote commands via Azure VM Agent</p>
            </div>

            <div class="space-y-4">
              <div>
                <label :class="['block text-sm font-medium mb-1', textPrimary]">Command Type</label>
                <select
                  v-model="runCommandType"
                  :class="[bgSecondary, textPrimary, borderSecondary, 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500']"
                >
                  <option value="RunPowerShellScript">PowerShell Script</option>
                  <option value="RunShellScript">Shell Script (Linux)</option>
                </select>
              </div>

              <div>
                <label :class="['block text-sm font-medium mb-1', textPrimary]">Script</label>
                <textarea
                  v-model="runCommandScript"
                  rows="12"
                  :class="[bgSecondary, textPrimary, borderSecondary, 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500 font-mono text-sm']"
                  placeholder="Write-Output 'Hello from Azure VM!'"
                ></textarea>
              </div>

              <div class="flex justify-end space-x-3">
                <button
                  @click="clearRunCommand"
                  :class="[bgSecondary, textPrimary, 'px-4 py-2 rounded-lg hover:bg-opacity-80 transition-colors']"
                >
                  Clear
                </button>
                <button
                  @click="executeRunCommand"
                  :disabled="runCommandExecuting || !runCommandScript"
                  class="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors"
                >
                  {{ runCommandExecuting ? 'Executing...' : 'Execute' }}
                </button>
              </div>

              <div v-if="runCommandOutput" :class="[bgSecondary, 'p-4 rounded-lg mt-4']">
                <h4 :class="['font-semibold mb-2', textPrimary]">Output</h4>
                <pre :class="['text-sm max-h-96 overflow-auto', textPrimary]" style="white-space: pre-wrap; word-wrap: break-word;">{{ runCommandOutput }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- MI Token Tab -->
        <div v-if="currentTab === 'mi-token'" class="p-6">
          <div v-if="!selectedVM" :class="['text-center py-12', textSecondary]">
            <p>Please select a VM from the Overview tab</p>
          </div>
          
          <div v-else>
            <div class="mb-6">
              <h3 :class="['text-lg font-semibold', textPrimary]">Extract Managed Identity Token from {{ selectedVM.name }}</h3>
              <p :class="['text-sm mt-2', textSecondary]">
                Extract access token from VM's Managed Identity via Azure IMDS endpoint (169.254.169.254)
              </p>
            </div>

            <!-- Resource Selection -->
            <div class="mb-4">
              <label :class="['block text-sm font-medium mb-2', textPrimary]">Target Resource</label>
              <select 
                v-model="tokenResource"
                :class="[
                  isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900',
                  'w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500'
                ]"
              >
                <option value="https://management.azure.com/">Azure Resource Manager (ARM)</option>
                <option value="https://graph.microsoft.com/">Microsoft Graph</option>
                <option value="https://storage.azure.com/">Azure Storage</option>
                <option value="https://vault.azure.net/">Azure Key Vault</option>
                <option value="https://database.windows.net/">Azure SQL Database</option>
              </select>
            </div>

            <!-- Extract Button -->
            <button
              @click="performTokenExtraction"
              :disabled="extractingToken"
              :class="[
                'px-6 py-3 rounded font-medium transition-colors',
                extractingToken 
                  ? 'bg-gray-500 cursor-not-allowed' 
                  : 'bg-purple-600 hover:bg-purple-700',
                'text-white'
              ]"
            >
              <span v-if="extractingToken">
                <span class="inline-block animate-spin mr-2">⟳</span>
                Extracting Token...
              </span>
              <span v-else>🔓 Extract Token</span>
            </button>

            <!-- Error Display -->
            <div v-if="tokenError" :class="[isDark ? 'bg-red-900 border-red-700' : 'bg-red-50 border-red-200', 'p-4 rounded-lg border mt-4']">
              <div class="flex items-start">
                <svg class="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                <div>
                  <h4 :class="['font-semibold', isDark ? 'text-red-300' : 'text-red-800']">Token Extraction Failed</h4>
                  <p :class="['text-sm mt-1', isDark ? 'text-red-200' : 'text-red-700']">{{ tokenError }}</p>
                </div>
              </div>
            </div>

            <!-- Success Display -->
            <div v-if="extractedToken" class="mt-6 space-y-4">
              <!-- Success Banner -->
              <div :class="[isDark ? 'bg-green-900 border-green-700' : 'bg-green-50 border-green-200', 'p-4 rounded-lg border']">
                <div class="flex items-start">
                  <svg class="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  <div>
                    <h4 :class="['font-semibold', isDark ? 'text-green-300' : 'text-green-800']">Token Extracted Successfully!</h4>
                    <p :class="['text-sm mt-1', isDark ? 'text-green-200' : 'text-green-700']">
                      Managed Identity token retrieved from {{ selectedVM.name }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Token Details -->
              <div :class="[bgSecondary, 'p-4 rounded-lg']">
                <h4 :class="['font-semibold mb-3', textPrimary]">Token Details</h4>
                <div class="space-y-2 text-sm">
                  <div v-if="extractedToken.identity?.displayName" class="flex justify-between">
                    <span :class="[textSecondary]">Identity Name:</span>
                    <span :class="[textPrimary, 'font-semibold']">
                      {{ extractedToken.identity.displayName }}
                    </span>
                  </div>
                  <div v-if="extractedToken.identity?.oid" class="flex justify-between">
                    <span :class="[textSecondary]">Object ID:</span>
                    <span :class="[textPrimary, 'font-mono text-xs']">
                      {{ extractedToken.identity.oid }}
                    </span>
                  </div>
                  <div v-if="extractedToken.identity" class="flex justify-between">
                    <span :class="[textSecondary]">Client ID:</span>
                    <span :class="[textPrimary, 'font-mono text-xs']">
                      {{ extractedToken.identity.appId || extractedToken.identity.oid || 'N/A' }}
                      <span v-if="!extractedToken.identity.appId && extractedToken.identity.oid" 
                            :class="['ml-2 text-xs', isDark ? 'text-yellow-400' : 'text-yellow-600']">
                        ⚠️ (Graph resolution failed - using Object ID)
                      </span>
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span :class="[textSecondary]">Resource:</span>
                    <span :class="[textPrimary, 'font-mono']">{{ extractedToken.resource }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span :class="[textSecondary]">Expires On:</span>
                    <span :class="[textPrimary]">{{ new Date(parseInt(extractedToken.expires_on) * 1000).toLocaleString() }}</span>
                  </div>
                  <div v-if="extractedToken.claims" class="flex justify-between">
                    <span :class="[textSecondary]">Token Type:</span>
                    <span :class="[textPrimary]">{{ extractedToken.claims.aud || 'N/A' }}</span>
                  </div>
                </div>
              </div>

              <!-- JWT Claims -->
              <div v-if="extractedToken.claims" :class="[bgSecondary, 'p-4 rounded-lg']">
                <h4 :class="['font-semibold mb-3', textPrimary]">JWT Claims</h4>
                <pre :class="['text-xs overflow-auto max-h-64', textPrimary]" style="white-space: pre-wrap;">{{ JSON.stringify(extractedToken.claims, null, 2) }}</pre>
              </div>

              <!-- Access Token (collapsible) -->
              <div :class="[bgSecondary, 'p-4 rounded-lg']">
                <button 
                  @click="showFullToken = !showFullToken"
                  :class="['flex items-center justify-between w-full font-semibold', textPrimary]"
                >
                  <span>Access Token</span>
                  <svg 
                    :class="['w-5 h-5 transition-transform', showFullToken ? 'rotate-180' : '']" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div v-if="showFullToken" class="mt-3">
                  <textarea 
                    :value="extractedToken.access_token"
                    readonly
                    :class="[
                      isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-900',
                      'w-full px-3 py-2 border rounded font-mono text-xs'
                    ]"
                    rows="8"
                  ></textarea>
                  <div class="flex space-x-2 mt-2">
                    <button
                      @click="copyTokenToClipboard"
                      class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                    >
                      📋 Copy to Clipboard
                    </button>
                    <button
                      @click="importTokenToDatabase"
                      :disabled="importingToken"
                      :class="[
                        'px-4 py-2 text-white text-sm rounded transition-colors',
                        importingToken 
                          ? 'bg-gray-500 cursor-not-allowed'
                          : 'bg-green-600 hover:bg-green-700'
                      ]"
                    >
                      {{ importingToken ? '⏳ Importing...' : '💾 Import to Database' }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Red Team Notes -->
              <div :class="[isDark ? 'bg-yellow-900 border-yellow-700' : 'bg-yellow-50 border-yellow-200', 'p-4 rounded-lg border']">
                <div class="flex items-start">
                  <svg class="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  <div>
                    <h4 :class="['font-semibold', isDark ? 'text-yellow-300' : 'text-yellow-800']">Red Team Usage</h4>
                    <p :class="['text-sm mt-1', isDark ? 'text-yellow-200' : 'text-yellow-700']">
                      This token can be used to authenticate as the VM's Managed Identity. Use it in API calls by setting the Authorization header: 
                      <code :class="[isDark ? 'bg-yellow-800' : 'bg-yellow-100', 'px-1 py-0.5 rounded font-mono text-xs']">Bearer {token}</code>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Security Scan Tab -->
        <div v-if="currentTab === 'security-scan'" class="p-6">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <h3 :class="['text-lg font-semibold', textPrimary]">VM Managed Identity Security Scan</h3>
              <p :class="['text-sm', textSecondary]">Identify VMs with overly permissive Managed Identities</p>
            </div>
            <button
              @click="startSecurityScan"
              :disabled="scanLoading || !selectedSubscription"
              style="background: #dc2626; padding: 10px 20px; border: none; border-radius: 5px; font-weight: 600; cursor: pointer; color: white; display: flex; align-items: center; gap: 0.5rem; transition: background 0.2s;"
              :style="{ background: (scanLoading || !selectedSubscription) ? '#dc2626' : '#dc2626', opacity: (scanLoading || !selectedSubscription) ? '0.6' : '1', cursor: (scanLoading || !selectedSubscription) ? 'not-allowed' : 'pointer' }"
              @mouseover="!scanLoading && selectedSubscription && ($event.target.style.background = '#b91c1c')"
              @mouseout="!scanLoading && selectedSubscription && ($event.target.style.background = '#dc2626')"
            >
              <svg v-if="scanLoading" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span>{{ scanLoading ? 'Scanning...' : 'Start Scan' }}</span>
            </button>
          </div>

          <!-- Loading State -->
          <div v-if="scanLoading" class="text-center py-12">
            <svg class="animate-spin h-8 w-8 mx-auto text-red-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p :class="['mt-4', textSecondary]">Scanning all VMs for Managed Identity security risks...</p>
            <p :class="['text-sm mt-2', textPlaceholder]">This may take a few moments for large subscriptions</p>
          </div>

          <!-- Scan Results -->
          <div v-else-if="scanResults">
            <!-- Summary Cards -->
            <div class="grid grid-cols-5 gap-4 mb-6">
              <div class="bg-gray-800 rounded-lg border-2 border-red-500 p-4 text-center">
                <div class="text-3xl font-bold text-red-400">{{ scanResults.summary.critical }}</div>
                <div class="text-sm mt-1 text-gray-400">Critical</div>
              </div>
              <div class="bg-gray-800 rounded-lg border-2 border-orange-500 p-4 text-center">
                <div class="text-3xl font-bold text-orange-400">{{ scanResults.summary.high }}</div>
                <div class="text-sm mt-1 text-gray-400">High</div>
              </div>
              <div class="bg-gray-800 rounded-lg border-2 border-yellow-500 p-4 text-center">
                <div class="text-3xl font-bold text-yellow-400">{{ scanResults.summary.medium }}</div>
                <div class="text-sm mt-1 text-gray-400">Medium</div>
              </div>
              <div class="bg-gray-800 rounded-lg border-2 border-green-500 p-4 text-center">
                <div class="text-3xl font-bold text-green-400">{{ scanResults.summary.low }}</div>
                <div class="text-sm mt-1 text-gray-400">Low</div>
              </div>
              <div class="bg-gray-800 rounded-lg border-2 border-gray-600 p-4 text-center">
                <div class="text-3xl font-bold text-gray-400">{{ scanResults.summary.none }}</div>
                <div class="text-sm mt-1 text-gray-400">No Identity</div>
              </div>
            </div>

            <!-- Critical VMs Alert -->
            <div v-if="scanResults.criticalVMs.length > 0" class="mb-6 bg-red-900/40 border-2 border-red-500 rounded-lg p-4">
              <div class="flex items-start">
                <svg class="w-8 h-8 text-red-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h4 class="text-lg font-semibold text-red-300 mb-2">🚨 High-Risk VMs Detected</h4>
                  <p class="text-sm text-red-200">
                    {{ scanResults.criticalVMs.length }} VMs have overly permissive Managed Identities that could be used for privilege escalation
                  </p>
                </div>
              </div>
            </div>

            <!-- VMs List -->
            <div class="space-y-4">
              <div 
                v-for="vm in scanResults.vms" 
                :key="vm.id"
                class="bg-gray-800 rounded-lg border-l-4 p-4"
                :class="vm.riskScore === 'Critical' ? 'border-red-500' :
                        vm.riskScore === 'High' ? 'border-orange-500' :
                        vm.riskScore === 'Medium' ? 'border-yellow-500' :
                        vm.riskScore === 'Low' ? 'border-green-500' :
                        'border-gray-500'"
              >
                <div class="flex items-start justify-between mb-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-3 mb-1">
                      <h4 class="font-semibold text-lg text-white">{{ vm.name }}</h4>
                      <span 
                        class="px-2 py-1 rounded text-xs font-semibold"
                        :class="vm.riskScore === 'Critical' ? 'bg-red-900 text-red-300' :
                                vm.riskScore === 'High' ? 'bg-orange-900 text-orange-300' :
                                vm.riskScore === 'Medium' ? 'bg-yellow-900 text-yellow-300' :
                                vm.riskScore === 'Low' ? 'bg-green-900 text-green-300' :
                                'bg-gray-700 text-gray-300'"
                      >
                        {{ vm.riskScore.toUpperCase() }}
                      </span>
                    </div>
                    <div class="text-sm text-gray-400">
                      📍 Location: {{ vm.location }}
                    </div>
                  </div>
                </div>

                <!-- Identity Info -->
                <div v-if="vm.identity.enabled" class="bg-gray-900 rounded-lg p-3 mb-3 border border-gray-700">
                  <h5 class="text-sm font-semibold text-white mb-2">🎭 Identity Information</h5>
                  <div class="text-sm space-y-2">
                    <div class="flex justify-between text-gray-300">
                      <span>Identity:</span>
                      <span class="font-semibold text-white">{{ vm.identity.type }}</span>
                    </div>
                    <div class="flex flex-col pt-2 border-t border-gray-700">
                      <span class="text-gray-400 text-xs mb-1">Principal ID:</span>
                      <span class="font-mono text-xs text-blue-400 break-all">{{ vm.identity.principalId }}</span>
                    </div>
                    <div class="flex justify-between text-gray-300 pt-2 border-t border-gray-700">
                      <span>Roles:</span>
                      <span class="font-semibold text-xl text-white">{{ vm.roleAssignments.length }}</span>
                    </div>
                  </div>
                </div>

                <!-- Role Assignments -->
                <div v-if="vm.roleAssignments.length > 0" class="mb-3">
                  <h5 class="text-sm font-semibold text-white mb-2">🔑 Role Assignments</h5>
                  <div class="space-y-2">
                    <div 
                      v-for="(role, idx) in vm.roleAssignments" 
                      :key="idx"
                      class="bg-gray-900 rounded-lg p-3 border-l-4"
                      :class="role.roleName.toLowerCase().includes('owner') || role.roleName.toLowerCase().includes('contributor') ? 'border-red-500' : 
                              role.roleName.toLowerCase().includes('admin') ? 'border-orange-500' : 
                              'border-blue-500'"
                    >
                      <div class="flex items-center justify-between">
                        <span class="font-medium text-white">{{ role.roleName }}</span>
                        <span 
                          class="text-xs px-2 py-1 rounded font-semibold"
                          :class="role.scopeLevel === 'Subscription' ? 'bg-purple-900 text-purple-300' :
                                  role.scopeLevel === 'Resource Group' ? 'bg-blue-900 text-blue-300' :
                                  'bg-gray-700 text-gray-300'"
                        >
                          {{ role.scopeLevel }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Recommendations -->
                <div v-if="vm.recommendations.length > 0">
                  <h5 class="text-sm font-semibold text-white mb-2">💡 Recommendations</h5>
                  <ul class="space-y-2">
                    <li 
                      v-for="(rec, idx) in vm.recommendations" 
                      :key="idx"
                      class="text-sm flex items-start bg-yellow-900/20 p-2 rounded-lg"
                    >
                      <span class="text-yellow-400 mr-2">⚠️</span>
                      <span class="text-gray-300">{{ rec }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- No Scan Yet -->
          <div v-else class="text-center py-12">
            <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 :class="['text-lg font-semibold mb-2', textTertiary]">No Scan Performed</h3>
            <p :class="[textPlaceholder]">Click "Start Scan" to analyze VMs for security risks</p>
          </div>
        </div>
      </div>
    </div>

    <!-- No VMs -->
    <div v-else-if="!loading && selectedSubscription && vms.length === 0" :class="[bgPrimary, borderPrimary, 'text-center py-12 rounded-lg border']">
      <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 :class="['text-lg font-semibold mb-2', textTertiary]">No Virtual Machines</h3>
      <p :class="[textPlaceholder]">No VMs found in this subscription</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'VirtualMachinesView',
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    bgPrimary() {
      return this.isDark ? 'bg-gray-800' : 'bg-white';
    },
    bgSecondary() {
      return this.isDark ? 'bg-gray-700' : 'bg-gray-100';
    },
    bgContainer() {
      return this.isDark ? 'bg-gray-900' : 'bg-gray-50';
    },
    textPrimary() {
      return this.isDark ? 'text-white' : 'text-gray-900';
    },
    textSecondary() {
      return this.isDark ? 'text-gray-400' : 'text-gray-600';
    },
    textTertiary() {
      return this.isDark ? 'text-gray-300' : 'text-gray-700';
    },
    textPlaceholder() {
      return this.isDark ? 'text-gray-500' : 'text-gray-500';
    },
    textIcon() {
      return this.isDark ? 'text-gray-600' : 'text-gray-400';
    },
    borderPrimary() {
      return this.isDark ? 'border-gray-700' : 'border-gray-300';
    },
    borderSecondary() {
      return this.isDark ? 'border-gray-600' : 'border-gray-400';
    }
  },
  data() {
    return {
      subscriptions: [],
      selectedSubscription: '',
      selectedSubscriptionName: '',
      vms: [],
      loading: false,
      error: null,
      actionLoading: {},
      statusPollInterval: null,
      
      // Cache (5 min TTL)
      vmCache: null,
      vmCacheTime: null,
      CACHE_TTL: 300000, // 5 minutes
      
      // Cross-user token banner
      showCrossUserBanner: false,
      crossUserTokens: [],
      currentUserUPN: '',
      bannerDismissed: false,
      
      // Tabs
      currentTab: 'overview',
      tabs: [
        { id: 'overview', name: 'Overview' },
        { id: 'run-command', name: 'Run Command' },
        { id: 'mi-token', name: 'MI Token' },
        { id: 'security-scan', name: 'Security Scan' }
      ],
      
      // Selected VM
      selectedVM: null,
      
      // Run Command
      runCommandType: 'RunPowerShellScript',
      runCommandScript: '',
      runCommandOutput: '',
      runCommandExecuting: false,
      
      // Managed Identity Token Extraction
      extractingToken: false,
      extractedToken: null,
      tokenResource: 'https://management.azure.com/',
      tokenError: null,
      showFullToken: false,
      importingToken: false,
      
      // Security Scan
      scanResults: null,
      scanLoading: false
    }
  },
  mounted() {
    this.loadSubscriptions()
  },
  beforeUnmount() {
    this.stopStatusPolling()
  },
  methods: {
    async loadSubscriptions() {
      try {
        const response = await axios.get('http://localhost:5000/api/azure/subscriptions')
        
        if (!response.data.success && response.data.cross_user_tokens_available) {
          console.log('[CROSS-USER] Cross-user tokens available:', response.data.available_tokens)
          this.showCrossUserBanner = true
          this.crossUserTokens = response.data.available_tokens || []
          this.currentUserUPN = response.data.current_upn || ''
          this.error = null
          return
        }
        
        if (response.data.success) {
          this.subscriptions = response.data.subscriptions
          if (this.subscriptions.length === 1) {
            this.selectedSubscription = this.subscriptions[0].id
            this.selectedSubscriptionName = this.subscriptions[0].displayName
            this.loadVMs()
          }
          this.showCrossUserBanner = false
        } else {
          this.error = response.data.error || 'Failed to load subscriptions'
        }
      } catch (err) {
        console.error('Failed to load subscriptions:', err)
        this.error = err.response?.data?.error || 'Network error loading subscriptions'
      }
    },
    
    async loadVMs(useCache = true) {
      if (!this.selectedSubscription) return
      
      // Update subscription name
      const sub = this.subscriptions.find(s => s.id === this.selectedSubscription)
      this.selectedSubscriptionName = sub ? sub.displayName : this.selectedSubscription
      
      // Check cache (5 min TTL)
      if (useCache && this.vmCache && this.vmCacheTime) {
        const age = Date.now() - this.vmCacheTime
        if (age < this.CACHE_TTL) {
          console.log('[CACHE HIT] VMs from cache')
          this.vms = this.vmCache
          return
        }
      }
      
      this.loading = true
      this.error = null
      this.showCrossUserBanner = false
      this.vms = []
      
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/subscriptions/${this.selectedSubscription}/vms`)
        
        if (response.data.success) {
          this.vms = response.data.virtual_machines
          
          // Cache results
          this.vmCache = this.vms
          this.vmCacheTime = Date.now()
          
          this.loadVMStatuses()
          this.startStatusPolling()
        } else if (response.data.cross_user_tokens_available) {
          this.showCrossUserBanner = true
          this.crossUserTokens = response.data.available_tokens
          this.currentUserUPN = response.data.current_upn
          this.error = response.data.error
        } else {
          this.error = response.data.error || 'Failed to load VMs'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loading = false
      }
    },
    
    forceRefresh() {
      this.vmCache = null
      this.vmCacheTime = null
      this.loadVMs(false)
    },
    
    async loadVMStatuses() {
      for (const vm of this.vms) {
        try {
          const response = await axios.post('http://localhost:5000/api/azure/vms/status', {
            vmId: vm.id
          })
          if (response.data.success) {
            vm.powerState = response.data.powerState
          }
        } catch (err) {
          console.error(`Failed to get status for ${vm.name}:`, err)
        }
      }
    },
    
    startStatusPolling() {
      this.statusPollInterval = setInterval(() => {
        if (this.vms.length > 0 && !this.loading) {
          this.loadVMStatuses()
        }
      }, 30000)
    },
    
    stopStatusPolling() {
      if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval)
      }
    },
    
    selectVM(vm) {
      this.selectedVM = vm
    },
    
    goToRunCommand(vm) {
      this.selectedVM = vm
      this.runCommandType = vm.osType === 'Linux' ? 'RunShellScript' : 'RunPowerShellScript'
      this.currentTab = 'run-command'
    },
    
    async startVM(vm) {
      this.actionLoading[vm.id] = true
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/start', {
          vmId: vm.id
        })
        if (response.data.success) {
          vm.powerState = 'starting'
          setTimeout(() => this.loadVMStatuses(), 5000)
        } else {
          alert(`Failed to start VM: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        delete this.actionLoading[vm.id]
      }
    },
    
    async stopVM(vm) {
      this.actionLoading[vm.id] = true
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/stop', {
          vmId: vm.id
        })
        if (response.data.success) {
          vm.powerState = 'stopping'
          setTimeout(() => this.loadVMStatuses(), 5000)
        } else {
          alert(`Failed to stop VM: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        delete this.actionLoading[vm.id]
      }
    },
    
    async restartVM(vm) {
      this.actionLoading[vm.id] = true
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/restart', {
          vmId: vm.id
        })
        if (response.data.success) {
          vm.powerState = 'restarting'
          setTimeout(() => this.loadVMStatuses(), 5000)
        } else {
          alert(`Failed to restart VM: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        delete this.actionLoading[vm.id]
      }
    },
    
    async deallocateVM(vm) {
      this.actionLoading[vm.id] = true
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/deallocate', {
          vmId: vm.id
        })
        if (response.data.success) {
          vm.powerState = 'deallocating'
          setTimeout(() => this.loadVMStatuses(), 5000)
        } else {
          alert(`Failed to deallocate VM: ${response.data.error}`)
        }
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || err.message}`)
      } finally {
        delete this.actionLoading[vm.id]
      }
    },
    
    clearRunCommand() {
      this.runCommandScript = ''
      this.runCommandOutput = ''
    },
    
    async executeRunCommand() {
      this.runCommandExecuting = true
      this.runCommandOutput = ''
      
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/run-command', {
          vmId: this.selectedVM.id,
          commandId: this.runCommandType,
          script: this.runCommandScript
        })
        
        if (response.data.success) {
          // Use output directly as string (already formatted by backend)
          this.runCommandOutput = response.data.output || 'Command executed successfully (no output)'
        } else {
          this.runCommandOutput = `Error: ${response.data.error}`
        }
      } catch (err) {
        this.runCommandOutput = `Error: ${err.response?.data?.error || err.message}`
      } finally {
        this.runCommandExecuting = false
      }
    },
    
    extractManagedIdentityToken(vm) {
      this.selectedVM = vm
      this.currentTab = 'mi-token'
      this.extractedToken = null
      this.tokenError = null
      this.showFullToken = false
    },
    
    async performTokenExtraction() {
      this.extractingToken = true
      this.extractedToken = null
      this.tokenError = null
      
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/extract-mi-token', {
          vmId: this.selectedVM.id,
          resource: this.tokenResource
        })
        
        if (response.data.success) {
          this.extractedToken = response.data
        } else {
          this.tokenError = response.data.error || 'Token extraction failed'
        }
      } catch (err) {
        this.tokenError = err.response?.data?.error || err.message
      } finally {
        this.extractingToken = false
      }
    },
    
    copyTokenToClipboard() {
      if (!this.extractedToken?.access_token) return
      
      navigator.clipboard.writeText(this.extractedToken.access_token).then(() => {
        alert('Token copied to clipboard!')
      }).catch(err => {
        alert('Failed to copy token: ' + err.message)
      })
    },
    
    async importTokenToDatabase() {
      if (!this.extractedToken) return
      
      this.importingToken = true
      
      try {
        const response = await axios.post('http://localhost:5000/api/azure/vms/import-mi-token', {
          access_token: this.extractedToken.access_token,
          resource: this.extractedToken.resource,
          expires_on: this.extractedToken.expires_on,
          claims: this.extractedToken.claims,
          identity: this.extractedToken.identity,
          vm_id: this.extractedToken.vm_id
        })
        
        if (response.data.success) {
          const displayName = this.extractedToken.identity?.displayName || 'Managed Identity'
          alert(`✅ Token imported successfully!\n\nIdentity: ${displayName}\nToken ID: ${response.data.token_id}\n\nGo to Tokens page to view and activate.`)
        } else {
          alert(`❌ Import failed: ${response.data.error}`)
        }
      } catch (err) {
        alert(`❌ Error: ${err.response?.data?.error || err.message}`)
      } finally {
        this.importingToken = false
      }
    },
    
    async activateCrossUserToken(tokenId) {
      console.log('[CROSS-USER] Activating token:', tokenId)
      
      try {
        const response = await axios.post('http://localhost:5000/api/tokens/activate', {
          token_id: tokenId
        })
        
        if (response.data.success) {
          console.log('[CROSS-USER] ✅ Token activated successfully')
          this.showCrossUserBanner = false
          this.bannerDismissed = true
          await this.loadSubscriptions()
          this.error = null
        } else {
          this.error = response.data.error || 'Failed to activate token'
        }
      } catch (err) {
        console.error('[CROSS-USER] Error activating token:', err)
        this.error = err.response?.data?.error || 'Network error activating token'
      }
    },
    
    dismissCrossUserBanner() {
      this.showCrossUserBanner = false
      this.bannerDismissed = true
    },
    
    formatTokenExpiry(expiresAt) {
      if (!expiresAt) return 'Unknown'
      
      try {
        const date = new Date(expiresAt)
        const now = new Date()
        const diffMs = date - now
        const diffMins = Math.floor(diffMs / 60000)
        
        if (diffMins < 0) return 'Expired'
        if (diffMins < 60) return `${diffMins}m`
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h`
        
        return date.toLocaleString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      } catch {
        return 'Unknown'
      }
    },
    
    async startSecurityScan() {
      if (!this.selectedSubscription) return
      
      this.scanLoading = true
      this.scanResults = null
      this.error = null
      
      try {
        console.log('[SECURITY SCAN] Starting scan for subscription:', this.selectedSubscription)
        
        const response = await axios.post('http://localhost:5000/api/azure/vms/scan-managed-identities', {
          subscriptionId: this.selectedSubscription
        })
        
        if (response.data.success) {
          this.scanResults = response.data
          console.log('[SECURITY SCAN] Scan complete:', this.scanResults.summary)
        } else {
          this.error = response.data.error || 'Failed to scan VMs'
        }
      } catch (err) {
        console.error('[SECURITY SCAN] Error:', err)
        this.error = err.response?.data?.error || err.message || 'Failed to perform security scan'
      } finally {
        this.scanLoading = false
      }
    },
    
    getStatusClass(powerState) {
      const state = (powerState || '').toLowerCase()
      if (state === 'running') return 'bg-green-900 text-green-300'
      if (state === 'stopped' || state === 'deallocated') return 'bg-red-900 text-red-300'
      if (state.includes('starting') || state.includes('stopping') || state.includes('deallocating')) return 'bg-yellow-900 text-yellow-300'
      return 'bg-gray-700 text-gray-300'
    }
  }
}
</script>

<style scoped>
.bg-gray-750 {
  background-color: #2d3748;
}

/* KeyVaults-style buttons */
.subscription-select {
  padding: 10px 15px;
  border: 1px solid #4a5568;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  min-width: 250px;
  background: #2d3748;
  color: #f3f4f6;
}

.subscription-select:focus {
  outline: none;
  border-color: #3498db;
}

.refresh-btn {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #2980b9;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

