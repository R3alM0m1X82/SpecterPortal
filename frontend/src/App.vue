<template>
  <div 
    id="app" 
    class="flex h-screen transition-colors duration-300"
    :class="isDark ? 'bg-gray-900' : 'bg-gray-50'"
  >
    <!-- Sidebar - Hidden on login page -->
    <Sidebar v-if="!isLoginPage" :isDark="isDark" />
    
    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Navbar - Hidden on login page -->
      <div 
        v-if="!isLoginPage" 
        class="h-14 shadow-sm flex items-center justify-end px-6 transition-colors duration-300"
        :class="isDark ? 'bg-gray-800 border-b border-gray-700' : 'bg-white border-b border-gray-200'"
      >
        <!-- Theme Toggle Button -->
        <button 
          @click="toggleTheme"
          class="p-2 rounded-lg transition-all duration-300 hover:scale-110"
          :class="isDark 
            ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400' 
            : 'bg-gray-100 hover:bg-gray-200 text-gray-600'"
          :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          <span class="text-lg">{{ isDark ? '☀️' : '🌙' }}</span>
        </button>
      </div>
      
      <!-- Main Content -->
      <div class="flex-1 overflow-auto">
        <router-view v-slot="{ Component }">
          <keep-alive include="EmailsView,FilesView">
            <component :is="Component" :isDark="isDark" />
          </keep-alive>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { useTheme } from './composables/useTheme'

const route = useRoute()
const { isDark, toggleTheme } = useTheme()

// Hide sidebar and navbar on login page
const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
/* Global dark mode transitions */
* {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* Scrollbar styling for dark mode */
.dark ::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.dark ::-webkit-scrollbar-track {
  background: #1f2937;
}

.dark ::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>
