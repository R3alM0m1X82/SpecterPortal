<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Azure Permissions</h1>
    </div>

    <!-- Token Warning -->
    <div v-if="!hasARMToken" class="mb-6 p-4 rounded-lg border border-red-500" :class="isDark ? 'bg-red-900/20' : 'bg-red-50'">
      <div class="flex items-center">
        <span class="text-2xl mr-3">⚠️</span>
        <div>
          <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-800'">No ARM token available</p>
          <p class="text-sm mt-1" :class="isDark ? 'text-red-400' : 'text-red-700'">
            Please authenticate with Azure PowerShell to view permissions.
          </p>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="mb-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <div class="flex space-x-1">
        <button
          @click="activeTab = 'my-permissions'"
          :class="[
            'px-6 py-3 font-semibold transition-colors border-b-2',
            activeTab === 'my-permissions'
              ? isDark
                ? 'border-blue-500 text-blue-400 bg-gray-800'
                : 'border-blue-500 text-blue-600 bg-white'
              : isDark
                ? 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-800'
                : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          ]"
        >
          My Permissions
        </button>
        <button
          @click="activeTab = 'all-assignments'"
          :class="[
            'px-6 py-3 font-semibold transition-colors border-b-2',
            activeTab === 'all-assignments'
              ? isDark
                ? 'border-blue-500 text-blue-400 bg-gray-800'
                : 'border-blue-500 text-blue-600 bg-white'
              : isDark
                ? 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-800'
                : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          ]"
        >
          All Role Assignments
        </button>
        <button
          @click="activeTab = 'effective'"
          :class="[
            'px-6 py-3 font-semibold transition-colors border-b-2',
            activeTab === 'effective'
              ? isDark
                ? 'border-blue-500 text-blue-400 bg-gray-800'
                : 'border-blue-500 text-blue-600 bg-white'
              : isDark
                ? 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-800'
                : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          ]"
        >
          Effective Permissions
        </button>
      </div>
    </div>

    <!-- Tab 1: My Permissions (EXISTING) -->
    <div v-if="activeTab === 'my-permissions'">
      <!-- Info Banner -->
      <div class="mb-6 p-4 rounded-lg border" :class="isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200'">
        <p class="text-sm" :class="isDark ? 'text-blue-300' : 'text-blue-700'">
          💡 Showing Azure RBAC role assignments across all accessible subscriptions. Click on a subscription to filter results.
        </p>
      </div>

      <div class="flex space-x-4 mb-6">
        <button @click="loadMyPermissions(true)" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'" :disabled="loading">
          {{ loading ? '🔄 Loading...' : '🔄 Refresh' }}
        </button>
      </div>

      <!-- Global Admin Elevation Card -->
      <div v-if="elevationStatus && elevationStatus.isGlobalAdmin" class="mb-6 rounded-lg shadow-md p-6 border-2" 
           :class="elevationStatus.isElevated 
             ? (isDark ? 'bg-green-900/20 border-green-700' : 'bg-green-50 border-green-300')
             : (isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-300')">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center mb-2">
              <span class="text-2xl mr-3">{{ elevationStatus.isElevated ? '🔓' : '🔒' }}</span>
              <h3 class="text-lg font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
                Global Admin Elevation
              </h3>
            </div>
            <p class="text-sm mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              <strong>User:</strong> {{ elevationStatus.userInfo?.upn || 'Unknown' }}
            </p>
            <p class="text-sm mb-4" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
              {{ elevationStatus.isElevated 
                ? '✅ You have elevated access as User Access Administrator at root scope (/). You can manage IAM across all subscriptions and resources.'
                : '⚠️ You are a Global Administrator but not elevated. Click below to elevate your access to User Access Administrator at root scope (/).' 
              }}
            </p>
            
            <!-- Success/Error messages -->
            <div v-if="elevationSuccess" class="mb-3 p-3 rounded-lg" :class="isDark ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800'">
              ✓ {{ elevationSuccess }}
            </div>
            <div v-if="elevationError" class="mb-3 p-3 rounded-lg" :class="isDark ? 'bg-red-900/30 text-red-300' : 'bg-red-100 text-red-800'">
              ⚠️ {{ elevationError }}
            </div>
            
            <!-- Action buttons -->
            <div class="flex space-x-3">
              <button 
                v-if="!elevationStatus.isElevated"
                @click="elevateAccess" 
                :disabled="elevationLoading"
                class="px-6 py-2 rounded-lg font-semibold transition-colors"
                :class="elevationLoading 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : (isDark ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-600 text-white hover:bg-blue-700')">
                {{ elevationLoading ? '⏳ Processing...' : '🔓 Elevate Access' }}
              </button>
              <button 
                v-if="elevationStatus.isElevated"
                @click="removeElevation" 
                :disabled="elevationLoading"
                class="px-6 py-2 rounded-lg font-semibold transition-colors"
                :class="elevationLoading 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : (isDark ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-red-600 text-white hover:bg-red-700')">
                {{ elevationLoading ? '⏳ Processing...' : '🔒 Remove Elevation' }}
              </button>
              <button 
                @click="checkElevationStatus" 
                :disabled="elevationLoading"
                class="px-6 py-2 rounded-lg font-semibold transition-colors"
                :class="elevationLoading 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : (isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-800 hover:bg-gray-300')">
                🔄 Check Status
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Subscription Filters -->
      <div v-if="!loading && subscriptions.length > 0" class="mb-6 rounded-lg shadow-md p-4" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <h3 class="text-sm font-semibold mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Filter by Subscription:</h3>
        <div class="flex flex-wrap gap-2">
          <button
            @click="selectedSubscription = null"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              selectedSubscription === null
                ? 'bg-blue-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            All Subscriptions ({{ roleAssignments.length }})
          </button>
          <button
            v-for="sub in subscriptions"
            :key="sub.id"
            @click="selectedSubscription = sub.id"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              selectedSubscription === sub.id
                ? 'bg-blue-600 text-white'
                : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            {{ sub.name }} ({{ sub.count }})
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading role assignments...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="rounded-lg shadow-md p-6 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">⚠️</div>
        <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">Error Loading Permissions</h2>
        <p class="mb-6" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ error }}</p>
        <button @click="loadMyPermissions" class="btn btn-primary">
          Try Again
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="roleAssignments.length === 0" class="rounded-lg shadow-md p-6 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">🔐</div>
        <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">No Role Assignments Found</h2>
        <p class="mb-6" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          You don't have any Azure RBAC role assignments, or your token doesn't have permission to view them.
        </p>
        <p class="text-sm" :class="isDark ? 'text-gray-500' : 'text-gray-600'">
          Required permission: <code class="px-2 py-1 rounded" :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">Microsoft.Authorization/roleAssignments/read</code>
        </p>
      </div>

      <!-- Role Assignments Grid -->
      <div v-else>
        <div class="mb-4 text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          {{ filteredRoleAssignments.length }} role assignment(s)
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="assignment in filteredRoleAssignments"
            :key="assignment.id"
            class="rounded-lg shadow-md p-6 transition-all hover:shadow-lg"
            :class="isDark ? 'bg-gray-800 hover:bg-gray-750' : 'bg-white hover:bg-gray-50'"
          >
            <!-- Role Name Badge -->
            <div class="mb-4">
              <span
                class="px-3 py-1 rounded-full text-sm font-semibold"
                :class="getRoleBadgeClass(assignment.roleName)"
              >
                {{ assignment.roleName || 'Unknown Role' }}
              </span>
            </div>

            <!-- Subscription Info -->
            <div class="mb-3">
              <div class="text-xs font-semibold mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                SUBSCRIPTION
              </div>
              <div class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                {{ assignment.subscriptionName || 'Unknown' }}
              </div>
              <div class="text-xs font-mono mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-600'">
                {{ assignment.subscriptionId }}
              </div>
            </div>

            <!-- Scope Info -->
            <div class="mb-3">
              <div class="text-xs font-semibold mb-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                SCOPE
              </div>
              <div 
                class="text-sm break-words" 
                :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                :title="assignment.scope"
              >
                {{ getScopeName(assignment.scope) }}
              </div>
              <div 
                class="text-xs font-mono mt-1 break-all" 
                :class="isDark ? 'text-gray-500' : 'text-gray-600'"
              >
                {{ assignment.scope }}
              </div>
            </div>

            <!-- Assignment ID -->
            <div class="pt-3 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
              <div class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-600'">
                <span class="font-semibold">Assignment ID:</span>
                <div class="font-mono break-all mt-1">
                  {{ getAssignmentIdShort(assignment.id) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: All Role Assignments -->
    <div v-if="activeTab === 'all-assignments'">
      <!-- Info Box -->
      <div class="mb-6 p-4 rounded-lg border" :class="isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200'">
        <p class="text-sm" :class="isDark ? 'text-blue-300' : 'text-blue-700'">
          💡 Shows ALL role assignments (subscription + resource level). PowerShell equivalent: <code class="px-2 py-1 rounded font-mono" :class="isDark ? 'bg-blue-800' : 'bg-blue-100'">Get-AzRoleAssignment</code>
        </p>
      </div>

      <button 
        @click="loadAllRoleAssignments(true)" 
        :disabled="!hasARMToken || loadingAll"
        class="btn btn-primary mb-6"
      >
        <span v-if="!loadingAll">🔄 Load All Role Assignments</span>
        <span v-else>⏳ Loading...</span>
      </button>

      <!-- Loading State -->
      <div v-if="loadingAll" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading all role assignments...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="errorAll" class="rounded-lg shadow-md p-6 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">⚠️</div>
        <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">Error Loading Assignments</h2>
        <p class="mb-6" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ errorAll }}</p>
        <button @click="loadAllRoleAssignments(true)" class="btn btn-primary">
          Try Again
        </button>
      </div>

      <!-- Stats Cards -->
      <div v-else-if="allRoleAssignments.length > 0">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-blue-400' : 'text-blue-600'">{{ allRoleAssignments.length }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Total Assignments</div>
          </div>
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-green-400' : 'text-green-600'">{{ uniqueRolesCount }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Unique Roles</div>
          </div>
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-cyan-400' : 'text-cyan-600'">{{ userAssignmentsCount }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">User Assignments</div>
          </div>
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-orange-400' : 'text-orange-600'">{{ spAssignmentsCount }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">SP Assignments</div>
          </div>
        </div>

        <!-- Filters -->
        <div class="mb-6 rounded-lg shadow-md p-4" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              v-model="searchAll"
              type="text"
              placeholder="Search roles, scopes, principal ID..."
              class="px-4 py-2 rounded-lg border"
              :class="isDark 
                ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'"
            />
            <select
              v-model="filterPrincipalType"
              class="px-4 py-2 rounded-lg border"
              :class="isDark 
                ? 'bg-gray-700 border-gray-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'"
            >
              <option value="">All Principal Types</option>
              <option value="User">User</option>
              <option value="ServicePrincipal">Service Principal</option>
              <option value="Group">Group</option>
            </select>
          </div>
        </div>

        <!-- Table -->
        <div class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="border-b" :class="isDark ? 'bg-gray-750 border-gray-700' : 'bg-gray-50 border-gray-200'">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Role
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Scope
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Principal Type
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Principal ID
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                    Subscription
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
                <tr 
                  v-for="assignment in filteredAllRoleAssignments" 
                  :key="assignment.id"
                  class="transition-colors"
                  :class="isDark ? 'hover:bg-gray-750' : 'hover:bg-gray-50'"
                >
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="px-3 py-1 rounded-full text-xs font-semibold"
                      :class="getRoleBadgeClass(assignment.roleDefinitionName)"
                    >
                      {{ assignment.roleDefinitionName || 'Unknown' }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-900'">
                      {{ getScopeDisplay(assignment.scope) }}
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="px-3 py-1 rounded-full text-xs font-semibold"
                      :class="getPrincipalTypeBadgeClass(assignment.principalType)"
                    >
                      {{ assignment.principalType || 'Unknown' }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="text-xs" :class="isDark ? 'text-gray-300' : 'text-gray-700'" :title="assignment.principalId">
                      {{ getPrincipalDisplay(assignment.principalId) }}
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-900'">
                      {{ assignment.subscriptionName || 'N/A' }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="mt-4 text-sm text-center" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Showing {{ filteredAllRoleAssignments.length }} of {{ allRoleAssignments.length }} assignments
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="rounded-lg shadow-md p-12 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">📋</div>
        <p class="text-lg" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Click "Load All Role Assignments" to view all RBAC assignments
        </p>
      </div>
    </div>

    <!-- Tab 3: Effective Permissions -->
    <div v-if="activeTab === 'effective'">
      <!-- Info Box -->
      <div class="mb-6 p-4 rounded-lg border" :class="isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200'">
        <p class="text-sm" :class="isDark ? 'text-blue-300' : 'text-blue-700'">
          💡 Analyzes effective permissions for ALL Azure resources. Shows Actions, NotActions, DataActions, and NotDataActions for each resource.
        </p>
      </div>

      <button 
        @click="analyzeEffectivePermissions(true)" 
        :disabled="!hasARMToken || loadingEffective"
        class="btn btn-primary mb-6"
      >
        <span v-if="!loadingEffective">🔄 Analyze All Permissions</span>
        <span v-else>⏳ Analyzing...</span>
      </button>

      <!-- Loading State -->
      <div v-if="loadingEffective" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Analyzing permissions across all resources...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="errorEffective" class="rounded-lg shadow-md p-6 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">⚠️</div>
        <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">Error Analyzing Permissions</h2>
        <p class="mb-6" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ errorEffective }}</p>
        <button @click="analyzeEffectivePermissions(true)" class="btn btn-primary">
          Try Again
        </button>
      </div>

      <!-- Stats Cards -->
      <div v-else-if="effectivePermissions.length > 0">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-blue-400' : 'text-blue-600'">{{ effectivePermissions.length }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Total Resources</div>
          </div>
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-green-400' : 'text-green-600'">{{ uniqueResourceTypesCount }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Resource Types</div>
          </div>
          <div class="rounded-lg shadow-md p-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
            <div class="text-2xl font-bold" :class="isDark ? 'text-purple-400' : 'text-purple-600'">{{ uniqueSubscriptionsCount }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Subscriptions</div>
          </div>
        </div>

        <!-- Filters -->
        <div class="mb-6 rounded-lg shadow-md p-4" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              v-model="searchEffective"
              type="text"
              placeholder="Search resource name, type, or resource group..."
              class="px-4 py-2 rounded-lg border"
              :class="isDark 
                ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'"
            />
            <select
              v-model="filterResourceType"
              class="px-4 py-2 rounded-lg border"
              :class="isDark 
                ? 'bg-gray-700 border-gray-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'"
            >
              <option value="">All Resource Types</option>
              <option v-for="type in uniqueResourceTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
        </div>

        <!-- Permissions Cards -->
        <div class="space-y-6">
          <div 
            v-for="resource in filteredEffectivePermissions" 
            :key="resource.resourceId"
            class="rounded-lg shadow-md p-6"
            :class="isDark ? 'bg-gray-800' : 'bg-white'"
          >
            <!-- Resource Header -->
            <div class="mb-4 pb-4 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
              <h3 class="text-lg font-semibold mb-2" :class="isDark ? 'text-white' : 'text-gray-800'">
                {{ resource.resourceName }}
              </h3>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 rounded-full text-xs font-mono" :class="isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'">
                  {{ resource.resourceType }}
                </span>
                <span class="px-3 py-1 rounded-full text-xs" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'">
                  📊 {{ resource.subscriptionName }}
                </span>
                <span class="px-3 py-1 rounded-full text-xs" :class="isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-700'">
                  📁 {{ resource.resourceGroup }}
                </span>
              </div>
            </div>

            <!-- Permissions Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <!-- Actions -->
              <div>
                <h4 class="text-sm font-semibold mb-2 flex items-center" :class="isDark ? 'text-green-400' : 'text-green-600'">
                  ✅ Actions ({{ resource.permissions.actions.length }})
                </h4>
                <div class="max-h-48 overflow-y-auto rounded-lg p-3" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
                  <div v-if="resource.permissions.actions.length > 0" class="space-y-1">
                    <div 
                      v-for="(action, idx) in resource.permissions.actions" 
                      :key="idx"
                      class="text-xs font-mono"
                      :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                    >
                      {{ action }}
                    </div>
                  </div>
                  <div v-else class="text-xs italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    None
                  </div>
                </div>
              </div>

              <!-- NotActions -->
              <div>
                <h4 class="text-sm font-semibold mb-2 flex items-center" :class="isDark ? 'text-red-400' : 'text-red-600'">
                  ❌ NotActions ({{ resource.permissions.notActions.length }})
                </h4>
                <div class="max-h-48 overflow-y-auto rounded-lg p-3" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
                  <div v-if="resource.permissions.notActions.length > 0" class="space-y-1">
                    <div 
                      v-for="(action, idx) in resource.permissions.notActions" 
                      :key="idx"
                      class="text-xs font-mono"
                      :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                    >
                      {{ action }}
                    </div>
                  </div>
                  <div v-else class="text-xs italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    None
                  </div>
                </div>
              </div>

              <!-- DataActions -->
              <div>
                <h4 class="text-sm font-semibold mb-2 flex items-center" :class="isDark ? 'text-blue-400' : 'text-blue-600'">
                  📊 DataActions ({{ resource.permissions.dataActions.length }})
                </h4>
                <div class="max-h-48 overflow-y-auto rounded-lg p-3" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
                  <div v-if="resource.permissions.dataActions.length > 0" class="space-y-1">
                    <div 
                      v-for="(action, idx) in resource.permissions.dataActions" 
                      :key="idx"
                      class="text-xs font-mono"
                      :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                    >
                      {{ action }}
                    </div>
                  </div>
                  <div v-else class="text-xs italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    None
                  </div>
                </div>
              </div>

              <!-- NotDataActions -->
              <div>
                <h4 class="text-sm font-semibold mb-2 flex items-center" :class="isDark ? 'text-orange-400' : 'text-orange-600'">
                  🚫 NotDataActions ({{ resource.permissions.notDataActions.length }})
                </h4>
                <div class="max-h-48 overflow-y-auto rounded-lg p-3" :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
                  <div v-if="resource.permissions.notDataActions.length > 0" class="space-y-1">
                    <div 
                      v-for="(action, idx) in resource.permissions.notDataActions" 
                      :key="idx"
                      class="text-xs font-mono"
                      :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                    >
                      {{ action }}
                    </div>
                  </div>
                  <div v-else class="text-xs italic" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    None
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 text-sm text-center" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Showing {{ filteredEffectivePermissions.length }} of {{ effectivePermissions.length }} resources
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="rounded-lg shadow-md p-12 text-center" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">🔍</div>
        <p class="text-lg" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          Click "Analyze All Permissions" to view effective permissions for all resources
        </p>
      </div>
    </div>

    <!-- UPN Resolution Warning Toast (Non-blocking) -->
    <div v-if="showUPNWarning" 
         class="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg border max-w-md z-50 animate-slide-in"
         :class="isDark ? 'bg-yellow-900/90 border-yellow-700' : 'bg-yellow-50 border-yellow-300'">
      <div class="flex items-start">
        <span class="text-2xl mr-3">⚠️</span>
        <div class="flex-1">
          <p class="font-semibold" :class="isDark ? 'text-yellow-300' : 'text-yellow-800'">
            UPN Resolution Unavailable
          </p>
          <p class="text-sm mt-1" :class="isDark ? 'text-yellow-400' : 'text-yellow-700'">
            No Microsoft Graph token found. Principal IDs will be displayed as GUIDs. 
            Authenticate with Microsoft Graph PowerShell to enable UPN resolution.
          </p>
        </div>
        <button 
          @click="showUPNWarning = false" 
          class="ml-3 text-xl font-bold hover:opacity-70"
          :class="isDark ? 'text-yellow-400' : 'text-yellow-600'"
        >
          &times;
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

// Tab state
const activeTab = ref('my-permissions')

// Token check
const hasARMToken = ref(true)

// Tab 1: My Permissions (existing)
const loading = ref(false)
const error = ref(null)
const roleAssignments = ref([])
const selectedSubscription = ref(null)

// Tab 2: All Role Assignments
const loadingAll = ref(false)
const errorAll = ref(null)
const allRoleAssignments = ref([])
const searchAll = ref('')
const filterPrincipalType = ref('')
const principalNamesCache = ref({}) // Cache for resolved UPN/displayName
const showUPNWarning = ref(false) // Show warning when UPN resolution unavailable

// Cache system (5 minutes TTL)
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes in milliseconds
const dataCache = ref({
  myPermissions: { data: null, timestamp: null },
  allAssignments: { data: null, timestamp: null, principals: null },
  effectivePermissions: { data: null, timestamp: null }
})

// Tab 3: Effective Permissions
const loadingEffective = ref(false)
const errorEffective = ref(null)
const effectivePermissions = ref([])
const searchEffective = ref('')
const filterResourceType = ref('')

// Global Admin Elevation
const elevationLoading = ref(false)
const elevationStatus = ref(null) // { isGlobalAdmin, isElevated, userInfo }
const elevationError = ref(null)
const elevationSuccess = ref(null)

// Check ARM token
const checkARMToken = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/azure/permissions/check-tokens')
    if (response.data.success) {
      hasARMToken.value = response.data.has_arm_token
    }
  } catch (err) {
    console.error('Failed to check ARM token:', err)
  }
}

