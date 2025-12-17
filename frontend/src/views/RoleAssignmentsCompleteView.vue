<template>
  <div :class="['p-6', isDark ? 'bg-gray-900 text-gray-100' : 'bg-gray-50 text-gray-900']">
    <h1 class="text-3xl font-bold mb-6">Role Assignments (Complete)</h1>

    <!-- Token Check Warning -->
    <div v-if="!hasARMToken" :class="[
      'mb-6 p-4 rounded-lg border',
      isDark ? 'bg-red-900/20 border-red-700' : 'bg-red-50 border-red-200'
    ]">
      <p :class="['font-semibold', isDark ? 'text-red-300' : 'text-red-800']">
        ⚠️ No ARM token available
      </p>
      <p :class="['text-sm mt-1', isDark ? 'text-red-400' : 'text-red-600']">
        Please authenticate with Azure PowerShell to view role assignments.
      </p>
    </div>

    <!-- Info Box -->
    <div :class="[
      'mb-6 p-4 rounded-lg border',
      isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200'
    ]">
      <p :class="['text-sm', isDark ? 'text-blue-300' : 'text-blue-800']">
        💡 Shows ALL role assignments (subscription + resource level). 
        PowerShell equivalent: <code class="font-mono bg-black/20 px-1 rounded">Get-AzRoleAssignment</code>
      </p>
    </div>

    <!-- Load Button -->
    <button
      @click="loadRoleAssignments"
      :disabled="loading || !hasARMToken"
      :class="[
        'px-6 py-3 rounded-lg font-semibold mb-6 transition-all',
        loading || !hasARMToken
          ? 'bg-gray-400 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      ]"
    >
      {{ loading ? 'Loading...' : 'Load All Role Assignments' }}
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">
        Loading role assignments...
      </p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" :class="[
      'p-6 rounded-lg border text-center',
      isDark ? 'bg-red-900/20 border-red-700' : 'bg-red-50 border-red-200'
    ]">
      <p class="text-2xl mb-2">⚠️</p>
      <h3 :class="['text-lg font-semibold mb-2', isDark ? 'text-red-300' : 'text-red-800']">
        Error Loading Role Assignments
      </h3>
      <p :class="['text-sm mb-4', isDark ? 'text-red-400' : 'text-red-600']">
        {{ error }}
      </p>
      <button
        @click="loadRoleAssignments"
        class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        Try Again
      </button>
    </div>

    <!-- Results -->
    <div v-else-if="roleAssignments.length > 0">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Total Assignments</p>
          <p class="text-2xl font-bold">{{ roleAssignments.length }}</p>
        </div>
        
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Unique Roles</p>
          <p class="text-2xl font-bold">{{ uniqueRoles }}</p>
        </div>
        
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">User Assignments</p>
          <p class="text-2xl font-bold">{{ userAssignments }}</p>
        </div>
        
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">SP Assignments</p>
          <p class="text-2xl font-bold">{{ spAssignments }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-6 flex gap-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search roles, scopes..."
          :class="[
            'flex-1 px-4 py-2 rounded-lg border',
            isDark
              ? 'bg-gray-800 border-gray-700 text-gray-100'
              : 'bg-white border-gray-300'
          ]"
        />
        
        <select
          v-model="filterPrincipalType"
          :class="[
            'px-4 py-2 rounded-lg border',
            isDark
              ? 'bg-gray-800 border-gray-700 text-gray-100'
              : 'bg-white border-gray-300'
          ]"
        >
          <option value="">All Principal Types</option>
          <option value="User">User</option>
          <option value="ServicePrincipal">Service Principal</option>
          <option value="Group">Group</option>
        </select>
      </div>

      <!-- Assignments Table -->
      <div :class="[
        'rounded-lg overflow-hidden',
        isDark ? 'bg-gray-800' : 'bg-white shadow'
      ]">
        <table class="w-full">
          <thead :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-semibold">Role</th>
              <th class="px-4 py-3 text-left text-sm font-semibold">Scope</th>
              <th class="px-4 py-3 text-left text-sm font-semibold">Principal Type</th>
              <th class="px-4 py-3 text-left text-sm font-semibold">Principal ID</th>
              <th class="px-4 py-3 text-left text-sm font-semibold">Subscription</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="assignment in filteredAssignments"
              :key="assignment.id"
              :class="[
                'border-t',
                isDark ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'
              ]"
            >
              <td class="px-4 py-3">
                <span :class="[
                  'px-2 py-1 text-xs font-semibold rounded',
                  getRoleBadgeClass(assignment.roleDefinitionName)
                ]">
                  {{ assignment.roleDefinitionName }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm font-mono max-w-xs truncate" :title="assignment.scope">
                {{ getScopeDisplay(assignment.scope) }}
              </td>
              <td class="px-4 py-3 text-sm">
                <span :class="[
                  'px-2 py-1 text-xs rounded',
                  assignment.principalType === 'User'
                    ? (isDark ? 'bg-cyan-900 text-cyan-300' : 'bg-cyan-100 text-cyan-800')
                    : assignment.principalType === 'ServicePrincipal'
                    ? (isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800')
                    : (isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800')
                ]">
                  {{ assignment.principalType }}
                </span>
              </td>
              <td class="px-4 py-3 text-xs">
                <span :class="isDark ? 'text-gray-300' : 'text-gray-700'" :title="assignment.principalId">
                  {{ getPrincipalDisplay(assignment.principalId) }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm">
                {{ assignment.subscriptionName }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && roleAssignments.length === 0 && !error" :class="[
      'text-center py-12 rounded-lg',
      isDark ? 'bg-gray-800' : 'bg-white shadow'
    ]">
      <p class="text-4xl mb-4">🔐</p>
      <h3 :class="['text-xl font-semibold mb-2', isDark ? 'text-gray-200' : 'text-gray-800']">
        No Role Assignments Loaded
      </h3>
      <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
        Click "Load All Role Assignments" to scan your subscriptions.
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'RoleAssignmentsCompleteView',
  props: {
    isDark: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      roleAssignments: [],
      searchQuery: '',
      filterPrincipalType: '',
      hasARMToken: true,
      principalNamesCache: {}, // Cache for resolved UPN/displayName
      resolvingNames: false
    };
  },
  computed: {
    uniqueRoles() {
      return new Set(this.roleAssignments.map(a => a.roleDefinitionName)).size;
    },
    userAssignments() {
      return this.roleAssignments.filter(a => a.principalType === 'User').length;
    },
    spAssignments() {
      return this.roleAssignments.filter(a => a.principalType === 'ServicePrincipal').length;
    },
    filteredAssignments() {
      let filtered = this.roleAssignments;

      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(a => {
          const principalName = this.getPrincipalDisplay(a.principalId).toLowerCase();
          return a.roleDefinitionName.toLowerCase().includes(query) ||
                 a.scope.toLowerCase().includes(query) ||
                 a.principalId.toLowerCase().includes(query) ||
                 principalName.includes(query);
        });
      }

      if (this.filterPrincipalType) {
        filtered = filtered.filter(a => a.principalType === this.filterPrincipalType);
      }

      return filtered;
    }
  },
  methods: {
    async loadRoleAssignments() {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get('/api/azure/permissions/role-assignments-all');

        if (response.data.success) {
          this.roleAssignments = response.data.roleAssignments;
          console.log('[LOAD] Loaded', this.roleAssignments.length, 'role assignments');
          
          // Resolve principal names in background (non-blocking)
          this.resolvePrincipalNames();
        } else {
          this.error = response.data.error || 'Failed to load role assignments';
          
          if (response.data.error && response.data.error.includes('No ARM token')) {
            this.hasARMToken = false;
          }
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message || 'Failed to load role assignments';
      } finally {
        this.loading = false;
      }
    },
    
    async resolvePrincipalNames() {
      console.log('[UPN RESOLUTION] Starting resolution...');
      this.resolvingNames = true;
      
      // Get unique principals
      const uniquePrincipals = new Map();
      this.roleAssignments.forEach(assignment => {
        if (!uniquePrincipals.has(assignment.principalId)) {
          uniquePrincipals.set(assignment.principalId, assignment.principalType);
        }
      });
      
      console.log('[UPN RESOLUTION] Found', uniquePrincipals.size, 'unique principals');
      
      // Build batch request
      const batchRequest = Array.from(uniquePrincipals.entries()).map(([id, type]) => ({
        id: id,
        type: type
      }));
      
      console.log('[UPN RESOLUTION] Batch request:', batchRequest);
      
      try {
        // Single batch call to resolve all principals
        console.log('[UPN RESOLUTION] Calling POST /api/tenant/resolve-principals...');
        const response = await axios.post('/api/tenant/resolve-principals', batchRequest);
        
        console.log('[UPN RESOLUTION] Response:', response.data);
        
        if (response.data.success) {
          // Cache all resolved names
          this.principalNamesCache = response.data.principals;
          console.log(`[UPN RESOLUTION] ✓ Resolved ${response.data.count} principals`);
        } else {
          console.error('[UPN RESOLUTION] Failed:', response.data.error);
        }
      } catch (err) {
        console.error('[UPN RESOLUTION] Error:', err.message);
        console.error('[UPN RESOLUTION] Full error:', err);
        // Fallback: populate cache with GUIDs
        uniquePrincipals.forEach((type, id) => {
          this.principalNamesCache[id] = id.substring(0, 8) + '...';
        });
      }
      
      this.resolvingNames = false;
      console.log('[UPN RESOLUTION] Finished');
    },
    
    getPrincipalDisplay(principalId) {
      // Return cached name or GUID
      return this.principalNamesCache[principalId] || (principalId.substring(0, 8) + '...');
    },
    
    async checkARMToken() {
      try {
        const response = await axios.get('/api/azure/permissions/check-tokens');
        if (response.data.success) {
          this.hasARMToken = response.data.has_arm_token;
        }
      } catch (err) {
        console.error('Failed to check ARM token:', err);
      }
    },
    
    getRoleBadgeClass(roleName) {
      const name = roleName.toLowerCase();
      
      if (name.includes('owner')) {
        return this.isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800';
      } else if (name.includes('contributor')) {
        return this.isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800';
      } else if (name.includes('reader')) {
        return this.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800';
      } else {
        return this.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700';
      }
    },
    
    getScopeDisplay(scope) {
      const parts = scope.split('/');
      
      if (scope.includes('/resourceGroups/') && scope.includes('/providers/')) {
        // Resource level
        const resourceName = parts[parts.length - 1];
        const resourceType = parts[parts.length - 2];
        return `${resourceType}/${resourceName}`;
      } else if (scope.includes('/resourceGroups/')) {
        // Resource group level
        return 'RG: ' + parts[parts.indexOf('resourceGroups') + 1];
      } else if (scope.includes('/subscriptions/')) {
        // Subscription level
        return 'Subscription';
      }
      
      return scope;
    }
  },
  mounted() {
    this.checkARMToken();
  }
};
</script>
