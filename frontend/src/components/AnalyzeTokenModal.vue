<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div :class="['modal-container', isDark ? 'bg-gray-800 text-gray-100' : 'bg-white']">
      <!-- Header -->
      <div :class="['modal-header', isDark ? 'border-gray-700' : 'border-gray-200']">
        <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
          🔍 Analyze Active Token
        </h2>
        <button @click="closeModal" :class="['close-btn', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-800']">
          ✕
        </button>
      </div>

      <!-- Tabs -->
      <div :class="['tabs', isDark ? 'border-gray-700' : 'border-gray-200']">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'tab-button',
            activeTab === tab.id
              ? (isDark ? 'tab-active-dark' : 'tab-active')
              : (isDark ? 'tab-inactive-dark' : 'tab-inactive')
          ]"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="modal-body">
        <!-- JWT Decoder Tab -->
        <div v-show="activeTab === 'decoder'" class="tab-panel">
          <div v-if="loading.decoder" class="loading-state">
            <div class="spinner"></div>
            <p>Decoding JWT...</p>
          </div>

          <div v-else-if="decoderData" class="space-y-4">
            <!-- Identity Badge -->
            <div v-if="decoderData.identity" :class="['identity-badge', isDark ? 'bg-blue-900/30 border-blue-700' : 'bg-blue-50 border-blue-200']">
              <span class="text-2xl">{{ decoderData.identity_type === 'user' ? '👤' : '🤖' }}</span>
              <div>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                  {{ decoderData.identity_type === 'user' ? 'User' : 'Service Principal' }}
                </p>
                <p :class="['text-lg font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
                  {{ decoderData.identity }}
                </p>
              </div>
            </div>

            <!-- Expiration Status -->
            <div :class="[
              'expiration-banner',
              decoderData.is_expired
                ? (isDark ? 'bg-red-900/30 border-red-700' : 'bg-red-50 border-red-200')
                : (isDark ? 'bg-green-900/30 border-green-700' : 'bg-green-50 border-green-200')
            ]">
              <span class="text-2xl">{{ decoderData.is_expired ? '⏱️' : '✅' }}</span>
              <div>
                <p :class="['font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
                  {{ decoderData.is_expired ? 'Token Expired' : 'Token Valid' }}
                </p>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                  {{ formatExpirationTime(decoderData.expires_in_seconds) }}
                </p>
              </div>
            </div>

            <!-- Header Section -->
            <div :class="['claims-section', isDark ? 'bg-gray-700' : 'bg-gray-50']">
              <h3 :class="['claims-title', isDark ? 'text-gray-200' : 'text-gray-800']">📋 Header</h3>
              <pre :class="['claims-content', isDark ? 'text-gray-300' : 'text-gray-700']">{{ JSON.stringify(decoderData.header, null, 2) }}</pre>
            </div>

            <!-- Payload Section -->
            <div :class="['claims-section', isDark ? 'bg-gray-700' : 'bg-gray-50']">
              <h3 :class="['claims-title', isDark ? 'text-gray-200' : 'text-gray-800']">📦 Payload (Claims)</h3>
              <pre :class="['claims-content', isDark ? 'text-gray-300' : 'text-gray-700']">{{ JSON.stringify(decoderData.payload, null, 2) }}</pre>
            </div>
          </div>

          <div v-else :class="['error-state', isDark ? 'text-red-400' : 'text-red-600']">
            Failed to decode token
          </div>
        </div>

        <!-- Scope Analyzer Tab -->
        <div v-show="activeTab === 'scope'" class="tab-panel">
          <div v-if="loading.scope" class="loading-state">
            <div class="spinner"></div>
            <p>Analyzing scopes...</p>
          </div>

          <div v-else-if="scopeData" class="space-y-4">
            <!-- CRITICAL BANNER - Roles Required -->
            <div :class="['warnings-section', isDark ? 'bg-orange-900/40 border-2 border-orange-700' : 'bg-orange-50 border-2 border-orange-300']">
              <div class="flex items-start">
                <svg class="w-6 h-6 text-orange-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h4 :class="['text-lg font-semibold mb-2', isDark ? 'text-orange-300' : 'text-orange-800']">⚠️ Important: Scopes Require Appropriate Roles</h4>
                  <p :class="['text-sm mb-2', isDark ? 'text-orange-200' : 'text-orange-700']">
                    Having powerful scopes is <strong>not sufficient</strong> to perform privileged operations. The user must also hold appropriate <strong>Entra ID directory roles</strong> (e.g., Global Administrator, User Administrator) to execute admin actions like creating users, resetting passwords, or modifying groups.
                  </p>
                  <p :class="['text-sm', isDark ? 'text-orange-200' : 'text-orange-700']">
                    <strong>Example:</strong> A token with <span class="font-mono bg-orange-800/50 px-1 rounded">User.ReadWrite.All</span> scope but <strong>no admin role</strong> can only read users, not create/modify them.
                  </p>
                </div>
              </div>
            </div>

            <!-- Summary Cards -->
            <div class="grid grid-cols-3 gap-4">
              <div :class="['summary-card', isDark ? 'bg-blue-900/30 border-blue-700' : 'bg-blue-50 border-blue-200']">
                <p :class="['text-3xl font-bold', isDark ? 'text-blue-300' : 'text-blue-600']">{{ scopeData.total_scopes }}</p>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Total Scopes</p>
              </div>
              <div :class="['summary-card', isDark ? 'bg-red-900/30 border-red-700' : 'bg-red-50 border-red-200']">
                <p :class="['text-3xl font-bold', isDark ? 'text-red-300' : 'text-red-600']">{{ scopeData.admin_scopes.length }}</p>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Admin Scopes</p>
              </div>
              <div :class="['summary-card', isDark ? 'bg-yellow-900/30 border-yellow-700' : 'bg-yellow-50 border-yellow-200']">
                <p :class="['text-3xl font-bold', isDark ? 'text-yellow-300' : 'text-yellow-600']">{{ scopeData.warnings.length }}</p>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Warnings</p>
              </div>
            </div>

            <!-- Warnings -->
            <div v-if="scopeData.warnings.length > 0" :class="['warnings-section', isDark ? 'bg-yellow-900/30 border-yellow-700' : 'bg-yellow-50 border-yellow-200']">
              <h4 :class="['font-semibold mb-2', isDark ? 'text-yellow-300' : 'text-yellow-800']">⚠️ Security Warnings</h4>
              <ul class="space-y-1">
                <li v-for="(warning, idx) in scopeData.warnings" :key="idx" :class="['text-sm', isDark ? 'text-yellow-200' : 'text-yellow-700']">
                  {{ warning }}
                </li>
              </ul>
            </div>

            <!-- Capabilities by Category -->
            <div v-for="(capabilities, category) in scopeData.capabilities" :key="category" :class="['capability-section', isDark ? 'bg-gray-700' : 'bg-gray-50']">
              <h4 :class="['capability-title', isDark ? 'text-gray-200' : 'text-gray-800']">{{ getCategoryIcon(category) }} {{ category }}</h4>
              <ul class="capability-list">
                <li v-for="(cap, idx) in capabilities" :key="idx" :class="['capability-item', isDark ? 'text-gray-300' : 'text-gray-700']">
                  ✓ {{ cap }}
                </li>
              </ul>
            </div>

            <!-- Missing High-Value Scopes -->
            <div v-if="scopeData.missing_high_value.length > 0" :class="['missing-scopes', isDark ? 'bg-gray-700' : 'bg-gray-50']">
              <h4 :class="['font-semibold mb-2', isDark ? 'text-gray-200' : 'text-gray-800']">🔒 Missing High-Value Scopes</h4>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="scope in scopeData.missing_high_value"
                  :key="scope"
                  :class="['scope-badge', isDark ? 'bg-red-900/50 text-red-300 border-red-700' : 'bg-red-50 text-red-700 border-red-200']"
                >
                  {{ scope }}
                </span>
              </div>
            </div>
          </div>

          <div v-else :class="['error-state', isDark ? 'text-red-400' : 'text-red-600']">
            Failed to analyze scopes
          </div>
        </div>

        <!-- Token Validator Tab -->
        <div v-show="activeTab === 'validator'" class="tab-panel">
          <div v-if="loading.validator" class="loading-state">
            <div class="spinner"></div>
            <p>Validating token...</p>
          </div>

          <div v-else-if="validatorData" class="space-y-4">
            <!-- Overall Status -->
            <div :class="[
              'status-banner',
              validatorData.can_be_used
                ? (isDark ? 'bg-green-900/30 border-green-700' : 'bg-green-50 border-green-200')
                : (isDark ? 'bg-red-900/30 border-red-700' : 'bg-red-50 border-red-200')
            ]">
              <span class="text-4xl">{{ validatorData.can_be_used ? '✅' : '❌' }}</span>
              <div>
                <p :class="['text-xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">
                  {{ validatorData.can_be_used ? 'Token Can Be Used' : 'Token Cannot Be Used' }}
                </p>
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                  {{ validatorData.valid ? 'All checks passed' : 'Some checks failed' }}
                </p>
              </div>
            </div>

            <!-- Validation Checks -->
            <div class="space-y-3">
              <div
                v-for="(check, name) in validatorData.checks"
                :key="name"
                :class="[
                  'check-item',
                  isDark ? 'bg-gray-700' : 'bg-gray-50'
                ]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <span class="text-2xl">{{ check.valid ? '✅' : '❌' }}</span>
                    <div>
                      <p :class="['font-semibold', isDark ? 'text-gray-200' : 'text-gray-800']">
                        {{ formatCheckName(name) }}
                      </p>
                      <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                        {{ check.message }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Warnings -->
            <div v-if="validatorData.warnings.length > 0" :class="['warnings-section', isDark ? 'bg-yellow-900/30 border-yellow-700' : 'bg-yellow-50 border-yellow-200']">
              <h4 :class="['font-semibold mb-2', isDark ? 'text-yellow-300' : 'text-yellow-800']">⚠️ Warnings</h4>
              <ul class="space-y-1">
                <li v-for="(warning, idx) in validatorData.warnings" :key="idx" :class="['text-sm', isDark ? 'text-yellow-200' : 'text-yellow-700']">
                  {{ warning }}
                </li>
              </ul>
            </div>
          </div>

          <div v-else :class="['error-state', isDark ? 'text-red-400' : 'text-red-600']">
            Failed to validate token
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div :class="['modal-footer', isDark ? 'border-gray-700' : 'border-gray-200']">
        <button @click="closeModal" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { tokenAPI } from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const tabs = [
  { id: 'decoder', icon: '🔍', label: 'JWT Decoder' },
  { id: 'scope', icon: '📊', label: 'Graph Scope Analyzer' },
  { id: 'validator', icon: '✅', label: 'Token Validator' }
]

const activeTab = ref('decoder')
const loading = ref({
  decoder: false,
  scope: false,
  validator: false
})

const decoderData = ref(null)
const scopeData = ref(null)
const validatorData = ref(null)

// Watch show prop to load data when modal opens
watch(() => props.show, (newVal) => {
  if (newVal) {
    loadAllData()
  }
})

const loadAllData = async () => {
  // Load all tabs data in parallel
  await Promise.all([
    loadDecoderData(),
    loadScopeData(),
    loadValidatorData()
  ])
}

const loadDecoderData = async () => {
  loading.value.decoder = true
  try {
    const response = await tokenAPI.decodeJwt()
    if (response.data.success) {
      decoderData.value = response.data
    }
  } catch (error) {
    console.error('Decoder error:', error)
  } finally {
    loading.value.decoder = false
  }
}

const loadScopeData = async () => {
  loading.value.scope = true
  try {
    const response = await tokenAPI.analyzeScope()
    if (response.data.success) {
      scopeData.value = response.data
    }
  } catch (error) {
    console.error('Scope analyzer error:', error)
  } finally {
    loading.value.scope = false
  }
}

const loadValidatorData = async () => {
  loading.value.validator = true
  try {
    const response = await tokenAPI.validateToken()
    if (response.data.success) {
      validatorData.value = response.data
    }
  } catch (error) {
    console.error('Validator error:', error)
  } finally {
    loading.value.validator = false
  }
}

const closeModal = () => {
  emit('close')
}

const formatExpirationTime = (seconds) => {
  if (seconds === null || seconds === undefined) {
    return 'Unknown expiration'
  }
  
  if (seconds < 0) {
    const hours = Math.floor(Math.abs(seconds) / 3600)
    const minutes = Math.floor((Math.abs(seconds) % 3600) / 60)
    return `Expired ${hours}h ${minutes}m ago`
  }
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `Valid for ${hours}h ${minutes}m`
}

const formatCheckName = (name) => {
  return name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ')
}

const getCategoryIcon = (category) => {
  const icons = {
    'User Operations': '👤',
    'Directory Operations': '📁',
    'Group Operations': '👥',
    'Mail Operations': '📧',
    'File Operations': '📄',
    'SharePoint Operations': '🌐',
    'Role Operations': '🔐',
    'Teams Operations': '💬',
    'Application Operations': '📱'
  }
  return icons[category] || '📋'
}
</script>

<style scoped>
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

/* Modal Container */
.modal-container {
  width: 100%;
  max-width: 900px;
  max-height: 85vh;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.close-btn {
  font-size: 1.5rem;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid;
  padding: 0 2rem;
}

.tab-button {
  padding: 1rem 1.5rem;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-active-dark {
  color: #60a5fa;
  border-bottom-color: #60a5fa;
}

.tab-inactive {
  color: #6b7280;
}

.tab-inactive-dark {
  color: #9ca3af;
}

.tab-button:hover {
  opacity: 0.8;
}

/* Modal Body */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.tab-panel {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  text-align: center;
  padding: 3rem 2rem;
  font-weight: 600;
}

/* Claims Section */
.claims-section {
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.claims-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.claims-content {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Identity Badge */
.identity-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
}

/* Expiration Banner */
.expiration-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
}

/* Summary Cards */
.summary-card {
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid;
  text-align: center;
}

/* Warnings Section */
.warnings-section {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
}

/* Capability Section */
.capability-section {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.capability-title {
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.capability-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.capability-item {
  padding: 0.25rem 0;
  font-size: 0.875rem;
}

/* Missing Scopes */
.missing-scopes {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.scope-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  border: 1px solid;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Status Banner */
.status-banner {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid;
}

/* Check Item */
.check-item {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Footer */
.modal-footer {
  padding: 1rem 2rem;
  border-top: 1px solid;
  display: flex;
  justify-content: flex-end;
}
</style>