// Tab 1: My Permissions functions
const subscriptions = computed(() => {
  const subsMap = new Map()
  
  roleAssignments.value.forEach(assignment => {
    const subId = assignment.subscriptionId
    const subName = assignment.subscriptionName || 'Unknown'
    
    if (subsMap.has(subId)) {
      subsMap.get(subId).count++
    } else {
      subsMap.set(subId, { id: subId, name: subName, count: 1 })
    }
  })
  
  return Array.from(subsMap.values())
})

const filteredRoleAssignments = computed(() => {
  if (!selectedSubscription.value) {
    return roleAssignments.value
  }
  
  return roleAssignments.value.filter(
    assignment => assignment.subscriptionId === selectedSubscription.value
  )
})

// Cache helper function
const isCacheValid = (cacheEntry) => {
  if (!cacheEntry || !cacheEntry.timestamp) {
    return false
  }
  const age = Date.now() - cacheEntry.timestamp
  return age < CACHE_TTL
}

const loadMyPermissions = async (forceRefresh = false) => {
  // Check cache first (5 min TTL) - skip if force refresh
  if (!forceRefresh && isCacheValid(dataCache.value.myPermissions)) {
    console.log('[CACHE] Using cached My Permissions')
    roleAssignments.value = dataCache.value.myPermissions.data
    return
  }
  
  if (forceRefresh) {
    console.log('[CACHE] Force refresh - invalidating cache')
  }
  
  loading.value = true
  error.value = null
  
  try {
    const response = await axios.get('http://localhost:5000/api/azure/permissions/my-roles')
    
    if (response.data.success) {
      roleAssignments.value = response.data.roleAssignments || []
      
      // Update cache
      dataCache.value.myPermissions = {
        data: roleAssignments.value,
        timestamp: Date.now()
      }
      console.log('[CACHE] My Permissions cached')
    } else {
      error.value = response.data.error || 'Failed to load permissions'
    }
  } catch (err) {
    console.error('Failed to load permissions:', err)
    error.value = 'Failed to connect to server'
  } finally {
    loading.value = false
  }
}

