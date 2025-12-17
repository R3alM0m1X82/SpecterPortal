<template>
  <div :class="['p-6', isDark ? 'bg-gray-900 text-gray-100' : 'bg-gray-50 text-gray-900']">
    <h1 class="text-3xl font-bold mb-6">Effective Permissions</h1>

    <!-- Token Check Warning -->
    <div v-if="!hasARMToken" :class="[
      'mb-6 p-4 rounded-lg border',
      isDark ? 'bg-red-900/20 border-red-700' : 'bg-red-50 border-red-200'
    ]">
      <p :class="['font-semibold', isDark ? 'text-red-300' : 'text-red-800']">
        ⚠️ No ARM token available
      </p>
      <p :class="['text-sm mt-1', isDark ? 'text-red-400' : 'text-red-600']">
        Please authenticate with Azure PowerShell to view effective permissions.
      </p>
    </div>

    <!-- Info Box -->
    <div :class="[
      'mb-6 p-4 rounded-lg border',
      isDark ? 'bg-blue-900/20 border-blue-700' : 'bg-blue-50 border-blue-200'
    ]">
      <p :class="['text-sm', isDark ? 'text-blue-300' : 'text-blue-800']">
        💡 This shows your effective permissions on ALL Azure resources. For each resource, you'll see:
        <strong>Actions</strong> (what you can do), <strong>NotActions</strong> (exceptions), 
        <strong>DataActions</strong> (data plane operations), and <strong>NotDataActions</strong>.
      </p>
    </div>

    <!-- Analyze Button -->
    <button
      @click="analyzePermissions"
      :disabled="loading || !hasARMToken"
      :class="[
        'px-6 py-3 rounded-lg font-semibold mb-6 transition-all',
        loading || !hasARMToken
          ? 'bg-gray-400 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      ]"
    >
      {{ loading ? 'Analyzing...' : 'Analyze All Permissions' }}
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-600'">
        Analyzing permissions across all resources...
      </p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" :class="[
      'p-6 rounded-lg border text-center',
      isDark ? 'bg-red-900/20 border-red-700' : 'bg-red-50 border-red-200'
    ]">
      <p class="text-2xl mb-2">⚠️</p>
      <h3 :class="['text-lg font-semibold mb-2', isDark ? 'text-red-300' : 'text-red-800']">
        Error Loading Permissions
      </h3>
      <p :class="['text-sm mb-4', isDark ? 'text-red-400' : 'text-red-600']">
        {{ error }}
      </p>
      <button
        @click="analyzePermissions"
        class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        Try Again
      </button>
    </div>

    <!-- Results -->
    <div v-else-if="effectivePermissions.length > 0">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Total Resources</p>
          <p class="text-2xl font-bold">{{ effectivePermissions.length }}</p>
        </div>
        
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Resource Types</p>
          <p class="text-2xl font-bold">{{ uniqueResourceTypes }}</p>
        </div>
        
        <div :class="[
          'p-4 rounded-lg',
          isDark ? 'bg-gray-800' : 'bg-white shadow'
        ]">
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">Subscriptions</p>
          <p class="text-2xl font-bold">{{ uniqueSubscriptions }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-6 flex gap-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search resources..."
          :class="[
            'flex-1 px-4 py-2 rounded-lg border',
            isDark
              ? 'bg-gray-800 border-gray-700 text-gray-100'
              : 'bg-white border-gray-300'
          ]"
        />
        
        <select
          v-model="filterResourceType"
          :class="[
            'px-4 py-2 rounded-lg border',
            isDark
              ? 'bg-gray-800 border-gray-700 text-gray-100'
              : 'bg-white border-gray-300'
          ]"
        >
          <option value="">All Resource Types</option>
          <option v-for="type in resourceTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>

      <!-- Permissions List -->
      <div class="space-y-4">
        <div
          v-for="perm in filteredPermissions"
          :key="perm.resourceId"
          :class="[
            'p-6 rounded-lg',
            isDark ? 'bg-gray-800' : 'bg-white shadow'
          ]"
        >
          <!-- Resource Header -->
          <div class="mb-4">
            <h3 :class="['text-lg font-semibold', isDark ? 'text-gray-100' : 'text-gray-900']">
              {{ perm.resourceName }}
            </h3>
            <p :class="['text-sm font-mono', isDark ? 'text-gray-400' : 'text-gray-600']">
              {{ perm.resourceType }}
            </p>
            <div class="flex gap-2 mt-2">
              <span :class="[
                'px-2 py-1 text-xs rounded',
                isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
              ]">
                {{ perm.subscriptionName }}
              </span>
              <span :class="[
                'px-2 py-1 text-xs rounded',
                isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
              ]">
                {{ perm.resourceGroup }}
              </span>
            </div>
          </div>

          <!-- Permissions Grid -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Actions -->
            <div>
              <h4 :class="['font-semibold mb-2 flex items-center gap-2', isDark ? 'text-green-300' : 'text-green-700']">
                ✅ Actions ({{ perm.permissions.actions.length }})
              </h4>
              <div :class="[
                'p-3 rounded max-h-48 overflow-y-auto text-xs font-mono',
                isDark ? 'bg-gray-900' : 'bg-gray-50'
              ]">
                <div v-for="action in perm.permissions.actions" :key="action" class="mb-1">
                  {{ action }}
                </div>
              </div>
            </div>

            <!-- NotActions -->
            <div>
              <h4 :class="['font-semibold mb-2 flex items-center gap-2', isDark ? 'text-red-300' : 'text-red-700']">
                ❌ NotActions ({{ perm.permissions.notActions.length }})
              </h4>
              <div :class="[
                'p-3 rounded max-h-48 overflow-y-auto text-xs font-mono',
                isDark ? 'bg-gray-900' : 'bg-gray-50'
              ]">
                <div v-for="action in perm.permissions.notActions" :key="action" class="mb-1">
                  {{ action }}
                </div>
                <div v-if="perm.permissions.notActions.length === 0" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  None
                </div>
              </div>
            </div>

            <!-- DataActions -->
            <div>
              <h4 :class="['font-semibold mb-2 flex items-center gap-2', isDark ? 'text-blue-300' : 'text-blue-700']">
                📊 DataActions ({{ perm.permissions.dataActions.length }})
              </h4>
              <div :class="[
                'p-3 rounded max-h-48 overflow-y-auto text-xs font-mono',
                isDark ? 'bg-gray-900' : 'bg-gray-50'
              ]">
                <div v-for="action in perm.permissions.dataActions" :key="action" class="mb-1">
                  {{ action }}
                </div>
                <div v-if="perm.permissions.dataActions.length === 0" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  None
                </div>
              </div>
            </div>

            <!-- NotDataActions -->
            <div>
              <h4 :class="['font-semibold mb-2 flex items-center gap-2', isDark ? 'text-orange-300' : 'text-orange-700']">
                🚫 NotDataActions ({{ perm.permissions.notDataActions.length }})
              </h4>
              <div :class="[
                'p-3 rounded max-h-48 overflow-y-auto text-xs font-mono',
                isDark ? 'bg-gray-900' : 'bg-gray-50'
              ]">
                <div v-for="action in perm.permissions.notDataActions" :key="action" class="mb-1">
                  {{ action }}
                </div>
                <div v-if="perm.permissions.notDataActions.length === 0" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  None
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && effectivePermissions.length === 0 && !error" :class="[
      'text-center py-12 rounded-lg',
      isDark ? 'bg-gray-800' : 'bg-white shadow'
    ]">
      <p class="text-4xl mb-4">🔐</p>
      <h3 :class="['text-xl font-semibold mb-2', isDark ? 'text-gray-200' : 'text-gray-800']">
        No Permissions Analyzed Yet
      </h3>
      <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
        Click "Analyze All Permissions" to scan your resources.
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EffectivePermissionsView',
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
      effectivePermissions: [],
      searchQuery: '',
      filterResourceType: '',
      hasARMToken: true
    };
  },
  computed: {
    uniqueResourceTypes() {
      return new Set(this.effectivePermissions.map(p => p.resourceType)).size;
    },
    uniqueSubscriptions() {
      return new Set(this.effectivePermissions.map(p => p.subscriptionName)).size;
    },
    resourceTypes() {
      return [...new Set(this.effectivePermissions.map(p => p.resourceType))].sort();
    },
    filteredPermissions() {
      let filtered = this.effectivePermissions;

      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(p =>
          p.resourceName.toLowerCase().includes(query) ||
          p.resourceType.toLowerCase().includes(query) ||
          p.resourceGroup.toLowerCase().includes(query)
        );
      }

      if (this.filterResourceType) {
        filtered = filtered.filter(p => p.resourceType === this.filterResourceType);
      }

      return filtered;
    }
  },
  methods: {
    async analyzePermissions() {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get('/api/azure/permissions/effective-all');

        if (response.data.success) {
          this.effectivePermissions = response.data.effectivePermissions;
        } else {
          this.error = response.data.error || 'Failed to analyze permissions';
          
          if (response.data.error && response.data.error.includes('No ARM token')) {
            this.hasARMToken = false;
          }
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message || 'Failed to analyze permissions';
      } finally {
        this.loading = false;
      }
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
    }
  },
  mounted() {
    this.checkARMToken();
  }
};
</script>
