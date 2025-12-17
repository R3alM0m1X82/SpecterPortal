<template>
  <div class="p-8 min-h-screen" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header with Tab Switch -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <h1 class="text-3xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">Users & Groups</h1>
        
        <!-- Tab Switch -->
        <div class="flex rounded-lg p-1" :class="isDark ? 'bg-gray-700' : 'bg-gray-200'">
          <button 
            @click="activeTab = 'users'"
            :class="activeTab === 'users' ? (isDark ? 'bg-gray-600 shadow-sm' : 'bg-white shadow-sm') : (isDark ? 'hover:bg-gray-600' : 'hover:bg-gray-300')"
            class="px-4 py-2 rounded-md text-sm font-medium transition-all"
          >
            <span :class="isDark ? 'text-gray-200' : 'text-gray-700'">👤 Users</span>
          </button>
          <button 
            @click="activeTab = 'groups'"
            :class="activeTab === 'groups' ? (isDark ? 'bg-gray-600 shadow-sm' : 'bg-white shadow-sm') : (isDark ? 'hover:bg-gray-600' : 'hover:bg-gray-300')"
            class="px-4 py-2 rounded-md text-sm font-medium transition-all"
          >
            <span :class="isDark ? 'text-gray-200' : 'text-gray-700'">👥 Groups</span>
          </button>
        </div>
      </div>
      
      <div class="flex items-center space-x-4">
        <!-- Admin Capabilities Badge -->
        <span 
          v-if="hasAdminCapabilities" 
          :class="['px-3 py-1 rounded-full text-xs font-medium', isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800']"
          title="Admin actions available"
        >
          ⚡ Admin Mode
        </span>
        <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">
          {{ activeTab === 'users' ? users.length : groups.length }} {{ activeTab }}
        </span>
        <button 
          @click="openCreateModal" 
          :disabled="!canCreate || checkingPermissions"
          :title="!canCreate ? 'Requires admin privileges (User.ReadWrite.All or Group.ReadWrite.All)' : ''"
          class="btn" 
          :class="canCreate ? (isDark ? 'bg-green-700 text-white hover:bg-green-600' : 'bg-green-600 text-white hover:bg-green-700') : 'bg-gray-400 text-gray-200 cursor-not-allowed'"
        >
          <span v-if="checkingPermissions" class="animate-spin mr-2">⏳</span>
          {{ checkingPermissions ? 'Checking...' : `➕ Create ${activeTab === 'users' ? 'User' : 'Group'}` }}
        </button>
        <button @click="loadData(true)" :disabled="loading" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
          <span v-if="loading" class="animate-spin mr-2">⏳</span>
          {{ loading ? 'Loading...' : '🔄 Refresh' }}
        </button>
        
        <!-- Export Button -->
        <div class="relative">
          <button 
            @click="showExportMenu = !showExportMenu"
            :disabled="(activeTab === 'users' ? users.length : groups.length) === 0"
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
      </div>
    </div>
    
    <!-- Search -->
    <div class="mb-6">
      <input
        v-model="searchQuery"
        @keyup.enter="search"
        @input="onSearchInput"
        type="text"
        :placeholder="activeTab === 'users' ? 'Search users by name or UPN...' : 'Search groups by name...'"
        class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        :class="isDark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900'"
      />
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading {{ activeTab }}...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="rounded-lg p-6 text-center" :class="isDark ? 'bg-red-900/50 border border-red-700' : 'bg-red-50 border border-red-200'">
      <p class="font-semibold" :class="isDark ? 'text-red-300' : 'text-red-600'">{{ error }}</p>
      <button @click="loadData" class="mt-4 btn btn-primary">Retry</button>
    </div>
    
    <!-- Users Table -->
    <div v-else-if="activeTab === 'users' && users.length > 0" class="rounded-lg shadow-md overflow-hidden" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <table class="min-w-full divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
        <thead :class="isDark ? 'bg-gray-750' : 'bg-gray-50'">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Display Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">UPN</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">User Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">On-Prem Sync</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">MFA Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Job Title</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
          <tr v-for="user in users" :key="user.id" :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
            <td class="px-6 py-4 whitespace-nowrap font-medium" :class="isDark ? 'text-white' : 'text-gray-900'">
              <!-- Display Name with Object ID Tooltip -->
              <span 
                :title="`📋 Object ID: ${user.id}`"
                class="cursor-help"
              >
                {{ user.displayName }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ user.userPrincipalName }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ user.mail || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span :class="user.userType === 'Guest' ? (isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800') : (isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800')" 
                    class="px-2 py-1 text-xs font-semibold rounded">
                {{ user.userType || 'Member' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span v-if="user.onPremisesSyncEnabled" class="text-green-500">✓ Yes</span>
              <span v-else :class="isDark ? 'text-gray-500' : 'text-gray-400'">No</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              <span v-if="userMfaStatus[user.id] === undefined" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                <span class="animate-pulse">...</span>
              </span>
              <span v-else-if="userMfaStatus[user.id] === true" 
                    :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'" 
                    class="px-2 py-1 text-xs font-semibold rounded inline-flex items-center">
                🛡️ MFA Enabled
              </span>
              <span v-else-if="userMfaStatus[user.id] === false" 
                    :class="isDark ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800'" 
                    class="px-2 py-1 text-xs font-semibold rounded inline-flex items-center">
                ⚠️ No MFA
              </span>
              <span v-else 
                    :class="isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500'" 
                    class="px-2 py-1 text-xs font-semibold rounded inline-flex items-center"
                    title="Permission required">
                ❓ Unknown
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
              {{ user.jobTitle || 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="user.accountEnabled ? (isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800') : (isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800')" 
                    class="px-2 py-1 text-xs font-semibold rounded-full">
                {{ user.accountEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <!-- Actions Column -->
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex space-x-2">
                <button
                  @click="openAdminModal(user)"
                  class="px-3 py-1 text-sm font-medium rounded-lg transition-colors"
                  :class="isDark ? 'bg-red-900 text-red-300 hover:bg-red-800' : 'bg-red-100 text-red-700 hover:bg-red-200'"
                  title="Admin Actions"
                >
                  ⚡ Actions
                </button>
                <button
                  @click="openOwnedModal(user)"
                  class="px-3 py-1 text-sm font-medium rounded-lg transition-colors"
                  :class="isDark ? 'bg-blue-900 text-blue-300 hover:bg-blue-800' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'"
                  title="View Owned Objects"
                >
                  📦 Owned
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Groups List (Expandable Cards) -->
    <div v-else-if="activeTab === 'groups' && groups.length > 0" class="space-y-4">
      <div 
        v-for="group in groups" 
        :key="group.id" 
        class="rounded-lg shadow-md overflow-hidden border-l-4"
        :class="[
          isDark ? 'bg-gray-800' : 'bg-white',
          group.securityEnabled ? 'border-red-500' : 'border-blue-500'
        ]"
      >
        <!-- Group Header (clickable) -->
        <div 
          @click="toggleGroupExpand(group.id)"
          class="p-4 cursor-pointer"
          :class="isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <span class="text-2xl">👥</span>
                <div>
                  <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-gray-800'">
                    <span :title="`📋 Object ID: ${group.id}`" class="cursor-help">
                      {{ group.displayName }}
                    </span>
                  </h3>
                  <p v-if="group.description" class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                    {{ group.description }}
                  </p>
                </div>
              </div>
            </div>
            
            <div class="flex items-center space-x-3">
              <div class="flex space-x-2">
                <span v-if="group.securityEnabled" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800'">
                  🛡️ Security
                </span>
                <span v-if="group.groupTypes && group.groupTypes.includes('Unified')" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                  📧 M365
                </span>
              </div>
              
              <svg 
                class="w-5 h-5 transition-transform"
                :class="[
                  expandedGroup === group.id ? 'rotate-180' : '',
                  isDark ? 'text-gray-400' : 'text-gray-500'
                ]"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Group Members (expanded) -->
        <div v-if="expandedGroup === group.id" class="border-t" :class="isDark ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'">
          <div class="p-4">
            <!-- Loading Members -->
            <div v-if="loadingMembers[group.id]" class="text-center py-8">
              <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              <p class="mt-2" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading members...</p>
            </div>
            
            <!-- Member Error -->
            <div v-else-if="memberErrors[group.id]" class="text-center py-8">
              <p class="text-red-500">{{ memberErrors[group.id] }}</p>
              <button @click="loadGroupMembers(group.id)" class="mt-4 btn btn-primary">Retry</button>
            </div>
            
            <!-- Members List -->
            <div v-else-if="groupMembers[group.id] && groupMembers[group.id].length > 0" class="space-y-2">
              <h4 class="font-semibold mb-3" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Members ({{ groupMembers[group.id].length }})
              </h4>
              <div 
                v-for="member in groupMembers[group.id]" 
                :key="member.id"
                class="flex items-center justify-between p-3 rounded-lg"
                :class="isDark ? 'bg-gray-700' : 'bg-white'"
              >
                <div class="flex items-center space-x-3">
                  <span class="text-xl">{{ getMemberIcon(member.type) }}</span>
                  <div>
                    <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                      {{ member.displayName }}
                    </p>
                    <p v-if="member.userPrincipalName" class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                      {{ member.userPrincipalName }}
                    </p>
                  </div>
                </div>
                <span class="px-2 py-1 text-xs font-semibold rounded" :class="getMemberTypeClass(member.type)">
                  {{ member.type }}
                </span>
              </div>
            </div>
            
            <!-- No Members -->
            <div v-else class="text-center py-8">
              <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">No members</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="!loading && !error" class="text-center py-12 rounded-lg shadow-md" :class="isDark ? 'bg-gray-800' : 'bg-white'">
      <div class="text-6xl mb-4">{{ activeTab === 'users' ? '👤' : '👥' }}</div>
      <h2 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-gray-100' : 'text-gray-800'">
        No {{ activeTab }} found
      </h2>
      <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">
        {{ searchQuery ? 'Try a different search' : 'Get started by creating a new ' + (activeTab === 'users' ? 'user' : 'group') }}
      </p>
    </div>
    
    <!-- Create Modal (Sprint 5.1) -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="closeCreateModal">
      <div class="rounded-lg shadow-xl max-w-2xl w-full" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <h2 class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
            {{ activeTab === 'users' ? '➕ Create User' : '➕ Create Group' }}
          </h2>
          <button @click="closeCreateModal" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Body -->
        <div class="p-6">
          <!-- User Form -->
          <div v-if="activeTab === 'users'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Display Name <span class="text-red-500">*</span>
              </label>
              <input
                v-model="createForm.displayName"
                type="text"
                placeholder="John Doe"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                User Principal Name <span class="text-red-500">*</span>
              </label>
              <input
                v-model="createForm.userPrincipalName"
                type="text"
                placeholder="john.doe@domain.com"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Password <span class="text-red-500">*</span>
              </label>
              <input
                v-model="createForm.password"
                type="password"
                placeholder="Minimum 8 characters"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Job Title
              </label>
              <input
                v-model="createForm.jobTitle"
                type="text"
                placeholder="Software Engineer"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Department
              </label>
              <input
                v-model="createForm.department"
                type="text"
                placeholder="Engineering"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                v-model="createForm.accountEnabled"
                type="checkbox"
                id="accountEnabled"
                class="rounded"
              />
              <label for="accountEnabled" class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Account Enabled
              </label>
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                v-model="createForm.forceChangePassword"
                type="checkbox"
                id="forceChangePassword"
                class="rounded"
              />
              <label for="forceChangePassword" class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Force Password Change on First Login
              </label>
            </div>
          </div>
          
          <!-- Group Form -->
          <div v-else class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Display Name <span class="text-red-500">*</span>
              </label>
              <input
                v-model="createForm.displayName"
                type="text"
                placeholder="Engineering Team"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Description
              </label>
              <textarea
                v-model="createForm.description"
                placeholder="Group description"
                rows="3"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Mail Nickname
              </label>
              <input
                v-model="createForm.mailNickname"
                type="text"
                placeholder="engineering-team"
                class="w-full px-3 py-2 border rounded-lg"
                :class="isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
              />
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                v-model="createForm.securityEnabled"
                type="checkbox"
                id="securityEnabled"
                class="rounded"
              />
              <label for="securityEnabled" class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Security Enabled
              </label>
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                v-model="createForm.mailEnabled"
                type="checkbox"
                id="mailEnabled"
                class="rounded"
              />
              <label for="mailEnabled" class="text-sm" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
                Mail Enabled (M365 Group)
              </label>
            </div>
          </div>
          
          <!-- Error Message -->
          <div v-if="createError" class="p-3 rounded-lg" :class="isDark ? 'bg-red-900/50 text-red-300' : 'bg-red-50 text-red-600'">
            {{ createError }}
          </div>
          
          <!-- Success Message -->
          <div v-if="createSuccess" class="p-3 rounded-lg" :class="isDark ? 'bg-green-900/50 text-green-300' : 'bg-green-50 text-green-600'">
            {{ createSuccess }}
          </div>
        </div>
        
        <!-- Modal Footer -->
        <div class="flex items-center justify-end space-x-3 p-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <button @click="closeCreateModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            Cancel
          </button>
          <button 
            @click="handleCreate" 
            :disabled="creatingEntity"
            class="btn bg-green-600 text-white hover:bg-green-700"
          >
            <span v-if="creatingEntity" class="animate-spin mr-2">⏳</span>
            {{ creatingEntity ? 'Creating...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Owned Objects Modal (Sprint 5.1) -->
    <div v-if="showOwnedModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="closeOwnedModal">
      <div class="rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" :class="isDark ? 'bg-gray-800' : 'bg-white'">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <h2 class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-gray-800'">
            📦 Owned Objects - {{ selectedUserForOwned?.displayName }}
          </h2>
          <button @click="closeOwnedModal" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Body -->
        <div class="p-6">
          <!-- Loading -->
          <div v-if="loadingOwned" class="text-center py-12">
            <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p class="mt-4" :class="isDark ? 'text-gray-400' : 'text-gray-500'">Loading owned objects...</p>
          </div>
          
          <!-- Error -->
          <div v-else-if="ownedError" class="text-center py-12">
            <p class="text-red-500">{{ ownedError }}</p>
            <button @click="loadOwnedObjects" class="mt-4 btn btn-primary">Retry</button>
          </div>
          
          <!-- Owned Objects -->
          <div v-else-if="ownedObjects" class="space-y-6">
            <!-- Summary -->
            <div class="grid grid-cols-4 gap-4">
              <div class="p-4 rounded-lg" :class="isDark ? 'bg-blue-900/20' : 'bg-blue-50'">
                <div class="text-2xl font-bold" :class="isDark ? 'text-blue-300' : 'text-blue-600'">
                  {{ ownedObjects.counts.applications }}
                </div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Applications</div>
              </div>
              <div class="p-4 rounded-lg" :class="isDark ? 'bg-green-900/20' : 'bg-green-50'">
                <div class="text-2xl font-bold" :class="isDark ? 'text-green-300' : 'text-green-600'">
                  {{ ownedObjects.counts.groups }}
                </div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Groups</div>
              </div>
              <div class="p-4 rounded-lg" :class="isDark ? 'bg-purple-900/20' : 'bg-purple-50'">
                <div class="text-2xl font-bold" :class="isDark ? 'text-purple-300' : 'text-purple-600'">
                  {{ ownedObjects.counts.servicePrincipals }}
                </div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Service Principals</div>
              </div>
              <div class="p-4 rounded-lg" :class="isDark ? 'bg-orange-900/20' : 'bg-orange-50'">
                <div class="text-2xl font-bold" :class="isDark ? 'text-orange-300' : 'text-orange-600'">
                  {{ ownedObjects.counts.devices }}
                </div>
                <div class="text-sm" :class="isDark ? 'text-gray-400' : 'text-gray-600'">Devices</div>
              </div>
            </div>
            
            <!-- Applications -->
            <div v-if="ownedObjects.ownedObjects.applications.length > 0">
              <h3 class="text-lg font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">
                🏢 Applications ({{ ownedObjects.ownedObjects.applications.length }})
              </h3>
              <div class="space-y-2">
                <div 
                  v-for="app in ownedObjects.ownedObjects.applications" 
                  :key="app.id"
                  class="p-3 rounded-lg"
                  :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ app.displayName }}
                      </p>
                      <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        App ID: {{ app.appId }}
                      </p>
                    </div>
                    <span class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                      {{ app.signInAudience }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Groups -->
            <div v-if="ownedObjects.ownedObjects.groups.length > 0">
              <h3 class="text-lg font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">
                👥 Groups ({{ ownedObjects.ownedObjects.groups.length }})
              </h3>
              <div class="space-y-2">
                <div 
                  v-for="group in ownedObjects.ownedObjects.groups" 
                  :key="group.id"
                  class="p-3 rounded-lg"
                  :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ group.displayName }}
                      </p>
                      <p v-if="group.description" class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        {{ group.description }}
                      </p>
                    </div>
                    <div class="flex gap-1">
                      <span v-if="group.securityEnabled" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-800'">
                        Security
                      </span>
                      <span v-if="group.groupTypes && group.groupTypes.includes('Unified')" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'">
                        M365
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Service Principals -->
            <div v-if="ownedObjects.ownedObjects.servicePrincipals.length > 0">
              <h3 class="text-lg font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">
                🤖 Service Principals ({{ ownedObjects.ownedObjects.servicePrincipals.length }})
              </h3>
              <div class="space-y-2">
                <div 
                  v-for="sp in ownedObjects.ownedObjects.servicePrincipals" 
                  :key="sp.id"
                  class="p-3 rounded-lg"
                  :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
                >
                  <div>
                    <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                      {{ sp.displayName }}
                    </p>
                    <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                      App ID: {{ sp.appId }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Devices -->
            <div v-if="ownedObjects.ownedObjects.devices.length > 0">
              <h3 class="text-lg font-semibold mb-3" :class="isDark ? 'text-white' : 'text-gray-800'">
                💻 Devices ({{ ownedObjects.ownedObjects.devices.length }})
              </h3>
              <div class="space-y-2">
                <div 
                  v-for="device in ownedObjects.ownedObjects.devices" 
                  :key="device.id"
                  class="p-3 rounded-lg"
                  :class="isDark ? 'bg-gray-700' : 'bg-gray-100'"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium" :class="isDark ? 'text-white' : 'text-gray-800'">
                        {{ device.displayName }}
                      </p>
                      <p class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        {{ device.operatingSystem }} {{ device.operatingSystemVersion }}
                      </p>
                    </div>
                    <span v-if="device.isCompliant" class="px-2 py-1 text-xs font-semibold rounded" :class="isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'">
                      Compliant
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- No Owned Objects -->
            <div v-if="ownedObjects.counts.total === 0" class="text-center py-12">
              <div class="text-6xl mb-4">📦</div>
              <p class="text-lg" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                No owned objects found
              </p>
            </div>
          </div>
        </div>
        
        <!-- Modal Footer -->
        <div class="flex items-center justify-end p-6 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <button @click="closeOwnedModal" class="btn" :class="isDark ? 'btn-secondary-dark' : 'btn-secondary'">
            Close
          </button>
        </div>
      </div>
    </div>
  
    <!-- Admin Actions Modal (Sprint 4.2-4.5) - RIPRISTINATO -->
    <AdminActionsModal
      :isOpen="showAdminModal"
      :user="selectedUser"
      :accessToken="activeAccessToken"
      :isDark="isDark"
      @close="showAdminModal = false"
      @action-completed="onAdminActionCompleted"
      @token-exchanged="onTokenExchanged"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, defineProps, computed } from 'vue'
import AdminActionsModal from '../components/AdminActionsModal.vue'
import { tokenAPI, adminAPI } from '../services/api'

// Props
const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const isDark = computed(() => props.isDark)

const activeTab = ref('users')
const users = ref([])
const groups = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

// Cache refs (5 minutes TTL)
const usersCache = ref({ data: null, timestamp: null })
const groupsCache = ref({ data: null, timestamp: null })
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes
const showExportMenu = ref(false)

// Group expansion state
const expandedGroup = ref(null)
const groupMembers = ref({})
const loadingMembers = ref({})
const memberErrors = ref({})

// Admin Actions state
const showAdminModal = ref(false)
const selectedUser = ref(null)
const activeAccessToken = ref(null)

// Current token info (for admin role detection)
const currentTokenInfo = ref(null)

// Admin role WIDs for badge visibility
const ADMIN_ROLE_WIDS = [
  '62e90394-69f5-4237-9190-012177145e10', // Global Administrator
  '194ae4cb-b126-40b2-bd5b-6091b380977d', // Security Administrator
  'fe930be7-5e62-47db-91af-98c3a49a38b1', // User Administrator
  '729827e3-9c14-49f7-bb1b-9608f156bbb8', // Helpdesk Administrator
  '9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3', // Application Administrator
  'c4e39bd9-1100-46d3-8c65-fb160da0071f', // Authentication Administrator
  '158c047a-c907-4556-b7ef-446551a6b5f7', // Cloud Application Administrator
  'e8611ab8-c189-46e8-94e1-60213ab1f814', // Privileged Role Administrator
]

// Admin capabilities: show badge ONLY if token has admin roles
const hasAdminCapabilities = computed(() => {
  if (!currentTokenInfo.value || !currentTokenInfo.value.roles) {
    return false
  }
  return currentTokenInfo.value.roles.some(roleWid => ADMIN_ROLE_WIDS.includes(roleWid))
})

// MFA Status tracking
const userMfaStatus = ref({})

// Create permissions (Sprint 5.1)
const canCreateUsers = ref(false)
const canCreateGroups = ref(false)
const checkingPermissions = ref(false)

// Create Modal state (Sprint 5.1)
const showCreateModal = ref(false)
const createForm = ref({
  displayName: '',
  userPrincipalName: '',
  password: '',
  jobTitle: '',
  department: '',
  accountEnabled: true,
  forceChangePassword: true,
  description: '',
  mailNickname: '',
  securityEnabled: true,
  mailEnabled: false
})
const creatingEntity = ref(false)
const createError = ref(null)
const createSuccess = ref(null)

// Owned Objects Modal state (Sprint 5.1)
const showOwnedModal = ref(false)
const selectedUserForOwned = ref(null)
const loadingOwned = ref(false)
const ownedError = ref(null)
const ownedObjects = ref(null)

// Load active token for admin actions
const loadActiveToken = async () => {
  try {
    const tokenResponse = await tokenAPI.getActive()
    console.log('[Admin] Token API response:', tokenResponse.data)
    if (tokenResponse.data.success && tokenResponse.data.token) {
      const token = tokenResponse.data.token.access_token
      console.log('[Admin] Token length:', token ? token.length : 0)
      console.log('[Admin] Token preview:', token ? token.substring(0, 100) + '...' : 'null')
      activeAccessToken.value = token
      console.log('[Admin] Active token loaded, stored length:', activeAccessToken.value ? activeAccessToken.value.length : 0)
      
      // Load current token info with roles for admin badge
      await loadCurrentTokenInfo()
      
      // Check create permissions after loading token
      await checkCreatePermissions()
    } else {
      console.warn('[Admin] No active token found')
    }
  } catch (err) {
    console.warn('[Admin] Could not load active token:', err.message)
  }
}

// Load current token info (for admin role detection)
const loadCurrentTokenInfo = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/auth/verify')
    const data = await response.json()
    if (data) {
      currentTokenInfo.value = data
      console.log('[Admin] Token roles:', data.roles)
    }
  } catch (err) {
    console.warn('[Admin] Could not load token info:', err.message)
  }
}

// Check create permissions (Sprint 5.1)
const checkCreatePermissions = async () => {
  if (!activeAccessToken.value) return
  
  checkingPermissions.value = true
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/check-create-permissions', {
      headers: {
        'Authorization': `Bearer ${activeAccessToken.value}`
      }
    })
    const data = await response.json()
    
    if (data.success) {
      canCreateUsers.value = data.canCreateUsers || false
      canCreateGroups.value = data.canCreateGroups || false
      console.log('[Permissions] Create capabilities:', { users: canCreateUsers.value, groups: canCreateGroups.value })
    }
  } catch (err) {
    console.warn('[Permissions] Could not check create permissions:', err.message)
    // Assume no permissions on error
    canCreateUsers.value = false
    canCreateGroups.value = false
  } finally {
    checkingPermissions.value = false
  }
}