// Tab 2: All Role Assignments functions
const uniqueRolesCount = computed(() => {
  const roles = new Set(allRoleAssignments.value.map(a => a.roleDefinitionName))
  return roles.size
})

const userAssignmentsCount = computed(() => {
  return allRoleAssignments.value.filter(a => a.principalType === 'User').length
})

const spAssignmentsCount = computed(() => {
  return allRoleAssignments.value.filter(a => a.principalType === 'ServicePrincipal').length
})

const filteredAllRoleAssignments = computed(() => {
  let filtered = allRoleAssignments.value

  if (filterPrincipalType.value) {
    filtered = filtered.filter(a => a.principalType === filterPrincipalType.value)
  }

  if (searchAll.value) {
    const search = searchAll.value.toLowerCase()
    filtered = filtered.filter(a => {
      const principalName = getPrincipalDisplay(a.principalId).toLowerCase()
      return (a.roleDefinitionName && a.roleDefinitionName.toLowerCase().includes(search)) ||
             (a.scope && a.scope.toLowerCase().includes(search)) ||
             (a.principalId && a.principalId.toLowerCase().includes(search)) ||
             principalName.includes(search)
    })
  }

  return filtered
})

const loadAllRoleAssignments = async (forceRefresh = false) => {
  // Check cache first (5 min TTL) - skip if force refresh
  if (!forceRefresh && isCacheValid(dataCache.value.allAssignments)) {
    console.log('[CACHE] Using cached All Role Assignments')
    allRoleAssignments.value = dataCache.value.allAssignments.data
    principalNamesCache.value = dataCache.value.allAssignments.principals || {}
    return
  }
  
  if (forceRefresh) {
    console.log('[CACHE] Force refresh - invalidating cache')
  }
  
  loadingAll.value = true
  errorAll.value = null

  try {
    const response = await axios.get('/api/azure/permissions/role-assignments-all')
    
    if (response.data.success) {
      allRoleAssignments.value = response.data.roleAssignments || []
      console.log('[LOAD ALL] Loaded', allRoleAssignments.value.length, 'role assignments')
      
      // Resolve principal names in background
      await resolvePrincipalNames()
      
      // Update cache (including resolved principals)
      dataCache.value.allAssignments = {
        data: allRoleAssignments.value,
        principals: principalNamesCache.value,
        timestamp: Date.now()
      }
      console.log('[CACHE] All Role Assignments cached')
    } else {
      errorAll.value = response.data.error || 'Failed to load role assignments'
    }
  } catch (err) {
    console.error('Failed to load all role assignments:', err)
    errorAll.value = 'Failed to connect to server'
  } finally {
    loadingAll.value = false
  }
}

