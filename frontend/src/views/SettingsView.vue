<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Settings</h1>
        <p class="mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Manage database and application settings</p>
      </div>
    </div>

    <!-- Database Management Section -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-6">
        <!-- Database Icon SVG -->
        <div class="flex-shrink-0 w-8 h-8">
          <svg id="database-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18" class="w-full h-full">
            <path d="M1.155,4.93v.512L9,9.868l7.006-3.957,0,1.6L9,11.491,1.55,7.258l-.395.22V10.54L9,14.955l7.006-3.942,0,1.586L9,16.581,1.55,12.347l-.395.22v.519L9,17.5l7.845-4.414V10.021l-.4-.218L9,14.036,1.992,10.054V8.476L9,12.414,16.845,8V4.978l-.4-.219L9,8.993,2.352,5.215,9,1.46l5.476,3.094.479-.269V3.863L9,.5Z" fill="#ff3621"/>
          </svg>
        </div>
        <div>
          <h2 class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
            Database Management
          </h2>
          <p class="text-sm mt-0.5" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
            Manage, backup, and optimize your SpecterPortal database
          </p>
        </div>
      </div>
      
      <!-- Current Database Info Card -->
      <div class="rounded-lg shadow-md p-6 mb-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">Current Database</h3>
          <button 
            @click="loadDatabaseInfo" 
            class="text-sm px-3 py-1 rounded-lg transition-colors"
            :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          >
            🔄 Refresh
          </button>
        </div>
        
        <div v-if="loadingInfo" class="text-center py-4">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        </div>
        
        <div v-else-if="dbInfo" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- DB Name -->
            <div class="p-4 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
              <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Database Name</p>
              <p class="font-mono text-sm" :class="isDark ? 'text-white' : 'text-gray-800'">{{ dbInfo.name }}</p>
            </div>
            
            <!-- Size -->
            <div class="p-4 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
              <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Size</p>
              <p class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">{{ dbInfo.size_human }}</p>
            </div>
            
            <!-- Total Records -->
            <div class="p-4 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
              <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Total Records</p>
              <p class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">{{ dbInfo.total_records || 0 }}</p>
            </div>
          </div>
          
          <!-- Table Breakdown -->
          <div v-if="dbInfo.tables && Object.keys(dbInfo.tables).length > 0">
            <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Tables</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(count, table) in dbInfo.tables"
                :key="table"
                class="px-3 py-1 rounded-full text-xs font-medium"
                :class="count > 0 
                  ? (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700')
                  : (isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500')"
              >
                {{ table }}: {{ count }}
              </span>
            </div>
          </div>
          
          <!-- Last Modified -->
          <p class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
            Last modified: {{ formatDateTime(dbInfo.modified) }}
          </p>
        </div>
      </div>
      
      <!-- Database Actions -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <!-- Backup -->
        <button
          @click="backupDatabase"
          :disabled="actionLoading"
          class="group p-5 rounded-lg shadow-md text-left transition-all hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600' : 'bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300'"
        >
          <div class="text-3xl mb-3 transition-transform group-hover:scale-110">💾</div>
          <h4 class="font-semibold mb-1" :class="isDark ? 'text-white' : 'text-gray-800'">Backup Database</h4>
          <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Create a timestamped backup</p>
        </button>
        
        <!-- Download -->
        <button
          @click="downloadDatabase"
          :disabled="actionLoading"
          class="group p-5 rounded-lg shadow-md text-left transition-all hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600' : 'bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300'"
        >
          <div class="text-3xl mb-3 transition-transform group-hover:scale-110">📥</div>
          <h4 class="font-semibold mb-1" :class="isDark ? 'text-white' : 'text-gray-800'">Download Database</h4>
          <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Export .db file</p>
        </button>
        
        <!-- Optimize -->
        <button
          @click="vacuumDatabase"
          :disabled="actionLoading"
          class="group p-5 rounded-lg shadow-md text-left transition-all hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600' : 'bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300'"
        >
          <div class="text-3xl mb-3 transition-transform group-hover:scale-110">⚡</div>
          <h4 class="font-semibold mb-1" :class="isDark ? 'text-white' : 'text-gray-800'">Optimize Database</h4>
          <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Run VACUUM to reclaim space</p>
        </button>
        
        <!-- Reset (Danger) -->
        <button
          @click="showResetModal = true"
          :disabled="actionLoading"
          class="group p-5 rounded-lg shadow-md text-left transition-all hover:shadow-xl hover:-translate-y-0.5 border-2 border-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          :class="isDark ? 'bg-red-900/30 hover:bg-red-900/50' : 'bg-red-50 hover:bg-red-100'"
        >
          <div class="text-3xl mb-3 transition-transform group-hover:scale-110">🗑️</div>
          <h4 class="font-semibold text-red-500 mb-1">Reset Database</h4>
          <p class="text-xs" :class="isDark ? 'text-red-400' : 'text-red-600'">Delete all data</p>
        </button>
      </div>
      
      <!-- Create New Database -->
      <div class="rounded-lg shadow-md p-6 mb-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h3 class="font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Create New Database</h3>
        <div class="flex space-x-4">
          <input
            v-model="newDbName"
            type="text"
            placeholder="Database name (optional)"
            class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            :class="isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
          />
          <button
            @click="createDatabase"
            :disabled="actionLoading"
            class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold"
          >
            ➕ Create
          </button>
        </div>
        <p class="text-xs mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          Leave empty for auto-generated name. New database will be empty and ready for GitHub publishing.
        </p>
      </div>
      
      <!-- Available Databases -->
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">Available Databases</h3>
          <button 
            @click="loadDatabaseList" 
            class="text-sm px-3 py-1 rounded-lg transition-colors"
            :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          >
            🔄 Refresh
          </button>
        </div>
        
        <div v-if="loadingList" class="text-center py-4">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        </div>
        
        <div v-else-if="databases.length === 0" class="text-center py-8">
          <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">No databases found</p>
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="db in databases"
            :key="db.name"
            class="flex items-center justify-between p-4 rounded-lg"
            :class="[
              db.is_active 
                ? (isDark ? 'bg-blue-900/30 border border-blue-500' : 'bg-blue-50 border border-blue-200')
                : (isDark ? 'bg-gray-700' : 'bg-gray-50')
            ]"
          >
            <div>
              <div class="flex items-center space-x-2">
                <span class="font-mono text-sm" :class="isDark ? 'text-white' : 'text-gray-800'">{{ db.name }}</span>
                <span v-if="db.is_active" class="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-600 text-white">
                  ACTIVE
                </span>
              </div>
              <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                {{ db.size_human }} • Modified: {{ formatDateTime(db.modified) }}
              </p>
            </div>
            
            <div class="flex space-x-2">
              <button
                v-if="!db.is_active"
                @click="confirmDeleteDb = db.name"
                class="px-3 py-1 text-xs rounded-lg transition-colors"
                :class="isDark ? 'bg-red-900 text-red-300 hover:bg-red-800' : 'bg-red-100 text-red-700 hover:bg-red-200'"
              >
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
        
        <p class="text-xs mt-4" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
          💡 Tip: To switch databases, modify the DATABASE_PATH in config.py and restart the server.
        </p>
      </div>
    </div>
    
    <!-- Application Info -->
    <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <h3 class="font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Application Info</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <p class="text-xs font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Version</p>
          <p class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">v2.0.0</p>
        </div>
        <div>
          <p class="text-xs font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Project</p>
          <p class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">SpecterPortal</p>
        </div>
        <div>
          <p class="text-xs font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Data Directory</p>
          <p class="font-mono text-xs" :class="isDark ? 'text-gray-300' : 'text-gray-600'">{{ dataDirectory }}</p>
        </div>
      </div>
    </div>
    
    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 max-w-md w-full mx-4" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h3 class="text-xl font-bold text-red-500 mb-4">⚠️ Reset Database</h3>
        <p :class="isDark ? 'text-gray-300' : 'text-gray-600'" class="mb-4">
          This will <strong>permanently delete</strong> all data in the current database. This action cannot be undone.
        </p>
        <p :class="isDark ? 'text-gray-400' : 'text-gray-500'" class="text-sm mb-4">
          Consider creating a backup first.
        </p>
        
        <div class="mb-4">
          <label class="text-sm font-medium" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
            Type <strong>RESET</strong> to confirm:
          </label>
          <input
            v-model="resetConfirmText"
            type="text"
            class="w-full mt-2 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500"
            :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
            placeholder="Type RESET"
          />
        </div>
        
        <div class="flex justify-end space-x-3">
          <button
            @click="showResetModal = false; resetConfirmText = ''"
            class="px-4 py-2 rounded-lg transition-colors"
            :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
          >
            Cancel
          </button>
          <button
            @click="resetDatabase"
            :disabled="resetConfirmText !== 'RESET'"
            class="px-4 py-2 rounded-lg font-semibold transition-colors"
            :class="resetConfirmText === 'RESET' 
              ? 'bg-red-600 text-white hover:bg-red-700' 
              : 'bg-gray-400 text-gray-200 cursor-not-allowed'"
          >
            Reset Database
          </button>
        </div>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="confirmDeleteDb" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 max-w-md w-full mx-4" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h3 class="text-xl font-bold text-red-500 mb-4">🗑️ Delete Database</h3>
        <p :class="isDark ? 'text-gray-300' : 'text-gray-600'" class="mb-4">
          Delete <strong>{{ confirmDeleteDb }}</strong>? This cannot be undone.
        </p>
        
        <div class="flex justify-end space-x-3">
          <button
            @click="confirmDeleteDb = null"
            class="px-4 py-2 rounded-lg transition-colors"
            :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
          >
            Cancel
          </button>
          <button
            @click="deleteDatabase(confirmDeleteDb)"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
    
    <!-- Toast Notification -->
    <div 
      v-if="toast.show" 
      class="fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all"
      :class="toast.type === 'success' 
        ? 'bg-green-600 text-white' 
        : toast.type === 'error' 
          ? 'bg-red-600 text-white'
          : 'bg-blue-600 text-white'"
    >
      {{ toast.message }}
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

// State
const dbInfo = ref(null)
const databases = ref([])
const loadingInfo = ref(false)
const loadingList = ref(false)
const actionLoading = ref(false)
const newDbName = ref('')
const showResetModal = ref(false)
const resetConfirmText = ref('')
const confirmDeleteDb = ref(null)
const dataDirectory = ref('')

// Toast
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// Load database info
const loadDatabaseInfo = async () => {
  loadingInfo.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/info')
    const data = await response.json()
    
    if (data.success) {
      dbInfo.value = data.database
      dataDirectory.value = data.data_directory
    }
  } catch (error) {
    console.error('Failed to load database info:', error)
    showToast('Failed to load database info', 'error')
  } finally {
    loadingInfo.value = false
  }
}

