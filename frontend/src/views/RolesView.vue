<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Roles & Licenses</h1>
        <p class="mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Enumerate Entra ID directory roles and tenant licenses</p>
      </div>
      <div class="flex items-center space-x-3">
        <button @click="fetchSecuritySummary" :disabled="loading" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
          🔍 Security Summary
        </button>
        <button @click="refreshData" :disabled="loading" class="btn btn-primary">
          <span v-if="loading" class="animate-spin mr-2">⏳</span>
          {{ loading ? 'Loading...' : '🔄 Refresh' }}
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="rounded-lg p-4 mb-6" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p :class="isDark ? 'text-red-300' : 'text-red-800'">{{ error }}</p>
    </div>

    <!-- Security Summary Modal -->
    <div v-if="showSecuritySummary" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="bg-gradient-to-r from-red-600 to-orange-500 text-white p-6 rounded-t-lg">
          <h2 class="text-2xl font-bold">🔒 Security Summary</h2>
        </div>
        <div class="p-6">
          <div v-if="securitySummary">
            <div class="grid grid-cols-2 gap-4 mb-6">
              <div class="rounded-lg p-4 text-center" :class="isDark ? 'bg-red-900/30' : 'bg-red-50'">
                <div class="text-3xl font-bold text-red-500">{{ securitySummary.total_privileged_users }}</div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Privileged Users</div>
              </div>
              <div class="rounded-lg p-4 text-center" :class="isDark ? 'bg-blue-900/30' : 'bg-blue-50'">
                <div class="text-3xl font-bold text-blue-500">{{ securitySummary.licenses?.length || 0 }}</div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Active Licenses</div>
              </div>
            </div>

            <div v-if="securitySummary.security_findings?.length" class="mb-4">
              <h3 class="font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">Security Findings</h3>
              <div v-for="(finding, index) in securitySummary.security_findings" :key="index" 
                   :class="['p-3 rounded-lg mb-2', 
                     finding.severity === 'high' ? (isDark ? 'bg-red-900/30 border-l-4 border-red-500' : 'bg-red-50 border-l-4 border-red-500') : 
                     finding.severity === 'medium' ? (isDark ? 'bg-yellow-900/30 border-l-4 border-yellow-500' : 'bg-yellow-50 border-l-4 border-yellow-500') : 
                     (isDark ? 'bg-blue-900/30 border-l-4 border-blue-500' : 'bg-blue-50 border-l-4 border-blue-500')]">
                <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">{{ finding.finding }}</p>
                <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-600'">{{ finding.recommendation }}</p>
              </div>
            </div>
          </div>
          <div class="text-right">
            <button @click="showSecuritySummary = false" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="rounded-lg shadow-md mb-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="flex border-b overflow-x-auto" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
        <button
          @click="activeTab = 'roles'; fetchRoles()"
          :class="[
            'px-6 py-4 font-semibold transition-colors whitespace-nowrap',
            activeTab === 'roles'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          🛡️ Directory Roles ({{ roles.length }})
        </button>
        <button
          @click="activeTab = 'auscoped'; fetchAUScopedRoles()"
          :class="[
            'px-6 py-4 font-semibold transition-colors whitespace-nowrap',
            activeTab === 'auscoped'
              ? 'text-purple-500 border-b-2 border-purple-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          🏢 AU-Scoped ({{ auScopedData.total_assignments || 0 }})
        </button>
        <button
          @click="activeTab = 'licenses'; fetchLicenses()"
          :class="[
            'px-6 py-4 font-semibold transition-colors whitespace-nowrap',
            activeTab === 'licenses'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          📜 Licenses ({{ licenses.length }})
        </button>
        <button
          @click="activeTab = 'privileged'; fetchPrivilegedRoles()"
          :class="[
            'px-6 py-4 font-semibold transition-colors whitespace-nowrap',
            activeTab === 'privileged'
              ? 'text-red-500 border-b-2 border-red-500'
              : isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          ⚠️ Privileged Roles
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading data...</p>
    </div>

    <!-- Directory Roles Tab -->
    <div v-else-if="activeTab === 'roles'" class="space-y-4">
      <div v-if="roles.length === 0" class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">🛡️</div>
        <h2 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">No Roles Loaded</h2>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Click Refresh to load directory roles</p>
      </div>

      <div v-for="role in roles" :key="role.id" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div 
          @click="toggleRoleExpand(role.id)"
          class="p-4 cursor-pointer flex items-center justify-between"
          :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'"
        >
          <div>
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">{{ role.displayName }}</h3>
            <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ role.description || 'No description' }}</p>
          </div>
          <div class="flex items-center space-x-3">
            <span v-if="roleMembers[role.id]" class="px-3 py-1 rounded-full text-sm font-medium" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
              {{ roleMembers[role.id].length }} members
            </span>
            <span v-else-if="loadingMembers[role.id]" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
              Loading...
            </span>
            <svg 
              class="w-5 h-5 transition-transform"
              :class="[isDark ? 'text-gray-500' : 'text-gray-400', { 'rotate-180': expandedRole === role.id }]"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </div>
        </div>

        <!-- Expanded Members -->
        <div v-if="expandedRole === role.id && roleMembers[role.id]" class="border-t p-4" :class="isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'">
          <h4 class="font-medium mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Members ({{ roleMembers[role.id].length }})</h4>
          <div v-if="roleMembers[role.id].length === 0" class="italic" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
            No members assigned to this role
          </div>
          <div v-else class="space-y-2">
            <div 
              v-for="member in roleMembers[role.id]" 
              :key="member.id"
              class="rounded p-3 flex items-center justify-between"
              :class="isDark ? 'bg-gray-800' : 'bg-white'"
            >
              <div>
                <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">{{ member.displayName }}</p>
                <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ member.userPrincipalName }}</p>
              </div>
              <div class="flex items-center space-x-2">
                <span :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  member.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')
                ]">
                  {{ member.accountEnabled ? 'Enabled' : 'Disabled' }}
                </span>
                <span class="text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">{{ member.memberType }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AU-Scoped Roles Tab (NEW) -->
    <div v-else-if="activeTab === 'auscoped'" class="space-y-4">
      <div v-if="loadingAUScoped" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading AU-scoped roles (this may take a moment)...</p>
      </div>

      <div v-else-if="!auScopedData.administrative_units?.length" class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">🏢</div>
        <h2 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">No AU-Scoped Roles Found</h2>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
          {{ auScopedData.message || 'No Administrative Units with scoped role assignments' }}
        </p>
      </div>

      <template v-else>
        <!-- Summary Cards -->
        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="rounded-lg p-4 text-center" :class="isDark ? 'bg-purple-900/30' : 'bg-purple-50'">
            <div class="text-3xl font-bold text-purple-500">{{ auScopedData.total_aus || 0 }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Administrative Units</div>
          </div>
          <div class="rounded-lg p-4 text-center" :class="isDark ? 'bg-blue-900/30' : 'bg-blue-50'">
            <div class="text-3xl font-bold text-blue-500">{{ auScopedData.aus_with_assignments || 0 }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">AUs with Assignments</div>
          </div>
          <div class="rounded-lg p-4 text-center" :class="isDark ? 'bg-orange-900/30' : 'bg-orange-50'">
            <div class="text-3xl font-bold text-orange-500">{{ auScopedData.total_assignments || 0 }}</div>
            <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Total Scoped Assignments</div>
          </div>
        </div>

        <!-- Role Summary -->
        <div v-if="auScopedData.role_summary?.length" class="rounded-lg shadow-md mb-6" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div class="p-4 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">📊 Role Summary</h3>
          </div>
          <div class="p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <div 
              v-for="role in auScopedData.role_summary" 
              :key="role.roleName"
              class="rounded-lg p-3"
              :class="[
                role.isPrivileged 
                  ? (isDark ? 'bg-red-900/30 border border-red-700' : 'bg-red-50 border border-red-200')
                  : (isDark ? 'bg-gray-700' : 'bg-gray-100')
              ]"
            >
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium truncate" :class="role.isPrivileged ? 'text-red-400' : (isDark ? 'text-gray-200' : 'text-gray-700')">
                  {{ role.roleName }}
                </span>
                <span class="px-2 py-1 rounded text-xs font-bold" :class="isDark ? 'bg-gray-600 text-white' : 'bg-gray-200 text-gray-700'">
                  {{ role.count }}
                </span>
              </div>
              <div v-if="role.isPrivileged" class="mt-1 text-xs text-red-400">⚠️ Privileged</div>
            </div>
          </div>
        </div>

        <!-- Administrative Units List -->
        <div v-for="au in auScopedData.administrative_units" :key="au.id" class="rounded-lg shadow-md overflow-hidden border-l-4 border-purple-500" :class="isDark ? 'bg-gray-800' : 'bg-white'">
          <div 
            @click="expandedAU = expandedAU === au.id ? null : au.id"
            class="p-4 cursor-pointer"
            :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-purple-50'"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                  🏢 {{ au.displayName }}
                </h3>
                <p v-if="au.description" class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                  {{ au.description }}
                </p>
              </div>
              <div class="flex items-center space-x-3">
                <span class="px-3 py-1 rounded-full text-sm font-medium" :class="[
                  au.scopedRoleCount > 0 
                    ? (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800')
                    : (isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500')
                ]">
                  {{ au.scopedRoleCount }} scoped role{{ au.scopedRoleCount !== 1 ? 's' : '' }}
                </span>
                <svg 
                  class="w-5 h-5 transition-transform"
                  :class="[isDark ? 'text-gray-500' : 'text-gray-400', { 'rotate-180': expandedAU === au.id }]"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- Expanded AU Assignments -->
          <div v-if="expandedAU === au.id && au.assignments?.length" class="border-t p-4" :class="isDark ? 'border-gray-700 bg-purple-900/10' : 'border-gray-200 bg-purple-50'">
            <h4 class="font-medium mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Scoped Role Assignments ({{ au.assignments.length }})
            </h4>
            <div class="space-y-2">
              <div 
                v-for="assignment in au.assignments" 
                :key="assignment.assignmentId"
                class="rounded p-3 flex items-center justify-between"
                :class="[
                  assignment.isPrivileged
                    ? (isDark ? 'bg-red-900/30 border-l-4 border-red-500' : 'bg-red-50 border-l-4 border-red-500')
                    : (isDark ? 'bg-gray-800' : 'bg-white')
                ]"
              >
                <div>
                  <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                    {{ assignment.userDisplayName }}
                  </p>
                  <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                    {{ assignment.userPrincipalName }}
                  </p>
                </div>
                <div class="text-right">
                  <span class="px-2 py-1 rounded text-xs font-medium" :class="[
                    assignment.isPrivileged 
                      ? (isDark ? 'bg-red-800 text-red-200' : 'bg-red-100 text-red-800')
                      : (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')
                  ]">
                    {{ assignment.roleName }}
                  </span>
                  <p v-if="assignment.isPrivileged" class="text-xs mt-1 text-red-400">⚠️ Privileged Role</p>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="expandedAU === au.id && !au.assignments?.length" class="border-t p-4" :class="isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'">
            <p class="italic" :class="isDark ? 'text-gray-500' : 'text-gray-500'">No scoped role assignments in this AU</p>
          </div>
        </div>
      </template>
    </div>

    <!-- Licenses Tab -->
    <div v-else-if="activeTab === 'licenses'" class="space-y-4">
      <div v-if="licenses.length === 0" class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">📜</div>
        <h2 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">No Licenses Loaded</h2>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Click Refresh to load tenant licenses</p>
      </div>

      <div v-for="license in licenses" :key="license.id" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div 
          @click="toggleLicenseExpand(license.skuId)"
          class="p-4 cursor-pointer"
          :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'"
        >
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">{{ license.displayName }}</h3>
            <svg 
              class="w-5 h-5 transition-transform"
              :class="[isDark ? 'text-gray-500' : 'text-gray-400', { 'rotate-180': expandedLicense === license.skuId }]"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </div>
          <p class="text-sm mb-3" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ license.skuPartNumber }}</p>
          
          <!-- Usage Bar -->
          <div class="mb-2">
            <div class="flex justify-between text-sm mb-1">
              <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                {{ license.consumedUnits }} / {{ license.prepaidUnits.enabled }} used
              </span>
              <span :class="[
                'font-medium',
                license.usagePercent > 90 ? 'text-red-500' : 
                license.usagePercent > 70 ? 'text-yellow-500' : 'text-green-500'
              ]">
                {{ license.usagePercent }}%
              </span>
            </div>
            <div class="w-full rounded-full h-2" :class="isDark ? 'bg-gray-700' : 'bg-gray-200'">
              <div 
                class="h-2 rounded-full transition-all"
                :class="[
                  license.usagePercent > 90 ? 'bg-red-500' : 
                  license.usagePercent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                ]"
                :style="{ width: `${Math.min(license.usagePercent, 100)}%` }"
              ></div>
            </div>
          </div>
          
          <div class="flex space-x-4 text-sm">
            <span class="text-green-500">✓ {{ license.availableUnits }} available</span>
            <span v-if="license.prepaidUnits.suspended > 0" class="text-yellow-500">
              ⚠️ {{ license.prepaidUnits.suspended }} suspended
            </span>
          </div>
        </div>

        <!-- Expanded License Users -->
        <div v-if="expandedLicense === license.skuId" class="border-t p-4" :class="isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'">
          <div v-if="loadingLicenseUsers[license.skuId]" class="text-center py-4">
            <span :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading users...</span>
          </div>
          <div v-else-if="licenseUsers[license.skuId]">
            <h4 class="font-medium mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
              Assigned Users ({{ licenseUsers[license.skuId].length }})
            </h4>
            <div v-if="licenseUsers[license.skuId].length === 0" class="italic" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
              No users assigned
            </div>
            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
              <div 
                v-for="user in licenseUsers[license.skuId]" 
                :key="user.id"
                class="rounded p-3"
                :class="isDark ? 'bg-gray-800' : 'bg-white'"
              >
                <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">{{ user.displayName }}</p>
                <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ user.userPrincipalName }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Privileged Roles Tab -->
    <div v-else-if="activeTab === 'privileged'" class="space-y-4">
      <div v-if="loadingPrivileged" class="text-center py-12">
        <div class="animate-spin h-12 w-12 border-4 border-red-500 border-t-transparent rounded-full mx-auto"></div>
        <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading privileged roles...</p>
      </div>

      <div v-else-if="privilegedRoles.length === 0" class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div class="text-6xl mb-4">✅</div>
        <h2 class="text-xl font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">No Privileged Roles Found</h2>
        <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">No high-privilege role assignments detected</p>
      </div>

      <div v-for="role in privilegedRoles" :key="role.roleId" class="rounded-lg shadow-md overflow-hidden border-l-4 border-red-500" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <div 
          @click="expandedPrivileged = expandedPrivileged === role.roleId ? null : role.roleId"
          class="p-4 cursor-pointer"
          :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-red-50'"
        >
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-semibold text-red-500">{{ role.displayName }}</h3>
              <p class="text-sm mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                {{ role.members.length }} member(s)
              </p>
            </div>
            <svg 
              class="w-5 h-5 transition-transform"
              :class="[isDark ? 'text-gray-500' : 'text-gray-400', { 'rotate-180': expandedPrivileged === role.roleId }]"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </div>
        </div>

        <!-- Expanded Members -->
        <div v-if="expandedPrivileged === role.roleId" class="border-t p-4" :class="isDark ? 'border-gray-700 bg-red-900/20' : 'border-gray-200 bg-red-50'">
          <h4 class="font-medium mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">Privileged Members</h4>
          <div v-if="role.members.length === 0" class="italic" :class="isDark ? 'text-gray-500' : 'text-gray-500'">
            No members assigned
          </div>
          <div v-else class="space-y-2">
            <div 
              v-for="member in role.members" 
              :key="member.id"
              class="rounded p-3 flex items-center justify-between border-l-4 border-red-500"
              :class="isDark ? 'bg-gray-800' : 'bg-white'"
            >
              <div>
                <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">{{ member.displayName }}</p>
                <p class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ member.userPrincipalName }}</p>
              </div>
              <div class="flex items-center space-x-2">
                <span :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  member.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')
                ]">
                  {{ member.accountEnabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, computed } from 'vue'
import { rolesAPI } from '../services/api'

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

const loading = ref(false)
const error = ref('')
const activeTab = ref('roles')

// Roles data
const roles = ref([])
const roleMembers = ref({})
const loadingMembers = ref({})
const expandedRole = ref(null)

// AU-Scoped data (NEW)
const auScopedData = ref({})
const loadingAUScoped = ref(false)
const expandedAU = ref(null)

// Licenses data
const licenses = ref([])
const licenseUsers = ref({})
const loadingLicenseUsers = ref({})
const expandedLicense = ref(null)

// Privileged roles data
const privilegedRoles = ref([])
const loadingPrivileged = ref(false)
const expandedPrivileged = ref(null)

// Security summary
const showSecuritySummary = ref(false)
const securitySummary = ref(null)

const refreshData = async () => {
  if (activeTab.value === 'roles') {
    await fetchRoles()
  } else if (activeTab.value === 'auscoped') {
    await fetchAUScopedRoles()
  } else if (activeTab.value === 'licenses') {
    await fetchLicenses()
  } else if (activeTab.value === 'privileged') {
    await fetchPrivilegedRoles()
  }
}

const fetchRoles = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await rolesAPI.getDirectoryRoles()
    
    if (response.data.success) {
      roles.value = response.data.roles
    } else {
      error.value = response.data.error || 'Failed to fetch roles'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
  } finally {
    loading.value = false
  }
}