const resolvePrincipalNames = async () => {
  console.log('[UPN RESOLUTION] Starting resolution...')
  
  // Get unique principals
  const uniquePrincipals = new Map()
  allRoleAssignments.value.forEach(assignment => {
    if (!uniquePrincipals.has(assignment.principalId)) {
      uniquePrincipals.set(assignment.principalId, assignment.principalType)
    }
  })
  
  console.log('[UPN RESOLUTION] Found', uniquePrincipals.size, 'unique principals')
  
  // Build batch request
  const batchRequest = Array.from(uniquePrincipals.entries()).map(([id, type]) => ({
    id: id,
    type: type
  }))
  
  try {
    console.log('[UPN RESOLUTION] Calling POST /api/tenant/resolve-principals...')
    const response = await axios.post('/api/tenant/resolve-principals', batchRequest)
    
    if (response.data.success) {
      principalNamesCache.value = response.data.principals
      console.log(`[UPN RESOLUTION] ✓ Resolved ${response.data.count} principals`)
    } else if (response.data.error_type === 'no_graph_token') {
      // No Graph token available - NON-BLOCKING error
      console.warn('[UPN RESOLUTION] No Graph token:', response.data.error)
      
      // Show warning toast
      showUPNWarning.value = true
      
      // Auto-hide after 8 seconds
      setTimeout(() => {
        showUPNWarning.value = false
      }, 8000)
      
      // Fallback: populate cache with GUIDs
      uniquePrincipals.forEach((type, id) => {
        principalNamesCache.value[id] = id.substring(0, 8) + '...'
      })
    } else {
      // Other error
      console.error('[UPN RESOLUTION] Failed:', response.data.error)
      
      // Fallback: populate cache with GUIDs
      uniquePrincipals.forEach((type, id) => {
        principalNamesCache.value[id] = id.substring(0, 8) + '...'
      })
    }
  } catch (err) {
    console.error('[UPN RESOLUTION] Error:', err.message)
    // Fallback: populate cache with GUIDs
    uniquePrincipals.forEach((type, id) => {
      principalNamesCache.value[id] = id.substring(0, 8) + '...'
    })
  }
  
  console.log('[UPN RESOLUTION] Finished')
}

