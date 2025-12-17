<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Devices</h1>
      <div class="flex items-center space-x-4">
        <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ filteredDevices.length }} device(s)</span>
        <button @click="loadDevices(true)" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
          🔄 Refresh
        </button>
        
        <!-- Export Button -->
        <div class="relative">
          <button 
            @click="showExportMenu = !showExportMenu"
            :disabled="devices.length === 0"
            class="btn"
            :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'"
          >
            📥 Export
          </button>
          <div 
            v-if="showExportMenu"
            class="absolute right-0 mt-2 w-40 rounded-lg shadow-lg z-10"
            :class="isDark ? 'bg-gray-700 border border-gray-600' : 'bg-white border border-gray-200'"
          >
            <button 
              @click="exportData('json')"
              class="block w-full px-4 py-2 text-left text-sm hover:bg-gray-600 rounded-t-lg"
              :class="isDark ? 'text-gray-200 hover:bg-gray-600' : 'text-gray-700 hover:bg-gray-100'"
            >
              Export JSON
            </button>
            <button 
              @click="exportData('csv')"
              class="block w-full px-4 py-2 text-left text-sm rounded-b-lg"
              :class="isDark ? 'text-gray-200 hover:bg-gray-600' : 'text-gray-700 hover:bg-gray-100'"
            >
              Export CSV
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search devices by name, OS, or owner..."
        class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        :class="isDark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
      />
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading devices...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ error }}</p>
      <button @click="loadDevices" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Devices Table -->
    <div v-else-if="filteredDevices.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Enabled</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">OS</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Version</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Join Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Owner</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Registered</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Compliant</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="device in filteredDevices" :key="device.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
              {{ device.displayName }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span v-if="device.accountEnabled !== false" class="text-green-500">✓</span>
              <span v-else class="text-red-500">✗</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ device.operatingSystem || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ device.operatingSystemVersion || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="getJoinTypeClass(device.trustType)" class="px-2 py-1 text-xs font-semibold rounded">
                {{ device.trustType || 'N/A' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ device.registeredOwner || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ formatDate(device.registrationDateTime) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span v-if="device.isCompliant === true" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'">
                Yes
              </span>
              <span v-else-if="device.isCompliant === false" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800'">
                No
              </span>
              <span v-else class="text-sm" :class="isDark ? 'text-gray-500' : 'text-gray-400'">N/A</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Empty -->
    <div v-else class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="text-6xl mb-4">💻</div>
      <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">No Devices Found</h2>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineProps } from 'vue'

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

const devices = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

// Cache refs (5 minutes TTL)
const devicesCache = ref({ data: null, timestamp: null })
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes
const showExportMenu = ref(false)

const filteredDevices = computed(() => {
  if (!searchQuery.value.trim()) {
    return devices.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return devices.value.filter(device => 
    device.displayName?.toLowerCase().includes(query) ||
    device.operatingSystem?.toLowerCase().includes(query) ||
    device.registeredOwner?.toLowerCase().includes(query) ||
    device.trustType?.toLowerCase().includes(query)
  )
})

// Check if cache is valid
const isCacheValid = (cache) => {
  if (!cache.data || !cache.timestamp) return false
  return (Date.now() - cache.timestamp) < CACHE_TTL
}

const loadDevices = async (forceRefresh = false) => {
  loading.value = true
  error.value = null
  
  // Check cache first (unless force refresh)
  if (!forceRefresh && isCacheValid(devicesCache.value)) {
    console.log('[CACHE] Using cached devices')
    devices.value = devicesCache.value.data
    loading.value = false
    return
  }
  
  console.log('[API] Fetching devices', forceRefresh ? '(forced)' : '')
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/devices')
    const data = await response.json()
    
    if (data.success) {
      devices.value = data.devices
      devicesCache.value = { data: data.devices, timestamp: Date.now() }
      console.log('[CACHE] Devices cached:', data.devices.length, 'items')
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load devices'
  } finally {
    loading.value = false
  }
}

// Export data
const exportData = async (format) => {
  showExportMenu.value = false
  
  try {
    const data = devices.value
    const filename = `devices-${new Date().toISOString().split('T')[0]}.${format}`
    
    if (format === 'csv') {
      // Convert to CSV
      const headers = Object.keys(data[0] || {})
      const csv = [
        headers.join(','),
        ...data.map(item => headers.map(h => {
          const val = item[h]
          return typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        }).join(','))
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
    } else {
      // JSON format
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error('Export failed:', err)
  }
}

const getJoinTypeClass = (trustType) => {
  switch (trustType) {
    case 'AzureAd':
      return props.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
    case 'Hybrid':
      return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
    case 'Workplace':
      return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-800'
    default:
      return props.isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-600'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold text-sm transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-700 hover:bg-gray-300;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-200 hover:bg-gray-600;
}

.bg-gray-750 {
  background-color: #2d3748;
}
</style>
