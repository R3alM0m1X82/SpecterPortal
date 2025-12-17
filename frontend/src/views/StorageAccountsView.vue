<template>
  <div :class="['p-8 min-h-screen', bgContainer]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 :class="['text-3xl font-bold', textPrimary]">Storage Accounts</h1>
        <p :class="['text-sm mt-1', textSecondary]">Azure Storage enumeration and management</p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Subscription Selector -->
        <select 
          v-model="selectedSubscription" 
          @change="loadStorageAccounts"
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
          @click="loadStorageAccounts" 
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
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
        <h3 :class="['text-lg font-semibold mb-2', textTertiary]">Select a Subscription</h3>
        <p :class="[textPlaceholder]">Choose a subscription from the dropdown to view Storage Accounts</p>
      </div>

      <!-- Storage Accounts Table -->
      <div v-else-if="storageAccounts.length > 0" :class="[bgPrimary, borderPrimary, 'rounded-lg border overflow-hidden']">
        <table class="w-full">
          <thead :class="[bgSecondary]">
            <tr>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Name</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Kind</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">SKU</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Location</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Status</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Endpoints</th>
            </tr>
          </thead>
          <tbody :class="['divide-y', isDark ? 'divide-gray-700' : 'divide-gray-300']">
            <tr 
              v-for="account in storageAccounts" 
              :key="account.id" 
              @click="selectStorageAccount(account)"
              :class="[
                'hover:bg-gray-750 transition-colors cursor-pointer',
                selectedStorageAccount?.id === account.id ? 'bg-blue-900/30 border-l-4 border-blue-500' : ''
              ]"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-8 w-8">
                    <svg class="h-8 w-8" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M0 3.5C0 1.567 1.567 0 3.5 0h11C16.433 0 18 1.567 18 3.5v11c0 1.933-1.567 3.5-3.5 3.5h-11C1.567 18 0 16.433 0 14.5v-11z" fill="url(#storageIconGradient)"/>
                      <defs>
                        <linearGradient id="storageIconGradient" x1="9" y1="0" x2="9" y2="18" gradientUnits="userSpaceOnUse">
                          <stop stop-color="#FFB900"/>
                          <stop offset="1" stop-color="#F25022"/>
                        </linearGradient>
                      </defs>
                      <path d="M4 5h10v2H4V5zm0 3h10v2H4V8zm0 3h10v2H4v-2z" fill="white"/>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <div :class="['text-sm font-medium', textPrimary]">{{ account.name }}</div>
                    <div :class="['text-xs', textSecondary]">{{ account.id }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ account.kind }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ account.sku }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ account.location }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-900 text-green-300">
                  {{ account.provisioningState }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-300">
                <div class="space-y-1">
                  <div v-if="account.primaryEndpoints?.blob" class="text-xs">
                    <span :class="[textPlaceholder]">Blob:</span> {{ account.primaryEndpoints.blob }}
                  </div>
                  <div v-if="account.primaryEndpoints?.file" class="text-xs">
                    <span :class="[textPlaceholder]">File:</span> {{ account.primaryEndpoints.file }}
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No Storage Accounts -->
      <div v-else-if="!loading && selectedSubscription" :class="['text-center py-12 rounded-lg border', bgPrimary, borderPrimary]">
        <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
        <h3 :class="['text-lg font-semibold mb-2', textTertiary]">No Storage Accounts</h3>
        <p :class="[textPlaceholder]">No storage accounts found in this subscription</p>
      </div>

      <!-- Security Audit Section (Sprint 11.1) -->
      <div v-if="selectedStorageAccount" class="mt-8 space-y-6">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-white flex items-center">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Security Audit: {{ selectedStorageAccount.name }}
          </h2>
          <button 
            @click="runSecurityAudit"
            :disabled="auditLoading"
            class="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg class="w-5 h-5" :class="{ 'animate-spin': auditLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span>{{ auditLoading ? 'Auditing...' : 'Run Security Audit' }}</span>
          </button>
        </div>

        <!-- PHASE 1: Security Overview Cards -->
        <div v-if="auditData" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Firewall Card -->
          <div class="bg-gray-800 rounded-lg border p-4" :class="auditData.properties?.firewall?.allowAllIPs ? 'border-red-500' : 'border-green-500'">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-white flex items-center">
                🔥 Firewall
              </h3>
              <span v-if="auditData.properties?.firewall?.allowAllIPs" class="px-2 py-1 text-xs font-semibold rounded-full bg-red-900 text-red-300">HIGH RISK</span>
              <span v-else class="px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300">SECURE</span>
            </div>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between text-gray-300">
                <span>Default Action:</span>
                <span class="font-semibold">{{ auditData.properties?.firewall?.defaultAction }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>IP Rules:</span>
                <span class="font-semibold">{{ auditData.properties?.firewall?.ipRulesCount || 0 }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>VNet Rules:</span>
                <span class="font-semibold">{{ auditData.properties?.firewall?.vnetRulesCount || 0 }}</span>
              </div>
              
              <!-- IP Rules Details (Expandable) -->
              <div v-if="auditData.properties?.firewall?.ipRules?.length > 0" class="mt-3 pt-3 border-t border-gray-700">
                <button 
                  @click="showIPRules = !showIPRules"
                  class="text-blue-400 hover:text-blue-300 text-xs flex items-center"
                >
                  <svg class="w-4 h-4 mr-1 transition-transform" :class="{ 'rotate-90': showIPRules }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  {{ showIPRules ? 'Hide' : 'Show' }} Allowed IPs
                </button>
                <div v-if="showIPRules" class="mt-2 space-y-1">
                  <div v-for="(rule, idx) in auditData.properties.firewall.ipRules" :key="idx" class="bg-gray-900 rounded px-2 py-1 text-xs">
                    <span class="text-blue-400 font-mono">{{ rule.value }}</span>
                    <span v-if="rule.action" class="text-gray-500 ml-2">({{ rule.action }})</span>
                  </div>
                </div>
              </div>
              
              <p v-if="auditData.properties?.firewall?.allowAllIPs" class="text-red-400 mt-2 text-xs">
                ⚠️ All IPs allowed (0.0.0.0/0)
              </p>
            </div>
          </div>

          <!-- Public Access Card -->
          <div class="bg-gray-800 rounded-lg border p-4" :class="auditData.properties?.publicAccess?.publicAccessEnabled ? 'border-yellow-500' : 'border-green-500'">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-white flex items-center">
                🌐 Public Access
              </h3>
              <span v-if="auditData.properties?.publicAccess?.publicAccessEnabled" class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-900 text-yellow-300">WARNING</span>
              <span v-else class="px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300">DISABLED</span>
            </div>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between text-gray-300">
                <span>Network Access:</span>
                <span class="font-semibold">{{ auditData.properties?.publicAccess?.publicNetworkAccess }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>Blob Public Access:</span>
                <span class="font-semibold">{{ auditData.properties?.publicAccess?.allowBlobPublicAccess ? 'Enabled' : 'Disabled' }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>Public Containers:</span>
                <span class="font-semibold text-red-400">{{ auditData.public_containers?.length || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- Encryption Card -->
          <div class="bg-gray-800 rounded-lg border border-green-500 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-white flex items-center">
                🔐 Encryption
              </h3>
              <span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300">SECURE</span>
            </div>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between text-gray-300">
                <span>Key Source:</span>
                <span class="font-semibold">{{ auditData.properties?.encryption?.keySource }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>HTTPS Only:</span>
                <span class="font-semibold">{{ auditData.properties?.https?.supportsHttpsTrafficOnly ? 'Yes' : 'No' }}</span>
              </div>
              <div class="flex justify-between text-gray-300">
                <span>TLS Version:</span>
                <span class="font-semibold">{{ auditData.properties?.minimumTlsVersion }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Risk Summary -->
        <div v-if="auditData?.risk_score" class="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 class="text-lg font-semibold text-white mb-4">📊 Risk Summary</h3>
          <div class="grid grid-cols-4 gap-4 mb-4">
            <div class="text-center">
              <div class="text-3xl font-bold text-red-400">{{ auditData.risk_score.critical }}</div>
              <div :class="['text-sm', textSecondary]">Critical</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-orange-400">{{ auditData.risk_score.high }}</div>
              <div :class="['text-sm', textSecondary]">High</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-yellow-400">{{ auditData.risk_score.medium }}</div>
              <div :class="['text-sm', textSecondary]">Medium</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-green-400">{{ auditData.risk_score.passed_checks }}</div>
              <div :class="['text-sm', textSecondary]">Passed</div>
            </div>
          </div>

          <!-- Issues List -->
          <div v-if="auditData.risks?.length > 0" class="space-y-2">
            <h4 class="font-semibold text-white">🚨 Critical/High Issues:</h4>
            <div v-for="(risk, idx) in auditData.risks" :key="idx" class="bg-gray-900 rounded p-3 border-l-4" :class="risk.severity === 'CRITICAL' ? 'border-red-500' : 'border-orange-500'">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-1">
                    <span class="px-2 py-0.5 text-xs font-semibold rounded" :class="risk.severity === 'CRITICAL' ? 'bg-red-900 text-red-300' : 'bg-orange-900 text-orange-300'">
                      {{ risk.severity }}
                    </span>
                    <span :class="['text-sm', textSecondary]">{{ risk.category }}</span>
                  </div>
                  <p class="text-white text-sm font-semibold">{{ risk.issue }}</p>
                  <p class="text-gray-400 text-xs mt-1">💡 {{ risk.recommendation }}</p>
                  <div v-if="risk.details" class="mt-2 text-xs text-gray-500">
                    Affected: {{ risk.details.join(', ') }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- PHASE 2: Containers Table -->
        <div v-if="containers.length > 0" :class="[bgPrimary, borderPrimary, 'rounded-lg border overflow-hidden']">
          <div class="px-6 py-3 bg-gray-700">
            <h3 class="text-lg font-semibold text-white">📦 Blob Containers ({{ containers.length }})</h3>
          </div>
          <table class="w-full">
            <thead :class="[bgSecondary]">
              <tr>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Name</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Public Access</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Lease Status</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Last Modified</th>
                <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Actions</th>
              </tr>
            </thead>
            <tbody :class="['divide-y', isDark ? 'divide-gray-700' : 'divide-gray-300']">
              <tr v-for="container in containers" :key="container.id" class="hover:bg-gray-750">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{{ container.name }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="container.publicAccess === 'None'" class="px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300">Private</span>
                  <span v-else class="px-2 py-1 text-xs font-semibold rounded-full bg-red-900 text-red-300">{{ container.publicAccess }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ container.leaseStatus }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ formatDate(container.lastModifiedTime) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    v-if="container.publicAccess !== 'None'"
                    @click="viewBlobs(container)"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs transition-colors"
                  >
                    🔍 View Blobs
                  </button>
                  <span v-else class="text-gray-500 text-xs">🔒 Private</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- PHASE 3: Storage Keys -->
        <div v-if="auditData" class="bg-gray-800 rounded-lg border p-4" :class="auditData.keys_accessible ? 'border-red-500' : 'border-green-500'">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white flex items-center">
              🔑 Storage Account Keys
            </h3>
            <span v-if="auditData.keys_accessible" class="px-2 py-1 text-xs font-semibold rounded-full bg-red-900 text-red-300">ACCESSIBLE</span>
            <span v-else class="px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300">PROTECTED</span>
          </div>
          <div v-if="auditData.keys_accessible" class="space-y-3">
            <div class="bg-red-900/20 border border-red-700 rounded p-3">
              <p class="text-red-300 text-sm font-semibold">⚠️ CRITICAL: Storage account keys are accessible!</p>
              <p class="text-red-400 text-xs mt-1">These keys provide FULL access to all blobs, files, queues, and tables. Review RBAC permissions immediately.</p>
            </div>
            <button 
              @click="downloadKeys"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              📥 Download Keys (Use Carefully!)
            </button>
          </div>
          <div v-else class="text-gray-400 text-sm">
            ✅ Storage account keys are properly protected. User does not have listKeys permission.
          </div>
        </div>
      </div>
    
    <!-- Blob Viewer Modal -->
    <div v-if="showBlobModal" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="closeBlobModal">
      <div class="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <div class="px-6 py-4 bg-gray-700 flex items-center justify-between">
          <h3 class="text-xl font-semibold text-white">
            📦 Blobs in "{{ selectedContainer?.name }}"
            <span v-if="containerBlobs.length > 0" class="text-gray-400 text-sm ml-2">({{ containerBlobs.length }} blobs)</span>
          </h3>
          <button @click="closeBlobModal" class="text-gray-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
          <!-- Loading -->
          <div v-if="loadingBlobs" class="text-center py-12">
            <svg class="animate-spin h-12 w-12 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-400 mt-4">Loading blobs...</p>
          </div>
          
          <!-- No Blobs -->
          <div v-else-if="containerBlobs.length === 0" class="text-center py-12">
            <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p class="text-gray-400">No blobs in this container</p>
          </div>
          
          <!-- Blobs Table -->
          <table v-else class="w-full">
            <thead :class="[bgSecondary]">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Name</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Size</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Type</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Last Modified</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody :class="['divide-y', isDark ? 'divide-gray-700' : 'divide-gray-300']">
              <tr v-for="blob in containerBlobs" :key="blob.name" class="hover:bg-gray-750">
                <td class="px-4 py-3 text-sm text-white">
                  <div class="flex items-center">
                    <span class="mr-2">📄</span>
                    <span class="font-mono text-xs">{{ blob.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-sm text-gray-300">{{ formatFileSize(blob.size) }}</td>
                <td class="px-4 py-3 text-sm text-gray-300">{{ blob.contentType || 'unknown' }}</td>
                <td class="px-4 py-3 text-sm text-gray-300">{{ formatDate(blob.lastModified) }}</td>
                <td class="px-4 py-3 text-sm">
                  <a 
                    :href="blob.url" 
                    target="_blank"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs transition-colors inline-block"
                  >
                    📥 Download
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
    name: 'StorageAccountsView',
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
      storageAccounts: [],
      loading: false,
      error: null,
      // Sprint 11.1: Security Audit
      selectedStorageAccount: null,
      auditData: null,
      containers: [],
      auditLoading: false,
      showIPRules: false,
      // Blob Viewer
      showBlobModal: false,
      selectedContainer: null,
      containerBlobs: [],
      loadingBlobs: false
    }
  },
  mounted() {
    this.loadSubscriptions()
  },
  methods: {
    async loadSubscriptions() {
      try {
        const response = await axios.get('http://localhost:5000/api/azure/subscriptions')
        if (response.data.success) {
          this.subscriptions = response.data.subscriptions
          // Check if no subscriptions - likely no ARM token
          if (this.subscriptions.length === 0) {
            this.error = 'No valid ARM token found'
          } else {
            this.error = null
            if (this.subscriptions.length === 1) {
              this.selectedSubscription = this.subscriptions[0].id
              this.loadStorageAccounts()
            }
          }
        } else {
          this.error = response.data.error || 'Failed to load subscriptions'
        }
      } catch (err) {
        console.error('Failed to load subscriptions:', err)
        this.error = err.response?.data?.error || 'Network error loading subscriptions'
      }
    },
    
    async loadStorageAccounts() {
      if (!this.selectedSubscription) return
      
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/subscriptions/${this.selectedSubscription}/storage`)
        
        if (response.data.success) {
          this.storageAccounts = response.data.storage_accounts
        } else {
          this.error = response.data.error || 'Failed to load storage accounts'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loading = false
      }
    },
    
    // Sprint 11.1: Security Audit Methods
    
    selectStorageAccount(account) {
      this.selectedStorageAccount = account
      this.auditData = null
      this.containers = []
      // Auto-run audit on selection
      this.runSecurityAudit()
    },
    
    async runSecurityAudit() {
      if (!this.selectedStorageAccount) return
      
      this.auditLoading = true
      
      try {
        // Call comprehensive security audit endpoint
        const response = await axios.get(
          `http://localhost:5000/api/azure/storage/${encodeURIComponent(this.selectedStorageAccount.id)}/security-audit`
        )
        
        if (response.data.success) {
          this.auditData = response.data
          
          // Load containers separately for table
          await this.loadContainers()
        } else {
          alert('Security audit failed: ' + (response.data.error || 'Unknown error'))
        }
      } catch (err) {
        console.error('Security audit error:', err)
        alert('Security audit failed: ' + (err.response?.data?.error || err.message))
      } finally {
        this.auditLoading = false
      }
    },
    
    async loadContainers() {
      if (!this.selectedStorageAccount) return
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/azure/storage/${encodeURIComponent(this.selectedStorageAccount.id)}/containers`
        )
        
        if (response.data.success) {
          this.containers = response.data.containers
        }
      } catch (err) {
        console.error('Failed to load containers:', err)
      }
    },
    
    async downloadKeys() {
      if (!this.selectedStorageAccount) return
      
      if (!confirm('⚠️ WARNING: Storage account keys provide FULL access. Download only if authorized!')) {
        return
      }
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/azure/storage/${encodeURIComponent(this.selectedStorageAccount.id)}/keys`
        )
        
        if (response.data.success && response.data.accessible) {
          // Create downloadable JSON file
          const keysData = {
            storage_account: this.selectedStorageAccount.name,
            keys: response.data.keys,
            exported_at: new Date().toISOString()
          }
          
          const blob = new Blob([JSON.stringify(keysData, null, 2)], { type: 'application/json' })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `${this.selectedStorageAccount.name}_keys.json`
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          window.URL.revokeObjectURL(url)
        } else {
          alert('Failed to retrieve keys: ' + (response.data.error || 'Access denied'))
        }
      } catch (err) {
        alert('Failed to download keys: ' + (err.response?.data?.error || err.message))
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    },
    
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    async viewBlobs(container) {
      this.selectedContainer = container
      this.showBlobModal = true
      this.loadingBlobs = true
      this.containerBlobs = []
      
      try {
        const storageAccountName = this.selectedStorageAccount.name
        const containerName = container.name
        const blobEndpoint = this.selectedStorageAccount.primaryEndpoints.blob
        
        // Call backend proxy to bypass CORS
        const response = await axios.get(
          `http://localhost:5000/api/azure/storage/${storageAccountName}/container/${containerName}/blobs`,
          {
            params: {
              blob_endpoint: blobEndpoint
            }
          }
        )
        
        if (response.data.success) {
          this.containerBlobs = response.data.blobs
        } else {
          throw new Error(response.data.error || 'Failed to list blobs')
        }
      } catch (err) {
        console.error('Failed to list blobs:', err)
        alert('Failed to list blobs: ' + (err.response?.data?.error || err.message))
        this.closeBlobModal()
      } finally {
        this.loadingBlobs = false
      }
    },
    
    closeBlobModal() {
      this.showBlobModal = false
      this.selectedContainer = null
      this.containerBlobs = []
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

