<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Dashboard</h1>
    </div>

    <!-- System Health -->
    <div class="mb-6 rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">System Health</h3>
        <button 
          @click="checkHealth" 
          class="text-sm px-3 py-1 rounded-lg transition-colors"
          :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          🔄 Refresh
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Backend Status -->
        <div class="flex items-center space-x-3 p-3 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <div class="text-2xl">
            <span v-if="health.checking">⏳</span>
            <span v-else-if="health.backend">✅</span>
            <span v-else>❌</span>
          </div>
          <div>
            <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">Backend</p>
            <p class="text-sm" :class="health.backend ? 'text-green-500' : 'text-red-500'">
              {{ health.checking ? 'Checking...' : (health.backend ? 'Online' : 'Offline') }}
            </p>
          </div>
        </div>
        
        <!-- Database Status -->
        <div class="flex items-center space-x-3 p-3 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <div class="text-2xl">
            <span v-if="health.checking">⏳</span>
            <span v-else-if="health.database">✅</span>
            <span v-else>❌</span>
          </div>
          <div>
            <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">Database</p>
            <p class="text-sm" :class="health.database ? 'text-green-500' : 'text-red-500'">
              {{ health.checking ? 'Checking...' : (health.database ? 'Connected' : 'Disconnected') }}
            </p>
          </div>
        </div>

        <!-- API Status -->
        <div class="flex items-center space-x-3 p-3 rounded-lg" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <div class="text-2xl">
            <span v-if="health.checking">⏳</span>
            <span v-else-if="health.api">✅</span>
            <span v-else>❌</span>
          </div>
          <div>
            <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">API</p>
            <p class="text-sm" :class="health.api ? 'text-green-500' : 'text-red-500'">
              {{ health.checking ? 'Checking...' : (health.api ? 'Ready' : 'Not Ready') }}
            </p>
          </div>
        </div>
      </div>
      
      <!-- Token Health Bar -->
      <div v-if="stats.total_tokens > 0" class="mt-4 pt-4 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Token Health</span>
          <span class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
            {{ stats.total_tokens - (stats.expired_tokens || 0) }} valid / {{ stats.total_tokens }} total
          </span>
        </div>
        <div class="w-full rounded-full h-3" :class="isDark ? 'bg-gray-700' : 'bg-gray-200'">
          <div 
            class="h-3 rounded-full bg-gradient-to-r from-green-500 to-green-400 transition-all"
            :style="{ width: `${tokenHealthPercent}%` }"
          ></div>
        </div>
      </div>
      
      <p v-if="health.lastCheck" class="text-xs mt-3" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
        Last check: {{ health.lastCheck }}
      </p>
    </div>

    <!-- Auto-Refresh Scheduler -->
    <div class="mb-6 rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">🔄 Auto-Refresh Scheduler</h3>
          <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
            Automatically refresh expiring access tokens
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <button
            @click="triggerRefreshNow"
            :disabled="schedulerLoading"
            class="px-3 py-1 rounded-lg text-sm font-medium transition-colors"
            :class="isDark ? 'bg-blue-900 text-blue-300 hover:bg-blue-800' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'"
          >
            ⚡ Refresh Now
          </button>
          <button
            @click="toggleScheduler"
            :disabled="schedulerLoading"
            :class="[
              'px-4 py-2 rounded-lg font-semibold text-sm transition-colors',
              scheduler.is_running
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-green-600 text-white hover:bg-green-700'
            ]"
          >
            {{ schedulerLoading ? '...' : (scheduler.is_running ? '⏹️ Stop' : '▶️ Start') }}
          </button>
        </div>
      </div>

      <!-- Status & Config -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <!-- Status -->
        <div class="rounded-lg p-3" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</p>
          <p :class="scheduler.is_running ? 'text-green-500 font-semibold' : (isDark ? 'text-gray-400' : 'text-gray-500')">
            {{ scheduler.is_running ? '● Running' : '○ Stopped' }}
          </p>
          <p v-if="scheduler.next_run" class="text-xs mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
            Next: {{ formatTime(scheduler.next_run) }}
          </p>
        </div>

        <!-- Interval Config -->
        <div class="rounded-lg p-3" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Check Interval</p>
          <div class="flex items-center space-x-2">
            <input
              v-model.number="configInterval"
              type="number"
              min="1"
              max="60"
              class="w-16 px-2 py-1 rounded text-sm"
              :class="isDark ? 'bg-gray-600 text-white border-gray-500' : 'bg-white border-gray-300'"
            />
            <span class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-600'">min</span>
          </div>
        </div>

        <!-- Threshold Config -->
        <div class="rounded-lg p-3" :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
          <p class="text-xs font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Expiry Threshold</p>
          <div class="flex items-center space-x-2">
            <input
              v-model.number="configThreshold"
              type="number"
              min="1"
              max="120"
              class="w-16 px-2 py-1 rounded text-sm"
              :class="isDark ? 'bg-gray-600 text-white border-gray-500' : 'bg-white border-gray-300'"
            />
            <span class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-600'">min</span>
            <button
              @click="updateSchedulerConfig"
              class="px-2 py-1 rounded text-xs font-medium"
              :class="isDark ? 'bg-gray-600 text-gray-300 hover:bg-gray-500' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
            >
              Save
            </button>
          </div>
        </div>
      </div>

      <!-- Expiring Tokens -->
      <div v-if="expiringTokens.length > 0" class="mb-4">
        <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
          ⚠️ Expiring Soon ({{ expiringTokens.length }})
        </p>
        <div class="space-y-2 max-h-32 overflow-y-auto">
          <div
            v-for="token in expiringTokens"
            :key="token.id"
            class="flex items-center justify-between rounded p-2 text-sm"
            :class="isDark ? 'bg-orange-900/30' : 'bg-orange-50'"
          >
            <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">{{ token.upn || 'Unknown' }}</span>
            <div class="flex items-center space-x-2">
              <span :class="token.can_refresh ? 'text-green-500' : 'text-red-500'">
                {{ token.can_refresh ? '✓ RT' : '✗ No RT' }}
              </span>
              <span :class="isDark ? 'text-orange-400' : 'text-orange-600'">
                {{ token.minutes_until_expiry }}min
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent History -->
      <div v-if="schedulerHistory.length > 0">
        <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
          📋 Recent Activity
        </p>
        <div class="space-y-1 max-h-24 overflow-y-auto">
          <div
            v-for="(event, index) in schedulerHistory.slice(0, 5)"
            :key="index"
            class="flex items-center justify-between text-xs"
            :class="isDark ? 'text-gray-400' : 'text-gray-500'"
          >
            <span>{{ event.message }}</span>
            <span>{{ formatTime(event.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Token Details -->
    <div v-if="activeToken" class="mb-6">
      <h2 class="text-2xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Active Token Details</h2>
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- User -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">User Principal Name</p>
            <p class="text-lg font-mono" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.upn || 'N/A' }}</p>
          </div>

          <!-- Resource/Audience -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Resource / Audience</p>
            <p class="text-lg font-mono break-all" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.audience || 'N/A' }}</p>
          </div>

          <!-- Client ID -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Client ID</p>
            <p class="text-lg font-mono" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.client_id || 'N/A' }}</p>
          </div>

          <!-- Client App Name -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Client Application</p>
            <p class="text-lg" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.client_app_name || 'N/A' }}</p>
          </div>

          <!-- Expiration -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Expires At</p>
            <p class="text-lg font-mono" :class="activeToken.is_expired ? 'text-red-500' : 'text-green-500'">
              {{ formatDateTime(activeToken.expires_at) }}
            </p>
            <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ getTimeRemaining(activeToken.expires_at) }}
            </p>
          </div>

          <!-- Token Type -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Token Type</p>
            <p class="text-lg capitalize" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.token_type?.replace('_', ' ') || 'N/A' }}</p>
          </div>

          <!-- FOCI Status -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">FOCI Family</p>
            <p class="text-lg">
              <span v-if="activeToken.is_foci" class="text-green-500 font-semibold">✓ Yes</span>
              <span v-else :class="isDark ? 'text-gray-500' : 'text-gray-400'">✗ No</span>
            </p>
          </div>

          <!-- Source -->
          <div>
            <p class="text-sm font-medium mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Source</p>
            <p class="text-lg uppercase" :class="isDark ? 'text-white' : 'text-gray-800'">{{ activeToken.source || 'N/A' }}</p>
          </div>
        </div>

        <!-- User Roles Section (NEW - Sprint 2) -->
        <div class="mt-6 pt-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Roles -->
            <div>
              <p class="text-sm font-medium mb-3" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                🛡️ Directory Roles 
                <span v-if="userInfo.roles_permission_denied" 
                      class="ml-2 px-2 py-1 text-xs rounded-lg font-semibold"
                      :class="isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-700'">
                  ⚠️ Permission Required
                </span>
                <span v-else>({{ userInfo.roles?.length || 0 }})</span>
              </p>
              <div v-if="userInfoLoading" class="flex items-center space-x-2">
                <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading...</span>
              </div>
              <div v-else-if="userInfo.roles && userInfo.roles.length > 0" class="flex flex-wrap gap-2">
                <span
                  v-for="role in userInfo.roles"
                  :key="role.id"
                  class="px-3 py-1 rounded-full text-sm font-medium"
                  :class="role.isPrivileged 
                    ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-700')
                    : (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-700')"
                  :title="role.description"
                >
                  {{ role.isPrivileged ? '⚠️ ' : '' }}{{ role.displayName }}
                </span>
              </div>
              <p v-else-if="!userInfo.roles_permission_denied" class="text-sm" :class="isDark ? 'text-gray-500' : 'text-gray-400'">No roles assigned</p>
            </div>

            <!-- Licenses -->
            <div>
              <p class="text-sm font-medium mb-3" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                📜 Licenses 
                <span v-if="userInfo.licenses_permission_denied" 
                      class="ml-2 px-2 py-1 text-xs rounded-lg font-semibold"
                      :class="isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-700'">
                  ⚠️ Permission Required
                </span>
                <span v-else>({{ userInfo.licenses?.length || 0 }})</span>
              </p>
              <div v-if="userInfoLoading" class="flex items-center space-x-2">
                <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading...</span>
              </div>
              <div v-else-if="userInfo.licenses && userInfo.licenses.length > 0" class="flex flex-wrap gap-2">
                <span
                  v-for="license in userInfo.licenses"
                  :key="license.skuId"
                  class="px-3 py-1 rounded-full text-sm font-medium"
                  :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-700'"
                  :title="license.skuPartNumber"
                >
                  {{ license.displayName }}
                </span>
              </div>
              <p v-else-if="!userInfo.licenses_permission_denied" class="text-sm" :class="isDark ? 'text-gray-500' : 'text-gray-400'">No licenses assigned</p>
            </div>
          </div>
        </div>

        <!-- Scopes Section -->
        <div v-if="decodedScopes.length > 0" class="mt-6 pt-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <p class="text-sm font-medium mb-3" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Scopes ({{ decodedScopes.length }})</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="scope in decodedScopes"
              :key="scope"
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'"
            >
              {{ scope }}
            </span>
          </div>
        </div>

        <!-- Decode JWT Button -->
        <div v-else class="mt-6 pt-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <button
            @click="decodeToken"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            🔓 Decode JWT to View Scopes
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="mb-6">
      <h2 class="text-2xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Active Token Details</h2>
      <div class="rounded-lg shadow-md p-6 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">⚠️</div>
        <p class="text-lg" :class="isDark ? 'text-gray-300' : 'text-gray-600'">No active token selected</p>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Please activate a token to see details</p>
        <router-link to="/tokens" class="inline-block mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Go to Tokens
        </router-link>
      </div>
    </div>

    <!-- Admin Capabilities Widget (NEW - Sprint 4.1) -->
    <div v-if="activeToken" class="mb-6">
      <h2 class="text-2xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
        🔐 Admin Capabilities
      </h2>
      <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <!-- Loading -->
        <div v-if="permissionsLoading" class="flex items-center justify-center py-8">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          <span class="ml-3" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Analyzing permissions...</span>
        </div>

        <!-- Content -->
        <div v-else-if="permissions.success">
          <!-- Privilege Badge -->
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-3">
              <span class="text-3xl">{{ permissions.privilege_badge?.icon || '👤' }}</span>
              <div>
                <p class="text-lg font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                  {{ permissions.privilege_badge?.label || 'Unknown' }}
                </p>
                <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                  {{ permissions.privilege_badge?.description }}
                </p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-2xl font-bold" :class="permissions.available_count > 0 ? 'text-green-500' : (isDark ? 'text-gray-500' : 'text-gray-400')">
                {{ permissions.available_count }} / {{ permissions.total_actions }}
              </p>
              <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Actions Available</p>
            </div>
          </div>

          <!-- Directory Roles (JWT + AU-scoped) -->
          <div v-if="filteredDirectoryRoles.length > 0" class="mb-6">
            <p class="text-sm font-medium mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              Directory Roles
              <span v-if="permissions.has_au_scoped_roles" class="ml-2 text-xs px-2 py-0.5 rounded-full" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'">
                ℹ️ Includes AU-scoped
              </span>
            </p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="role in filteredDirectoryRoles"
                :key="role"
                class="px-3 py-1 rounded-full text-sm font-medium"
                :class="isPrivilegedRole(role) 
                  ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-700')
                  : (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-700')"
              >
                {{ isPrivilegedRole(role) ? '👑 ' : '' }}{{ role }}
              </span>
            </div>
          </div>

          <!-- Available Actions -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div
              v-for="(cap, actionId) in permissions.capabilities"
              :key="actionId"
              class="p-3 rounded-lg border transition-all"
              :class="[
                cap.available 
                  ? (isDark ? 'border-green-700 bg-green-900/20' : 'border-green-200 bg-green-50')
                  : (isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'),
                cap.available ? 'hover:shadow-md' : 'opacity-60'
              ]"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-sm" :class="isDark ? 'text-white' : 'text-gray-800'">
                  {{ cap.name }}
                </span>
                <span 
                  class="text-xs px-2 py-0.5 rounded-full"
                  :class="getRiskClass(cap.risk_level)"
                >
                  {{ cap.risk_level }}
                </span>
              </div>
              <p class="text-xs mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                {{ cap.description }}
              </p>
              <div class="flex items-center space-x-2">
                <span 
                  class="text-xs"
                  :class="cap.has_required_role ? 'text-green-500' : 'text-red-500'"
                >
                  {{ cap.has_required_role ? '✓' : '✗' }} Role
                </span>
                <span 
                  class="text-xs"
                  :class="cap.has_required_scope ? 'text-green-500' : 'text-red-500'"
                >
                  {{ cap.has_required_scope ? '✓' : '✗' }} Scope
                </span>
                <span v-if="cap.available" class="text-xs text-green-500 font-semibold ml-auto">
                  ✓ Available
                </span>
              </div>
            </div>
          </div>

          <!-- Refresh Button -->
          <div class="mt-4 pt-4 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <button
              @click="loadPermissions"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
            >
              🔄 Refresh Permissions
            </button>
          </div>
        </div>

        <!-- Error -->
        <div v-else class="text-center py-6">
          <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
            {{ permissions.error || 'Failed to analyze permissions' }}
          </p>
          <button
            @click="loadPermissions"
            class="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div>
      <h2 class="text-2xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Quick Actions</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Manage Tokens -->
        <router-link 
          to="/tokens"
          class="rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750' : 'bg-white'"
        >
          <div class="flex items-center space-x-4">
            <!-- Azure Token Service Icon - OFFICIAL from az-icons.com -->
            <div class="w-12 h-12 flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18"><path fill="#773adc" d="M13.276 3.608V10.6l-6.01 3.514V7.11l6.01-3.503z"/><path fill="#b796f9" d="M13.276 3.608L7.268 7.12l-6-3.514 6-3.514 6.008 3.515z"/><path fill="#a67af4" d="M7.267 7.12v6.994L1.258 10.6V3.607l6.01 3.514z"/><path d="M11.66 13.1c0 .033-.006.066-.012.1s-.013.054-.02.08l-.027.095c-.01.032-.02.05-.032.076l-.047.1a1.434 1.434 0 0 1-.08.134l-.016.02a1.531 1.531 0 0 1-.1.129l-.02.025-.133.13a1.03 1.03 0 0 1-.1.08l-.09.07-.113.076-.12.077a3.322 3.322 0 0 1-.3.151l-.1.038-.25.094-.1.03-.163.047-.124.033-.175.038-.12.024-.36.05c-.037 0-.075.006-.113.01l-.212.015H8.3l-.16-.008-.296-.034-.142-.02-.167-.03-.13-.027-.2-.048-.108-.03-.34-.114-.16-.068-.08-.035-.232-.12a1.582 1.582 0 0 1-.932-1.3v1.406a1.582 1.582 0 0 0 .932 1.3l.232.12c.026.013.054.024.082.036l.14.062.018.006.366.123c.026.008.054.013.08.02l.2.048.052.013.08.014.167.03.067.01c.025 0 .05.006.075.01l.157.017c.026 0 .05.007.075.01h.072l.16.008h.455q.107-.006.213-.015h.112l.36-.05h.017l.1-.02.176-.038.123-.033.164-.047.034-.01c.02-.006.037-.014.056-.02l.25-.094.1-.038.3-.15.04-.023c.03-.017.053-.036.08-.054l.114-.076.088-.07.1-.08.02-.016c.04-.037.078-.076.114-.114l.02-.025.06-.07a.68.68 0 0 0 .042-.059l.016-.02.07-.11.01-.024a1.079 1.079 0 0 0 .046-.1l.027-.058.006-.02a1.01 1.01 0 0 0 .027-.094l.018-.064v-.017a1.09 1.09 0 0 0 .012-.1c.003-.034.007-.044.007-.065V13l-.013.1z" fill="#32bedd"/><path d="M10.735 11.7c1.238.714 1.244 1.873.015 2.587a4.925 4.925 0 0 1-4.468 0c-1.238-.715-1.243-1.874-.013-2.588a4.92 4.92 0 0 1 4.466.001z" fill="#50e6ff"/><path d="M16.734 14.774c0 .033-.005.066-.01.1s-.014.054-.02.08l-.027.095c-.01.03-.02.05-.032.077l-.046.1c-.017.034-.05.1-.08.134l-.015.02-.1.13-.02.024-.133.13a1.46 1.46 0 0 1-.1.08l-.088.07c-.03.023-.075.05-.114.075l-.12.077a3.078 3.078 0 0 1-.3.151l-.1.04-.248.094-.09.03-.163.046-.124.034-.175.037-.12.024-.36.05-.113.01-.213.014h-.455c-.054 0-.107 0-.16-.01s-.1-.007-.146-.012l-.158-.018-.14-.02-.168-.03-.13-.026-.2-.048-.108-.03-.34-.115-.16-.068-.08-.035-.232-.12a1.581 1.581 0 0 1-.932-1.3v1.405a1.582 1.582 0 0 0 .932 1.3l.232.12.08.035.143.062.017.006q.165.064.34.114l.027.01.08.02.2.05c.018 0 .035.01.052.012l.08.014.168.03c.022 0 .044.01.066.012l.075.008.158.018.075.008h.07c.053 0 .106.006.16.008h.455c.07 0 .142-.01.213-.014.028 0 .057 0 .086-.006h.027l.36-.05h.017l.1-.022.174-.037.124-.034.163-.046.035-.01.056-.02.248-.095.1-.038a3.322 3.322 0 0 0 .3-.151l.04-.023c.03-.017.054-.036.08-.054l.114-.076.088-.07.1-.08.02-.017a1.532 1.532 0 0 0 .114-.114l.02-.025.06-.07.043-.058.015-.02.07-.1.012-.024c.017-.032.03-.065.046-.1l.027-.058v-.02c.01-.032.02-.063.027-.095l.02-.063v-.018c.006-.033.008-.066.01-.1s.007-.043.007-.065v-1.428c.007.026.002.057-.001.088z" fill="#32bedd"/><path d="M15.8 13.38a1.367 1.367 0 0 1 .014 2.587 4.921 4.921 0 0 1-4.468 0c-1.237-.715-1.243-1.874-.013-2.588a4.922 4.922 0 0 1 4.467.001z" fill="#50e6ff"/><path d="M16.742 11.62c0 .03-.005.062-.008.092l-.01.1c-.006.033-.014.054-.02.08l-.027.094c-.01.03-.02.05-.032.077l-.046.1c-.017.034-.05.1-.08.134l-.015.02-.1.13-.02.024a2.06 2.06 0 0 1-.133.131 1.46 1.46 0 0 1-.1.08l-.09.07-.113.075-.12.078a3.191 3.191 0 0 1-.3.15l-.1.04-.25.094-.1.03-.163.047-.124.033-.175.037-.12.024-.36.05-.113.01-.213.014h-.454c-.054 0-.107 0-.16-.01s-.1-.007-.146-.012l-.158-.018-.14-.02-.168-.03-.13-.026-.2-.05-.108-.03q-.174-.05-.34-.114l-.16-.068-.082-.035-.232-.12a1.583 1.583 0 0 1-.933-1.3v1.406a1.583 1.583 0 0 0 .933 1.3l.232.12.08.035.143.062.017.006.34.114.027.01.08.02.2.048c.018 0 .035.01.053.013l.078.014.168.03c.022 0 .044.01.067.012l.074.008.158.018.075.008h.07c.053 0 .106.006.16.008h.454c.072 0 .143-.008.214-.014.028 0 .057 0 .086-.006h.026l.36-.05h.018l.1-.022.175-.037.123-.034.164-.046.035-.01c.02-.006.036-.015.055-.02l.25-.094.1-.04a3.2 3.2 0 0 0 .3-.151l.038-.022.082-.055.113-.075.09-.07.1-.08.02-.017a1.75 1.75 0 0 0 .114-.114l.02-.024.06-.072.043-.058.015-.02a1.18 1.18 0 0 0 .069-.11l.012-.024c.017-.032.03-.065.046-.1l.027-.057v-.02a1.03 1.03 0 0 0 .027-.095l.02-.063v-.017c.006-.033.008-.067.01-.1s.007-.043.007-.064v-.028z" fill="#32bedd"/><ellipse cx="13.583" cy="11.61" rx="1.83" ry="3.159" transform="matrix(.002827 -.999996 .999996 .002827 1.935 25.16)" fill="#50e6ff"/></svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">Manage Tokens</h3>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Manage and activate tokens</p>
            </div>
          </div>
        </router-link>

        <!-- Entra ID -->
        <router-link 
          to="/users-groups"
          class="rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750' : 'bg-white'"
        >
          <div class="flex items-center space-x-4">
            <!-- Microsoft Entra ID Icon - OFFICIAL -->
            <div class="w-12 h-12 flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18" class="w-full h-full">
                <path d="m3.802,14.032c.388.242,1.033.511,1.715.511.621,0,1.198-.18,1.676-.487,0,0,.001,0,.002-.001l1.805-1.128v4.073c-.286,0-.574-.078-.824-.234l-4.374-2.734Z" fill="#225086"/>
                <path d="m7.853,1.507L.353,9.967c-.579.654-.428,1.642.323,2.111,0,0,2.776,1.735,3.126,1.954.388.242,1.033.511,1.715.511.621,0,1.198-.18,1.676-.487,0,0,.001,0,.002-.001l1.805-1.128-4.364-2.728,4.365-4.924V1s0,0,0,0c-.424,0-.847.169-1.147.507Z" fill="#6df"/>
                <polygon points="4.636 10.199 4.688 10.231 9 12.927 9.001 12.927 9.001 12.927 9.001 5.276 9 5.275 4.636 10.199" fill="#cbf8ff"/>
                <path d="m17.324,12.078c.751-.469.902-1.457.323-2.111l-4.921-5.551c-.397-.185-.842-.291-1.313-.291-.925,0-1.752.399-2.302,1.026l-.109.123h0s4.364,4.924,4.364,4.924h0s0,0,0,0l-4.365,2.728v4.073c.287,0,.573-.078.823-.234l7.5-4.688Z" fill="#074793"/>
                <path d="m9.001,1v4.275s.109-.123.109-.123c.55-.627,1.377-1.026,2.302-1.026.472,0,.916.107,1.313.291l-2.579-2.909c-.299-.338-.723-.507-1.146-.507Z" fill="#0294e4"/>
                <polygon points="13.365 10.199 13.365 10.199 13.365 10.199 9.001 5.276 9.001 12.926 13.365 10.199" fill="#96bcc2"/>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">Entra ID</h3>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Users, Groups, Devices</p>
            </div>
          </div>
        </router-link>

        <!-- Azure -->
        <router-link 
          to="/azure/permissions"
          class="rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          :class="isDark ? 'bg-gray-800 hover:bg-gray-750' : 'bg-white'"
        >
          <div class="flex items-center space-x-4">
            <!-- Azure A Icon - OFFICIAL from az-icons.com -->
            <div class="w-12 h-12 flex-shrink-0">
              <svg viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5.33492 1.37491C5.44717 1.04229 5.75909 0.818359 6.11014 0.818359H11.25L5.91513 16.6255C5.80287 16.9581 5.49095 17.182 5.13991 17.182H1.13968C0.579936 17.182 0.185466 16.6325 0.364461 16.1022L5.33492 1.37491Z" fill="url(#paint0_linear_6102_134469)"/><path d="M13.5517 11.4546H5.45126C5.1109 11.4546 4.94657 11.8715 5.19539 12.1037L10.4005 16.9618C10.552 17.1032 10.7515 17.1819 10.9587 17.1819H15.5453L13.5517 11.4546Z" fill="#0078D4"/><path d="M6.11014 0.818359C5.75909 0.818359 5.44717 1.04229 5.33492 1.37491L0.364461 16.1022C0.185466 16.6325 0.579936 17.182 1.13968 17.182H5.13991C5.49095 17.182 5.80287 16.9581 5.91513 16.6255L6.90327 13.6976L10.4005 16.9617C10.552 17.1032 10.7515 17.1818 10.9588 17.1818H15.5454L13.5517 11.4545H7.66032L11.25 0.818359H6.11014Z" fill="url(#paint1_linear_6102_134469)"/><path d="M12.665 1.37478C12.5528 1.04217 12.2409 0.818237 11.8898 0.818237H6.13629H6.16254C6.51358 0.818237 6.82551 1.04217 6.93776 1.37478L11.9082 16.1021C12.0872 16.6324 11.6927 17.1819 11.133 17.1819H11.0454H16.8603C17.42 17.1819 17.8145 16.6324 17.6355 16.1021L12.665 1.37478Z" fill="url(#paint2_linear_6102_134469)"/><defs><linearGradient id="paint0_linear_6102_134469" x1="6.07512" y1="1.38476" x2="0.738178" y2="17.1514" gradientUnits="userSpaceOnUse"><stop stop-color="#114A8B"/><stop offset="1" stop-color="#0669BC"/></linearGradient><linearGradient id="paint1_linear_6102_134469" x1="10.3402" y1="11.4564" x2="9.107" y2="11.8734" gradientUnits="userSpaceOnUse"><stop stop-opacity="0.3"/><stop offset="0.0711768" stop-opacity="0.2"/><stop offset="0.321031" stop-opacity="0.1"/><stop offset="0.623053" stop-opacity="0.05"/><stop offset="1" stop-opacity="0"/></linearGradient><linearGradient id="paint2_linear_6102_134469" x1="9.45858" y1="1.38467" x2="15.3168" y2="16.9926" gradientUnits="userSpaceOnUse"><stop stop-color="#3CCBF4"/><stop offset="1" stop-color="#2892DF"/></linearGradient></defs></svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">Azure</h3>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">My Permissions</p>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, defineProps } from 'vue'
import { systemAPI, tokenAPI } from '../services/api'

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

const stats = ref({
  total_tokens: 0,
  active_token_id: null,
  office_master_tokens: 0,
  has_active_token: false,
  expired_tokens: 0,
  refresh_tokens: 0
})

const activeToken = ref(null)
const decodedScopes = ref([])
const loading = ref(false)

// User info (roles & licenses) - Sprint 2
const userInfo = ref({
  roles: [],
  licenses: []
})
const userInfoLoading = ref(false)

// Permissions - Sprint 4.1
const permissions = ref({
  success: false,
  privilege_level: 'standard',
  privilege_badge: null,
  directory_roles: [],
  capabilities: {},
  available_count: 0,
  total_actions: 0
})
const permissionsLoading = ref(false)

// Scheduler state
const scheduler = ref({
  is_running: false,
  config: {
    interval_minutes: 5,
    expiry_threshold_minutes: 10
  },
  next_run: null
})
const schedulerLoading = ref(false)
const configInterval = ref(5)
const configThreshold = ref(10)
const expiringTokens = ref([])
const schedulerHistory = ref([])

// Health check state
const health = ref({
  backend: false,
  database: false,
  api: false,
  checking: true,
  lastCheck: null
})

// Interval IDs for cleanup
const intervals = ref([])

const tokenHealthPercent = computed(() => {
  if (!stats.value.total_tokens) return 100
  const valid = stats.value.total_tokens - (stats.value.expired_tokens || 0)
  return Math.round((valid / stats.value.total_tokens) * 100)
})

// Filter out "Unknown Role" from directory roles display
const filteredDirectoryRoles = computed(() => {
  if (!permissions.value.directory_roles) return []
  return permissions.value.directory_roles.filter(role => !role.startsWith('Unknown Role'))
})

// Privileged roles list
const privilegedRoles = [
  'Global Administrator',
  'Privileged Role Administrator',
  'Privileged Authentication Administrator',
  'User Administrator',
  'Exchange Administrator',
  'SharePoint Administrator',
  'Security Administrator'
]

const isPrivilegedRole = (roleName) => {
  return privilegedRoles.some(r => roleName.includes(r))
}

const getRiskClass = (riskLevel) => {
  const classes = {
    'critical': 'bg-red-600 text-white',
    'high': 'bg-orange-500 text-white',
    'medium': 'bg-yellow-500 text-black',
    'low': 'bg-green-500 text-white'
  }
  return classes[riskLevel] || 'bg-gray-500 text-white'
}

const checkHealth = async () => {
  health.value.checking = true
  
  try {
    const response = await fetch('http://localhost:5000/api/health')
    const data = await response.json()
    
    health.value.backend = true
    health.value.database = data.database || false
    health.value.api = data.api || false
    health.value.lastCheck = new Date().toLocaleTimeString()
  } catch (error) {
    console.error('Health check failed:', error)
    health.value.backend = false
    health.value.database = false
    health.value.api = false
    health.value.lastCheck = new Date().toLocaleTimeString()
  } finally {
    health.value.checking = false
  }
}

const loadStats = async () => {
  try {
    const response = await systemAPI.getStats()
    if (response.data.success) {
      stats.value = response.data.stats
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadActiveToken = async () => {
  loading.value = true
  try {
    const response = await tokenAPI.getActive()
    if (response.data.success && response.data.token) {
      activeToken.value = response.data.token
      decodeToken()
      // Load user roles/licenses when token changes
      loadActiveUserInfo()
      // Load permissions - Sprint 4.1
      loadPermissions()
    } else {
      activeToken.value = null
      userInfo.value = { roles: [], licenses: [] }
      permissions.value = { success: false }
    }
  } catch (error) {
    console.error('Failed to load active token:', error)
    activeToken.value = null
  } finally {
    loading.value = false
  }
}

// Load active user roles and licenses - Sprint 2
const loadActiveUserInfo = async () => {
  if (!activeToken.value?.upn) return
  
  userInfoLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/roles/active-user-info')
    const data = await response.json()
    
    if (data.success) {
      userInfo.value = {
        roles: data.roles || [],
        licenses: data.licenses || []
      }
    }
  } catch (error) {
    console.error('Failed to load user info:', error)
  } finally {
    userInfoLoading.value = false
  }
}

// Load permissions analysis
// With throttle to prevent too frequent API calls
let lastPermissionsLoad = 0
const loadPermissions = async (force = false) => {
  if (!activeToken.value) return
  
  // Throttle: only load if 30+ seconds since last load (unless forced)
  const now = Date.now()
  if (!force && now - lastPermissionsLoad < 30000) {
    console.log('[Dashboard] Permissions load throttled (< 30s since last load)')
    return
  }
  lastPermissionsLoad = now
  
  permissionsLoading.value = true
  try {
    const response = await fetch('http://localhost:5000/api/permissions/analyze')
    const data = await response.json()
    
    permissions.value = data
    console.log('[Dashboard] Permissions loaded successfully')
  } catch (error) {
    console.error('Failed to load permissions:', error)
    permissions.value = { success: false, error: 'Failed to analyze permissions' }
  } finally {
    permissionsLoading.value = false
  }
}

const decodeToken = () => {
  if (!activeToken.value || !activeToken.value.access_token_full) return

  try {
    const parts = activeToken.value.access_token_full.split('.')
    if (parts.length !== 3) return

    const payload = JSON.parse(atob(parts[1]))
    
    if (payload.scp) {
      decodedScopes.value = payload.scp.split(' ')
    }
  } catch (error) {
    console.error('Failed to decode JWT:', error)
    decodedScopes.value = []
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  
  let utcString = dateString
  if (!dateString.endsWith('Z') && !dateString.includes('+')) {
    utcString = dateString.replace(' ', 'T') + 'Z'
  }
  
  const date = new Date(utcString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  })
}

const getTimeRemaining = (expiresAt) => {
  if (!expiresAt) return ''
  
  let utcString = expiresAt
  if (!expiresAt.endsWith('Z') && !expiresAt.includes('+')) {
    utcString = expiresAt.replace(' ', 'T') + 'Z'
  }
  
  const now = new Date()
  const expiry = new Date(utcString)
  const diffMs = expiry - now
  
  if (diffMs < 0) {
    return '⚠️ Expired'
  }
  
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
  
  if (diffHours > 24) {
    const diffDays = Math.floor(diffHours / 24)
    return `⏱️ Expires in ${diffDays} day(s) ${diffHours % 24} hour(s)`
  } else if (diffHours > 0) {
    return `⏱️ Expires in ${diffHours} hour(s) ${diffMins} min(s)`
  } else {
    return `⚠️ Expires in ${diffMins} minute(s)`
  }
}

// Scheduler functions
const loadSchedulerStatus = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/scheduler/status')
    const data = await response.json()
    
    if (data.success) {
      scheduler.value = data.status
      configInterval.value = data.status.config?.interval_minutes || 5
      configThreshold.value = data.status.config?.expiry_threshold_minutes || 10
    }
  } catch (error) {
    console.error('Failed to load scheduler status:', error)
  }
}

const loadExpiringTokens = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/scheduler/expiring')
    const data = await response.json()
    
    if (data.success) {
      expiringTokens.value = data.expiring_tokens
    }
  } catch (error) {
    console.error('Failed to load expiring tokens:', error)
  }
}

const loadSchedulerHistory = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/scheduler/history?limit=10')
    const data = await response.json()
    
    if (data.success) {
      schedulerHistory.value = data.history
    }
  } catch (error) {
    console.error('Failed to load scheduler history:', error)
  }
}