const getPrincipalDisplay = (principalId) => {
  return principalNamesCache.value[principalId] || (principalId.substring(0, 8) + '...')
}

const getScopeDisplay = (scope) => {
  if (!scope) return 'Unknown'
  
  const parts = scope.split('/')
  
  // Subscription level
  if (parts.length === 3 && parts[1] === 'subscriptions') {
    return 'Subscription'
  }
  
  // Resource group level
  if (parts.includes('resourceGroups')) {
    const rgIndex = parts.indexOf('resourceGroups')
    if (rgIndex + 1 < parts.length) {
      return `RG: ${parts[rgIndex + 1]}`
    }
  }
  
  // Resource level
  if (parts.includes('providers')) {
    const resourceName = parts[parts.length - 1]
    const resourceType = parts[parts.length - 2]
    return `${resourceType}/${resourceName}`
  }
  
  return scope
}

const getPrincipalTypeBadgeClass = (type) => {
  if (!type) return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
  
  switch (type) {
    case 'User':
      return props.isDark ? 'bg-cyan-900 text-cyan-300' : 'bg-cyan-100 text-cyan-800'
    case 'ServicePrincipal':
      return props.isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800'
    case 'Group':
      return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
    default:
      return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
  }
}

// Tab 3: Effective Permissions functions
const uniqueResourceTypesCount = computed(() => {
  const types = new Set(effectivePermissions.value.map(r => r.resourceType))
  return types.size
})