// Computed property for Create button state (Sprint 5.1)
const canCreate = computed(() => {
  return activeTab.value === 'users' ? canCreateUsers.value : canCreateGroups.value
})

// Open admin modal for a user
const openAdminModal = async (user) => {
  // Ensure we have a fresh token
  if (!activeAccessToken.value) {
    await loadActiveToken()
  }
  console.log('[Admin] Opening modal for user:', user.displayName)
  console.log('[Admin] Token to pass, length:', activeAccessToken.value ? activeAccessToken.value.length : 0)
  selectedUser.value = user
  showAdminModal.value = true
}

// Handle admin action completion
const onAdminActionCompleted = (data) => {
  console.log('Admin action completed:', data)
  // Optionally refresh user list or show notification
}

// Handle token exchange from modal
const onTokenExchanged = async (data) => {
  console.log('[TokenExchange] New token received, ID:', data.token_id)
  console.log('[TokenExchange] New token length:', data.access_token ? data.access_token.length : 0)
  console.log('[TokenExchange] Token capabilities:', data.capabilities)
  
  // CRITICAL: Only update activeAccessToken if this is a TAP/MFA token
  // Password Reset tokens (FOCI) are ONLY for AdminActionsModal and don't have MFA scopes
  // Check if token has UserAuthenticationMethod.ReadWrite.All scope
  const hasMfaScopes = data.capabilities?.scopes?.includes('UserAuthenticationMethod.ReadWrite.All')
  
  if (hasMfaScopes) {
    console.log('[TokenExchange] Token has MFA scopes, updating activeAccessToken')
    activeAccessToken.value = data.access_token
    
    // Refresh MFA status with new token
    if (users.value && users.value.length > 0) {
      console.log('[TokenExchange] Refreshing MFA status for', users.value.length, 'users')
      await loadUsersMfaStatus(users.value)
    }
  } else {
    console.log('[TokenExchange] Password Reset token (no MFA scopes), keeping original activeAccessToken')
    // Do NOT update activeAccessToken - this is a password reset token only
    // AdminActionsModal will handle it internally
  }
}