const toggleScheduler = async () => {
  schedulerLoading.value = true
  
  try {
    const endpoint = scheduler.value.is_running ? 'stop' : 'start'
    const response = await fetch(`http://localhost:5000/api/scheduler/${endpoint}`, {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      await loadSchedulerStatus()
      await loadSchedulerHistory()
    } else {
      alert(data.error || 'Failed to toggle scheduler')
    }
  } catch (error) {
    console.error('Failed to toggle scheduler:', error)
    alert('Failed to toggle scheduler')
  } finally {
    schedulerLoading.value = false
  }
}

const triggerRefreshNow = async () => {
  schedulerLoading.value = true
  
  try {
    const response = await fetch('http://localhost:5000/api/scheduler/trigger', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      const msg = `Refreshed: ${data.refreshed}, Failed: ${data.failed}`
      alert(msg)
      await loadSchedulerHistory()
      await loadExpiringTokens()
      await loadStats()
    } else {
      alert(data.error || 'Refresh failed')
    }
  } catch (error) {
    console.error('Failed to trigger refresh:', error)
    alert('Failed to trigger refresh')
  } finally {
    schedulerLoading.value = false
  }
}

const updateSchedulerConfig = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/scheduler/config', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        interval_minutes: configInterval.value,
        expiry_threshold_minutes: configThreshold.value
      })
    })
    const data = await response.json()
    
    if (data.success) {
      await loadSchedulerStatus()
      alert('Configuration saved!')
    } else {
      alert(data.error || 'Failed to update config')
    }
  } catch (error) {
    console.error('Failed to update config:', error)
    alert('Failed to update configuration')
  }
}

const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  checkHealth()
  loadStats()
  loadActiveToken()
  loadSchedulerStatus()
  loadExpiringTokens()
  loadSchedulerHistory()
  
  intervals.value.push(setInterval(checkHealth, 60000))
  intervals.value.push(setInterval(loadStats, 30000))
  intervals.value.push(setInterval(loadActiveToken, 60000))
  intervals.value.push(setInterval(() => {
    loadSchedulerStatus()
    loadExpiringTokens()
    loadSchedulerHistory()
  }, 60000))
})

// Watch activeToken changes and force reload permissions
// FIX: This ensures Directory Roles update when switching active token
watch(() => activeToken.value?.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    console.log('[Dashboard] Active token changed, reloading permissions (force=true)')
    loadPermissions(true)  // Force reload, bypass throttle
    decodeToken()          // Also decode new token scopes
  }
})

onUnmounted(() => {
  intervals.value.forEach(interval => clearInterval(interval))
  intervals.value = []
})
</script>
