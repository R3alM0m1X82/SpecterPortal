<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Administrative Units</h1>
        <p class="mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          Delegated management containers for users, groups and devices
        </p>
      </div>
      <div class="flex items-center space-x-4">
        <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ filteredUnits.length }} unit(s)</span>
        <button @click="loadAdminUnits" :disabled="loading" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
          <span v-if="loading" class="animate-spin mr-2">⏳</span>
          {{ loading ? 'Loading...' : '🔄 Refresh' }}
        </button>
      </div>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search administrative units..."
        class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        :class="isDark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
      />
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading administrative units...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ error }}</p>
      <button @click="loadAdminUnits" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Admin Units List -->
    <div v-else-if="filteredUnits.length > 0" class="space-y-4">
      <div 
        v-for="unit in filteredUnits" 
        :key="unit.id" 
        class="rounded-lg shadow-md overflow-hidden border-l-4 border-purple-500"
        :class="isDark ? 'bg-gray-800' : 'bg-white'"
      >
        <!-- AU Header (clickable) -->
        <div 
          @click="toggleExpand(unit.id)"
          class="p-4 cursor-pointer"
          :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-purple-50'"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <span class="text-2xl">🏢</span>
                <div>
                  <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                    {{ unit.displayName }}
                  </h3>
                  <p v-if="unit.description" class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                    {{ unit.description }}
                  </p>
                </div>
              </div>
            </div>
            
            <div class="flex items-center space-x-3">
              <!-- Badges -->
              <span v-if="unit.isMemberManagementRestricted" 
                    class="px-2 py-1 text-xs font-semibold rounded"
                    :class="isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800'">
                🔒 Restricted
              </span>
              <span :class="getMembershipTypeClass(unit.membershipType)" 
                    class="px-2 py-1 text-xs font-semibold rounded">
                {{ unit.membershipType || 'Assigned' }}
              </span>
              
              <!-- Member count badge (if loaded) -->
              <span v-if="unitMembers[unit.id]" 
                    class="px-3 py-1 rounded-full text-sm font-medium"
                    :class="isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'">
                {{ unitMembers[unit.id].totalCount }} member(s)
              </span>
              <span v-else-if="loadingMembers[unit.id]" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                Loading...
              </span>
              
              <!-- Expand icon -->
              <svg 
                class="w-5 h-5 transition-transform"
                :class="[isDark ? 'text-gray-500' : 'text-gray-400', { 'rotate-180': expandedUnit === unit.id }]"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Expanded Members Section -->
        <div v-if="expandedUnit === unit.id" class="border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <!-- Loading members -->
          <div v-if="loadingMembers[unit.id]" class="p-6 text-center">
            <div class="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
            <p class="mt-2 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading members...</p>
          </div>
          
          <!-- Members loaded -->
          <div v-else-if="unitMembers[unit.id]" class="p-4" :class="isDark ? 'bg-purple-900/10' : 'bg-purple-50'">
            <!-- Summary tabs -->
            <div class="flex space-x-4 mb-4">
              <button 
                @click="memberTab[unit.id] = 'users'"
                :class="[
                  'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                  memberTab[unit.id] === 'users' || !memberTab[unit.id]
                    ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white')
                    : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
                ]"
              >
                👤 Users ({{ unitMembers[unit.id].userCount }})
              </button>
              <button 
                @click="memberTab[unit.id] = 'groups'"
                :class="[
                  'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                  memberTab[unit.id] === 'groups'
                    ? (isDark ? 'bg-green-600 text-white' : 'bg-green-500 text-white')
                    : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
                ]"
              >
                👥 Groups ({{ unitMembers[unit.id].groupCount }})
              </button>
              <button 
                v-if="unitMembers[unit.id].deviceCount > 0"
                @click="memberTab[unit.id] = 'devices'"
                :class="[
                  'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                  memberTab[unit.id] === 'devices'
                    ? (isDark ? 'bg-orange-600 text-white' : 'bg-orange-500 text-white')
                    : (isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300')
                ]"
              >
                💻 Devices ({{ unitMembers[unit.id].deviceCount }})
              </button>
            </div>
            
            <!-- Users list -->
            <div v-if="memberTab[unit.id] === 'users' || !memberTab[unit.id]">
              <div v-if="unitMembers[unit.id].users.length === 0" 
                   class="text-center py-6 italic" 
                   :class="isDark ? 'text-gray-500' : 'text-gray-500'">
                No users in this Administrative Unit
              </div>
              <div v-else class="space-y-2 max-h-80 overflow-y-auto">
                <div 
                  v-for="user in unitMembers[unit.id].users" 
                  :key="user.id"
                  class="rounded p-3 flex items-center justify-between"
                  :class="isDark ? 'bg-gray-800' : 'bg-white'"
                >
                  <div class="flex items-center space-x-3">
                    <span class="text-xl">👤</span>
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ user.displayName }}
                      </p>
                      <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        {{ user.userPrincipalName }}
                      </p>
                      <p v-if="user.jobTitle" class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        {{ user.jobTitle }}
                      </p>
                    </div>
                  </div>
                  <span :class="[
                    'px-2 py-1 rounded text-xs font-medium',
                    user.accountEnabled !== false 
                      ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') 
                      : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')
                  ]">
                    {{ user.accountEnabled !== false ? 'Enabled' : 'Disabled' }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Groups list -->
            <div v-else-if="memberTab[unit.id] === 'groups'">
              <div v-if="unitMembers[unit.id].groups.length === 0" 
                   class="text-center py-6 italic" 
                   :class="isDark ? 'text-gray-500' : 'text-gray-500'">
                No groups in this Administrative Unit
              </div>
              <div v-else class="space-y-2 max-h-80 overflow-y-auto">
                <div 
                  v-for="group in unitMembers[unit.id].groups" 
                  :key="group.id"
                  class="rounded p-3 flex items-center justify-between"
                  :class="isDark ? 'bg-gray-800' : 'bg-white'"
                >
                  <div class="flex items-center space-x-3">
                    <span class="text-xl">👥</span>
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ group.displayName }}
                      </p>
                      <p v-if="group.description" class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        {{ group.description }}
                      </p>
                      <p v-if="group.mail" class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        {{ group.mail }}
                      </p>
                    </div>
                  </div>
                  <span :class="[
                    'px-2 py-1 rounded text-xs font-medium',
                    group.securityEnabled 
                      ? (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')
                      : (isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600')
                  ]">
                    {{ group.securityEnabled ? 'Security' : 'M365' }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Devices list -->
            <div v-else-if="memberTab[unit.id] === 'devices'">
              <div v-if="unitMembers[unit.id].devices.length === 0" 
                   class="text-center py-6 italic" 
                   :class="isDark ? 'text-gray-500' : 'text-gray-500'">
                No devices in this Administrative Unit
              </div>
              <div v-else class="space-y-2 max-h-80 overflow-y-auto">
                <div 
                  v-for="device in unitMembers[unit.id].devices" 
                  :key="device.id"
                  class="rounded p-3 flex items-center justify-between"
                  :class="isDark ? 'bg-gray-800' : 'bg-white'"
                >
                  <div class="flex items-center space-x-3">
                    <span class="text-xl">💻</span>
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ device.displayName }}
                      </p>
                      <p v-if="device.operatingSystem" class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        {{ device.operatingSystem }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Error loading members -->
          <div v-else-if="memberErrors[unit.id]" class="p-4 text-center">
            <p class="text-red-500">{{ memberErrors[unit.id] }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty -->
    <div v-else class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="text-6xl mb-4">🏢</div>
      <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">No Administrative Units Found</h2>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">Administrative units allow delegated management of users and groups.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, defineProps } from 'vue'

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

const adminUnits = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

// Expansion state
const expandedUnit = ref(null)
const unitMembers = ref({})
const loadingMembers = ref({})
const memberErrors = ref({})
const memberTab = reactive({})

const filteredUnits = computed(() => {
  if (!searchQuery.value.trim()) {
    return adminUnits.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return adminUnits.value.filter(unit => 
    unit.displayName?.toLowerCase().includes(query) ||
    unit.description?.toLowerCase().includes(query)
  )
})

const loadAdminUnits = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/admin-units')
    const data = await response.json()
    
    if (data.success) {
      adminUnits.value = data.adminUnits
    } else {
      error.value = data.error || 'Failed to load administrative units'
    }
  } catch (err) {
    error.value = 'Failed to load administrative units: ' + err.message
  } finally {
    loading.value = false
  }
}