// Open Create Modal (Sprint 5.1)
const openCreateModal = () => {
  // Reset form
  createForm.value = {
    displayName: '',
    userPrincipalName: '',
    password: '',
    jobTitle: '',
    department: '',
    accountEnabled: true,
    forceChangePassword: true,
    description: '',
    mailNickname: '',
    securityEnabled: true,
    mailEnabled: false
  }
  createError.value = null
  createSuccess.value = null
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  createForm.value = {}
  createError.value = null
  createSuccess.value = null
}

// Handle Create User/Group (Sprint 5.1)
const handleCreate = async () => {
  createError.value = null
  createSuccess.value = null
  
  // Validate
  if (!createForm.value.displayName) {
    createError.value = 'Display Name is required'
    return
  }
  
  if (activeTab.value === 'users') {
    if (!createForm.value.userPrincipalName || !createForm.value.password) {
      createError.value = 'UPN and Password are required'
      return
    }
  }
  
  creatingEntity.value = true
  
  try {
    const endpoint = activeTab.value === 'users' ? '/api/tenant/users' : '/api/tenant/groups'
    const payload = activeTab.value === 'users' 
      ? {
          displayName: createForm.value.displayName,
          userPrincipalName: createForm.value.userPrincipalName,
          password: createForm.value.password,
          jobTitle: createForm.value.jobTitle,
          department: createForm.value.department,
          accountEnabled: createForm.value.accountEnabled,
          forceChangePassword: createForm.value.forceChangePassword
        }
      : {
          displayName: createForm.value.displayName,
          description: createForm.value.description,
          mailNickname: createForm.value.mailNickname,
          securityEnabled: createForm.value.securityEnabled,
          mailEnabled: createForm.value.mailEnabled
        }
    
    const response = await fetch(`http://localhost:5000${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${activeAccessToken.value}`
      },
      body: JSON.stringify(payload)
    })
    
    const data = await response.json()
    
    if (data.success) {
      createSuccess.value = data.message
      // Refresh list after 1 second
      setTimeout(() => {
        closeCreateModal()
        loadData()
      }, 1500)
    } else {
      // Check if it's a 403 permission error
      if (response.status === 403 || (data.error && data.error.includes('403'))) {
        createError.value = '⚠️ Insufficient privileges. You need admin permissions to create users/groups. Please use Device Code Flow in Token Management to authenticate as an admin.'
      } else {
        createError.value = data.error || data.details || 'Failed to create'
      }
    }
  } catch (err) {
    createError.value = 'Network error: ' + err.message
  } finally {
    creatingEntity.value = false
  }
}

