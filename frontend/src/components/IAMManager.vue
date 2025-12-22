<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeModal">
    <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 transition-opacity" @click="closeModal">
        <div class="absolute inset-0 bg-black opacity-75"></div>
      </div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full"
           :class="isDark ? 'bg-gray-800' : 'bg-white'"
           @click.stop>
        
        <!-- Header -->
        <div class="px-6 py-4 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">
                🔐 IAM - {{ resourceName }}
              </h3>
              <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                Manage role assignments for this resource
              </p>
            </div>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600 transition-colors">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Body -->
        <div class="px-6 py-4 max-h-[80vh] overflow-y-auto">
          
          <!-- Loading State -->
          <div v-if="loading" class="text-center py-8">
            <div class="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p class="mt-3 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Loading IAM data...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="p-4 rounded-lg mb-4" :class="isDark ? 'bg-red-900/20 text-red-300' : 'bg-red-50 text-red-800'">
            <div class="flex items-start">
              <svg class="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
              <div>
                <p class="font-semibold">Error</p>
                <p class="text-sm mt-1">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- Success Message -->
          <div v-if="successMessage" class="p-4 rounded-lg mb-4" :class="isDark ? 'bg-green-900/20 text-green-300' : 'bg-green-50 text-green-800'">
            <div class="flex items-start">
              <svg class="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <div>
                <p class="font-semibold">Success</p>
                <p class="text-sm mt-1">{{ successMessage }}</p>
              </div>
            </div>
          </div>

          <template v-if="!loading && !error">
            
            <!-- Your Roles -->
            <div class="mb-6">
              <h4 class="text-sm font-semibold mb-3 flex items-center" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Your Roles
              </h4>
              
              <div v-if="yourRoles.length === 0" class="text-sm italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                You have no role assignments on this resource
              </div>
              
              <div v-else class="space-y-2">
                <div v-for="(role, index) in yourRoles" :key="index" 
                     class="p-3 rounded-lg border" 
                     :class="isDark ? 'bg-green-900/20 border-green-700' : 'bg-green-50 border-green-200'">
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center space-x-2">
                        <span class="font-semibold text-sm" :class="isDark ? 'text-green-300' : 'text-green-800'">
                          {{ role.roleName }}
                        </span>
                        <span v-if="role.inherited" class="px-2 py-0.5 text-xs rounded-full"
                              :class="isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-800'">
                          Inherited
                        </span>
                      </div>
                      <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                        You have this role on this resource
                      </p>
                      <p class="text-xs mt-0.5 font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
                        Scope: {{ getScopeDisplay(role.scope) }}
                      </p>
                    </div>
                    <button v-if="!role.inherited && role.canDelete"
                            @click="removeRole(role.assignmentId)"
                            :disabled="actionLoading"
                            class="ml-3 px-3 py-1 text-xs font-semibold rounded transition-colors"
                            :class="actionLoading 
                              ? 'bg-gray-400 text-white cursor-not-allowed'
                              : (isDark ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-red-600 hover:bg-red-700 text-white')">
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Other Assignments (Collapsable) -->
            <div v-if="otherRoles.length > 0" class="mb-6">
              <button 
                @click="showOtherRoles = !showOtherRoles"
                class="w-full flex items-center justify-between p-3 rounded-lg transition-colors"
                :class="isDark ? 'bg-gray-700/30 hover:bg-gray-700/50' : 'bg-gray-100 hover:bg-gray-200'">
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-2" :class="isDark ? 'text-gray-400' : 'text-gray-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span class="text-sm font-semibold" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Other Assignments ({{ otherRoles.length }})
                  </span>
                </div>
                <svg 
                  class="w-5 h-5 transition-transform" 
                  :class="[showOtherRoles ? 'rotate-180' : '', isDark ? 'text-gray-400' : 'text-gray-600']"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              <div v-show="showOtherRoles" class="mt-2 space-y-2">
                <div v-for="(role, index) in otherRoles" :key="index" 
                     class="p-3 rounded-lg border" 
                     :class="isDark ? 'bg-gray-700/50 border-gray-600' : 'bg-gray-50 border-gray-200'">
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center space-x-2">
                        <span class="font-semibold text-sm" :class="isDark ? 'text-white' : 'text-gray-900'">
                          {{ role.roleName }}
                        </span>
                        <span v-if="role.inherited" class="px-2 py-0.5 text-xs rounded-full"
                              :class="isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-800'">
                          Inherited
                        </span>
                      </div>
                      <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        Principal: {{ role.principalName || role.principalId }}
                      </p>
                      <p class="text-xs mt-0.5 font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        Scope: {{ getScopeDisplay(role.scope) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Assign New Role -->
            <div class="border-t pt-4" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
              <h4 class="text-sm font-semibold mb-3 flex items-center" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                Assign New Role
              </h4>

              <div class="space-y-3">
                <!-- Principal (locked to current user) -->
                <div>
                  <label class="block text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                    Principal
                  </label>
                  <div class="px-3 py-2 rounded-lg border text-sm" 
                       :class="isDark ? 'bg-gray-700/30 border-gray-600 text-gray-400' : 'bg-gray-100 border-gray-300 text-gray-600'">
                    {{ currentUserUPN }} (You)
                  </div>
                </div>

                <!-- Role Selection -->
                <div>
                  <label class="block text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                    Role
                  </label>
                  <select v-model="selectedRole" 
                          class="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500"
                          :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'">
                    <option value="">-- Select a role --</option>
                    <option v-for="role in availableRoles" :key="role.id" :value="role.id">
                      {{ role.name }}
                    </option>
                  </select>
                  <p v-if="selectedRoleDescription" class="text-xs mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
                    {{ selectedRoleDescription }}
                  </p>
                </div>

                <!-- Assign Button -->
                <div class="flex justify-end">
                  <button @click="assignRole"
                          :disabled="!selectedRole || actionLoading"
                          class="px-4 py-2 rounded-lg font-semibold text-sm transition-colors"
                          :class="!selectedRole || actionLoading
                            ? 'bg-gray-400 text-white cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'">
                    {{ actionLoading ? '⏳ Assigning...' : '✅ Assign Role' }}
                  </button>
                </div>
              </div>
            </div>

          </template>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t" :class="isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'">
          <div class="flex justify-between items-center">
            <p class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
              Resource: <span class="font-mono">{{ resourceType }}</span>
            </p>
            <button @click="closeModal"
                    class="px-4 py-2 rounded-lg font-semibold text-sm transition-colors"
                    :class="isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'">
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  resourceId: {
    type: String,
    required: true
  },
  resourceName: {
    type: String,
    required: true
  },
  resourceType: {
    type: String,
    required: true
  },
  currentUserUPN: {
    type: String,
    default: 'Unknown User'
  },
  currentUserObjectId: {
    type: String,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'roleAssigned', 'roleRemoved'])

