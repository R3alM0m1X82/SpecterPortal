<template>
  <div
    :class="[
      'rounded-lg shadow-md p-6 hover:shadow-lg transition-all duration-300',
      isDark ? 'bg-gray-800' : 'bg-white',
      token.is_active ? getActiveCardClass : ''
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <h3 :class="[
          'text-lg font-semibold mb-1 flex items-center gap-2',
          token.is_active 
            ? 'text-green-400' 
            : (isDark ? 'text-gray-100' : 'text-gray-800')
        ]">
          <span v-if="token.is_active" class="text-green-400">⚡</span>
          Token #{{ token.id }}
        </h3>
        
        <!-- App Name - COLORED -->
        <p :class="['text-sm font-semibold truncate', isDark ? 'text-blue-400' : 'text-blue-600']">
          {{ displayName }}
        </p>
        
        <!-- GUID sotto il nome dell'app (client_id per user, appid per SP) - COLORED -->
        <p v-if="guidToShow" :class="['text-xs font-mono font-semibold truncate mt-0.5', isDark ? 'text-purple-400' : 'text-purple-600']">
          {{ guidToShow }}
        </p>
        
        <!-- Identity Badge (UPN or Service Principal) - PER TUTTI I TOKEN -->
        <div v-if="identityBadge" class="mt-2">
          <span
            :class="[
              'inline-flex items-center px-2 py-1 text-xs font-medium rounded-md',
              identityBadge.type === 'user' 
                ? (isDark ? 'bg-cyan-900/50 text-cyan-300 border border-cyan-700' : 'bg-cyan-50 text-cyan-700 border border-cyan-200')
                : (isDark ? 'bg-orange-900/50 text-orange-300 border border-orange-700' : 'bg-orange-50 text-orange-700 border border-orange-200')
            ]"
          >
            {{ identityBadge.icon }} <span v-html="highlightText(identityBadge.label)"></span>
          </span>
        </div>
      </div>

      <div class="flex flex-col items-end space-y-2">
        <span
          class="px-3 py-1 text-xs font-semibold rounded-full"
          :class="tokenTypeBadgeClass"
        >
          {{ tokenTypeLabel }}
        </span>

        <span
          v-if="token.is_foci"
          :class="[
            'px-2 py-1 text-xs font-semibold rounded-full border',
            isDark ? 'bg-purple-900/50 text-purple-300 border-purple-700' : 'bg-purple-50 text-purple-600 border-purple-200'
          ]"
          title="Family of Client IDs - Can use refresh tokens across apps"
        >
          FOCI
        </span>

        <!-- NEW: Classification Badge (only for Refresh Tokens - hide if FOCI badge already visible) -->
        <span
          v-if="token.token_type === 'refresh_token' && token.classification && !token.is_foci"
          :class="[
            'px-2 py-1 text-xs font-semibold rounded-full border',
            classificationBadgeClass
          ]"
          :title="classificationTooltip"
        >
          {{ classificationLabel }}
        </span>

        <span
          class="px-3 py-1 text-xs font-semibold rounded-full"
          :class="sourceBadgeClass"
        >
          {{ sourceLabel }}
        </span>

        <!-- NEW: Source Type Badge (AUTHORITY_FILE / PRT_FILE) -->
        <span
          v-if="token.source_type"
          :class="[
            'px-2 py-1 text-xs font-semibold rounded-full border',
            sourceTypeBadgeClass
          ]"
          :title="sourceTypeTooltip"
        >
          {{ sourceTypeLabel }}
        </span>

        <span
          v-if="token.is_active"
          :class="[
            'px-3 py-1 text-xs font-semibold rounded-full',
            isDark ? 'bg-green-900/70 text-green-300 border border-green-700' : 'bg-green-100 text-green-700'
          ]"
        >
          ✓ Active
        </span>

        <span
          v-if="isOfficeMaster"
          class="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full"
        >
          ⭐ Office Master
        </span>
      </div>
    </div>

    <!-- Token Details -->
    <div class="space-y-2 mb-4">
      <!-- Tenant ID -->
      <div v-if="token.tenant_id" class="flex items-center text-sm">
        <span :class="['w-24', isDark ? 'text-gray-400' : 'text-gray-500']">Tenant ID:</span>
        <span :class="['font-mono text-xs truncate', isDark ? 'text-yellow-300' : 'text-yellow-600']" :title="token.tenant_id">
          {{ token.tenant_id }}
        </span>
      </div>

      <div v-if="token.audience" class="flex items-center text-sm">
        <span :class="['w-24', isDark ? 'text-gray-400' : 'text-gray-500']">Audience:</span>
        <span 
          :class="['font-mono text-xs truncate', isDark ? 'text-gray-200' : 'text-gray-800']"
          v-html="highlightText(token.audience)"
        ></span>
      </div>

      <!-- Scope Display -->
      <div v-if="token.scope" class="flex items-start text-sm">
        <span :class="['w-24 flex-shrink-0', isDark ? 'text-gray-400' : 'text-gray-500']">Scope:</span>
        <div class="flex-1">
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="(scope, idx) in scopeList" 
              :key="idx"
              :class="[
                'inline-block px-2 py-0.5 text-xs font-mono rounded break-words',
                isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'
              ]"
              style="max-width: 100%; word-break: break-word; overflow-wrap: break-word;"
              v-html="highlightText(scope)"
            ></span>
          </div>
        </div>
      </div>

      <div v-if="token.expires_at || token.token_type === 'access_token'" class="flex items-center text-sm">
        <span :class="['w-24', isDark ? 'text-gray-400' : 'text-gray-500']">Expires:</span>
        <span :class="['text-xs', isExpired ? 'text-red-500 font-semibold' : (isDark ? 'text-gray-200' : 'text-gray-800')]">
          {{ expiresDisplay }}
        </span>
      </div>

      <div v-if="token.token_type === 'access_token'" class="flex items-center text-sm">
        <span :class="['w-24', isDark ? 'text-gray-400' : 'text-gray-500']">Refresh:</span>
        <span :class="['text-xs', isDark ? 'text-gray-200' : 'text-gray-800']">
          {{ token.has_refresh_token ? '✓ Available' : '✗ None' }}
        </span>
      </div>

      <div v-if="token.broker_cache_path" class="flex items-center text-sm">
        <span :class="['w-24', isDark ? 'text-gray-400' : 'text-gray-500']">Cache:</span>
        <span :class="['text-xs truncate', isDark ? 'text-gray-200' : 'text-gray-800']" :title="token.broker_cache_path">
          {{ token.broker_cache_path.split('\\').pop() }}
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div :class="['flex flex-wrap gap-2 pt-4 border-t', isDark ? 'border-gray-700' : '']">
      <!-- Use Refresh Token button -->
      <button
        v-if="token.token_type === 'refresh_token'"
        @click="$emit('use-refresh', token)"
        class="btn btn-success flex-1"
        title="Generate new Access Token from this Refresh Token"
      >
        🔄 Use RT
      </button>

      <button
        v-if="!token.is_active && (token.token_type === 'access_token' || token.token_type === 'Managed Identity')"
        @click="$emit('activate', token.id)"
        class="btn btn-primary flex-1"
      >
        Activate
      </button>

      <button
        @click="toggleToken"
        :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']"
      >
        {{ showToken ? 'Hide' : 'View' }}
      </button>

      <button
        @click="$emit('delete', token.id)"
        class="btn btn-danger"
      >
        Delete
      </button>

      <!-- Quick Actions Dropdown -->
      <div class="relative" v-if="token.token_type === 'access_token' || token.token_type === 'Managed Identity'">
        <button
          @click="showQuickActions = !showQuickActions"
          :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']"
        >
          ⚙️ Quick Actions
        </button>

        <!-- Dropdown Menu -->
        <div
          v-if="showQuickActions"
          ref="quickActionsDropdown"
          :class="[
            'absolute right-0 mt-2 w-64 rounded-lg shadow-xl border z-10',
            isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-200'
          ]"
        >
          <button
            @click="copyBearerHeader"
            :class="[
              'w-full text-left px-4 py-2 text-sm transition-colors flex items-center space-x-3',
              isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <span>{{ bearerCopied ? '✓ Copied!' : 'Copy Bearer Header' }}</span>
          </button>

          <button
            @click="generateCurlBash"
            :class="[
              'w-full text-left px-4 py-2 text-sm transition-colors flex items-center space-x-3',
              isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
            <span>{{ curlBashCopied ? '✓ Copied!' : 'Generate cURL (Bash)' }}</span>
          </button>

          <button
            @click="generatePowershell"
            :class="[
              'w-full text-left px-4 py-2 text-sm transition-colors flex items-center space-x-3',
              isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span>{{ powershellCopied ? '✓ Copied!' : 'Generate PowerShell' }}</span>
          </button>

          <button
            @click="exportJson"
            :class="[
              'w-full text-left px-4 py-2 text-sm transition-colors flex items-center space-x-3',
              isDark ? 'hover:bg-gray-600 text-gray-200' : 'hover:bg-gray-100 text-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
            </svg>
            <span>{{ jsonCopied ? '✓ Copied!' : 'Export to JSON' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Token Display -->
    <div v-if="showToken" :class="['mt-4 pt-4 border-t', isDark ? 'border-gray-700' : '']">
      <div :class="['rounded p-3', isDark ? 'bg-gray-700' : 'bg-gray-50']">
        <div class="flex items-center justify-between mb-2">
          <span :class="['text-xs font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">{{ tokenDisplayLabel }}:</span>
          <button @click="copyToken" :class="['text-xs', isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800']">
            {{ copied ? '✓ Copied!' : '📋 Copy' }}
          </button>
        </div>
        <div :class="['font-mono text-xs break-all p-2 rounded border max-h-32 overflow-y-auto', isDark ? 'bg-gray-800 border-gray-600 text-gray-200' : 'bg-white']">
          {{ fullToken }}
        </div>
        <a
          v-if="token.token_type === 'access_token' || token.token_type === 'Managed Identity'"
          href="https://jwt.io"
          target="_blank"
          :class="['text-xs hover:underline mt-2 inline-block', isDark ? 'text-blue-400' : 'text-blue-600']"
        >
          → Analyze on jwt.io
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { tokenAPI } from '../services/api'

const props = defineProps({
  token: {
    type: Object,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  },
  highlightText: {
    type: String,
    default: ''
  }
})

defineEmits(['activate', 'delete', 'use-refresh'])

const showToken = ref(false)
const fullToken = ref('')
const copied = ref(false)

// Quick Actions
const showQuickActions = ref(false)
const bearerCopied = ref(false)
const curlBashCopied = ref(false)
const powershellCopied = ref(false)
const jsonCopied = ref(false)

const displayName = computed(() => {
  // Service Principal - show app_displayname
  if (props.token.appid && props.token.app_displayname) {
    return props.token.app_displayname
  }
  
  // Standard logic - prefer client_app_name over UPN for display name
  if (props.token.client_app_name && props.token.client_app_name !== props.token.client_id) {
    return props.token.client_app_name
  }
  
  // Fallback to client_id
  return props.token.client_id
})

// GUID to show under display name
const guidToShow = computed(() => {
  // Service Principal token - show appid
  if (props.token.appid) {
    return props.token.appid
  }
  
  // User token - ALWAYS show client_id (unless it's already the display name)
  if (props.token.client_id && props.token.client_id !== displayName.value) {
    return props.token.client_id
  }
  
  return null
})

// Scope list for display
const scopeList = computed(() => {
  if (!props.token.scope) return []
  
  // Split by space and filter empty
  return props.token.scope.split(' ').filter(s => s.trim())
})

// Identity Badge - Shows UPN for user tokens or AppName for service principals - PER TUTTI I TOKEN TYPES
const identityBadge = computed(() => {
  // User token - has UPN (mostra per TUTTI i tipi di token, non solo access_token)
  if (props.token.upn) {
    return {
      type: 'user',
      icon: '👤',
      label: props.token.upn
    }
  }
  
  // Service Principal token - has appid but show app_displayname (solo per access token)
  if (props.token.appid && props.token.token_type === 'access_token') {
    const displayName = props.token.app_displayname || `App ${props.token.appid.substring(0, 8)}...`
    return {
      type: 'sp',
      icon: '🤖',
      label: displayName
    }
  }
  
  return null
})

// Active Token Glow Effect
const getActiveCardClass = computed(() => {
  if (!props.token.is_active) return ''
  
  if (props.isDark) {
    // Dark mode: Green glow + green overlay background + thick green border
    return 'border-[3px] border-green-500 shadow-lg shadow-green-500/50 bg-gradient-to-br from-gray-700 to-green-900/20'
  } else {
    // Light mode: Green glow + subtle green tint + thick green border
    return 'border-[3px] border-green-500 shadow-lg shadow-green-500/40 bg-gradient-to-br from-white to-green-50'
  }
})

const tokenTypeLabel = computed(() => {
  const labels = {
    'access_token': 'AT',
    'refresh_token': 'RT',
    'ngc_token': 'NGC',
    'Managed Identity': 'MI'
  }
  return labels[props.token.token_type] || 'AT'
})

const tokenTypeBadgeClass = computed(() => {
  const classes = {
    'access_token': 'bg-blue-100 text-blue-700',
    'refresh_token': 'bg-yellow-100 text-yellow-700',
    'ngc_token': 'bg-indigo-100 text-indigo-700',
    'Managed Identity': 'bg-purple-100 text-purple-700'
  }
  return classes[props.token.token_type] || 'bg-gray-100 text-gray-700'
})

const sourceLabel = computed(() => {
  const labels = {
    'tbres': 'TBRes',
    'broker': 'Broker',
    'roadtx': 'ROADtx',
    'manual': 'Manual',
    'refresh': 'refresh'
  }
  return labels[props.token.source] || props.token.source
})

const sourceBadgeClass = computed(() => {
  const classes = {
    'tbres': 'bg-green-100 text-green-700',
    'broker': 'bg-orange-100 text-orange-700',
    'roadtx': 'bg-pink-100 text-pink-700',
    'manual': 'bg-gray-100 text-gray-700',
    'refresh': 'bg-cyan-100 text-cyan-700'
  }
  return classes[props.token.source] || 'bg-gray-100 text-gray-700'
})

// NEW: Source Type Badge (SpecterBroker v1.2)
const sourceTypeLabel = computed(() => {
  const labels = {
    'AUTHORITY_FILE': 'AUTHORITY',
    'PRT_FILE': 'PRT',
    'UNKNOWN': 'UNKNOWN'
  }
  return labels[props.token.source_type] || props.token.source_type
})

const sourceTypeBadgeClass = computed(() => {
  if (!props.token.source_type) return ''
  
  const colors = {
    'AUTHORITY_FILE': props.isDark 
      ? 'bg-green-900/50 text-green-300 border-green-700' 
      : 'bg-green-50 text-green-700 border-green-200',
    'PRT_FILE': props.isDark 
      ? 'bg-orange-900/50 text-orange-300 border-orange-700' 
      : 'bg-orange-50 text-orange-700 border-orange-200',
    'UNKNOWN': props.isDark 
      ? 'bg-gray-900/50 text-gray-300 border-gray-700' 
      : 'bg-gray-50 text-gray-700 border-gray-200'
  }
  return colors[props.token.source_type] || colors['UNKNOWN']
})

const sourceTypeTooltip = computed(() => {
  const tooltips = {
    'AUTHORITY_FILE': 'Extracted from Authority cache file (a_*.def) - Standalone token',
    'PRT_FILE': 'Extracted from PRT cache file (p_*.def) - May be device-bound',
    'UNKNOWN': 'Source type unknown'
  }
  return tooltips[props.token.source_type] || 'Source type'
})

// NEW: Classification Badge (SpecterBroker v1.2)
const classificationLabel = computed(() => {
  const labels = {
    'FOCI': 'FOCI',
    'STANDALONE': 'Standalone',
    'PRT_BOUND': 'PRT-Bound'
  }
  return labels[props.token.classification] || props.token.classification
})

const classificationBadgeClass = computed(() => {
  if (!props.token.classification) return ''
  
  const colors = {
    'FOCI': props.isDark 
      ? 'bg-purple-900/50 text-purple-300 border-purple-700' 
      : 'bg-purple-50 text-purple-700 border-purple-200',
    'STANDALONE': props.isDark 
      ? 'bg-blue-900/50 text-blue-300 border-blue-700' 
      : 'bg-blue-50 text-blue-700 border-blue-200',
    'PRT_BOUND': props.isDark 
      ? 'bg-orange-900/50 text-orange-300 border-orange-700' 
      : 'bg-orange-50 text-orange-700 border-orange-200'
  }
  return colors[props.token.classification] || ''
})

const classificationTooltip = computed(() => {
  const tooltips = {
    'FOCI': 'FOCI-enabled - Can exchange refresh token across Microsoft applications',
    'STANDALONE': 'Standalone token - Cannot be exchanged with other applications',
    'PRT_BOUND': 'PRT-bound token - Requires Primary Refresh Token and device context'
  }
  return tooltips[props.token.classification] || 'Token classification'
})

const tokenDisplayLabel = computed(() => {
  const labels = {
    'access_token': 'Access Token',
    'refresh_token': 'Refresh Token',
    'ngc_token': 'NGC Token',
    'Managed Identity': 'Managed Identity'
  }
  return labels[props.token.token_type] || 'Token'
})

const isOfficeMaster = computed(() => {
  return props.token.client_id === 'd3590ed6-52b3-4102-aeff-aad2292ab01c'
})

const expiresDisplay = computed(() => {
  if (!props.token.expires_at) {
    if (props.token.token_type === 'refresh_token') {
      return 'No expiration'
    }
    if (props.token.token_type === 'ngc_token') {
      return 'Device-bound'
    }
    return 'Unknown'
  }

  const expiresDateStr = props.token.expires_at.endsWith('Z') 
    ? props.token.expires_at 
    : props.token.expires_at + 'Z'
  
  const expiresDate = new Date(expiresDateStr)
  const now = new Date()

  if (expiresDate < now) {
    return '⚠️ EXPIRED'
  }

  const diffMs = expiresDate - now
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h`
  if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m`
  return `${diffMins}m`
})

const isExpired = computed(() => {
  if (!props.token.expires_at) return false
  
  const expiresDateStr = props.token.expires_at.endsWith('Z') 
    ? props.token.expires_at 
    : props.token.expires_at + 'Z'
  
  return new Date(expiresDateStr) < new Date()
})

// Highlight scope text based on search query (like browser Ctrl+F)
const highlightText = (text) => {
  if (!text || !props.highlightText || !props.highlightText.trim()) {
    return text
  }
  
  const searchText = props.highlightText.trim()
  // Escape special regex characters
  const escapedSearch = searchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escapedSearch})`, 'gi')
  return text.replace(regex, '<mark class="scope-highlight">$1</mark>')
}

const loadFullToken = async () => {
  if (fullToken.value) return

  try {
    const response = await tokenAPI.getById(props.token.id)
    if (response.data.success) {
      fullToken.value = response.data.token.access_token_full || response.data.token.access_token
    }
  } catch (error) {
    console.error('Failed to load full token:', error)
  }
}

const copyToken = async () => {
  if (!fullToken.value) await loadFullToken()

  try {
    await navigator.clipboard.writeText(fullToken.value)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

const toggleToken = async () => {
  showToken.value = !showToken.value
  if (showToken.value && !fullToken.value) {
    await loadFullToken()
  }
}

// Quick Actions Functions
const closeQuickActions = () => {
  showQuickActions.value = false
}

const copyBearerHeader = async () => {
  if (!fullToken.value) await loadFullToken()

  try {
    const bearerHeader = `Authorization: Bearer ${fullToken.value}`
    await navigator.clipboard.writeText(bearerHeader)
    bearerCopied.value = true
    setTimeout(() => {
      bearerCopied.value = false
      showQuickActions.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy bearer header:', error)
    alert('Failed to copy bearer header')
  }
}

const generateCurlBash = async () => {
  if (!fullToken.value) await loadFullToken()

  try {
    const response = await tokenAPI.generateCurl(fullToken.value)
    if (response.data.success) {
      await navigator.clipboard.writeText(response.data.bash_command)
      curlBashCopied.value = true
      setTimeout(() => {
        curlBashCopied.value = false
        showQuickActions.value = false
      }, 2000)
    }
  } catch (error) {
    console.error('Failed to generate cURL:', error)
    alert('Failed to generate cURL command')
  }
}

const generatePowershell = async () => {
  if (!fullToken.value) await loadFullToken()

  try {
    const response = await tokenAPI.generateCurl(fullToken.value)
    if (response.data.success) {
      await navigator.clipboard.writeText(response.data.powershell_command)
      powershellCopied.value = true
      setTimeout(() => {
        powershellCopied.value = false
        showQuickActions.value = false
      }, 2000)
    }
  } catch (error) {
    console.error('Failed to generate PowerShell:', error)
    alert('Failed to generate PowerShell command')
  }
}

const exportJson = async () => {
  try {
    const response = await tokenAPI.exportJson(props.token.id)
    if (response.data.success) {
      const jsonOutput = JSON.stringify(response.data.json_output, null, 2)
      await navigator.clipboard.writeText(jsonOutput)
      jsonCopied.value = true
      setTimeout(() => {
        jsonCopied.value = false
        showQuickActions.value = false
      }, 2000)
    }
  } catch (error) {
    console.error('Failed to export JSON:', error)
    alert('Failed to export to JSON')
  }
}

// Ref per dropdown menu
const quickActionsDropdown = ref(null)

// Click outside listener per chiudere dropdown
const handleClickOutside = (event) => {
  if (quickActionsDropdown.value && !quickActionsDropdown.value.contains(event.target)) {
    // Controlla anche se il click è sul pulsante "Quick Actions"
    const quickActionsButton = event.target.closest('button')
    if (!quickActionsButton || !quickActionsButton.textContent.includes('Quick Actions')) {
      closeQuickActions()
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700;
}

/* Fix scope overflow - Sprint 5.4 */
.scope-badge,
.flex-wrap span[class*="font-mono"] {
  max-width: 100%;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  line-height: 1.4;
  display: inline-block;
}

/* Scope highlight - like browser Ctrl+F */
:deep(.scope-highlight) {
  background-color: #fef08a;
  color: #854d0e;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-weight: 600;
}
</style>
