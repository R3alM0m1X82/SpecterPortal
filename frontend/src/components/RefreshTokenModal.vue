<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div :class="['rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto', isDark ? 'bg-gray-800' : 'bg-white']">
      <!-- Header -->
      <div class="bg-gradient-to-r from-yellow-500 to-orange-500 text-white p-6 rounded-t-lg">
        <h2 class="text-2xl font-bold flex items-center">
          <span class="mr-2">🔄</span>
          Use Refresh Token
        </h2>
        <p class="text-yellow-100 text-sm mt-1">
          Generate new Access Token from Refresh Token
        </p>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Token Info -->
        <div v-if="token" :class="['rounded-lg p-4 mb-6', isDark ? 'bg-gray-700' : 'bg-gray-50']">
          <h3 :class="['font-semibold mb-2', isDark ? 'text-gray-200' : 'text-gray-700']">Source Refresh Token</h3>
          <div class="space-y-1 text-sm">
            <p><span :class="isDark ? 'text-gray-400' : 'text-gray-500'">ID:</span> <span :class="['font-mono', isDark ? 'text-gray-200' : '']">{{ token.id }}</span></p>
            <p><span :class="isDark ? 'text-gray-400' : 'text-gray-500'">App:</span> <span :class="isDark ? 'text-gray-200' : ''">{{ token.client_app_name }}</span></p>
            <p><span :class="isDark ? 'text-gray-400' : 'text-gray-500'">UPN:</span> <span :class="isDark ? 'text-gray-200' : ''">{{ token.upn || 'N/A' }}</span></p>
            <p v-if="token.is_foci" class="text-purple-400 font-semibold">
              ✓ FOCI Compatible - Can generate tokens for other apps
            </p>
          </div>
        </div>

        <!-- Loading FOCI targets -->
        <div v-if="loadingTargets" class="text-center py-8">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          <p :class="['mt-2', isDark ? 'text-gray-400' : 'text-gray-500']">Loading available apps...</p>
        </div>

        <!-- Error -->
        <div v-if="error" :class="['border rounded-lg p-4 mb-4', isDark ? 'bg-red-900/30 border-red-800' : 'bg-red-50 border-red-200']">
          <p :class="['text-sm', isDark ? 'text-red-400' : 'text-red-800']">{{ error }}</p>
        </div>

        <!-- Target Selection (only for FOCI) -->
        <div v-if="!loadingTargets && fociTargets.length > 0" class="mb-6">
          <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
            Target Application *
          </label>
          <select 
            v-model="selectedTarget"
            :class="[
              'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300'
            ]"
          >
            <option value="">Same app ({{ token.client_app_name }})</option>
            <option 
              v-for="target in sortedFociTargets" 
              :key="target.client_id"
              :value="target.client_id"
              :disabled="target.is_current"
            >
              {{ target.app_name }} {{ target.is_current ? '(current)' : '' }}
            </option>
          </select>
          <p :class="['text-xs mt-1', isDark ? 'text-gray-400' : 'text-gray-500']">
            FOCI allows using this refresh token to generate access tokens for any app in the family
          </p>
        </div>

        <!-- Resource/Scope Selection -->
        <div class="mb-6">
          <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
            Target Resource/Scope *
          </label>
          <select 
            v-model="selectedResource"
            :class="[
              'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-2',
              isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300'
            ]"
          >
            <option value="https://management.azure.com/.default">Azure Management</option>
            <option value="https://vault.azure.net/.default">Azure Key Vault</option>
            <option value="https://graph.windows.net/.default">Azure AD Graph (CAP/Legacy)</option>
            <option value="https://graph.microsoft.com/.default">Microsoft Graph (default)</option>
            <option value="https://outlook.office365.com/.default">Outlook/Exchange</option>
            <option value="https://api.spaces.skype.com/.default">Skype API (Teams Chat)</option>
            <option value="custom">Custom scope...</option>
          </select>

          <!-- Custom scope input -->
          <input 
            v-if="selectedResource === 'custom'"
            v-model="customResource"
            type="text"
            placeholder="https://example.com/.default"
            :class="[
              'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
            ]"
          />
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" :class="['border rounded-lg p-4 mb-4', isDark ? 'bg-green-900/30 border-green-800' : 'bg-green-50 border-green-200']">
          <p :class="['font-semibold', isDark ? 'text-green-400' : 'text-green-800']">✓ {{ successMessage }}</p>
          <p v-if="newTokenId" :class="['text-sm mt-1', isDark ? 'text-green-300' : 'text-green-700']">
            New token created with ID: {{ newTokenId }}
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div :class="['px-6 py-4 rounded-b-lg flex justify-end space-x-3', isDark ? 'bg-gray-700' : 'bg-gray-50']">
        <button
          @click="close"
          :class="[
            'px-4 py-2 border rounded-lg transition-colors',
            isDark ? 'border-gray-600 text-gray-300 hover:bg-gray-600' : 'border-gray-300 text-gray-700 hover:bg-gray-100'
          ]"
        >
          Cancel
        </button>
        <button
          @click="generateToken"
          :disabled="generating || !canGenerate"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="generating">Generating...</span>
          <span v-else>🚀 Generate Access Token</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  isOpen: Boolean,
  token: Object,
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'success'])