const uniqueSubscriptionsCount = computed(() => {
  const subs = new Set(effectivePermissions.value.map(r => r.subscriptionName))
  return subs.size
})

const uniqueResourceTypes = computed(() => {
  const types = new Set(effectivePermissions.value.map(r => r.resourceType))
  return Array.from(types).sort()
})

const filteredEffectivePermissions = computed(() => {
  let filtered = effectivePermissions.value

  if (filterResourceType.value) {
    filtered = filtered.filter(r => r.resourceType === filterResourceType.value)
  }

  if (searchEffective.value) {
    const search = searchEffective.value.toLowerCase()
    filtered = filtered.filter(r => 
      (r.resourceName && r.resourceName.toLowerCase().includes(search)) ||
      (r.resourceType && r.resourceType.toLowerCase().includes(search)) ||
      (r.resourceGroup && r.resourceGroup.toLowerCase().includes(search))
    )
  }

  return filtered
})

const analyzeEffectivePermissions = async (forceRefresh = false) => {
  // Check cache first (5 min TTL) - skip if force refresh
  if (!forceRefresh && isCacheValid(dataCache.value.effectivePermissions)) {
    console.log('[CACHE] Using cached Effective Permissions')
    effectivePermissions.value = dataCache.value.effectivePermissions.data
    return
  }
  
  if (forceRefresh) {
    console.log('[CACHE] Force refresh - invalidating cache')
  }
  
  loadingEffective.value = true
  errorEffective.value = null

  try {
    const response = await axios.get('http://localhost:5000/api/azure/permissions/effective-all')
    
    if (response.data.success) {
      effectivePermissions.value = response.data.effectivePermissions || []
      
      // Update cache
      dataCache.value.effectivePermissions = {
        data: effectivePermissions.value,
        timestamp: Date.now()
      }
      console.log('[CACHE] Effective Permissions cached')
    } else {
      errorEffective.value = response.data.error || 'Failed to analyze permissions'
    }
  } catch (err) {
    console.error('Failed to analyze effective permissions:', err)
    errorEffective.value = 'Failed to connect to server'
  } finally {
    loadingEffective.value = false
  }
}