// State
const loading = ref(false)
const error = ref(null)
const successMessage = ref(null)
const actionLoading = ref(false)

const currentRoles = ref([])
const availableRoles = ref([])
const selectedRole = ref('')
const showOtherRoles = ref(false) // Collapse state for other assignments

// Computed
const yourRoles = computed(() => {
  return currentRoles.value.filter(role => 
    role.principalId === props.currentUserObjectId
  )
})

const otherRoles = computed(() => {
  return currentRoles.value.filter(role => 
    role.principalId !== props.currentUserObjectId
  )
})

const selectedRoleDescription = computed(() => {
  if (!selectedRole.value) return ''
  const role = availableRoles.value.find(r => r.id === selectedRole.value)
  return role?.description || ''
})

// Watch for modal open
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    console.log('[IAM] Modal opened with props:', {
      resourceId: props.resourceId,
      resourceName: props.resourceName,
      resourceType: props.resourceType,
      currentUserUPN: props.currentUserUPN,
      currentUserObjectId: props.currentUserObjectId
    })
    loadIAMData()
  } else {
    // Reset on close
    error.value = null
    successMessage.value = null
    selectedRole.value = ''
  }
})

// Methods
const closeModal = () => {
  emit('close')
}

const loadIAMData = async () => {
  loading.value = true
  error.value = null
  
  console.log('[IAM] Loading IAM data for:', props.resourceId, props.resourceType)
  
  // Skip if no resourceId (component mounted but not opened yet)
  if (!props.resourceId) {
    console.log('[IAM] No resourceId, skipping load')
    loading.value = false
    return
  }
  
  try {
    // Load current roles and available roles in parallel
    const [rolesResponse, availableResponse] = await Promise.all([
      axios.get(`http://localhost:5000/api/iam/resource-roles`, {
        params: { resourceId: props.resourceId }
      }),
      axios.get(`http://localhost:5000/api/iam/available-roles`, {
        params: { resourceType: props.resourceType }
      })
    ])

    console.log('[IAM] Roles response:', rolesResponse.data)
    console.log('[IAM] Available roles response:', availableResponse.data)

    if (rolesResponse.data.success) {
      currentRoles.value = rolesResponse.data.roles || []
      console.log('[IAM] Current roles loaded:', currentRoles.value.length)
      console.log('[IAM] Current user objectId:', props.currentUserObjectId)
      
      // Debug filtered roles (computed will run after this)
      const yourCount = currentRoles.value.filter(r => r.principalId === props.currentUserObjectId).length
      const otherCount = currentRoles.value.filter(r => r.principalId !== props.currentUserObjectId).length
      console.log('[IAM] Your roles:', yourCount, '| Other roles:', otherCount)
    } else {
      error.value = rolesResponse.data.error || 'Failed to load current roles'
      console.error('[IAM] Failed to load current roles:', error.value)
    }

    if (availableResponse.data.success) {
      availableRoles.value = availableResponse.data.roles || []
      console.log('[IAM] Available roles loaded:', availableRoles.value.length)
    } else {
      console.warn('[IAM] Failed to load available roles:', availableResponse.data.error)
      // Non-blocking error - continue with empty available roles
    }

  } catch (err) {
    console.error('[IAM] Failed to load IAM data:', err)
    error.value = 'Failed to connect to server'
  } finally {
    loading.value = false
  }
}