// Open Owned Objects Modal (Sprint 5.1)
const openOwnedModal = async (user) => {
  selectedUserForOwned.value = user
  showOwnedModal.value = true
  await loadOwnedObjects()
}

const closeOwnedModal = () => {
  showOwnedModal.value = false
  selectedUserForOwned.value = null
  ownedObjects.value = null
  ownedError.value = null
}

// Load Owned Objects (Sprint 5.1)
const loadOwnedObjects = async () => {
  loadingOwned.value = true
  ownedError.value = null
  ownedObjects.value = null
  
  // Ensure we have active token
  if (!activeAccessToken.value) {
    await loadActiveToken()
  }
  
  if (!selectedUserForOwned.value?.id) {
    ownedError.value = 'No user selected'
    loadingOwned.value = false
    return
  }
  
  try {
    const response = await fetch(`http://localhost:5000/api/tenant/owned-objects?user_id=${selectedUserForOwned.value.id}`, {
      headers: {
        'Authorization': `Bearer ${activeAccessToken.value}`
      }
    })
    const data = await response.json()
    
    if (data.success) {
      ownedObjects.value = data
    } else {
      // Check if it's a 403 permission error
      if (response.status === 403 || (data.error && data.error.includes('403'))) {
        ownedError.value = '⚠️ Insufficient privileges to view owned objects of other users. This requires User.Read.All or Directory.Read.All scope.'
      } else {
        ownedError.value = data.error || 'Failed to load owned objects'
      }
    }
  } catch (err) {
    ownedError.value = 'Failed to load owned objects: ' + err.message
  } finally {
    loadingOwned.value = false
  }
}

