/**
 * useTheme - Global theme composable for SpecterPortal
 * Manages dark/light mode across the entire application
 */
import { ref, watch } from 'vue'

// Global reactive state (singleton pattern)
const isDark = ref(false)

// Initialize from localStorage on first load
const savedTheme = localStorage.getItem('tbres-spy-theme')
if (savedTheme === 'dark') {
  isDark.value = true
  document.documentElement.classList.add('dark')
}

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  const setTheme = (dark) => {
    isDark.value = dark
  }

  // Watch for changes and persist
  watch(isDark, (newValue) => {
    localStorage.setItem('tbres-spy-theme', newValue ? 'dark' : 'light')
    
    if (newValue) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  })

  return {
    isDark,
    toggleTheme,
    setTheme
  }
}
