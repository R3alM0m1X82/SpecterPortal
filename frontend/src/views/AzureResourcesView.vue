<template>
  <div class="min-h-screen p-6" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-900'">
          ☁️ Azure Resources
        </h1>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Enumerate Azure subscriptions and resources (VMs, Storage, KeyVault, SQL, App Services)
        </p>
      </div>

      <!-- Subscriptions Selector -->
      <div class="mb-6 p-4 rounded-lg" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <label class="block text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
          Select Subscription:
        </label>
        <select 
          v-model="selectedSubscription" 
          @change="loadResourcesForSubscription"
          class="w-full px-3 py-2 rounded border"
          :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'"
        >
          <option value="">-- Load Subscriptions --</option>
          <option v-for="sub in subscriptions" :key="sub.id" :value="sub.id">
            {{ sub.displayName }} ({{ sub.state }})
          </option>
        </select>
        <button 
          @click="loadSubscriptions" 
          :disabled="loadingSubs"
          class="mt-2 px-4 py-2 rounded font-medium"
          :class="loadingSubs ? 'bg-gray-600 cursor-not-allowed' : (isDark ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600 text-white')"
        >
          {{ loadingSubs ? 'Loading...' : 'Refresh Subscriptions' }}
        </button>
      </div>

      <!-- Error message -->
      <div v-if="errorSubs" class="mb-6 p-4 rounded-lg" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
        <p :class="isDark ? 'text-red-300' : 'text-red-800'">{{ errorSubs }}</p>
      </div>

      <!-- Tabs -->
      <div class="mb-6 flex space-x-2 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 font-medium transition-colors"
          :class="activeTab === tab.id 
            ? (isDark ? 'border-b-2 border-blue-500 text-blue-400' : 'border-b-2 border-blue-500 text-blue-600')
            : (isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900')"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Tab: Resource Groups -->
      <div v-if="activeTab === 'resource-groups'" class="space-y-4">
        <div v-if="loadingRGs" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading resource groups...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="resourceGroups.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No resource groups found</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-4">
          <div 
            v-for="rg in resourceGroups" 
            :key="rg.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ rg.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ rg.location }}</p>
            <div v-if="Object.keys(rg.tags).length > 0" class="mt-2 flex flex-wrap gap-2">
              <span 
                v-for="(value, key) in rg.tags" 
                :key="key"
                class="px-2 py-1 text-xs rounded"
                :class="isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'"
              >
                {{ key }}: {{ value }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Virtual Machines -->
      <div v-if="activeTab === 'vms'" class="space-y-4">
        <div v-if="loadingVMs" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading VMs...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="vms.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No VMs found</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div 
            v-for="vm in vms" 
            :key="vm.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ vm.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ vm.location }}</p>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">💻 {{ vm.vmSize }}</p>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">🖥️ {{ vm.osType }}</p>
            <span 
              class="inline-block mt-2 px-2 py-1 text-xs rounded"
              :class="vm.provisioningState === 'Succeeded' 
                ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')
                : (isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800')"
            >
              {{ vm.provisioningState }}
            </span>
          </div>
        </div>
      </div>

      <!-- Tab: Storage Accounts -->
      <div v-if="activeTab === 'storage'" class="space-y-4">
        <div v-if="loadingStorage" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading storage accounts...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="storageAccounts.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No storage accounts found</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-4">
          <div 
            v-for="sa in storageAccounts" 
            :key="sa.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ sa.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ sa.location }}</p>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📦 {{ sa.kind }} - {{ sa.sku }}</p>
            <div v-if="sa.primaryEndpoints" class="mt-2 text-xs font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-600'">
              <div v-if="sa.primaryEndpoints.blob">Blob: {{ sa.primaryEndpoints.blob }}</div>
              <div v-if="sa.primaryEndpoints.file">File: {{ sa.primaryEndpoints.file }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Key Vaults -->
      <div v-if="activeTab === 'keyvaults'" class="space-y-4">
        <div v-if="loadingKeyVaults" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading Key Vaults...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="keyVaults.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No Key Vaults found</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div 
            v-for="kv in keyVaults" 
            :key="kv.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ kv.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ kv.location }}</p>
            <p class="text-sm font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-600'">{{ kv.vaultUri }}</p>
            <span 
              class="inline-block mt-2 px-2 py-1 text-xs rounded"
              :class="kv.enableRbacAuthorization 
                ? (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')
                : (isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-700')"
            >
              {{ kv.enableRbacAuthorization ? 'RBAC Enabled' : 'Access Policy' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Tab: SQL Servers -->
      <div v-if="activeTab === 'sql'" class="space-y-4">
        <div v-if="loadingSQL" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading SQL servers...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="sqlServers.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No SQL servers found</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-4">
          <div 
            v-for="sql in sqlServers" 
            :key="sql.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ sql.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ sql.location }}</p>
            <p class="text-sm font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-600'">{{ sql.fullyQualifiedDomainName }}</p>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Version: {{ sql.version }}</p>
            <span 
              class="inline-block mt-2 px-2 py-1 text-xs rounded"
              :class="sql.state === 'Ready' 
                ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')
                : (isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800')"
            >
              {{ sql.state }}
            </span>
          </div>
        </div>
      </div>

      <!-- Tab: App Services -->
      <div v-if="activeTab === 'appservices'" class="space-y-4">
        <div v-if="loadingAppServices" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading App Services...</p>
        </div>
        <div v-else-if="!selectedSubscription" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">Select a subscription first</p>
        </div>
        <div v-else-if="appServices.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">No App Services found</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div 
            v-for="app in appServices" 
            :key="app.id"
            class="p-4 rounded-lg"
            :class="isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white shadow'"
          >
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ app.name }}</h3>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">📍 {{ app.location }}</p>
            <p class="text-sm font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-600'">{{ app.defaultHostName }}</p>
            <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ app.kind }}</p>
            <span 
              class="inline-block mt-2 px-2 py-1 text-xs rounded"
              :class="app.state === 'Running' 
                ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')
                : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')"
            >
              {{ app.state }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

// Tab system
const tabs = [
  { id: 'resource-groups', label: 'Resource Groups', icon: '📁' },
  { id: 'vms', label: 'Virtual Machines', icon: '💻' },
  { id: 'storage', label: 'Storage', icon: '💾' },
  { id: 'keyvaults', label: 'Key Vaults', icon: '🔑' },
  { id: 'sql', label: 'SQL Servers', icon: '🗄️' },
  { id: 'appservices', label: 'App Services', icon: '🌐' }
]
const activeTab = ref('resource-groups')

// Subscriptions
const subscriptions = ref([])
const selectedSubscription = ref('')
const loadingSubs = ref(false)
const errorSubs = ref(null)

// Resources
const resourceGroups = ref([])
const vms = ref([])
const storageAccounts = ref([])
const keyVaults = ref([])
const sqlServers = ref([])
const appServices = ref([])

const loadingRGs = ref(false)
const loadingVMs = ref(false)
const loadingStorage = ref(false)
const loadingKeyVaults = ref(false)
const loadingSQL = ref(false)
const loadingAppServices = ref(false)

const loadSubscriptions = async () => {
  loadingSubs.value = true
  errorSubs.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/azure/subscriptions')
    const data = await response.json()
    
    if (data.success) {
      subscriptions.value = data.subscriptions || []
      if (subscriptions.value.length === 1) {
        selectedSubscription.value = subscriptions.value[0].id
        loadResourcesForSubscription()
      }
    } else {
      errorSubs.value = data.error || 'Failed to load subscriptions'
    }
  } catch (err) {
    errorSubs.value = 'Failed to load subscriptions: ' + err.message
  } finally {
    loadingSubs.value = false
  }
}

const loadResourcesForSubscription = async () => {
  if (!selectedSubscription.value) return
  
  // Load all resources for selected subscription
  loadResourceGroups()
  loadVMs()
  loadStorageAccounts()
  loadKeyVaults()
  loadSQLServers()
  loadAppServices()
}

const loadResourceGroups = async () => {
  loadingRGs.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/resource-groups`)
    const data = await response.json()
    if (data.success) {
      resourceGroups.value = data.resource_groups || []
    }
  } catch (err) {
    console.error('Failed to load resource groups:', err)
  } finally {
    loadingRGs.value = false
  }
}

const loadVMs = async () => {
  loadingVMs.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/vms`)
    const data = await response.json()
    if (data.success) {
      vms.value = data.virtual_machines || []
    }
  } catch (err) {
    console.error('Failed to load VMs:', err)
  } finally {
    loadingVMs.value = false
  }
}

const loadStorageAccounts = async () => {
  loadingStorage.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/storage`)
    const data = await response.json()
    if (data.success) {
      storageAccounts.value = data.storage_accounts || []
    }
  } catch (err) {
    console.error('Failed to load storage accounts:', err)
  } finally {
    loadingStorage.value = false
  }
}

const loadKeyVaults = async () => {
  loadingKeyVaults.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/keyvaults`)
    const data = await response.json()
    if (data.success) {
      keyVaults.value = data.key_vaults || []
    }
  } catch (err) {
    console.error('Failed to load Key Vaults:', err)
  } finally {
    loadingKeyVaults.value = false
  }
}

const loadSQLServers = async () => {
  loadingSQL.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/sql`)
    const data = await response.json()
    if (data.success) {
      sqlServers.value = data.sql_servers || []
    }
  } catch (err) {
    console.error('Failed to load SQL servers:', err)
  } finally {
    loadingSQL.value = false
  }
}

const loadAppServices = async () => {
  loadingAppServices.value = true
  try {
    const response = await fetch(`http://localhost:5000/api/azure/subscriptions/${selectedSubscription.value}/appservices`)
    const data = await response.json()
    if (data.success) {
      appServices.value = data.app_services || []
    }
  } catch (err) {
    console.error('Failed to load App Services:', err)
  } finally {
    loadingAppServices.value = false
  }
}

onMounted(() => {
  loadSubscriptions()
})
</script>