// Shared utility functions
const getRoleBadgeClass = (roleName) => {
  if (!roleName) return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
  
  const name = roleName.toLowerCase()
  
  if (name.includes('owner')) {
    return props.isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800'
  } else if (name.includes('contributor')) {
    return props.isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800'
  } else if (name.includes('reader')) {
    return props.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
  } else if (name.includes('admin')) {
    return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
  } else {
    return props.isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'
  }
}

const getScopeName = (scope) => {
  if (!scope) return 'Unknown'
  
  const parts = scope.split('/')
  
  // Subscription level
  if (parts.length === 3 && parts[1] === 'subscriptions') {
    return 'Subscription (Root)'
  }
  
  // Resource group level
  if (parts.includes('resourceGroups')) {
    const rgIndex = parts.indexOf('resourceGroups')
    if (rgIndex + 1 < parts.length) {
      return `Resource Group: ${parts[rgIndex + 1]}`
    }
  }
  
  // Resource level
  if (parts.includes('providers')) {
    const providerIndex = parts.indexOf('providers')
    if (providerIndex + 2 < parts.length) {
      const resourceType = parts[providerIndex + 1]
      const resourceName = parts[parts.length - 1]
      return `${resourceType.split('/').pop()}: ${resourceName}`
    }
  }
  
  return 'Resource Level'
}

