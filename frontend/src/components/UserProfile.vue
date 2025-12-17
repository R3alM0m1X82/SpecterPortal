<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="text-gray-500 mt-4">Loading profile...</p>
    </div>
    
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600 font-semibold">⚠️ {{ error }}</p>
      <p v-if="errorDetails" class="text-sm text-gray-600 mt-2">{{ errorDetails }}</p>
      <div v-if="errorHint" class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-left">
        <p class="font-semibold text-yellow-800">💡 Possible issue:</p>
        <p class="text-yellow-700">{{ errorHint }}</p>
      </div>
      <button @click="loadProfile" class="mt-4 btn btn-primary">
        Retry
      </button>
    </div>
    
    <div v-else-if="profile" class="flex items-start space-x-4">
      <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <span class="text-2xl text-blue-600">
          {{ getInitials(profile.displayName) }}
        </span>
      </div>
      
      <div class="flex-1">
        <h2 class="text-xl font-bold text-gray-800">
          {{ profile.displayName }}
        </h2>
        <p class="text-gray-600 text-sm">
          {{ profile.mail || profile.userPrincipalName }}
        </p>
        
        <div class="mt-3 space-y-1 text-sm">
          <p v-if="profile.jobTitle" class="text-gray-700">
            <span class="font-semibold">Title:</span> {{ profile.jobTitle }}
          </p>
          <p v-if="profile.officeLocation" class="text-gray-700">
            <span class="font-semibold">Office:</span> {{ profile.officeLocation }}
          </p>
          <p v-if="profile.mobilePhone" class="text-gray-700">
            <span class="font-semibold">Mobile:</span> {{ profile.mobilePhone }}
          </p>
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-8">
      <p class="text-gray-500">No active token selected</p>
      <p class="text-sm text-gray-400 mt-2">Activate a token to view profile</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { graphAPI } from '../services/api'

const profile = ref(null)
const loading = ref(false)
const error = ref(null)
const errorDetails = ref(null)
const errorHint = ref(null)
let refreshInterval = null

const loadProfile = async () => {
  loading.value = true
  error.value = null
  errorDetails.value = null
  errorHint.value = null
  
  try {
    const response = await graphAPI.getUserProfile()
    if (response.data.success) {
      profile.value = response.data.profile
    } else {
      error.value = response.data.error || 'Failed to load profile'
      errorDetails.value = response.data.details
      
      if (response.data.details) {
        const details = response.data.details.toLowerCase()
        if (details.includes('unauthorized') || details.includes('401')) {
          errorHint.value = 'Token may not have correct audience. Need token with audience: graph.microsoft.com'
        } else if (details.includes('forbidden') || details.includes('403')) {
          errorHint.value = 'Token lacks required permissions (scopes) to access user profile'
        } else if (details.includes('expired')) {
          errorHint.value = 'Token has expired. Import fresh tokens.'
        } else if (details.includes('toomanyrequ')) {
          errorHint.value = 'Rate limited by Microsoft. Wait 2-5 minutes and retry.'
        }
      }
    }
  } catch (err) {
    if (err.response?.status === 429) {
      error.value = 'Rate Limited'
      errorHint.value = 'Too many requests to Microsoft Graph. Wait 2-5 minutes and retry.'
    } else if (err.response?.status === 401) {
      error.value = 'No active token'
      errorHint.value = 'Go to Tokens page and click Activate on a token'
    } else if (err.response?.data?.error) {
      error.value = err.response.data.error
      errorDetails.value = err.response?.data?.details
    } else {
      error.value = 'Failed to load profile'
      errorDetails.value = err.message
    }
  } finally {
    loading.value = false
  }
}

const getInitials = (name) => {
  if (!name) return '??'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

onMounted(() => {
  loadProfile()
  refreshInterval = setInterval(loadProfile, 60000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
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
</style>
