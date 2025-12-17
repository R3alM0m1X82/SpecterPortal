<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header with Tab System -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
        🏢 Tenant Information
      </h1>
      
      <!-- Tab Buttons -->
      <div class="flex space-x-2 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-2 font-medium text-sm transition-colors border-b-2',
            activeTab === tab.id
              ? (isDark ? 'border-blue-500 text-blue-400' : 'border-blue-500 text-blue-600')
              : (isDark ? 'border-transparent text-gray-400 hover:text-gray-300' : 'border-transparent text-gray-600 hover:text-gray-800')
          ]"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Tab 1: Overview -->
    <div v-show="activeTab === 'overview'">
      <!-- Loading -->
      <div v-if="loadingOverview" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading tenant info...</p>
      </div>
      
      <!-- Error -->
      <div v-else-if="errorOverview" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
        <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ errorOverview }}</p>
        <button @click="loadOverview" class="mt-4 btn btn-primary">Retry</button>
      </div>
      
      <!-- Content -->
      <div v-else class="space-y-6">
        <!-- Organization -->
        <div v-if="organization" class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">🏢 Organization</h2>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</p>
              <p class="text-base font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ organization.displayName }}</p>
            </div>
            <div>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Tenant Type</p>
              <p class="text-base font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ organization.tenantType }}</p>
            </div>
            <div>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Tenant ID</p>
              <p class="text-base font-mono text-xs" :class="isDark ? 'text-white' : 'text-gray-900'">{{ organization.id }}</p>
            </div>
            <div>
              <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Created</p>
              <p class="text-base font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ formatDate(organization.createdDateTime) }}</p>
            </div>
          </div>
        </div>
        
        <!-- Domains -->
        <div v-if="domains.length > 0" class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-bold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">🌐 Domains</h2>
          <div class="space-y-3">
            <div v-for="domain in domains" :key="domain.id" 
                 class="flex items-center justify-between p-3 rounded-lg"
                 :class="isDark ? 'bg-gray-700' : 'bg-gray-50'">
              <div>
                <p class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-900'">{{ domain.id }}</p>
                <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ domain.authenticationType }}</p>
              </div>
              <div class="flex space-x-2">
                <span v-if="domain.isDefault" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                  Default
                </span>
                <span v-if="domain.isVerified" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'">
                  Verified
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Authentication Methods -->
    <div v-show="activeTab === 'auth-methods'">
      <!-- Loading -->
      <div v-if="loadingAuth" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading authentication methods...</p>
      </div>
      
      <!-- Error / Missing Permissions -->
      <div v-else-if="errorAuth || missingAuthPermissions" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-yellow-900/50 border border-yellow-700' : 'bg-yellow-50 border border-yellow-200'">
        <p class="text-2xl mb-3">🔒</p>
        <p class="font-semibold mb-2" :class="isDark ? 'text-yellow-300' : 'text-yellow-800'">Missing Required Permissions</p>
        <p class="text-sm" :class="isDark ? 'text-yellow-400' : 'text-yellow-700'">
          Required scope: <code class="bg-gray-800 text-yellow-300 px-2 py-1 rounded">Policy.Read.All</code> or 
          <code class="bg-gray-800 text-yellow-300 px-2 py-1 rounded">Policy.ReadWrite.AuthenticationMethod</code>
        </p>
        <p class="text-xs mt-3" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Current token does not have sufficient privileges to view authentication policies.
        </p>
        <div v-if="authErrorDetails" class="mt-4 p-3 rounded text-left" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <p class="text-xs font-mono" :class="isDark ? 'text-red-400' : 'text-red-600'">
            <strong>Error Code:</strong> {{ authErrorDetails.error_code || 'N/A' }}
          </p>
          <p class="text-xs font-mono mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-700'">
            <strong>Details:</strong> {{ authErrorDetails.details || 'N/A' }}
          </p>
        </div>
      </div>
      
      <!-- Content -->
      <div v-else class="space-y-6">
        <!-- Policy Overview -->
        <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
            📋 Policy Overview
          </h2>
          <div class="space-y-2" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
            <p><strong>Policy Name:</strong> {{ authPolicy.displayName }}</p>
            <p v-if="authPolicy.description"><strong>Description:</strong> {{ authPolicy.description }}</p>
          </div>
        </div>

        <!-- Authentication Methods -->
        <div class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <h2 class="text-xl font-semibold flex items-center" :class="isDark ? 'text-white' : 'text-gray-800'">
              🔑 Enabled Authentication Methods
              <span class="ml-3 px-3 py-1 text-sm rounded-full" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                {{ enabledMethodsCount }} enabled
              </span>
            </h2>
          </div>
          
          <div class="p-6">
            <div v-if="authMethods.length === 0" class="text-center py-8" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              No authentication methods configured
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div 
                v-for="method in authMethods" 
                :key="method.id"
                class="rounded-lg p-4 border-l-4"
                :class="[
                  isDark ? 'bg-gray-750' : 'bg-gray-50',
                  method.state === 'enabled' ? 'border-green-500' : 'border-gray-400'
                ]"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center space-x-2">
                    <span class="text-2xl">{{ getMethodIcon(method.type) }}</span>
                    <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                      {{ formatMethodType(method.type) }}
                    </h3>
                  </div>
                  <span 
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="method.state === 'enabled' 
                      ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')
                      : (isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600')"
                  >
                    {{ method.state }}
                  </span>
                </div>
                
                <div class="mt-3 space-y-1 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                  <div v-if="method.includeTargets && method.includeTargets.length > 0">
                    <strong>Include:</strong> {{ method.includeTargets.length }} target(s)
                  </div>
                  <div v-if="method.excludeTargets && method.excludeTargets.length > 0">
                    <strong>Exclude:</strong> {{ method.excludeTargets.length }} target(s)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Auth Strength Policies -->
        <div class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <h2 class="text-xl font-semibold flex items-center" :class="isDark ? 'text-white' : 'text-gray-800'">
              🛡️ Authentication Strength Policies
              <span class="ml-3 px-3 py-1 text-sm rounded-full" :class="isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'">
                {{ strengthPolicies.length }} policies
              </span>
            </h2>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
              <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Policy Name</th>
                  <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Type</th>
                  <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Combinations</th>
                  <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Description</th>
                  <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
                <tr v-for="policy in strengthPolicies" :key="policy.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
                  <td class="px-6 py-4 whitespace-nowrap font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
                    {{ policy.displayName }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span 
                      class="px-2 py-1 text-xs font-semibold rounded-full"
                      :class="policy.policyType === 'builtIn' 
                        ? (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')
                        : (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800')"
                    >
                      {{ policy.policyType }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-3 py-1 rounded-full text-sm font-semibold" :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'">
                      {{ policy.combinationCount }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                    {{ policy.description || 'N/A' }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <button
                      @click="viewCombinations(policy)"
                      class="px-3 py-1 text-sm font-medium rounded-lg transition-colors"
                      :class="isDark ? 'bg-blue-900 text-blue-300 hover:bg-blue-800' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'"
                    >
                      👁️ View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 3: Authorization Policy -->
    <div v-show="activeTab === 'authorization'">
      <!-- Loading -->
      <div v-if="loadingAuthz" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading authorization policy...</p>
      </div>
      
      <!-- Error / Missing Permissions -->
      <div v-else-if="errorAuthz || missingAuthzPermissions" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-yellow-900/50 border border-yellow-700' : 'bg-yellow-50 border border-yellow-200'">
        <p class="text-2xl mb-3">🔒</p>
        <p class="font-semibold mb-2" :class="isDark ? 'text-yellow-300' : 'text-yellow-800'">Missing Required Permissions</p>
        <p class="text-sm" :class="isDark ? 'text-yellow-400' : 'text-yellow-700'">
          Required scope: <code class="bg-gray-800 text-yellow-300 px-2 py-1 rounded">Policy.Read.All</code>
        </p>
        <p class="text-xs mt-3" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Current token does not have sufficient privileges to view authorization policy.
        </p>
        <div v-if="authzErrorDetails" class="mt-4 p-3 rounded text-left" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <p class="text-xs font-mono" :class="isDark ? 'text-red-400' : 'text-red-600'">
            <strong>Error Code:</strong> {{ authzErrorDetails.error_code || 'N/A' }}
          </p>
          <p class="text-xs font-mono mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-700'">
            <strong>Details:</strong> {{ authzErrorDetails.details || 'N/A' }}
          </p>
        </div>
      </div>
      
      <!-- Content -->
      <div v-else class="space-y-6">
        <!-- Default User Permissions -->
        <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
            👤 Default User Permissions
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Create Applications</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToCreateApps ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')">
                {{ authzPolicy.allowedToCreateApps ? '⚠️ Enabled' : '✓ Disabled' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Create Security Groups</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToCreateSecurityGroups ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')">
                {{ authzPolicy.allowedToCreateSecurityGroups ? '⚠️ Enabled' : '✓ Disabled' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Create Tenants</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToCreateTenants ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')">
                {{ authzPolicy.allowedToCreateTenants ? '⚠️ Enabled' : '✓ Disabled' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Read Other Users</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToReadOtherUsers ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')">
                {{ authzPolicy.allowedToReadOtherUsers ? '✓ Enabled' : '⚠️ Disabled' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Read BitLocker Keys</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToReadBitlockerKeysForOwnedDevice ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')">
                {{ authzPolicy.allowedToReadBitlockerKeysForOwnedDevice ? '⚠️ Enabled' : '✓ Disabled' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Guest & External Collaboration -->
        <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
            🌍 Guest & External Collaboration
          </h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Allow Invites From</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                {{ authzPolicy.allowInvitesFrom }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Email Verified Users Can Join</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowEmailVerifiedUsersToJoinOrganization ? (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800') : (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800')">
                {{ authzPolicy.allowEmailVerifiedUsersToJoinOrganization ? '⚠️ Enabled' : '✓ Disabled' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Email Subscriptions</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.allowedToSignUpEmailBasedSubscriptions ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')">
                {{ authzPolicy.allowedToSignUpEmailBasedSubscriptions ? '✓ Enabled' : '⚠️ Disabled' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Security Settings -->
        <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <h2 class="text-xl font-semibold mb-4" :class="isDark ? 'text-white' : 'text-gray-800'">
            🔒 Security Settings
          </h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span :class="isDark ? 'text-gray-300' : 'text-gray-700'">Block MSOL PowerShell</span>
              <span class="px-3 py-1 text-sm font-semibold rounded-full" :class="authzPolicy.blockMsolPowerShell ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')">
                {{ authzPolicy.blockMsolPowerShell ? '✓ Enabled' : '⚠️ Disabled' }}
              </span>
            </div>
            <div v-if="authzPolicy.guestUserRoleId" class="p-3 rounded-lg" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
              <span class="block mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Guest User Role ID</span>
              <code class="text-xs px-2 py-1 rounded" :class="isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'">
                {{ authzPolicy.guestUserRoleId }}
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Combinations Modal (for Auth Strength Policies) -->
    <div 
      v-if="showCombinationsModal" 
      @click="showCombinationsModal = false"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <div 
        @click.stop
        class="rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden"
        :class="isDark ? 'bg-gray-800' : 'bg-white'"
      >
        <div class="p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                {{ selectedPolicy?.displayName }}
              </h3>
              <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                Allowed authentication combinations
              </p>
            </div>
            <button 
              @click="showCombinationsModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <div class="space-y-2">
            <div 
              v-for="(combination, index) in selectedPolicy?.allowedCombinations" 
              :key="index"
              class="px-4 py-3 rounded-lg"
              :class="isDark ? 'bg-gray-750' : 'bg-gray-50'"
            >
              <div class="flex items-center space-x-2">
                <span class="text-green-500">✓</span>
                <code class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                  {{ combination }}
                </code>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <button 
            @click="showCombinationsModal = false"
            class="w-full btn"
            :class="isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

// Tab system
const tabs = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'auth-methods', label: 'Auth Methods', icon: '🔐' },
  { id: 'authorization', label: 'Authorization Policy', icon: '🔑' }
]
const activeTab = ref('overview')

// Tab 1: Overview
const organization = ref(null)
const domains = ref([])
const loadingOverview = ref(false)
const errorOverview = ref(null)

// Tab 2: Auth Methods
const authPolicy = ref({})
const authMethods = ref([])
const strengthPolicies = ref([])
const loadingAuth = ref(false)
const errorAuth = ref(null)
const missingAuthPermissions = ref(false)
const authErrorDetails = ref(null)
const showCombinationsModal = ref(false)
const selectedPolicy = ref(null)

// Tab 3: Authorization Policy
const authzPolicy = ref({})
const loadingAuthz = ref(false)
const errorAuthz = ref(null)
const missingAuthzPermissions = ref(false)
const authzErrorDetails = ref(null)

const enabledMethodsCount = computed(() => {
  return authMethods.value.filter(m => m.state === 'enabled').length
})

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString()
}

const formatMethodType = (type) => {
  const cleaned = type
    .replace('AuthenticationMethodConfiguration', '')
    .replace('AuthenticationMethodsPolicy', '')
  return cleaned.replace(/([A-Z])/g, ' $1').trim()
}

const getMethodIcon = (type) => {
  const iconMap = {
    'fido2': '🔐',
    'microsoftAuthenticator': '📱',
    'softwareOath': '🔢',
    'sms': '📞',
    'voice': '📞',
    'temporaryAccessPass': '🎫',
    'password': '🔑',
    'email': '📧',
    'x509Certificate': '📜'
  }
  const typeKey = type.toLowerCase().replace('authenticationmethodconfiguration', '')
  return iconMap[typeKey] || '🔒'
}

const viewCombinations = (policy) => {
  selectedPolicy.value = policy
  showCombinationsModal.value = true
}

// Load functions
const loadOverview = async () => {
  loadingOverview.value = true
  errorOverview.value = null
  
  try {
    const [orgRes, domainsRes] = await Promise.all([
      fetch('http://localhost:5000/api/tenant/organization'),
      fetch('http://localhost:5000/api/tenant/domains')
    ])
    
    const orgData = await orgRes.json()
    const domainsData = await domainsRes.json()
    
    if (orgData.success) {
      organization.value = orgData.organization
    }
    
    if (domainsData.success) {
      domains.value = domainsData.domains
    }
  } catch (err) {
    errorOverview.value = 'Failed to load tenant information'
  } finally {
    loadingOverview.value = false
  }
}

const loadAuthMethods = async () => {
  loadingAuth.value = true
  errorAuth.value = null
  missingAuthPermissions.value = false
  authErrorDetails.value = null
  
  try {
    const policyResponse = await fetch('http://localhost:5000/api/tenant/auth-methods-policy')
    const policyData = await policyResponse.json()
    
    // Check for 403/unauthorized
    if (!policyResponse.ok && policyResponse.status === 403) {
      missingAuthPermissions.value = true
      authErrorDetails.value = {
        error_code: policyData.error_code,
        details: policyData.details
      }
      return
    }
    
    if (policyData.success) {
      authPolicy.value = policyData.policy
      authMethods.value = policyData.policy.authenticationMethodConfigurations || []
    } else {
      // Check if error is permission-related
      if (policyData.error && (policyData.error.includes('Authorization') || policyData.error.includes('Forbidden') || policyData.error.includes('403'))) {
        missingAuthPermissions.value = true
        authErrorDetails.value = {
          error_code: policyData.error_code,
          details: policyData.details
        }
        return
      }
      errorAuth.value = policyData.error || 'Failed to load authentication methods policy'
      return
    }
    
    const strengthResponse = await fetch('http://localhost:5000/api/tenant/auth-strength-policies')
    const strengthData = await strengthResponse.json()
    
    if (strengthData.success) {
      strengthPolicies.value = strengthData.policies || []
    }
    
  } catch (err) {
    errorAuth.value = 'Failed to load authentication methods: ' + err.message
  } finally {
    loadingAuth.value = false
  }
}

const loadAuthzPolicy = async () => {
  loadingAuthz.value = true
  errorAuthz.value = null
  missingAuthzPermissions.value = false
  authzErrorDetails.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/authorization-policy')
    const data = await response.json()
    
    // Check for 403/unauthorized
    if (!response.ok && response.status === 403) {
      missingAuthzPermissions.value = true
      authzErrorDetails.value = {
        error_code: data.error_code,
        details: data.details
      }
      return
    }
    
    if (data.success) {
      authzPolicy.value = data.policy
    } else {
      // Check if error is permission-related
      if (data.error && (data.error.includes('Authorization') || data.error.includes('Forbidden') || data.error.includes('403'))) {
        missingAuthzPermissions.value = true
        authzErrorDetails.value = {
          error_code: data.error_code,
          details: data.details
        }
        return
      }
      errorAuthz.value = data.error || 'Failed to load authorization policy'
    }
  } catch (err) {
    errorAuthz.value = 'Failed to load authorization policy: ' + err.message
  } finally {
    loadingAuthz.value = false
  }
}

onMounted(() => {
  loadOverview()
})

// LAZY LOADING con watch() - FIXED!
watch(activeTab, (newTab) => {
  if (newTab === 'auth-methods' && authMethods.value.length === 0 && !missingAuthPermissions.value && !errorAuth.value) {
    loadAuthMethods()
  } else if (newTab === 'authorization' && !authzPolicy.value.id && !missingAuthzPermissions.value && !errorAuthz.value) {
    loadAuthzPolicy()
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

.bg-gray-750 {
  background-color: #2d3748;
}
</style>
