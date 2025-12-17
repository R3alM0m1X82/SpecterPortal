<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Applications</h1>
      <div class="flex space-x-4">
        <button 
          @click="viewMode = 'sp'" 
          :class="viewMode === 'sp' ? 'btn-primary' : (isDark ? 'btn-secondary-dark' : 'btn-secondary')"
          class="btn"
        >
          Service Principals
        </button>
        <button 
          @click="viewMode = 'apps'" 
          :class="viewMode === 'apps' ? 'btn-primary' : (isDark ? 'btn-secondary-dark' : 'btn-secondary')"
          class="btn"
        >
          App Registrations
        </button>
        <button 
          @click="viewMode = 'myapps'" 
          :class="viewMode === 'myapps' ? 'btn-primary' : (isDark ? 'btn-secondary-dark' : 'btn-secondary')"
          class="btn"
        >
          🔐 My Apps
        </button>
        <button 
          @click="viewMode = 'consent'" 
          :class="viewMode === 'consent' ? 'btn-primary' : (isDark ? 'btn-secondary-dark' : 'btn-secondary')"
          class="btn"
        >
          ⚠️ OAuth Consent
        </button>
        <button 
          @click="viewMode = 'managed'" 
          :class="viewMode === 'managed' ? 'btn-primary' : (isDark ? 'btn-secondary-dark' : 'btn-secondary')"
          class="btn"
        >
          🆔 Managed Identities
        </button>
        <button @click="loadData(true)" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
          🔄 Refresh
        </button>
        
        <!-- Export Button -->
        <div class="relative" v-if="['sp', 'apps', 'managed'].includes(viewMode)">
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
        <button 
          v-if="['sp', 'apps', 'consent', 'managed'].includes(viewMode)" 
          @click="loadOwners" 
          class="btn"
          :class="loadingOwners ? 'btn-secondary' : 'btn-primary'"
          :disabled="loadingOwners || filteredItems.length === 0">
          {{ loadingOwners ? '⏳ Loading...' : (ownersLoaded ? '✅ Owners Loaded' : '👤 Load Owners') }}
        </button>
        <button 
          v-if="['sp', 'managed'].includes(viewMode)" 
          @click="loadRoles" 
          class="btn"
          :class="loadingRoles ? 'btn-secondary' : 'btn-primary'"
          :disabled="loadingRoles || filteredItems.length === 0">
          {{ loadingRoles ? '⏳ Loading...' : (rolesLoaded ? '✅ Roles Loaded' : '🛡️ Load Roles') }}
        </button>
        <button 
          v-if="viewMode === 'sp'" 
          @click="analyzePermissions" 
          class="btn"
          :class="analyzingPermissions ? 'btn-secondary' : 'btn-primary'"
          :disabled="analyzingPermissions || servicePrincipals.length === 0">
          {{ analyzingPermissions ? '⏳ Analyzing...' : (permissionsAnalyzed ? '✅ Analyzed' : '🔍 Analyze Permissions') }}
        </button>
        <button 
          v-if="viewMode === 'myapps'" 
          @click="openCreateModal" 
          class="btn btn-success"
          :disabled="!canCreateApps"
          :title="!canCreateApps ? 'App registration is disabled by policy' : 'Create new App Registration'"
        >
          ➕ Create App
        </button>
      </div>
    </div>

    <!-- Policy Warning -->
    <div v-if="viewMode === 'myapps' && policyChecked && !canCreateApps" 
         class="mb-4 p-4 rounded-lg" 
         :class="isDark ? 'bg-yellow-900/50 border border-yellow-700' : 'bg-yellow-50 border border-yellow-200'">
      <p class="text-sm" :class="isDark ? 'text-yellow-300' : 'text-yellow-700'">
        ⚠️ App registration is disabled by tenant policy. Only admins can create applications.
      </p>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        type="text"
        :placeholder="getSearchPlaceholder()"
        class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        :class="isDark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
      />
    </div>
    
    <!-- Count -->
    <div class="mb-4 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
      {{ filteredItems.length }} {{ getCountLabel() }}
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading applications...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ error }}</p>
      <button @click="loadData" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Service Principals Table -->
    <div v-else-if="viewMode === 'sp' && filteredItems.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">App ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Owner</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Roles</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Risk</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Credentials</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="sp in filteredItems" :key="sp.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">{{ sp.displayName }}</div>
              <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ sp.appDisplayName }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="font-mono text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ sp.appId }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ sp.servicePrincipalType }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              <span v-if="sp.owner" :title="formatOwnerTooltip(sp.owners)">{{ sp.owner }}</span>
              <span v-else class="text-xs italic">—</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              <span v-if="sp.role" :title="formatRoleTooltip(sp.roles)">{{ sp.role }}</span>
              <span v-else class="text-xs italic">—</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span v-if="sp.riskAnalysis && sp.riskAnalysis.riskLevel !== 'None'" 
                    :class="getRiskBadgeClass(sp.riskAnalysis.riskLevel, isDark)"
                    :title="formatRiskTooltip(sp.riskAnalysis)"
                    class="px-2 py-1 text-xs font-semibold rounded-full">
                {{ sp.riskAnalysis.riskLevel }}
              </span>
              <span v-else class="text-xs italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">—</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <CredentialBadge :credentials="sp.credentials" :isDark="isDark" />
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="sp.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')" 
                    class="px-2 py-1 text-xs font-semibold rounded-full">
                {{ sp.accountEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- App Registrations Table -->
    <div v-else-if="viewMode === 'apps' && filteredItems.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">App ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Publisher</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Owner</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Credentials</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Created</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="app in filteredItems" :key="app.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
              {{ app.displayName }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="font-mono text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ app.appId }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ app.publisherDomain || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              <span v-if="app.owner" :title="formatOwnerTooltip(app.owners)">{{ app.owner }}</span>
              <span v-else class="text-xs italic">—</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <CredentialBadge :credentials="app.credentials" :isDark="isDark" />
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ formatDate(app.createdDateTime) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Managed Identities Table -->
    <div v-else-if="viewMode === 'managed' && filteredItems.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">App ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Owner</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Roles</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="mi in filteredItems" :key="mi.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">{{ mi.displayName }}</div>
              <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ mi.appDisplayName }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'" 
                    class="px-2 py-1 text-xs font-semibold rounded-full">
                {{ mi.servicePrincipalType }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="font-mono text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ mi.appId }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              <span v-if="mi.owner" :title="formatOwnerTooltip(mi.owners)">{{ mi.owner }}</span>
              <span v-else class="text-xs italic">—</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="mi.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')" 
                    class="px-2 py-1 text-xs font-semibold rounded-full">
                {{ mi.accountEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- My Apps Table (with actions) -->
    <div v-else-if="viewMode === 'myapps' && filteredItems.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">App ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Audience</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Credentials</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Created</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="app in filteredItems" :key="app.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
              {{ app.displayName }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="font-mono text-xs cursor-pointer hover:text-blue-500" 
                    :class="isDark ? 'text-gray-400' : 'text-gray-600'"
                    @click="copyToClipboard(app.appId)"
                    title="Click to copy">
                {{ app.appId }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ formatAudience(app.signInAudience) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <CredentialBadge :credentials="app.credentials" :isDark="isDark" />
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ formatDate(app.createdDateTime) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex space-x-2">
                <button @click="openSecretModal(app)" class="btn-sm btn-primary" title="Add Secret">
                  🔑
                </button>
                <button @click="openSecretsListModal(app)" class="btn-sm" 
                        :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'" 
                        title="View Secrets"
                        :disabled="!app.credentials || app.credentials.secretCount === 0">
                  📋
                </button>
                <button @click="confirmDelete(app)" class="btn-sm btn-danger" title="Delete App">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- OAuth Consent Table -->
    <div v-else-if="viewMode === 'consent' && filteredItems.length > 0">
      <!-- Stats Summary -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="rounded-lg p-4" :class="isDark ? 'bg-red-900/30 border border-red-700' : 'bg-red-50 border border-red-200'">
          <div class="text-2xl font-bold" :class="isDark ? 'text-red-400' : 'text-red-600'">{{ consentStats.critical || 0 }}</div>
          <div class="text-sm" :class="isDark ? 'text-red-300' : 'text-red-500'">Critical Risk</div>
        </div>
        <div class="rounded-lg p-4" :class="isDark ? 'bg-orange-900/30 border border-orange-700' : 'bg-orange-50 border border-orange-200'">
          <div class="text-2xl font-bold" :class="isDark ? 'text-orange-400' : 'text-orange-600'">{{ consentStats.high || 0 }}</div>
          <div class="text-sm" :class="isDark ? 'text-orange-300' : 'text-orange-500'">High Risk</div>
        </div>
        <div class="rounded-lg p-4" :class="isDark ? 'bg-yellow-900/30 border border-yellow-700' : 'bg-yellow-50 border border-yellow-200'">
          <div class="text-2xl font-bold" :class="isDark ? 'text-yellow-400' : 'text-yellow-600'">{{ consentStats.medium || 0 }}</div>
          <div class="text-sm" :class="isDark ? 'text-yellow-300' : 'text-yellow-500'">Medium Risk</div>
        </div>
        <div class="rounded-lg p-4" :class="isDark ? 'bg-green-900/30 border border-green-700' : 'bg-green-50 border border-green-200'">
          <div class="text-2xl font-bold" :class="isDark ? 'text-green-400' : 'text-green-600'">{{ consentStats.low || 0 }}</div>
          <div class="text-sm" :class="isDark ? 'text-green-300' : 'text-green-500'">Low Risk</div>
        </div>
      </div>

      <!-- Consent Apps Table -->
      <div class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Risk</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Application</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Publisher</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Owner</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Consent</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Permissions</th>
              <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
            <tr v-for="app in filteredItems" :key="app.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
              <!-- Risk Badge -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getRiskBadgeClass(app.risk.level)" class="px-2 py-1 text-xs font-bold rounded-full">
                  {{ app.risk.score }}/10
                </span>
                <div class="text-xs mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  {{ app.risk.level }}
                </div>
              </td>
              <!-- Application -->
              <td class="px-6 py-4">
                <div class="font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
                  {{ app.displayName }}
                  <span v-if="app.isMicrosoftApp" class="ml-1 text-xs" title="Microsoft App">🏢</span>
                </div>
                <div class="text-xs font-mono" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  {{ app.appId }}
                </div>
              </td>
              <!-- Publisher -->
              <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                {{ app.publisherName }}
                <span v-if="app.verifiedPublisher?.verifiedPublisherId" class="ml-1 text-blue-500" title="Verified Publisher">✓</span>
              </td>
              <!-- Owner -->
              <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                <span v-if="app.owner" :title="formatOwnerTooltip(app.owners)">{{ app.owner }}</span>
                <span v-else class="text-xs italic">—</span>
              </td>
              <!-- Consent Type -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="app.consentType === 'Admin' 
                  ? (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800')
                  : (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')"
                  class="px-2 py-1 text-xs font-semibold rounded-full">
                  {{ app.consentType }}
                </span>
              </td>
              <!-- Permissions -->
              <td class="px-6 py-4">
                <div class="flex flex-wrap gap-1 max-w-xs">
                  <span v-for="(perm, idx) in app.permissions.slice(0, 3)" :key="idx"
                        class="px-1.5 py-0.5 text-xs rounded"
                        :class="isHighRiskPerm(perm) 
                          ? (isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-100 text-red-700')
                          : (isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600')">
                    {{ perm }}
                  </span>
                  <span v-if="app.permissions.length > 3" 
                        class="px-1.5 py-0.5 text-xs rounded cursor-pointer"
                        :class="isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500'"
                        :title="app.permissions.slice(3).join(', ')">
                    +{{ app.permissions.length - 3 }} more
                  </span>
                </div>
              </td>
              <!-- Status -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="app.accountEnabled 
                  ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') 
                  : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')" 
                  class="px-2 py-1 text-xs font-semibold rounded-full">
                  {{ app.accountEnabled ? 'Enabled' : 'Disabled' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Risk Factors Legend -->
      <div class="mt-4 p-4 rounded-lg" :class="isDark ? 'bg-gray-800' : 'bg-gray-50'">
        <h4 class="text-sm font-semibold mb-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Risk Factors</h4>
        <div class="text-xs space-y-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          <p>• <span class="font-semibold text-red-500">Critical (9-10)</span>: Multiple high-risk permissions with dangerous combinations</p>
          <p>• <span class="font-semibold text-orange-500">High (6-8)</span>: Sensitive permissions like Mail.ReadWrite.All, Files.ReadWrite.All</p>
          <p>• <span class="font-semibold text-yellow-500">Medium (3-5)</span>: Some elevated permissions, review recommended</p>
          <p>• <span class="font-semibold text-green-500">Low (0-2)</span>: Standard permissions, low risk</p>
        </div>
      </div>
    </div>
    
    <!-- Empty -->
    <div v-else class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="text-6xl mb-4">{{ viewMode === 'consent' ? '🛡️' : '📱' }}</div>
      <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">
        {{ viewMode === 'myapps' ? 'No Apps Owned by You' : (viewMode === 'consent' ? 'No OAuth Consents Found' : 'No Applications Found') }}
      </h2>
      <p v-if="viewMode === 'myapps'" class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
        Click "Create App" to register a new application
      </p>
    </div>

    <!-- Create App Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 w-full max-w-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">Create App Registration</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Display Name *
            </label>
            <input v-model="createForm.displayName" type="text" 
                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                   :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'"
                   placeholder="My Application" />
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Sign-in Audience
            </label>
            <select v-model="createForm.signInAudience" 
                    class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'">
              <option value="AzureADMyOrg">Single tenant (this org only)</option>
              <option value="AzureADMultipleOrgs">Multi-tenant (any Azure AD)</option>
              <option value="AzureADandPersonalMicrosoftAccount">Multi-tenant + Personal MS accounts</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Description (optional)
            </label>
            <textarea v-model="createForm.description" 
                      class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'"
                      rows="2"
                      placeholder="Application description..."></textarea>
          </div>
        </div>
        
        <div v-if="createError" class="mt-4 p-3 rounded-lg" :class="isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-50 text-red-600'">
          {{ createError }}
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="closeCreateModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            Cancel
          </button>
          <button @click="createApplication" class="btn btn-success" :disabled="creating || !createForm.displayName">
            {{ creating ? 'Creating...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add Secret Modal -->
    <div v-if="showSecretModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 w-full max-w-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
          Add Client Secret
        </h2>
        <p class="text-sm mb-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          App: {{ selectedApp?.displayName }}
        </p>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Description
            </label>
            <input v-model="secretForm.description" type="text" 
                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                   :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'"
                   placeholder="SpecterPortal Secret" />
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Expires
            </label>
            <select v-model="secretForm.expiryMonths" 
                    class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'">
              <option :value="1">1 month</option>
              <option :value="6">6 months</option>
              <option :value="12">12 months (recommended)</option>
              <option :value="24">24 months</option>
            </select>
          </div>
        </div>
        
        <!-- Secret Result -->
        <div v-if="generatedSecret" class="mt-4 p-4 rounded-lg" :class="isDark ? 'bg-green-900/50 border border-green-700' : 'bg-green-50 border border-green-200'">
          <p class="font-semibold mb-2" :class="isDark ? 'text-green-300' : 'text-green-700'">
            ⚠️ Copy this secret now! It won't be shown again.
          </p>
          <div class="flex items-center space-x-2">
            <input type="text" :value="generatedSecret" readonly
                   class="flex-1 px-3 py-2 font-mono text-sm rounded border"
                   :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'" />
            <button @click="copyToClipboard(generatedSecret)" class="btn btn-primary">
              📋 Copy
            </button>
          </div>
        </div>
        
        <div v-if="secretError" class="mt-4 p-3 rounded-lg" :class="isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-50 text-red-600'">
          {{ secretError }}
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="closeSecretModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            {{ generatedSecret ? 'Close' : 'Cancel' }}
          </button>
          <button v-if="!generatedSecret" @click="addSecret" class="btn btn-success" :disabled="addingSecret">
            {{ addingSecret ? 'Creating...' : 'Generate Secret' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Secrets List Modal -->
    <div v-if="showSecretsListModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 w-full max-w-lg" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
          Client Secrets
        </h2>
        <p class="text-sm mb-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          App: {{ selectedApp?.displayName }}
        </p>
        
        <div v-if="selectedApp?.credentials?.secrets?.length > 0" class="space-y-3">
          <div v-for="secret in selectedApp.credentials.secrets" :key="secret.keyId" 
               class="p-3 rounded-lg flex items-center justify-between"
               :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
            <div>
              <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                {{ secret.displayName || 'Unnamed' }}
              </p>
              <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                Expires: {{ formatDate(secret.endDateTime) }}
                <span v-if="isExpired(secret.endDateTime)" class="text-red-500 ml-2">⚠️ Expired</span>
              </p>
            </div>
            <button @click="deleteSecret(secret.keyId)" class="btn-sm btn-danger" 
                    :disabled="deletingSecretId === secret.keyId">
              {{ deletingSecretId === secret.keyId ? '...' : '🗑️' }}
            </button>
          </div>
        </div>
        <div v-else class="text-center py-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          No secrets found
        </div>
        
        <div class="flex justify-end mt-6">
          <button @click="closeSecretsListModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl p-6 w-full max-w-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
          ⚠️ Delete Application?
        </h2>
        <p class="mb-4" :class="isDark ? 'text-gray-300' : 'text-gray-600'">
          Are you sure you want to delete <strong>{{ selectedApp?.displayName }}</strong>?
        </p>
        <p class="text-sm mb-4" :class="isDark ? 'text-red-400' : 'text-red-600'">
          This action cannot be undone. All secrets and configurations will be permanently deleted.
        </p>
        
        <div v-if="deleteError" class="mb-4 p-3 rounded-lg" :class="isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-50 text-red-600'">
          {{ deleteError }}
        </div>
        
        <div class="flex justify-end space-x-3">
          <button @click="closeDeleteModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            Cancel
          </button>
          <button @click="deleteApplication" class="btn btn-danger" :disabled="deleting">
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toast.show" 
         class="fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity"
         :class="toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, h } from 'vue'

// Credential Badge Component (inline) - Sprint 11.2: Enhanced with expiry visualization
const CredentialBadge = {
  props: {
    credentials: Object,
    isDark: Boolean
  },
  setup(props) {
    const cred = computed(() => props.credentials || {})
    
    const getExpiryDays = () => {
      if (!cred.value.earliestExpiry) return null
      const expiry = new Date(cred.value.earliestExpiry)
      const now = new Date()
      return Math.floor((expiry - now) / (1000 * 60 * 60 * 24))
    }
    
    const getBadgeClass = () => {
      const type = cred.value.credentialType
      const status = cred.value.expiryStatus
      
      // Expiry-based coloring
      if (status === 'expired') return 'bg-red-600 text-white'
      if (status === 'expiring_soon') return 'bg-orange-500 text-white'
      if (status === 'expiring') return 'bg-yellow-500 text-black'
      
      // Type-based coloring (default)
      if (type === 'both') return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-700'
      if (type === 'secret') return props.isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-700'
      if (type === 'certificate') return props.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'
      return props.isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500'
    }
    
    const getIcon = () => {
      const type = cred.value.credentialType
      const status = cred.value.expiryStatus
      
      // Add warning icon if expiring/expired
      let icon = ''
      if (type === 'both') icon = '🔑📜'
      else if (type === 'secret') icon = '🔑'
      else if (type === 'certificate') icon = '📜'
      else icon = '—'
      
      if (status === 'expired') return '❌ ' + icon
      if (status === 'expiring_soon') return '⚠️ ' + icon
      if (status === 'expiring') return '⏰ ' + icon
      
      return icon
    }
    
    const getLabel = () => {
      const type = cred.value.credentialType
      if (type === 'both') {
        return `${cred.value.secretCount}S + ${cred.value.certificateCount}C`
      }
      if (type === 'secret') return `${cred.value.secretCount} Secret${cred.value.secretCount > 1 ? 's' : ''}`
      if (type === 'certificate') return `${cred.value.certificateCount} Cert${cred.value.certificateCount > 1 ? 's' : ''}`
      return 'None'
    }
    
    const getTitle = () => {
      if (!cred.value.earliestExpiry) return ''
      const expiry = new Date(cred.value.earliestExpiry)
      const now = new Date()
      const days = getExpiryDays()
      
      if (days < 0) return `⚠️ EXPIRED ${Math.abs(days)} days ago!`
      if (days === 0) return `⚠️ EXPIRES TODAY!`
      if (days < 30) return `⚠️ Expires in ${days} days (${expiry.toLocaleDateString()})`
      if (days < 90) return `⏰ Expires in ${days} days (${expiry.toLocaleDateString()})`
      return `Earliest expiry: ${expiry.toLocaleDateString()} (${days} days)`
    }
    
    return () => h('span', {
      class: `px-2 py-1 text-xs font-semibold rounded-full inline-flex items-center space-x-1 ${getBadgeClass()}`,
      title: getTitle()
    }, [
      h('span', getIcon()),
      h('span', getLabel())
    ])
  }
}

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

// State
const viewMode = ref('sp')
const servicePrincipals = ref([])
const applications = ref([])
const myApplications = ref([])
const managedIdentities = ref([])
const consentApps = ref([])
const consentStats = ref({})
const loading = ref(false)

// Cache refs (5 minutes TTL)
const spCache = ref({ data: null, timestamp: null })
const appsCache = ref({ data: null, timestamp: null })
const myAppsCache = ref({ data: null, timestamp: null })
const managedCache = ref({ data: null, timestamp: null })
const consentCache = ref({ data: null, timestamp: null, stats: null })
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes
const error = ref(null)
const searchQuery = ref('')

// Owner loading state (Sprint 11.2)
const loadingOwners = ref(false)
const ownersLoaded = ref(false)

// Role loading state (Sprint 11.2 Step C)
const loadingRoles = ref(false)
const rolesLoaded = ref(false)

// Risky SP filter (Sprint 11.2 Step D)
const showRiskyOnly = ref(false)
const analyzingPermissions = ref(false)
const permissionsAnalyzed = ref(false)
const showExportMenu = ref(false)

// Policy
const policyChecked = ref(false)
const canCreateApps = ref(true)

// Create App Modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref(null)
const createForm = ref({
  displayName: '',
  signInAudience: 'AzureADMyOrg',
  description: ''
})

// Secret Modal
const showSecretModal = ref(false)
const addingSecret = ref(false)
const secretError = ref(null)
const generatedSecret = ref(null)
const secretForm = ref({
  description: 'SpecterPortal Secret',
  expiryMonths: 12
})

// Secrets List Modal
const showSecretsListModal = ref(false)
const deletingSecretId = ref(null)

// Delete Modal
const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref(null)

// Selected App
const selectedApp = ref(null)

// Toast
const toast = ref({ show: false, message: '', type: 'success' })

// Computed
const filteredItems = computed(() => {
  let items = []
  if (viewMode.value === 'sp') items = servicePrincipals.value
  else if (viewMode.value === 'apps') items = applications.value
  else if (viewMode.value === 'myapps') items = myApplications.value
  else if (viewMode.value === 'managed') items = managedIdentities.value
  else if (viewMode.value === 'consent') items = consentApps.value
  
  // Apply risky filter for SPs (Sprint 11.2 Step D)
  if (viewMode.value === 'sp' && showRiskyOnly.value) {
    items = items.filter(item => {
      const risk = item.riskAnalysis?.riskLevel
      return risk && ['Critical', 'High', 'Medium'].includes(risk)
    })
  }
  
  if (!searchQuery.value.trim()) return items
  
  const query = searchQuery.value.toLowerCase()
  
  return items.filter(item => 
    item.displayName?.toLowerCase().includes(query) ||
    item.appId?.toLowerCase().includes(query) ||
    item.appDisplayName?.toLowerCase().includes(query) ||
    item.publisherName?.toLowerCase().includes(query)
  )
})

// Methods
const getSearchPlaceholder = () => {
  if (viewMode.value === 'sp') return 'Search service principals...'
  if (viewMode.value === 'apps') return 'Search app registrations...'
  if (viewMode.value === 'managed') return 'Search managed identities...'
  if (viewMode.value === 'consent') return 'Search OAuth consents...'
  return 'Search your apps...'
}

const getCountLabel = () => {
  if (viewMode.value === 'sp') return 'service principal(s)'
  if (viewMode.value === 'apps') return 'application(s)'
  if (viewMode.value === 'managed') return 'managed identit(y|ies)'
  if (viewMode.value === 'consent') return 'app(s) with consent'
  return 'app(s) owned by you'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString()
}

const formatAudience = (audience) => {
  const map = {
    'AzureADMyOrg': 'Single tenant',
    'AzureADMultipleOrgs': 'Multi-tenant',
    'AzureADandPersonalMicrosoftAccount': 'Multi + Personal',
    'PersonalMicrosoftAccount': 'Personal only'
  }
  return map[audience] || audience
}

const isExpired = (dateStr) => {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

const isHighRiskPerm = (perm) => {
  const highRisk = ['Mail.ReadWrite', 'Mail.Send', 'Files.ReadWrite.All', 'Directory.ReadWrite.All', 
                   'Application.ReadWrite.All', 'RoleManagement.ReadWrite', 'User.ReadWrite.All']
  return highRisk.some(hr => perm.toLowerCase().includes(hr.toLowerCase()))
}

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => { toast.value.show = false }, 3000)
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast('Copied to clipboard!')
  } catch {
    showToast('Failed to copy', 'error')
  }
}

const formatOwnerTooltip = (owners) => {
  if (!owners || owners.length === 0) return ''
  if (owners.length === 1) {
    return owners[0].userPrincipalName || owners[0].displayName
  }
  return owners.map(o => o.displayName || o.userPrincipalName).join('\n')
}

const checkPolicy = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/apps/policy')
    const data = await response.json()
    if (data.success) {
      canCreateApps.value = data.allowedToCreateApps
    }
    policyChecked.value = true
  } catch {
    policyChecked.value = true
  }
}

// Check if cache is valid
const isCacheValid = (cache) => {
  if (!cache.data || !cache.timestamp) return false
  return (Date.now() - cache.timestamp) < CACHE_TTL
}

const loadData = async (forceRefresh = false) => {
  loading.value = true
  error.value = null
  
  try {
    if (viewMode.value === 'sp') {
      // Check cache first (unless force refresh)
      if (!forceRefresh && isCacheValid(spCache.value)) {
        console.log('[CACHE] Using cached service principals')
        servicePrincipals.value = spCache.value.data
        loading.value = false
        return
      }
      
      console.log('[API] Fetching service principals', forceRefresh ? '(forced)' : '')
      const response = await fetch('http://localhost:5000/api/tenant/service-principals')
      const data = await response.json()
      if (data.success) {
        servicePrincipals.value = data.servicePrincipals
        spCache.value = { data: data.servicePrincipals, timestamp: Date.now() }
        console.log('[CACHE] Service principals cached:', data.servicePrincipals.length, 'items')
      }
      else error.value = data.error
    } else if (viewMode.value === 'apps') {
      // Check cache
      if (!forceRefresh && isCacheValid(appsCache.value)) {
        console.log('[CACHE] Using cached applications')
        applications.value = appsCache.value.data
        loading.value = false
        return
      }
      
      console.log('[API] Fetching applications', forceRefresh ? '(forced)' : '')
      const response = await fetch('http://localhost:5000/api/tenant/applications')
      const data = await response.json()
      if (data.success) {
        applications.value = data.applications
        appsCache.value = { data: data.applications, timestamp: Date.now() }
        console.log('[CACHE] Applications cached:', data.applications.length, 'items')
      }
      else error.value = data.error
    } else if (viewMode.value === 'myapps') {
      // Check cache
      if (!forceRefresh && isCacheValid(myAppsCache.value)) {
        console.log('[CACHE] Using cached my apps')
        myApplications.value = myAppsCache.value.data
        loading.value = false
        return
      }
      
      console.log('[API] Fetching my apps', forceRefresh ? '(forced)' : '')
      const response = await fetch('http://localhost:5000/api/apps/my-apps')
      const data = await response.json()
      if (data.success) {
        myApplications.value = data.applications
        myAppsCache.value = { data: data.applications, timestamp: Date.now() }
        console.log('[CACHE] My apps cached:', data.applications.length, 'items')
      }
      else error.value = data.error
    } else if (viewMode.value === 'managed') {
      // Check cache
      if (!forceRefresh && isCacheValid(managedCache.value)) {
        console.log('[CACHE] Using cached managed identities')
        managedIdentities.value = managedCache.value.data
        loading.value = false
        return
      }
      
      console.log('[API] Fetching managed identities', forceRefresh ? '(forced)' : '')
      const response = await fetch('http://localhost:5000/api/tenant/managed-identities')
      const data = await response.json()
      if (data.success) {
        managedIdentities.value = data.managedIdentities
        managedCache.value = { data: data.managedIdentities, timestamp: Date.now() }
        console.log('[CACHE] Managed identities cached:', data.managedIdentities.length, 'items')
      }
      else error.value = data.error
    } else if (viewMode.value === 'consent') {
      // Check cache
      if (!forceRefresh && isCacheValid(consentCache.value)) {
        console.log('[CACHE] Using cached consent apps')
        consentApps.value = consentCache.value.data
        consentStats.value = consentCache.value.stats
        loading.value = false
        return
      }
      
      console.log('[API] Fetching consent apps', forceRefresh ? '(forced)' : '')
      const response = await fetch('http://localhost:5000/api/oauth-consent')
      const data = await response.json()
      if (data.success) {
        consentApps.value = data.consentApps
        consentStats.value = data.stats
        consentCache.value = { data: data.consentApps, stats: data.stats, timestamp: Date.now() }
        console.log('[CACHE] Consent apps cached:', data.consentApps.length, 'items')
      } else {
        error.value = data.error
      }
    }
  } catch (err) {
    error.value = 'Failed to load applications'
  } finally {
    loading.value = false
  }
}

// Export data
const exportData = async (format) => {
  showExportMenu.value = false
  
  try {
    let data = []
    let filename = ''
    
    if (viewMode.value === 'sp') {
      data = servicePrincipals.value
      filename = `service-principals-${new Date().toISOString().split('T')[0]}.${format}`
    } else if (viewMode.value === 'apps') {
      data = applications.value
      filename = `applications-${new Date().toISOString().split('T')[0]}.${format}`
    } else if (viewMode.value === 'managed') {
      data = managedIdentities.value
      filename = `managed-identities-${new Date().toISOString().split('T')[0]}.${format}`
    }
    
    if (format === 'csv') {
      // Convert to CSV
      const headers = Object.keys(data[0] || {})
      const csv = [
        headers.join(','),
        ...data.map(item => headers.map(h => {
          const val = item[h]
          return typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        }).join(','))
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
    } else {
      // JSON format
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error('Export failed:', err)
  }
}

// Create App
const openCreateModal = () => {
  createForm.value = { displayName: '', signInAudience: 'AzureADMyOrg', description: '' }
  createError.value = null
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
}

const createApplication = async () => {
  if (!createForm.value.displayName) return
  
  creating.value = true
  createError.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/apps/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(createForm.value)
    })
    const data = await response.json()
    
    if (data.success) {
      showToast(`Application "${data.application.displayName}" created!`)
      closeCreateModal()
      loadData()
    } else {
      createError.value = data.error
    }
  } catch (err) {
    createError.value = 'Failed to create application'
  } finally {
    creating.value = false
  }
}

// Add Secret
const openSecretModal = (app) => {
  selectedApp.value = app
  secretForm.value = { description: 'SpecterPortal Secret', expiryMonths: 12 }
  secretError.value = null
  generatedSecret.value = null
  showSecretModal.value = true
}

const closeSecretModal = () => {
  showSecretModal.value = false
  if (generatedSecret.value) loadData() // Refresh if secret was created
}

const addSecret = async () => {
  addingSecret.value = true
  secretError.value = null
  
  try {
    const response = await fetch(`http://localhost:5000/api/apps/${selectedApp.value.id}/secrets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(secretForm.value)
    })
    const data = await response.json()
    
    if (data.success) {
      generatedSecret.value = data.credential.secretText
      showToast('Secret created! Copy it now.')
    } else {
      secretError.value = data.error
    }
  } catch (err) {
    secretError.value = 'Failed to create secret'
  } finally {
    addingSecret.value = false
  }
}

// Secrets List
const openSecretsListModal = (app) => {
  selectedApp.value = app
  showSecretsListModal.value = true
}

const closeSecretsListModal = () => {
  showSecretsListModal.value = false
}

const deleteSecret = async (keyId) => {
  deletingSecretId.value = keyId
  
  try {
    const response = await fetch(`http://localhost:5000/api/apps/${selectedApp.value.id}/secrets/${keyId}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    
    if (data.success) {
      showToast('Secret deleted')
      // Refresh the app details
      const detailsResponse = await fetch(`http://localhost:5000/api/apps/${selectedApp.value.id}`)
      const detailsData = await detailsResponse.json()
      if (detailsData.success) {
        selectedApp.value = detailsData.application
        // Also update in the list
        const idx = myApplications.value.findIndex(a => a.id === selectedApp.value.id)
        if (idx !== -1) myApplications.value[idx] = detailsData.application
      }
    } else {
      showToast(data.error, 'error')
    }
  } catch {
    showToast('Failed to delete secret', 'error')
  } finally {
    deletingSecretId.value = null
  }
}

// Delete App
const confirmDelete = (app) => {
  selectedApp.value = app
  deleteError.value = null
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
}

const deleteApplication = async () => {
  deleting.value = true
  deleteError.value = null
  
  try {
    const response = await fetch(`http://localhost:5000/api/apps/${selectedApp.value.id}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    
    if (data.success) {
      showToast('Application deleted')
      closeDeleteModal()
      loadData()
    } else {
      deleteError.value = data.error
    }
  } catch (err) {
    deleteError.value = 'Failed to delete application'
  } finally {
    deleting.value = false
  }
}


const loadOwners = async () => {
  if (loadingOwners.value || ownersLoaded.value) return
  
  loadingOwners.value = true
  
  try {
    let endpoint = ''
    let entityType = ''
    let items = []
    
    if (viewMode.value === 'sp') {
      endpoint = 'http://localhost:5000/api/tenant/batch-owners'
      entityType = 'servicePrincipals'
      items = servicePrincipals.value
    } else if (viewMode.value === 'apps') {
      endpoint = 'http://localhost:5000/api/tenant/batch-owners'
      entityType = 'applications'
      items = applications.value
    } else if (viewMode.value === 'managed') {
      endpoint = 'http://localhost:5000/api/tenant/batch-owners'
      entityType = 'servicePrincipals'
      items = managedIdentities.value
    } else if (viewMode.value === 'consent') {
      endpoint = 'http://localhost:5000/api/oauth-consent/batch-owners'
      items = consentApps.value
    }
    
    if (!items || items.length === 0) {
      loadingOwners.value = false
      return
    }
    
    // Get IDs to fetch
    const entityIds = items.map(item => item.id).filter(Boolean)
    
    // Build request body
    const requestBody = viewMode.value === 'consent' 
      ? { appIds: entityIds }
      : { entityType, entityIds }
    
    // Call API
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
    
    const data = await response.json()
    
    if (data.success && data.owners) {
      // Merge owners into items
      items.forEach(item => {
        const ownerInfo = data.owners[item.id]
        if (ownerInfo) {
          item.owner = ownerInfo.owner
          item.owners = ownerInfo.owners
        }
      })
      
      ownersLoaded.value = true
      showToast(`Loaded owners for ${Object.keys(data.owners).length} items`)
    } else {
      showToast(data.error || 'Failed to load owners', 'error')
    }
  } catch (err) {
    console.error('Owner loading error:', err)
    showToast('Failed to load owners', 'error')
  } finally {
    loadingOwners.value = false
  }
}


const loadRoles = async () => {
  if (loadingRoles.value || rolesLoaded.value) return
  
  loadingRoles.value = true
  
  try {
    let items = []
    
    if (viewMode.value === 'sp') {
      items = servicePrincipals.value
    } else if (viewMode.value === 'managed') {
      items = managedIdentities.value
    }
    
    if (!items || items.length === 0) {
      loadingRoles.value = false
      return
    }
    
    // Get IDs to fetch
    const entityIds = items.map(item => item.id).filter(Boolean)
    
    // Call API
    const response = await fetch('http://localhost:5000/api/tenant/batch-roles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entityIds })
    })
    
    const data = await response.json()
    
    if (data.success && data.roles) {
      // Merge roles into items
      items.forEach(item => {
        const roleInfo = data.roles[item.id]
        if (roleInfo) {
          item.role = roleInfo.role
          item.roles = roleInfo.roles
          item.roleCount = roleInfo.roleCount
          item.hasTenantRole = roleInfo.hasTenantRole
          item.hasAURole = roleInfo.hasAURole
        }
      })
      
      rolesLoaded.value = true
      showToast(`Loaded roles for ${Object.keys(data.roles).length} items`)
    } else {
      showToast(data.error || 'Failed to load roles', 'error')
    }
  } catch (err) {
    console.error('Role loading error:', err)
    showToast('Failed to load roles', 'error')
  } finally {
    loadingRoles.value = false
  }
}


const formatRoleTooltip = (roles) => {
  if (!roles || roles.length === 0) return ''
  return roles.map(r => {
    if (r.scopeType === 'tenant') {
      return `🛡️ ${r.roleName} (Tenant-wide)`
    } else if (r.scopeType === 'au') {
      return `👥 ${r.roleName} (${r.scopeName})`
    } else {
      return `${r.roleName} (${r.scopeName})`
    }
  }).join('\n')
}


const getRiskBadgeClass = (riskLevel, isDark) => {
  const classes = 'px-2 py-1 text-xs font-semibold rounded-full '
  if (riskLevel === 'Critical') {
    return classes + (isDark ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800')
  } else if (riskLevel === 'High') {
    return classes + (isDark ? 'bg-orange-900 text-orange-200' : 'bg-orange-100 text-orange-800')
  } else if (riskLevel === 'Medium') {
    return classes + (isDark ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800')
  } else if (riskLevel === 'Low') {
    return classes + (isDark ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800')
  }
  return classes + (isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600')
}

const formatRiskTooltip = (riskAnalysis) => {
  if (!riskAnalysis) return ''
  const lines = [`Risk Score: ${riskAnalysis.riskScore}`]
  
  if (riskAnalysis.criticalCount > 0) {
    lines.push(`\n🔴 Critical: ${riskAnalysis.criticalCount} permission(s)`)
    riskAnalysis.criticalPermissions.forEach(p => {
      lines.push(`  • ${p.name}`)
    })
  }
  
  if (riskAnalysis.highCount > 0) {
    lines.push(`\n🟠 High: ${riskAnalysis.highCount} permission(s)`)
    riskAnalysis.highPermissions.forEach(p => {
      lines.push(`  • ${p.name}`)
    })
  }
  
  if (riskAnalysis.mediumCount > 0) {
    lines.push(`\n🟡 Medium: ${riskAnalysis.mediumCount} permission(s)`)
  }
  
  return lines.join('\n')
}


const analyzePermissions = async () => {
  if (analyzingPermissions.value || permissionsAnalyzed.value) return
  
  analyzingPermissions.value = true
  
  try {
    // Call risky-sps endpoint
    const response = await fetch('http://localhost:5000/api/tenant/risky-sps?min_risk=Low', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    
    const data = await response.json()
    
    if (data.success && data.riskyServicePrincipals) {
      const riskySPs = data.riskyServicePrincipals
      
      // Create a map of risky SPs
      const riskyMap = {}
      riskySPs.forEach(sp => {
        riskyMap[sp.id] = sp.riskAnalysis
      })
      
      // Update all service principals with risk analysis
      servicePrincipals.value.forEach(sp => {
        if (riskyMap[sp.id]) {
          sp.riskAnalysis = riskyMap[sp.id]
        } else {
          // Mark as analyzed but no risk
          sp.riskAnalysis = {
            riskLevel: 'None',
            riskScore: 0,
            permissions: [],
            criticalCount: 0,
            highCount: 0,
            mediumCount: 0
          }
        }
      })
      
      permissionsAnalyzed.value = true
      showToast(`Analyzed ${data.analyzed} SPs - Found ${riskySPs.length} risky`)
    } else {
      showToast(data.error || 'Failed to analyze permissions', 'error')
    }
  } catch (err) {
    console.error('Permission analysis error:', err)
    showToast('Failed to analyze permissions', 'error')
  } finally {
    analyzingPermissions.value = false
  }
}

// Watchers
watch(viewMode, () => {
  searchQuery.value = ''
  ownersLoaded.value = false  // Reset owner state on view change
  rolesLoaded.value = false  // Reset role state on view change
  permissionsAnalyzed.value = false  // Reset permissions state on view change
  loadData()
  if (viewMode.value === 'myapps' && !policyChecked.value) {
    checkPolicy()
  }
})

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-sm {
  @apply px-2 py-1 rounded font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
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

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700;
}

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.bg-gray-750 {
  background-color: #2d3748;
}
</style>
