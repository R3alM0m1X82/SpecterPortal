<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
          👥 External Users
        </h1>
        <span 
          class="px-3 py-1 rounded-full text-sm font-medium"
          :class="isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800'"
        >
          {{ guests.length }} Guests
        </span>
      </div>
      
      <div class="flex items-center space-x-3">
        <!-- Filter Dropdown -->
        <select 
          v-model="activeFilter"
          class="px-3 py-2 rounded-lg text-sm border"
          :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-700'"
        >
          <option value="all">All Guests</option>
          <option value="pending">Pending Acceptance</option>
          <option value="accepted">Accepted</option>
          <option value="disabled">Disabled</option>
          <option value="inactive">Inactive (90+ days)</option>
          <option value="never">Never Signed In</option>
        </select>
        
        <!-- Export Button -->
        <div class="relative">
          <button 
            @click="showExportMenu = !showExportMenu"
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
        
        <!-- Refresh Button -->
        <button 
          @click="loadGuests" 
          :disabled="loading" 
          class="btn" 
          :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'"
        >
          <span v-if="loading" class="animate-spin mr-2">⏳</span>
          {{ loading ? 'Loading...' : '🔄 Refresh' }}
        </button>
      </div>
    </div>
    
    <!-- Stats Cards -->
    <div v-if="stats && !loading" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ stats.total }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Total Guests</p>
      </div>
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold text-yellow-500">{{ stats.pending }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Pending</p>
      </div>
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold text-green-500">{{ stats.accepted }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Accepted</p>
      </div>
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold text-red-500">{{ stats.disabled }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Disabled</p>
      </div>
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold text-orange-500">{{ stats.neverSignedIn }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Never Signed In</p>
      </div>
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <p class="text-2xl font-bold text-blue-500">{{ stats.recentlyCreated }}</p>
        <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Recent (30d)</p>
      </div>
    </div>
    
    <!-- Source Tenants -->
    <div v-if="stats && stats.sourceTenants && stats.sourceTenants.length > 0 && !loading" class="mb-6">
      <div class="rounded-lg p-4" :class="isDark ? 'bg-gray-800' : 'bg-white shadow'">
        <h3 class="font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">
          🌐 Source Tenants
        </h3>
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="tenant in stats.sourceTenants" 
            :key="tenant.tenant"
            class="px-3 py-1 rounded-full text-sm"
            :class="isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'"
          >
            {{ tenant.tenant }} <strong>({{ tenant.count }})</strong>
          </span>
        </div>
      </div>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search guests by name, email, or source tenant..."
        class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        :class="isDark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
      />
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading external users...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ error }}</p>
      <button @click="loadGuests" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="filteredGuests.length === 0" class="text-center py-12">
      <p class="text-4xl mb-4">👻</p>
      <p class="text-xl font-semibold" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
        {{ searchQuery || activeFilter !== 'all' ? 'No guests match your criteria' : 'No external users found' }}
      </p>
      <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
        {{ searchQuery || activeFilter !== 'all' ? 'Try adjusting your filters' : 'This tenant has no guest users' }}
      </p>
    </div>
    
    <!-- Guests Table -->
    <div v-else class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Source Tenant</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">State</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Created</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Last Sign-In</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr 
            v-for="guest in filteredGuests" 
            :key="guest.id" 
            :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'"
          >
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <span class="text-lg mr-2">👤</span>
                <div>
                  <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-900'" :title="`ID: ${guest.id}`">
                    {{ guest.displayName }}
                  </p>
                  <p class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    {{ guest.companyName || 'No company' }}
                  </p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ guest.mail || guest.otherMails?.[0] || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span 
                v-if="guest.sourceTenant"
                class="px-2 py-1 rounded text-xs font-medium"
                :class="isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'"
              >
                {{ guest.sourceTenant }}
              </span>
              <span v-else :class="isDark ? 'text-gray-500' : 'text-gray-400'">Unknown</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span 
                class="px-2 py-1 text-xs font-semibold rounded"
                :class="getStateClass(guest.externalUserState)"
              >
                {{ guest.externalUserState || 'Unknown' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              <div>
                {{ formatDate(guest.createdDateTime) }}
                <span v-if="guest.daysSinceCreation !== null" class="text-xs block" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  ({{ guest.daysSinceCreation }}d ago)
                </span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <div v-if="guest.lastSignIn">
                <span :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ formatDate(guest.lastSignIn) }}</span>
              </div>
              <span 
                v-else 
                class="px-2 py-1 text-xs font-semibold rounded"
                :class="isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800'"
              >
                Never
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span 
                :class="guest.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')" 
                class="px-2 py-1 text-xs font-semibold rounded-full"
              >
                {{ guest.accountEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <button
                @click="openDetailModal(guest)"
                class="px-3 py-1 text-sm font-medium rounded-lg transition-colors"
                :class="isDark ? 'bg-blue-900 text-blue-300 hover:bg-blue-800' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'"
              >
                🔍 Details
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Detail Modal -->
    <div 
      v-if="showDetailModal" 
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="showDetailModal = false"
    >
      <div 
        class="w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-lg shadow-xl p-6"
        :class="isDark ? 'bg-gray-800' : 'bg-white'"
      >
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
            👤 Guest Details
          </h2>
          <button 
            @click="showDetailModal = false"
            class="text-2xl"
            :class="isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'"
          >
            ×
          </button>
        </div>
        
        <div v-if="loadingDetails" class="text-center py-8">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading details...</p>
        </div>
        
        <div v-else-if="selectedGuest" class="space-y-4">
          <!-- Basic Info -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.displayName }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Email</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.mail || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">UPN</p>
              <p class="text-xs font-mono break-all" :class="isDark ? 'text-gray-300' : 'text-gray-700'">{{ selectedGuest.userPrincipalName }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Object ID</p>
              <p class="text-xs font-mono" :class="isDark ? 'text-gray-300' : 'text-gray-700'">{{ selectedGuest.id }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Source Tenant</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.sourceTenant || 'Unknown' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Company</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.companyName || 'N/A' }}</p>
            </div>
          </div>
          
          <!-- Invited By -->
          <div v-if="selectedGuest.invitedBy" class="p-3 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
            <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">📨 Invited By</p>
            <p :class="isDark ? 'text-white' : 'text-gray-900'">
              {{ selectedGuest.invitedBy.displayName }} 
              <span class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                ({{ selectedGuest.invitedBy.userPrincipalName }})
              </span>
            </p>
            <p v-if="selectedGuest.invitedBy.invitedOn" class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
              on {{ formatDate(selectedGuest.invitedBy.invitedOn) }}
            </p>
          </div>
          
          <!-- Group Memberships -->
          <div>
            <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              👥 Group Memberships ({{ selectedGuest.groupCount || 0 }})
            </p>
            <div v-if="selectedGuest.memberships && selectedGuest.memberships.length > 0" class="space-y-2 max-h-48 overflow-y-auto">
              <div 
                v-for="membership in selectedGuest.memberships" 
                :key="membership.id"
                class="p-2 rounded text-sm flex items-center justify-between"
                :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
              >
                <div class="flex items-center space-x-2">
                  <span>{{ membership.type === 'group' ? '👥' : '🛡️' }}</span>
                  <span :class="isDark ? 'text-white' : 'text-gray-900'">{{ membership.displayName }}</span>
                </div>
                <span 
                  class="px-2 py-0.5 text-xs rounded"
                  :class="membership.securityEnabled ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')"
                >
                  {{ membership.securityEnabled ? 'Security' : 'M365' }}
                </span>
              </div>
            </div>
            <p v-else class="text-sm" :class="isDark ? 'text-gray-500' : 'text-gray-400'">No group memberships</p>
          </div>
          
          <!-- Sign-In Activity -->
          <div class="grid grid-cols-2 gap-4 p-3 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Last Interactive Sign-In</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.lastSignIn ? formatDate(selectedGuest.lastSignIn) : 'Never' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Last Non-Interactive</p>
              <p :class="isDark ? 'text-white' : 'text-gray-900'">{{ selectedGuest.lastNonInteractiveSignIn ? formatDate(selectedGuest.lastNonInteractiveSignIn) : 'Never' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

// State
const guests = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const activeFilter = ref('all')
const showExportMenu = ref(false)
const showDetailModal = ref(false)
const selectedGuest = ref(null)
const loadingDetails = ref(false)

// Computed
const filteredGuests = computed(() => {
  let result = guests.value
  
  // Apply filter
  if (activeFilter.value !== 'all') {
    switch (activeFilter.value) {
      case 'pending':
        result = result.filter(g => g.externalUserState === 'PendingAcceptance')
        break
      case 'accepted':
        result = result.filter(g => g.externalUserState === 'Accepted')
        break
      case 'disabled':
        result = result.filter(g => !g.accountEnabled)
        break
      case 'inactive':
        result = result.filter(g => {
          if (!g.lastSignIn) return true
          const lastSignIn = new Date(g.lastSignIn)
          const daysAgo = (Date.now() - lastSignIn.getTime()) / (1000 * 60 * 60 * 24)
          return daysAgo > 90
        })
        break
      case 'never':
        result = result.filter(g => !g.lastSignIn)
        break
    }
  }
  
  // Apply search
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(g => 
      g.displayName?.toLowerCase().includes(query) ||
      g.mail?.toLowerCase().includes(query) ||
      g.sourceTenant?.toLowerCase().includes(query) ||
      g.companyName?.toLowerCase().includes(query)
    )
  }
  
  return result
})

// Methods
const loadGuests = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/external-users')
    const data = await response.json()
    
    if (data.success) {
      guests.value = data.guests
      stats.value = data.stats
    } else {
      error.value = data.error || 'Failed to load external users'
    }
  } catch (err) {
    error.value = 'Failed to connect to server: ' + err.message
  } finally {
    loading.value = false
  }
}

const openDetailModal = async (guest) => {
  showDetailModal.value = true
  loadingDetails.value = true
  selectedGuest.value = guest
  
  try {
    const response = await fetch(`http://localhost:5000/api/external-users/${guest.id}`)
    const data = await response.json()
    
    if (data.success) {
      selectedGuest.value = data.guest
    }
  } catch (err) {
    console.error('Failed to load guest details:', err)
  } finally {
    loadingDetails.value = false
  }
}

const exportData = async (format) => {
  showExportMenu.value = false
  
  try {
    if (format === 'csv') {
      window.location.href = 'http://localhost:5000/api/external-users/export?format=csv'
    } else {
      const response = await fetch('http://localhost:5000/api/external-users/export?format=json')
      const data = await response.json()
      
      if (data.success) {
        const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'external_users.json'
        a.click()
        URL.revokeObjectURL(url)
      }
    }
  } catch (err) {
    console.error('Export failed:', err)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getStateClass = (state) => {
  switch (state) {
    case 'Accepted':
      return props.isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'
    case 'PendingAcceptance':
      return props.isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800'
    default:
      return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'
  }
}

// Lifecycle
onMounted(() => {
  loadGuests()
})

// Close export menu on click outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.relative')) {
    showExportMenu.value = false
  }
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
