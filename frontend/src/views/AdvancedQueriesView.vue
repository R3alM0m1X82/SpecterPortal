<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-6">
      <h1 :class="['text-3xl font-bold mb-2', isDark ? 'text-white' : 'text-gray-900']">Advanced Queries</h1>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Execute custom API queries against Microsoft Graph, ARM, Key Vault, and Storage endpoints</p>
    </div>

    <!-- Query Builder Section -->
    <div :class="['rounded-lg shadow-lg p-6 mb-6', isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200']">
      <!-- Endpoint & Method -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Endpoint</label>
          <select
            v-model="selectedEndpoint"
            :class="[
              'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
            ]"
          >
            <option value="graph-v1">Microsoft Graph v1.0</option>
            <option value="graph-beta">Microsoft Graph Beta</option>
            <option value="arm">Azure Resource Manager (ARM)</option>
            <option value="keyvault">Key Vault Data Plane</option>
            <option value="storage">Storage Accounts</option>
            <option value="custom">Custom URL</option>
          </select>
        </div>
        
        <div>
          <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">HTTP Method</label>
          <select
            v-model="httpMethod"
            :class="[
              'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
            ]"
          >
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PATCH">PATCH</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>

        <!-- Resource Name (for Key Vault / Storage) -->
        <div v-if="selectedEndpoint === 'keyvault' || selectedEndpoint === 'storage'">
          <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
            {{ selectedEndpoint === 'keyvault' ? 'Vault Name' : 'Storage Account Name' }}
          </label>
          <input
            v-model="resourceName"
            type="text"
            :placeholder="selectedEndpoint === 'keyvault' ? 'myvault' : 'mystorageaccount'"
            :class="[
              'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            ]"
          />
        </div>

        <div v-if="selectedEndpoint === 'custom'">
          <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Base URL</label>
          <input
            v-model="customBaseUrl"
            type="text"
            placeholder="https://api.example.com"
            :class="[
              'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            ]"
          />
        </div>
      </div>

      <!-- API Path -->
      <div class="mb-4">
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">API Path</label>
        <div class="flex items-center gap-2">
          <span :class="['text-sm font-mono', isDark ? 'text-gray-400' : 'text-gray-600']">{{ currentBaseUrl }}/</span>
          <input
            v-model="apiPath"
            type="text"
            placeholder="me/messages?$top=10&$filter=..."
            :class="[
              'flex-1 px-4 py-2 rounded-lg border font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            ]"
          />
        </div>
      </div>

      <!-- Request Body (for POST/PATCH/PUT) -->
      <div v-if="['POST', 'PATCH', 'PUT'].includes(httpMethod)" class="mb-4">
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">Request Body (JSON)</label>
        <textarea
          v-model="requestBody"
          rows="6"
          placeholder='{\n  "displayName": "Example",\n  "key": "value"\n}'
          :class="[
            'w-full px-4 py-3 rounded-lg border font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        ></textarea>
        <p v-if="requestBodyError" class="text-red-400 text-xs mt-1">{{ requestBodyError }}</p>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-3">
        <button
          @click="executeQuery"
          :disabled="loading || !apiPath"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ loading ? 'Executing...' : '🚀 Execute Query' }}</span>
        </button>
        
        <button
          @click="showTemplates = true"
          class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
        >
          📋 Templates
        </button>
        
        <button
          @click="showHistory = true"
          :disabled="queryHistory.length === 0"
          class="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          ⏱️ History ({{ queryHistory.length }})
        </button>
        
        <button
          @click="clearQuery"
          class="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
        >
          🗑️ Clear
        </button>
      </div>
    </div>

    <!-- Response Section -->
    <div v-if="response || error" :class="['rounded-lg shadow-lg p-6', isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200']">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <h2 :class="['text-xl font-semibold', isDark ? 'text-white' : 'text-gray-900']">Response</h2>
          <span
            v-if="response"
            :class="[
              'px-3 py-1 text-xs font-semibold rounded-full',
              responseStatusClass
            ]"
          >
            {{ response.status }} {{ response.statusText }}
          </span>
        </div>
        
        <div class="flex gap-2">
          <button
            v-if="response"
            @click="copyResponse"
            :class="[
              'px-4 py-2 rounded-lg transition-colors text-sm',
              isDark ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            ]"
          >
            📋 Copy
          </button>
          <button
            v-if="response"
            @click="downloadResponse"
            :class="[
              'px-4 py-2 rounded-lg transition-colors text-sm',
              isDark ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            ]"
          >
            📥 Download
          </button>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" :class="['rounded-lg p-4 mb-4 border-2', isDark ? 'bg-red-900/40 border-red-500' : 'bg-red-50 border-red-300']">
        <div class="flex items-start">
          <svg class="w-6 h-6 text-red-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h4 :class="['text-lg font-semibold mb-1', isDark ? 'text-red-300' : 'text-red-700']">Error</h4>
            <p :class="['text-sm font-mono', isDark ? 'text-red-200' : 'text-red-600']">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Response Body -->
      <div v-if="response" :class="['rounded-lg p-4 max-h-[500px] overflow-auto', isDark ? 'bg-gray-900' : 'bg-gray-100']">
        <pre :class="['text-sm font-mono whitespace-pre-wrap', isDark ? 'text-gray-200' : 'text-gray-800']">{{ formattedResponse }}</pre>
      </div>
    </div>

    <!-- Templates Modal -->
    <div v-if="showTemplates" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div :class="['rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[80vh] overflow-hidden flex flex-col', isDark ? 'bg-gray-800' : 'bg-white']">
        <div :class="['p-6 border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
          <div class="flex items-center justify-between">
            <h2 :class="['text-xl font-semibold', isDark ? 'text-white' : 'text-gray-900']">Query Templates</h2>
            <button
              @click="showTemplates = false"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'
              ]"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 overflow-y-auto flex-1">
          <div class="grid grid-cols-1 gap-3">
            <div
              v-for="template in queryTemplates"
              :key="template.name"
              @click="loadTemplate(template)"
              :class="[
                'p-4 rounded-lg cursor-pointer transition-colors border',
                isDark ? 'bg-gray-700 hover:bg-gray-600 border-gray-600' : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h3 :class="['font-semibold mb-1', isDark ? 'text-white' : 'text-gray-900']">{{ template.name }}</h3>
                  <p :class="['text-sm mb-2', isDark ? 'text-gray-400' : 'text-gray-600']">{{ template.description }}</p>
                  <div class="flex items-center gap-2 text-xs">
                    <span :class="['px-2 py-1 rounded', isDark ? 'bg-blue-900/50 text-blue-300' : 'bg-blue-100 text-blue-700']">{{ template.method }}</span>
                    <span :class="['font-mono', isDark ? 'text-gray-400' : 'text-gray-600']">{{ template.endpoint }}</span>
                  </div>
                </div>
                <span class="text-2xl">{{ template.icon }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- History Modal -->
    <div v-if="showHistory" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div :class="['rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[80vh] overflow-hidden flex flex-col', isDark ? 'bg-gray-800' : 'bg-white']">
        <div :class="['p-6 border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
          <div class="flex items-center justify-between">
            <h2 :class="['text-xl font-semibold', isDark ? 'text-white' : 'text-gray-900']">Query History (Last 30)</h2>
            <button
              @click="showHistory = false"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'
              ]"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 overflow-y-auto flex-1">
          <div class="space-y-3">
            <div
              v-for="(item, index) in queryHistory"
              :key="index"
              @click="loadHistoryItem(item)"
              :class="[
                'p-4 rounded-lg cursor-pointer transition-colors border',
                isDark ? 'bg-gray-700 hover:bg-gray-600 border-gray-600' : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
              ]"
            >
              <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span :class="['px-2 py-1 rounded text-xs font-semibold', isDark ? 'bg-blue-900/50 text-blue-300' : 'bg-blue-100 text-blue-700']">{{ item.method }}</span>
                  <span
                    :class="[
                      'px-2 py-1 rounded text-xs font-semibold',
                      item.status >= 200 && item.status < 300 ? (isDark ? 'bg-green-900/50 text-green-300' : 'bg-green-100 text-green-700') :
                      item.status >= 400 ? (isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-100 text-red-700') : (isDark ? 'bg-gray-600 text-gray-300' : 'bg-gray-200 text-gray-600')
                    ]"
                  >
                    {{ item.status }}
                  </span>
                </div>
                <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">{{ formatTimestamp(item.timestamp) }}</span>
              </div>
              <p :class="['font-mono text-sm truncate', isDark ? 'text-gray-300' : 'text-gray-700']">{{ item.endpoint }}/{{ item.path }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000'

// Dark mode
const isDark = ref(document.documentElement.classList.contains('dark'))

// Watch for theme changes
let themeObserver = null
onMounted(() => {
  themeObserver = new MutationObserver(() => {
    isDark.value = document.documentElement.classList.contains('dark')
  })
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
})

onUnmounted(() => {
  if (themeObserver) {
    themeObserver.disconnect()
  }
})

// Query State
const selectedEndpoint = ref('graph-v1')
const httpMethod = ref('GET')
const apiPath = ref('')
const requestBody = ref('')
const customBaseUrl = ref('')
const resourceName = ref('')

// Response State
const loading = ref(false)
const response = ref(null)
const error = ref(null)
const requestBodyError = ref('')

// UI State
const showTemplates = ref(false)
const showHistory = ref(false)

// History (localStorage)
const queryHistory = ref(JSON.parse(localStorage.getItem('advancedQueriesHistory') || '[]'))

// Query Templates
const queryTemplates = [
  {
    name: 'List All Users',
    description: 'Enumerate all users in the tenant with key properties',
    icon: '👥',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'users?$select=id,displayName,userPrincipalName,mail,userType,accountEnabled&$top=999',
  },
  {
    name: 'Find All Mailbox Rules',
    description: 'Retrieve all inbox rules for current user (persistence detection)',
    icon: '📧',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'me/mailFolders/inbox/messageRules',
  },
  {
    name: 'Enumerate SharePoint Sites',
    description: 'List all SharePoint sites the current user has access to',
    icon: '🗂️',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'sites?search=*',
  },
  {
    name: 'List Recent Calendar Events',
    description: 'Get calendar events from last 30 days and next 30 days',
    icon: '📅',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'me/calendar/calendarView?startDateTime=2025-11-14T00:00:00Z&endDateTime=2026-01-14T23:59:59Z',
  },
  {
    name: 'Get All Group Memberships',
    description: 'Enumerate all groups current user belongs to',
    icon: '👥',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'me/memberOf',
  },
  {
    name: 'List Service Principals with Secrets',
    description: 'Find service principals that have client secrets or certificates',
    icon: '🔑',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'servicePrincipals?$select=id,displayName,appId,keyCredentials,passwordCredentials&$top=999',
  },
  {
    name: 'Enumerate Conditional Access Policies',
    description: 'List all conditional access policies (security assessment)',
    icon: '🛡️',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'identity/conditionalAccess/policies',
  },
  {
    name: 'Find External/Guest Users',
    description: 'Identify all guest/external users in tenant',
    icon: '🌐',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'users?$filter=userType eq \'Guest\'&$select=id,displayName,userPrincipalName,mail,createdDateTime&$top=999',
  },
  {
    name: 'List All Applications',
    description: 'Enumerate all application registrations in tenant',
    icon: '📱',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'applications?$select=id,displayName,appId,createdDateTime,keyCredentials,passwordCredentials&$top=999',
  },
  {
    name: 'Get Directory Roles & Members',
    description: 'List all directory roles (Global Admin, User Admin, etc.) with members',
    icon: '👑',
    endpoint: 'graph-v1',
    method: 'GET',
    path: 'directoryRoles?$expand=members',
  },
]

// Computed
const currentBaseUrl = computed(() => {
  switch (selectedEndpoint.value) {
    case 'graph-v1': return 'https://graph.microsoft.com/v1.0'
    case 'graph-beta': return 'https://graph.microsoft.com/beta'
    case 'arm': return 'https://management.azure.com'
    case 'keyvault': 
      return resourceName.value 
        ? `https://${resourceName.value}.vault.azure.net` 
        : 'https://{vault-name}.vault.azure.net'
    case 'storage': 
      return resourceName.value 
        ? `https://${resourceName.value}.blob.core.windows.net` 
        : 'https://{account-name}.blob.core.windows.net'
    case 'custom': return customBaseUrl.value || 'https://api.example.com'
    default: return ''
  }
})

const responseStatusClass = computed(() => {
  if (!response.value) return ''
  const status = response.value.status
  if (status >= 200 && status < 300) return 'bg-green-900/50 text-green-300'
  if (status >= 300 && status < 400) return 'bg-blue-900/50 text-blue-300'
  if (status >= 400 && status < 500) return 'bg-orange-900/50 text-orange-300'
  return 'bg-red-900/50 text-red-300'
})

const formattedResponse = computed(() => {
  if (!response.value || !response.value.data) return ''
  try {
    return JSON.stringify(response.value.data, null, 2)
  } catch (e) {
    return String(response.value.data)
  }
})

// Validate JSON for POST/PATCH/PUT
watch([httpMethod, requestBody], () => {
  requestBodyError.value = ''
  if (['POST', 'PATCH', 'PUT'].includes(httpMethod.value) && requestBody.value) {
    try {
      JSON.parse(requestBody.value)
    } catch (e) {
      requestBodyError.value = 'Invalid JSON format'
    }
  }
})

// Methods
const executeQuery = async () => {
  if (!apiPath.value) return
  
  // Validate resource name for Key Vault and Storage
  if ((selectedEndpoint.value === 'keyvault' || selectedEndpoint.value === 'storage') && !resourceName.value) {
    error.value = `Please enter ${selectedEndpoint.value === 'keyvault' ? 'vault' : 'storage account'} name`
    return
  }
  
  loading.value = true
  response.value = null
  error.value = null
  
  try {
    // Call backend to execute the query
    const payload = {
      endpoint: selectedEndpoint.value,
      method: httpMethod.value,
      path: apiPath.value,
      baseUrl: selectedEndpoint.value === 'custom' ? customBaseUrl.value : null,
      resourceName: resourceName.value || null
    }
    
    if (['POST', 'PATCH', 'PUT'].includes(httpMethod.value) && requestBody.value) {
      try {
        payload.body = JSON.parse(requestBody.value)
      } catch (e) {
        error.value = 'Invalid JSON in request body'
        loading.value = false
        return
      }
    }
    
    const res = await axios.post(`${API_BASE}/api/advanced-queries/execute`, payload)
    
    response.value = {
      status: res.data.status,
      statusText: res.data.statusText || 'OK',
      data: res.data.data
    }
    
    // Add to history
    addToHistory({
      endpoint: selectedEndpoint.value,
      method: httpMethod.value,
      path: apiPath.value,
      status: res.data.status,
      timestamp: new Date().toISOString()
    })
    
  } catch (err) {
    console.error('Query execution error:', err)
    if (err.response) {
      error.value = `${err.response.status} ${err.response.statusText}: ${JSON.stringify(err.response.data)}`
    } else {
      error.value = err.message || 'Failed to execute query'
    }
  } finally {
    loading.value = false
  }
}

const clearQuery = () => {
  apiPath.value = ''
  requestBody.value = ''
  resourceName.value = ''
  response.value = null
  error.value = null
}

const loadTemplate = (template) => {
  selectedEndpoint.value = template.endpoint
  httpMethod.value = template.method
  apiPath.value = template.path
  requestBody.value = template.body || ''
  showTemplates.value = false
}

const loadHistoryItem = (item) => {
  selectedEndpoint.value = item.endpoint
  httpMethod.value = item.method
  apiPath.value = item.path
  showHistory.value = false
}

const copyResponse = () => {
  navigator.clipboard.writeText(formattedResponse.value)
  alert('Response copied to clipboard!')
}

const downloadResponse = () => {
  const blob = new Blob([formattedResponse.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `response-${new Date().toISOString()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const addToHistory = (item) => {
  queryHistory.value.unshift(item)
  if (queryHistory.value.length > 30) {
    queryHistory.value = queryHistory.value.slice(0, 30)
  }
  localStorage.setItem('advancedQueriesHistory', JSON.stringify(queryHistory.value))
}

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}
</script>