const getAssignmentIdShort = (id) => {
  if (!id) return 'N/A'
  const parts = id.split('/')
  return parts[parts.length - 1]
}

// Global Admin Elevation functions
const checkElevationStatus = async () => {
  elevationLoading.value = true
  elevationError.value = null
  
  try {
    const response = await axios.get('http://localhost:5000/api/azure/permissions/elevation-status')
    
    if (response.data.success) {
      elevationStatus.value = {
        isGlobalAdmin: response.data.isGlobalAdmin,
        isElevated: response.data.isElevated,
        roleAssignmentId: response.data.roleAssignmentId,
        userInfo: response.data.userInfo
      }
    } else {
      elevationError.value = response.data.error || 'Failed to check elevation status'
    }
  } catch (err) {
    console.error('Failed to check elevation status:', err)
    elevationError.value = 'Failed to connect to server'
  } finally {
    elevationLoading.value = false
  }
}

const elevateAccess = async () => {
  elevationLoading.value = true
  elevationError.value = null
  elevationSuccess.value = null
  
  try {
    const response = await axios.post('http://localhost:5000/api/azure/permissions/elevate-access')
    
    if (response.data.success) {
      elevationSuccess.value = 'Access elevated successfully! You now have User Access Administrator role at root scope.'
      await checkElevationStatus()
      await loadMyPermissions(true) // Reload permissions to show new role
    } else {
      elevationError.value = response.data.error || 'Failed to elevate access'
    }
  } catch (err) {
    console.error('Failed to elevate access:', err)
    elevationError.value = 'Failed to connect to server'
  } finally {
    elevationLoading.value = false
  }
}

const removeElevation = async () => {
  if (!confirm('Remove elevated access? This will revoke your User Access Administrator role at root scope.')) {
    return
  }
  
  elevationLoading.value = true
  elevationError.value = null
  elevationSuccess.value = null
  
  try {
    const response = await axios.delete('http://localhost:5000/api/azure/permissions/elevate-access')
    
    if (response.data.success) {
      elevationSuccess.value = 'Elevation removed successfully!'
      await checkElevationStatus()
      await loadMyPermissions(true) // Reload permissions
    } else {
      elevationError.value = response.data.error || 'Failed to remove elevation'
    }
  } catch (err) {
    console.error('Failed to remove elevation:', err)
    elevationError.value = 'Failed to connect to server'
  } finally {
    elevationLoading.value = false
  }
}

onMounted(() => {
  checkARMToken()
  loadMyPermissions()
  checkElevationStatus() // Check elevation status on mount
})
</script>

<style scoped>
.break-words {
  word-break: break-word;
  overflow-wrap: break-word;
}

.break-all {
  word-break: break-all;
}

.btn {
  @apply px-6 py-2 rounded-lg font-semibold transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-800 hover:bg-gray-300;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-200 hover:bg-gray-600;
}
</style>