// Load database list
const loadDatabaseList = async () => {
  loadingList.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/list')
    const data = await response.json()
    
    if (data.success) {
      databases.value = data.databases
    }
  } catch (error) {
    console.error('Failed to load database list:', error)
    showToast('Failed to load database list', 'error')
  } finally {
    loadingList.value = false
  }
}

// Backup database
const backupDatabase = async () => {
  actionLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/backup', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      showToast(data.message, 'success')
      await loadDatabaseList()
    } else {
      showToast(data.error, 'error')
    }
  } catch (error) {
    showToast('Backup failed', 'error')
  } finally {
    actionLoading.value = false
  }
}

// Download database
const downloadDatabase = () => {
  window.open('http://localhost:5000/api/database/download', '_blank')
}

// Vacuum database
const vacuumDatabase = async () => {
  actionLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/vacuum', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      showToast(`Optimized! Saved ${data.space_saved_human}`, 'success')
      await loadDatabaseInfo()
    } else {
      showToast(data.error, 'error')
    }
  } catch (error) {
    showToast('Optimization failed', 'error')
  } finally {
    actionLoading.value = false
  }
}

// Reset database
const resetDatabase = async () => {
  if (resetConfirmText.value !== 'RESET') return
  
  actionLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: true })
    })
    const data = await response.json()
    
    if (data.success) {
      showToast('Database reset successfully', 'success')
      showResetModal.value = false
      resetConfirmText.value = ''
      await loadDatabaseInfo()
    } else {
      showToast(data.error, 'error')
    }
  } catch (error) {
    showToast('Reset failed', 'error')
  } finally {
    actionLoading.value = false
  }
}

// Create new database
const createDatabase = async () => {
  actionLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newDbName.value })
    })
    const data = await response.json()
    
    if (data.success) {
      showToast(data.message, 'success')
      newDbName.value = ''
      await loadDatabaseList()
    } else {
      showToast(data.error, 'error')
    }
  } catch (error) {
    showToast('Create failed', 'error')
  } finally {
    actionLoading.value = false
  }
}

// Delete database
const deleteDatabase = async (name) => {
  actionLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/database/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, confirm: true })
    })
    const data = await response.json()
    
    if (data.success) {
      showToast(data.message, 'success')
      confirmDeleteDb.value = null
      await loadDatabaseList()
    } else {
      showToast(data.error, 'error')
    }
  } catch (error) {
    showToast('Delete failed', 'error')
  } finally {
    actionLoading.value = false
  }
}

// Format datetime
const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleString()
}

// Mount
onMounted(() => {
  loadDatabaseInfo()
  loadDatabaseList()
})
</script>

<style scoped>
.bg-gray-750 {
  background-color: #2d3748;
}
</style>