const toggleExpand = async (unitId) => {
  if (expandedUnit.value === unitId) {
    expandedUnit.value = null
    return
  }
  
  expandedUnit.value = unitId
  
  // Initialize tab to users
  if (!memberTab[unitId]) {
    memberTab[unitId] = 'users'
  }
  
  // Load members if not already loaded
  if (!unitMembers.value[unitId] && !loadingMembers.value[unitId]) {
    loadingMembers.value[unitId] = true
    memberErrors.value[unitId] = null
    
    try {
      const response = await fetch(`http://localhost:5000/api/tenant/admin-units/${unitId}/members`)
      const data = await response.json()
      
      if (data.success) {
        unitMembers.value[unitId] = {
          users: data.users || [],
          groups: data.groups || [],
          devices: data.devices || [],
          userCount: data.userCount || 0,
          groupCount: data.groupCount || 0,
          deviceCount: data.deviceCount || 0,
          totalCount: data.totalCount || 0
        }
      } else {
        memberErrors.value[unitId] = data.error || 'Failed to load members'
      }
    } catch (err) {
      memberErrors.value[unitId] = 'Failed to load members: ' + err.message
    } finally {
      loadingMembers.value[unitId] = false
    }
  }
}

const getMembershipTypeClass = (type) => {
  switch (type) {
    case 'Dynamic':
      return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
    case 'Assigned':
    default:
      return props.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
  }
}

onMounted(() => {
  loadAdminUnits()
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