const fetchAUScopedRoles = async () => {
  loadingAUScoped.value = true
  loading.value = true
  error.value = ''
  
  try {
    const response = await rolesAPI.getAUScopedRoles()
    
    if (response.data.success) {
      auScopedData.value = response.data
    } else {
      error.value = response.data.error || 'Failed to fetch AU-scoped roles'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
  } finally {
    loadingAUScoped.value = false
    loading.value = false
  }
}

const fetchLicenses = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await rolesAPI.getLicenses()
    
    if (response.data.success) {
      licenses.value = response.data.licenses
    } else {
      error.value = response.data.error || 'Failed to fetch licenses'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
  } finally {
    loading.value = false
  }
}

const fetchPrivilegedRoles = async () => {
  loadingPrivileged.value = true
  error.value = ''
  
  try {
    const response = await rolesAPI.getPrivilegedRoles()
    
    if (response.data.success) {
      privilegedRoles.value = response.data.privileged_roles
    } else {
      error.value = response.data.error || 'Failed to fetch privileged roles'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
  } finally {
    loadingPrivileged.value = false
  }
}

const toggleRoleExpand = async (roleId) => {
  if (expandedRole.value === roleId) {
    expandedRole.value = null
    return
  }
  
  expandedRole.value = roleId
  
  // Load members if not already loaded
  if (!roleMembers.value[roleId]) {
    loadingMembers.value[roleId] = true
    
    try {
      const response = await rolesAPI.getRoleMembers(roleId)
      
      if (response.data.success) {
        roleMembers.value[roleId] = response.data.members
      }
    } catch (err) {
      console.error('Failed to load members:', err)
    } finally {
      loadingMembers.value[roleId] = false
    }
  }
}

const toggleLicenseExpand = async (skuId) => {
  if (expandedLicense.value === skuId) {
    expandedLicense.value = null
    return
  }
  
  expandedLicense.value = skuId
  
  // Load users if not already loaded
  if (!licenseUsers.value[skuId]) {
    loadingLicenseUsers.value[skuId] = true
    
    try {
      const response = await rolesAPI.getLicenseUsers(skuId)
      
      if (response.data.success) {
        licenseUsers.value[skuId] = response.data.users
      }
    } catch (err) {
      console.error('Failed to load license users:', err)
    } finally {
      loadingLicenseUsers.value[skuId] = false
    }
  }
}

const fetchSecuritySummary = async () => {
  loading.value = true
  
  try {
    const response = await rolesAPI.getSecuritySummary()
    
    if (response.data.success) {
      securitySummary.value = response.data
      showSecuritySummary.value = true
    } else {
      error.value = response.data.error || 'Failed to fetch security summary'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchRoles()
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

.bg-gray-750 {
  background-color: #2d3748;
}
</style>
