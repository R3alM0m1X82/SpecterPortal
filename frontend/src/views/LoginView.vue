<template>
  <div class="login-container">
    <!-- Left Side - Branding -->
    <div class="brand-section">
      <div class="cyber-grid"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      
      <div class="brand-content">
        <div class="logo-wrapper">
          <img src="/logo.png" alt="SpecterPortal" class="logo-image">
        </div>
        
        <div class="tagline">POST-EXPLOITATION FRAMEWORK</div>
        
        <div class="acronym-subtitle">
          Security Platform for Entra Cloud Token Enumeration & Reconnaissance
        </div>
        
        <div class="author-badge">
          <div class="author-icon">R</div>
          <div class="author-text">by r3alm0m1x82 • safebreach.it</div>
        </div>
      </div>
    </div>

    <!-- Right Side - Login Form -->
    <div class="form-section">
      <div class="form-container">
        <div class="form-header">
          <h2 class="form-title">
            <span class="title-specter">Specter</span><span class="title-portal">Portal</span>
          </h2>
          <p class="form-subtitle">Enter your API key to continue</p>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label class="form-label">API Key</label>
            <div class="input-wrapper">
              <input 
                v-model="apiKey"
                type="password" 
                class="form-input" 
                placeholder="••••••••••••••••••••"
                :disabled="loading"
                autofocus
              >
              <span class="input-icon">🔑</span>
            </div>
          </div>

          <div class="remember-group">
            <input v-model="remember" type="checkbox" class="checkbox-custom" id="remember">
            <label for="remember" class="checkbox-label">Remember me for 30 days</label>
          </div>

          <div v-if="error" class="error-message">
            <span class="error-icon">⚠️</span>
            <span>{{ error }}</span>
          </div>

          <button type="submit" class="submit-button" :disabled="loading || !apiKey">
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>Access Portal</span>
          </button>
        </form>

        <div class="version-footer">
          <span class="version-badge">
            <span>⚡</span>
            <span>SpecterPortal v.2.0</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const apiKey = ref('')
const remember = ref(false)
const loading = ref(false)
const error = ref(null)

const handleLogin = async () => {
  if (!apiKey.value) return
  
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        username: 'admin',
        api_key: apiKey.value,
        remember: remember.value
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      if (remember.value) {
        localStorage.setItem('specter_auth', 'true')
      } else {
        sessionStorage.setItem('specter_auth', 'true')
      }
      
      router.push('/')
    } else {
      error.value = data.error || 'Authentication failed'
    }
  } catch (err) {
    error.value = 'Connection error. Please check if backend is running.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.login-container {
  position: fixed;
  inset: 0;
  display: flex;
  background: #0a0e1a;
  z-index: 9999;
}

/* Left Side - Logo & Branding */
.brand-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: linear-gradient(135deg, #0a0e1a 0%, #1a1035 50%, #0f1423 100%);
  position: relative;
  overflow: hidden;
}

/* Animated grid background */
.cyber-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(139, 92, 246, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(139, 92, 246, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: grid-move 30s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(60px, 60px); }
}

/* Glowing orbs */
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.25;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #8b5cf6, transparent);
  top: -250px;
  left: -200px;
  animation-delay: 0s;
}

.orb-2 {
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, #a78bfa, transparent);
  bottom: -200px;
  right: -150px;
  animation-delay: 7s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(50px, -50px) scale(1.1); }
  66% { transform: translate(-30px, 30px) scale(0.9); }
}

.brand-content {
  position: relative;
  z-index: 10;
  text-align: center;
  max-width: 1400px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100%;
}

.logo-wrapper {
  margin-bottom: 25px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo-image {
  position: relative;
  width: 1600px;
  height: auto;
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  animation: logo-appear 1s ease-out;
}

@keyframes logo-appear {
  from { opacity: 0; transform: scale(0.95) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.tagline {
  margin-top: 20px;
  font-size: 28px;
  color: #ffffff;
  letter-spacing: 4px;
  text-transform: uppercase;
  font-weight: 700;
  animation: fade-in 1s ease-out 0.3s both;
}

.acronym-subtitle {
  margin-top: 14px;
  font-size: 20px;
  color: #8b5cf6;
  letter-spacing: 2px;
  font-weight: 600;
  line-height: 1.6;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  animation: fade-in 1s ease-out 0.45s both;
}

.author-badge {
  margin-top: 30px;
  padding: 10px 20px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 100px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  align-self: center;
  animation: fade-in 1s ease-out 0.9s both;
}

.author-icon {
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  font-weight: bold;
}

.author-text {
  font-size: 12px;
  color: #94a3b8;
  letter-spacing: 0.5px;
  font-weight: 400;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Right Side - Login Form */
.form-section {
  width: 540px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: #0f1419;
  box-shadow: -20px 0 40px rgba(0, 0, 0, 0.5);
  position: relative;
}

.form-container {
  width: 100%;
  max-width: 420px;
  animation: slide-in 0.8s ease-out;
}

@keyframes slide-in {
  from { opacity: 0; transform: translateX(30px); }
  to { opacity: 1; transform: translateX(0); }
}

.form-header {
  margin-bottom: 40px;
}

.form-title {
  font-size: 44px;
  font-weight: 700;
  margin-bottom: 10px;
  letter-spacing: 2px;
}

.title-specter {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-portal {
  color: #e2e8f0;
}

.form-subtitle {
  font-size: 16px;
  color: #64748b;
  letter-spacing: 0.5px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 15px;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 16px 50px 16px 18px;
  background: rgba(15, 20, 25, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 17px;
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  outline: none;
}

.form-input:focus {
  border-color: #8b5cf6;
  background: rgba(15, 20, 25, 1);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-input::placeholder {
  color: #475569;
}

.input-icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  pointer-events: none;
}

.remember-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 28px;
}

.checkbox-custom {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #8b5cf6;
}

.checkbox-label {
  font-size: 16px;
  color: #94a3b8;
  cursor: pointer;
  user-select: none;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 15px;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 18px;
}

.submit-button {
  width: 100%;
  padding: 18px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(139, 92, 246, 0.5);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.version-footer {
  margin-top: 40px;
  text-align: center;
  font-size: 12px;
  color: #475569;
  padding-top: 24px;
  border-top: 1px solid rgba(71, 85, 105, 0.2);
}

.version-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 6px;
  color: #8b5cf6;
  font-family: monospace;
}

/* Responsive */
@media (max-width: 1600px) {
  .logo-image {
    width: 1300px;
  }
}

@media (max-width: 1400px) {
  .logo-image {
    width: 1100px;
  }
  
  .brand-section {
    padding: 50px;
  }
}

@media (max-width: 1024px) {
  .login-container {
    flex-direction: column;
  }

  .brand-section {
    padding: 40px;
    min-height: 60vh;
  }

  .logo-image {
    width: 600px;
    max-height: 50vh;
  }

  .form-section {
    width: 100%;
    padding: 40px;
  }
}

@media (max-width: 640px) {
  .brand-section {
    padding: 30px 20px;
    min-height: 50vh;
  }

  .logo-image {
    width: 400px;
    max-height: 40vh;
  }

  .tagline {
    font-size: 22px;
    letter-spacing: 3px;
  }

  .acronym-subtitle {
    font-size: 16px;
  }

  .form-section {
    padding: 32px 24px;
  }

  .form-title {
    font-size: 36px;
  }
}
</style>
