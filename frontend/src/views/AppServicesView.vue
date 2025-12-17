<template>
  <div :class="['p-8 min-h-screen', bgContainer]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 :class="['text-3xl font-bold', textPrimary]">App Services</h1>
        <p :class="['text-sm mt-1', textSecondary]">Azure App Service enumeration</p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Subscription Selector -->
        <select 
          v-model="selectedSubscription" 
          @change="loadAppServices"
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
          @click="loadAppServices" 
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
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
        </svg>
        <h3 :class="['text-lg font-semibold mb-2', textTertiary]">Select a Subscription</h3>
        <p :class="[textPlaceholder]">Choose a subscription from the dropdown to view App Services</p>
      </div>

      <!-- App Services Table -->
      <div v-else-if="appServices.length > 0" :class="[bgPrimary, borderPrimary, 'rounded-lg border overflow-hidden']">
        <table class="w-full">
          <thead :class="[bgSecondary]">
            <tr>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Name</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Default Hostname</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Kind</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">Location</th>
              <th :class="['px-6 py-3 text-left text-xs font-medium uppercase tracking-wider', textTertiary]">State</th>
            </tr>
          </thead>
          <tbody :class="['divide-y', isDark ? 'divide-gray-700' : 'divide-gray-300']">
            <tr v-for="app in appServices" :key="app.id" :class="[isDark ? 'hover:bg-gray-750' : 'hover:bg-gray-100', 'transition-colors']">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-8 w-8">
                    <svg class="h-8 w-8" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M0 3.5C0 1.567 1.567 0 3.5 0h11C16.433 0 18 1.567 18 3.5v11c0 1.933-1.567 3.5-3.5 3.5h-11C1.567 18 0 16.433 0 14.5v-11z" fill="url(#appServiceIconGradient)"/>
                      <defs>
                        <linearGradient id="appServiceIconGradient" x1="9" y1="0" x2="9" y2="18" gradientUnits="userSpaceOnUse">
                          <stop stop-color="#0089D6"/>
                          <stop offset="1" stop-color="#005BA1"/>
                        </linearGradient>
                      </defs>
                      <path d="M5 5h8v8H5V5z" stroke="white" stroke-width="1.5" fill="none"/>
                      <path d="M7 7h4M7 9h4M7 11h2" stroke="white" stroke-width="1" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <div :class="['text-sm font-medium', textPrimary]">{{ app.name }}</div>
                    <div :class="['text-xs', textSecondary]">{{ app.id }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-blue-400 hover:text-blue-300">
                <a :href="`https://${app.defaultHostName}`" target="_blank" class="hover:underline">
                  {{ app.defaultHostName }}
                </a>
              </td>
              <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ app.kind }}</td>
              <td :class="['px-6 py-4 whitespace-nowrap text-sm', textTertiary]">{{ app.location }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span 
                  class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                  :class="app.state === 'Running' ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-200 text-green-800') : (isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')"
                >
                  {{ app.state }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No App Services -->
      <div v-else-if="!loading && selectedSubscription" :class="['text-center py-12 rounded-lg border', bgPrimary, borderPrimary]">
        <svg :class="['w-16 h-16 mx-auto mb-4', textIcon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
        </svg>
        <h3 :class="['text-lg font-semibold mb-2', textTertiary]">No App Services</h3>
        <p :class="[textPlaceholder]">No App Services found in this subscription</p>
      </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AppServicesView',
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      subscriptions: [],
      selectedSubscription: '',
      appServices: [],
      loading: false,
      error: null
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
              this.loadAppServices()
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
    
    async loadAppServices() {
      if (!this.selectedSubscription) return
      
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`http://localhost:5000/api/azure/subscriptions/${this.selectedSubscription}/appservices`)
        
        if (response.data.success) {
          this.appServices = response.data.app_services
        } else {
          this.error = response.data.error || 'Failed to load App Services'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message
      } finally {
        this.loading = false
      }
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

