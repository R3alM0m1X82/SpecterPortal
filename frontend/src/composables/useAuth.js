/**
 * Authentication composable for SpecterPortal
 * Manages auth state and API calls
 */
import { ref, computed } from 'vue'

const isAuthenticated = ref(false)
const user = ref(null)
const loading = ref(true)

export function useAuth() {
  /**
   * Check if user is authenticated
   */
  const checkAuth = async () => {
    loading.value = true
    
    try {
      const response = await fetch('http://localhost:5000/api/auth/verify', {
        credentials: 'include'
      })
      
      const data = await response.json()
      
      if (data.success && data.authenticated) {
        isAuthenticated.value = true
        user.value = data.user
      } else {
        isAuthenticated.value = false
        user.value = null
        // Clear local storage if session is invalid
        localStorage.removeItem('specter_auth')
        sessionStorage.removeItem('specter_auth')
      }
    } catch (err) {
      console.error('Auth check failed:', err)
      isAuthenticated.value = false
      user.value = null
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Logout user
   */
  const logout = async () => {
    try {
      await fetch('http://localhost:5000/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('Logout failed:', err)
    } finally {
      isAuthenticated.value = false
      user.value = null
      localStorage.removeItem('specter_auth')
      sessionStorage.removeItem('specter_auth')
    }
  }
  
  /**
   * Check if user was previously authenticated (from storage)
   */
  const hasStoredAuth = () => {
    return !!(localStorage.getItem('specter_auth') || sessionStorage.getItem('specter_auth'))
  }
  
  return {
    isAuthenticated: computed(() => isAuthenticated.value),
    user: computed(() => user.value),
    loading: computed(() => loading.value),
    checkAuth,
    logout,
    hasStoredAuth
  }
}