const assignRole = async () => {
  if (!selectedRole.value) return

  actionLoading.value = true
  successMessage.value = null
  error.value = null

  try {
    const response = await axios.post('http://localhost:5000/api/iam/assign-role', {
      resourceId: props.resourceId,
      roleDefinitionId: selectedRole.value,
      principalId: props.currentUserObjectId
    })

    if (response.data.success) {
      successMessage.value = 'Role assigned successfully!'
      selectedRole.value = ''
      
      // Reload roles
      await loadIAMData()
      
      // Emit event
      emit('roleAssigned')
    } else {
      error.value = response.data.error || 'Failed to assign role'
    }
  } catch (err) {
    console.error('Failed to assign role:', err)
    error.value = 'Failed to connect to server'
  } finally {
    actionLoading.value = false
  }
}

const removeRole = async (assignmentId) => {
  if (!confirm('Remove this role assignment?')) return

  actionLoading.value = true
  successMessage.value = null
  error.value = null

  try {
    const response = await axios.delete(`http://localhost:5000/api/iam/remove-role/${assignmentId}`, {
      params: { resourceId: props.resourceId }
    })

    if (response.data.success) {
      successMessage.value = 'Role removed successfully!'
      
      // Reload roles
      await loadIAMData()
      
      // Emit event
      emit('roleRemoved')
    } else {
      error.value = response.data.error || 'Failed to remove role'
    }
  } catch (err) {
    console.error('Failed to remove role:', err)
    error.value = err.response?.data?.error || 'Failed to connect to server'
  } finally {
    actionLoading.value = false
  }
}

const getScopeDisplay = (scope) => {
  if (!scope) return 'Unknown'
  
  const parts = scope.split('/')
  
  if (parts.length <= 3) {
    return 'Subscription'
  } else if (parts.includes('resourceGroups') && parts.length <= 5) {
    return `Resource Group: ${parts[parts.indexOf('resourceGroups') + 1]}`
  } else {
    return 'Resource (Direct)'
  }
}
</script>

<style scoped>
/* Modal animation */
.fixed {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