const loadingTargets = ref(false)
const fociTargets = ref([])
const selectedTarget = ref('')
const selectedResource = ref('https://graph.microsoft.com/.default')
const customResource = ref('')
const generating = ref(false)
const error = ref('')
const successMessage = ref('')
const newTokenId = ref(null)

const canGenerate = computed(() => {
  if (selectedResource.value === 'custom') {
    return customResource.value.trim().length > 0
  }
  return true
})

const finalResource = computed(() => {
  return selectedResource.value === 'custom' 
    ? customResource.value 
    : selectedResource.value
})

// Sort FOCI targets alphabetically by app name
const sortedFociTargets = computed(() => {
  return [...fociTargets.value].sort((a, b) => {
    return a.app_name.localeCompare(b.app_name)
  })
})

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.token) {
    loadFociTargets()
    resetForm()
  }
})

const loadFociTargets = async () => {
  if (!props.token.is_foci) return

  loadingTargets.value = true
  error.value = ''

  try {
    const response = await axios.get(
      `http://localhost:5000/api/refresh/${props.token.id}/foci-targets`
    )

    if (response.data.success) {
      fociTargets.value = response.data.available_targets || []
    }
  } catch (err) {
    console.error('Failed to load FOCI targets:', err)
    error.value = 'Failed to load available applications'
  } finally {
    loadingTargets.value = false
  }
}

const generateToken = async () => {
  generating.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const payload = {
      target_resource: finalResource.value
    }

    if (selectedTarget.value) {
      payload.target_client_id = selectedTarget.value
    }

    const response = await axios.post(
      `http://localhost:5000/api/refresh/${props.token.id}/use`,
      payload
    )

    if (response.data.success) {
      successMessage.value = response.data.message
      newTokenId.value = response.data.new_token?.id

      // Wait 2 seconds then close and emit success
      setTimeout(() => {
        emit('success')
        close()
      }, 2000)
    } else {
      error.value = response.data.error || 'Failed to generate token'
    }
  } catch (err) {
    console.error('Token generation failed:', err)
    error.value = err.response?.data?.error_description || 
                  err.response?.data?.error || 
                  'Network error occurred'
  } finally {
    generating.value = false
  }
}

const resetForm = () => {
  selectedTarget.value = ''
  selectedResource.value = 'https://graph.microsoft.com/.default'
  customResource.value = ''
  error.value = ''
  successMessage.value = ''
  newTokenId.value = null
}

const close = () => {
  resetForm()
  emit('close')
}
</script>