// Check if cache is valid
const isCacheValid = (cache) => {
  if (!cache.data || !cache.timestamp) return false
  return (Date.now() - cache.timestamp) < CACHE_TTL
}

// Load data based on active tab
const loadData = async (forceRefresh = false) => {
  if (activeTab.value === 'users') {
    await loadUsers(forceRefresh)
  } else {
    await loadGroups(forceRefresh)
  }
}

// Load MFA status for all users in batch
const loadUsersMfaStatus = async (userList) => {
  if (!userList || userList.length === 0) return
  
  // Ensure we have active token
  if (!activeAccessToken.value) {
    await loadActiveToken()
  }
  
  // Skip if still no token
  if (!activeAccessToken.value) {
    console.warn('No active token available for MFA batch check')
    return
  }
  
  try {
    const userIds = userList.map(u => u.id)
    
    const response = await fetch('http://localhost:5000/api/tenant/users/mfa-batch', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${activeAccessToken.value}`
      },
      body: JSON.stringify({ userIds })
    })
    
    const data = await response.json()
    
    if (data.success && data.results) {
      // Update MFA status for each user
      for (const [userId, mfaData] of Object.entries(data.results)) {
        userMfaStatus.value[userId] = mfaData.mfaEnabled
      }
    }
  } catch (err) {
    console.warn('Failed to load MFA status:', err)
    // Don't show error to user, just leave MFA status unknown
  }
}

const loadUsers = async (forceRefresh = false) => {
  loading.value = true
  error.value = null
  
  // Check cache first (unless force refresh)
  if (!forceRefresh && isCacheValid(usersCache.value)) {
    console.log('[CACHE] Using cached users')
    users.value = usersCache.value.data
    loading.value = false
    return
  }
  
  console.log('[API] Fetching users', forceRefresh ? '(forced)' : '')
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/users')
    const data = await response.json()
    
    if (data.success) {
      users.value = data.users
      usersCache.value = { data: data.users, timestamp: Date.now() }
      console.log('[CACHE] Users cached:', data.users.length, 'items')
      // Load MFA status in background
      loadUsersMfaStatus(data.users)
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load users'
  } finally {
    loading.value = false
  }
}

const loadGroups = async (forceRefresh = false) => {
  loading.value = true
  error.value = null
  
  // Check cache first (unless force refresh)
  if (!forceRefresh && isCacheValid(groupsCache.value)) {
    console.log('[CACHE] Using cached groups')
    groups.value = groupsCache.value.data
    loading.value = false
    return
  }
  
  console.log('[API] Fetching groups', forceRefresh ? '(forced)' : '')
  
  try {
    const response = await fetch('http://localhost:5000/api/tenant/groups')
    const data = await response.json()
    
    if (data.success) {
      groups.value = data.groups
      groupsCache.value = { data: data.groups, timestamp: Date.now() }
      console.log('[CACHE] Groups cached:', data.groups.length, 'items')
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load groups'
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
    
    if (activeTab.value === 'users') {
      data = users.value
      filename = `users-${new Date().toISOString().split('T')[0]}.${format}`
    } else {
      data = groups.value
      filename = `groups-${new Date().toISOString().split('T')[0]}.${format}`
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

const toggleGroupExpand = async (groupId) => {
  if (expandedGroup.value === groupId) {
    expandedGroup.value = null
    return
  }
  
  expandedGroup.value = groupId
  
  // Load members if not already loaded
  if (!groupMembers.value[groupId] && !loadingMembers.value[groupId]) {
    await loadGroupMembers(groupId)
  }
}

const loadGroupMembers = async (groupId) => {
  loadingMembers.value[groupId] = true
  memberErrors.value[groupId] = null
  
  try {
    const response = await fetch(`http://localhost:5000/api/tenant/groups/${groupId}/members`)
    const data = await response.json()
    
    if (data.success) {
      groupMembers.value[groupId] = data.members || []
    } else {
      memberErrors.value[groupId] = data.error || 'Failed to load members'
    }
  } catch (err) {
    memberErrors.value[groupId] = 'Failed to load members: ' + err.message
  } finally {
    loadingMembers.value[groupId] = false
  }
}

const getMemberIcon = (type) => {
  switch (type) {
    case 'user':
      return '👤'
    case 'group':
      return '👥'
    case 'device':
      return '💻'
    case 'servicePrincipal':
      return '🤖'
    default:
      return '❓'
  }
}

const getMemberTypeClass = (type) => {
  switch (type) {
    case 'user':
      return props.isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
    case 'group':
      return props.isDark ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'
    case 'device':
      return props.isDark ? 'bg-orange-900 text-orange-300' : 'bg-orange-100 text-orange-800'
    case 'servicePrincipal':
      return props.isDark ? 'bg-purple-900 text-purple-300' : 'bg-purple-100 text-purple-800'
    default:
      return props.isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'
  }
}

const search = async () => {
  if (!searchQuery.value.trim()) {
    loadData()
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    if (activeTab.value === 'users') {
      const response = await fetch(
        `http://localhost:5000/api/tenant/users/search?q=${encodeURIComponent(searchQuery.value)}`
      )
      const data = await response.json()
      
      if (data.success) {
        users.value = data.users
        // Load MFA status in background
        loadUsersMfaStatus(data.users)
      } else {
        error.value = data.error
      }
    } else {
      const response = await fetch(
        `http://localhost:5000/api/tenant/groups/search?q=${encodeURIComponent(searchQuery.value)}`
      )
      const data = await response.json()
      
      if (data.success) {
        groups.value = data.groups
      } else {
        error.value = data.error
      }
    }
  } catch (err) {
    error.value = 'Search failed'
  } finally {
    loading.value = false
  }
}

const onSearchInput = () => {
  if (!searchQuery.value.trim()) {
    loadData()
  }
}

// Watch tab changes
watch(activeTab, () => {
  searchQuery.value = ''
  expandedGroup.value = null  // Reset expanded group when switching tabs
  loadData()
})

onMounted(() => {
  loadUsers()
  loadGroups()
  loadActiveToken()
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
