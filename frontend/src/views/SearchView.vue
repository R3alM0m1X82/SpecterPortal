<template>
  <div :class="['search-view', isDark ? 'dark-mode' : 'light-mode']">
    <!-- Page Header -->
    <div :class="['page-header', isDark ? 'dark' : 'light']">
      <div class="header-icon">🔎</div>
      <div class="header-text">
        <h1>Search & Discovery</h1>
        <p>Microsoft Search across M365 + Sensitive Data Pattern Detection</p>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div :class="['tabs-container', isDark ? 'dark' : 'light']">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Quick Search Tab -->
      <div v-show="activeTab === 'quick-search'" class="tab-panel">
        <div :class="['search-panel', isDark ? 'dark' : 'light']">
          <div class="panel-header">
            <h2>🔍 Graph Search</h2>
            <p>Search across Files, Emails, and SharePoint</p>
          </div>

          <div class="search-form">
            <div class="search-input-group">
              <label>Search Query:</label>
              <input 
                v-model="searchQuery"
                type="text"
                placeholder="e.g., confidential, password, API key..."
                class="search-input"
                @keyup.enter="performSearch"
              />
            </div>

            <div class="search-options">
              <label class="section-label">Search In:</label>
              <div class="checkbox-group">
                <label class="checkbox-item">
                  <input v-model="searchIn.files" type="checkbox" />
                  <span>📁 Files</span>
                </label>
                <label class="checkbox-item">
                  <input v-model="searchIn.emails" type="checkbox" />
                  <span>📧 Emails</span>
                </label>
              </div>
            </div>

            <div class="search-actions">
              <button @click="performSearch" class="btn btn-primary" :disabled="searching">
                <span v-if="searching">⏳ Searching...</span>
                <span v-else>🔍 Search</span>
              </button>
              <button @click="clearSearch" class="btn btn-secondary">
                ✕ Clear
              </button>
            </div>
          </div>

          <!-- Search Results -->
          <div v-if="searchResults.length > 0" class="search-results">
            <h3>Found {{ searchResults.length }} result(s)</h3>
            <div class="results-list">
              <div v-for="result in searchResults" :key="result.id" class="result-item">
                <div class="result-icon">{{ result.icon }}</div>
                <div class="result-content">
                  <div class="result-header">
                    <a 
                      v-if="result.url" 
                      :href="result.url" 
                      target="_blank" 
                      class="result-title"
                    >
                      {{ result.name }}
                    </a>
                    <span v-else class="result-title">{{ result.name }}</span>
                    <span class="result-type">{{ result.type }}</span>
                  </div>
                  <div class="result-path">{{ result.path }}</div>
                  <div v-if="result.preview" class="result-preview">{{ result.preview }}</div>
                  <div v-if="result.description" class="result-description">{{ result.description }}</div>
                  <div class="result-meta">
                    <span v-if="result.lastModified">Modified: {{ formatDate(result.lastModified) }}</span>
                    <span v-if="result.size"> • Size: {{ formatSize(result.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- OneDrive Scan Tab -->
      <div v-show="activeTab === 'scan-onedrive'" class="tab-panel">
        <div :class="['scan-panel', isDark ? 'dark' : 'light']">
          <div class="panel-header">
            <h2>🔐 Scan OneDrive</h2>
            <p>Deep content analysis for AWS keys, passwords, API tokens, and credentials in file contents</p>
          </div>

          <div class="scan-form">
            <div class="form-group">
              <label>Max Files to Scan:</label>
              <input v-model.number="onedriveMaxFiles" type="number" min="10" max="500" class="input-number" />
            </div>

            <button @click="scanOneDrive" class="btn btn-primary" :disabled="scanningOneDrive">
              <span v-if="scanningOneDrive">⏳ Scanning...</span>
              <span v-else>🔍 Start Scan</span>
            </button>
          </div>

          <!-- Error Banner (when token scope is wrong or AT missing) -->
          <transition name="fade-slide">
            <div v-if="onedriveError" :class="['error-banner', isDark ? 'dark' : 'light']">
              <div class="error-icon">⚠️</div>
              <div class="error-content">
                <h3>Scan Failed</h3>
                <p>{{ onedriveError }}</p>
                <p class="error-hint">Please ensure you have an active Access Token with the required Microsoft Graph API scopes for OneDrive access.</p>
              </div>
              <button @click="onedriveError = null" class="error-close">✕</button>
            </div>
          </transition>

          <!-- Empty State -->
          <div v-if="!scanningOneDrive && onedriveResults.length === 0 && !onedriveError" class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No Scan Results Yet</h3>
            <p>Start a scan to detect sensitive patterns in your OneDrive files</p>
          </div>

          <!-- OneDrive Results -->
          <div v-if="onedriveResults.length > 0" class="scan-results">
            <h3>Found {{ onedriveResults.length }} file(s) with sensitive patterns</h3>
            
            <div class="results-list">
              <div v-for="file in onedriveResults" :key="file.file_id" class="result-file-card">
                <!-- File Header -->
                <div class="file-header">
                  <div class="file-icon">📄</div>
                  <div class="file-info">
                    <a 
                      v-if="file.web_url" 
                      :href="file.web_url" 
                      target="_blank" 
                      class="file-name"
                    >
                      {{ file.file_name }}
                    </a>
                    <span v-else class="file-name">{{ file.file_name }}</span>
                    <div class="file-meta">
                      <span>{{ formatSize(file.file_size) }}</span>
                      <span> • {{ file.findings_count }} pattern(s) found</span>
                    </div>
                  </div>
                </div>

                <!-- Findings List -->
                <div class="findings-list">
                  <div 
                    v-for="(finding, idx) in file.findings" 
                    :key="idx"
                    class="finding-item"
                  >
                    <div class="finding-header">
                      <span 
                        class="severity-badge"
                        :class="'severity-' + finding.severity"
                      >
                        {{ getSeverityIcon(finding.severity) }} {{ finding.severity.toUpperCase() }}
                      </span>
                      <span class="pattern-name">{{ finding.description }}</span>
                    </div>
                    <div class="finding-context">
                      <code>{{ finding.context }}</code>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Teams Secrets Scanner Tab (NEW) -->
      <div v-show="activeTab === 'teams-scanner'" class="tab-panel">
        <div :class="['teams-scanner-wrapper', isDark ? 'dark' : 'light']">
          <TeamsSecretsScanner :isDark="isDark" />
        </div>
      </div>

      <!-- Patterns Tab -->
      <div v-show="activeTab === 'patterns'" class="tab-panel">
        <div :class="['patterns-panel', isDark ? 'dark' : 'light']">
          <div class="panel-header">
            <h2>📋 Detection Patterns</h2>
            <p>View all available sensitive data patterns</p>
          </div>

          <div class="patterns-list">
            <div class="pattern-category">
              <h3>🔴 Critical Severity</h3>
              <ul>
                <li>AWS Access Keys</li>
                <li>Azure Client Secrets</li>
                <li>Private Keys (RSA, SSH)</li>
                <li>Database Connection Strings</li>
              </ul>
            </div>

            <div class="pattern-category">
              <h3>🟠 High Severity</h3>
              <ul>
                <li>GitHub Tokens</li>
                <li>Slack Tokens</li>
                <li>Stripe API Keys</li>
                <li>OpenAI API Keys</li>
              </ul>
            </div>

            <div class="pattern-category">
              <h3>🟡 Medium Severity</h3>
              <ul>
                <li>JWT Tokens</li>
                <li>Password Patterns</li>
                <li>Credential Exchange</li>
              </ul>
            </div>

            <div class="pattern-category">
              <h3>🟢 Low Severity</h3>
              <ul>
                <li>Generic API Keys</li>
                <li>Email Addresses</li>
                <li>IP Addresses</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TeamsSecretsScanner from '../components/TeamsSecretsScanner.vue';
import axios from 'axios';

export default {
  name: 'SearchView',
  
  components: {
    TeamsSecretsScanner
  },
  
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  
  data() {
    return {
      activeTab: 'quick-search', // Default to Quick Search (first tab)
      
      tabs: [
        { id: 'quick-search', icon: '🔍', label: 'Quick Search' },
        { id: 'scan-onedrive', icon: '🔐', label: 'Scan OneDrive' },
        { id: 'teams-scanner', icon: '🔐', label: 'Scan Teams Chats' },
        { id: 'patterns', icon: '📋', label: 'Patterns' }
      ],
      
      // Quick Search
      searchQuery: '',
      searchIn: {
        files: true,
        emails: true
      },
      searching: false,
      searchResults: [],
      
      // OneDrive Scan
      onedriveMaxFiles: 100,
      scanningOneDrive: false,
      onedriveResults: [],
      onedriveError: null // Error handling
    };
  },
  
  methods: {
    async performSearch() {
      if (!this.searchQuery.trim()) {
        alert('Please enter a search query');
        return;
      }
      
      this.searching = true;
      
      try {
        const entityTypes = [];
        if (this.searchIn.files) entityTypes.push('driveItem');
        if (this.searchIn.emails) entityTypes.push('message');
        
        const response = await axios.post('/api/search/microsoft', {
          query: this.searchQuery,
          entity_types: entityTypes,
          size: 25
        });
        
        if (response.data.success) {
          // Parse results from backend
          const results = response.data.results || {};
          const allResults = [];
          
          // Files (driveItem)
          if (results.files && Array.isArray(results.files)) {
            results.files.forEach(file => {
              allResults.push({
                id: file.id || Math.random().toString(36),
                type: 'file',
                icon: '📄',
                name: file.name || 'Unnamed File',
                path: file.webUrl || file.path || '',
                url: file.webUrl || '',
                lastModified: file.lastModifiedDateTime || '',
                size: file.size || 0
              });
            });
          }
          
          // Emails (message)
          if (results.emails && Array.isArray(results.emails)) {
            results.emails.forEach(email => {
              allResults.push({
                id: email.id || Math.random().toString(36),
                type: 'email',
                icon: '📧',
                name: email.subject || 'No Subject',
                path: email.from?.emailAddress?.address || 'Unknown Sender',
                url: email.webLink || '',
                lastModified: email.receivedDateTime || email.sentDateTime || '',
                preview: email.bodyPreview || ''
              });
            });
          }
          
          // SharePoint Sites (site)
          if (results.sites && Array.isArray(results.sites)) {
            results.sites.forEach(site => {
              allResults.push({
                id: site.id || Math.random().toString(36),
                type: 'site',
                icon: '🌐',
                name: site.name || site.displayName || 'Unnamed Site',
                path: site.webUrl || '',
                url: site.webUrl || '',
                lastModified: site.lastModifiedDateTime || '',
                description: site.description || ''
              });
            });
          }
          
          this.searchResults = allResults;
        }
      } catch (error) {
        console.error('Search error:', error);
        alert('Search failed: ' + (error.response?.data?.error || error.message));
      } finally {
        this.searching = false;
      }
    },
    
    clearSearch() {
      this.searchQuery = '';
      this.searchResults = [];
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '';
      try {
        const date = new Date(dateStr);
        return date.toLocaleString('it-IT', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch {
        return dateStr;
      }
    },
    
    formatSize(bytes) {
      if (!bytes || bytes === 0) return '';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      return `${size.toFixed(1)} ${units[unitIndex]}`;
    },
    
    getSeverityIcon(severity) {
      const icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵'
      };
      return icons[severity] || '⚪';
    },
    
    async scanOneDrive() {
      // Clear previous errors
      this.onedriveError = null;
      this.scanningOneDrive = true;
      this.onedriveResults = [];
      
      try {
        const response = await axios.post('/api/search/scan/onedrive', {
          max_files: this.onedriveMaxFiles
        });
        
        // Check for error even if success is true
        if (response.data.error) {
          this.onedriveError = response.data.error;
          return;
        }
        
        if (response.data.success) {
          this.onedriveResults = response.data.results;
        } else {
          this.onedriveError = response.data.error || 'Scan failed';
        }
      } catch (error) {
        console.error('OneDrive scan error:', error);
        this.onedriveError = error.response?.data?.error || error.message || 'Scan failed';
      } finally {
        this.scanningOneDrive = false;
      }
    }
  }
};
</script>

<style scoped>
/* ==================== BASE STYLES ==================== */
.search-view {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100vh;
}

.search-view.dark-mode {
  background: #111827;
}

.search-view.light-mode {
  background: #f7fafc;
}

/* ==================== PAGE HEADER ==================== */
.page-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding: 2rem;
  border-radius: 16px;
}

.page-header.dark {
  background: #1f2937;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.page-header.light {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-icon {
  font-size: 3rem;
}

.header-text h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.page-header.dark .header-text h1 {
  color: #fff;
}

.page-header.light .header-text h1 {
  color: #1a202c;
}

.header-text p {
  font-size: 1rem;
  margin: 0;
}

.page-header.dark .header-text p {
  color: #a0aec0;
}

.page-header.light .header-text p {
  color: #718096;
}

/* ==================== TABS ==================== */
.tabs-container {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  padding: 0.5rem;
  border-radius: 12px;
}

.tabs-container.dark {
  background: #1f2937;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tabs-container.light {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tabs-container.dark .tab-button {
  color: #a0aec0;
}

.tabs-container.light .tab-button {
  color: #4a5568;
}

.tabs-container.dark .tab-button:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #cbd5e0;
}

.tabs-container.light .tab-button:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #2d3748;
}

.tabs-container.dark .tab-button.active {
  background: rgba(102, 126, 234, 0.2);
  color: #fff;
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.tabs-container.light .tab-button.active {
  background: #3b82f6;
  color: #fff;
  border: 1px solid #3b82f6;
}

.tab-icon {
  font-size: 1.25rem;
}

.tab-label {
  display: none;
}

@media (min-width: 768px) {
  .tab-label {
    display: inline;
  }
}

/* ==================== TAB CONTENT ==================== */
.tab-content {
  min-height: 500px;
}

.tab-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ==================== PANELS ==================== */
.search-panel,
.scan-panel,
.patterns-panel,
.teams-scanner-wrapper {
  border-radius: 12px;
  padding: 2rem;
}

.search-panel.dark,
.scan-panel.dark,
.patterns-panel.dark,
.teams-scanner-wrapper.dark {
  background: #1f2937;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.search-panel.light,
.scan-panel.light,
.patterns-panel.light,
.teams-scanner-wrapper.light {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header {
  margin-bottom: 2rem;
}

.panel-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.search-panel.dark .panel-header h2,
.scan-panel.dark .panel-header h2,
.patterns-panel.dark .panel-header h2 {
  color: #fff;
}

.search-panel.light .panel-header h2,
.scan-panel.light .panel-header h2,
.patterns-panel.light .panel-header h2 {
  color: #1a202c;
}

.panel-header p {
  font-size: 0.9rem;
  margin: 0;
}

.search-panel.dark .panel-header p,
.scan-panel.dark .panel-header p,
.patterns-panel.dark .panel-header p {
  color: #a0aec0;
}

.search-panel.light .panel-header p,
.scan-panel.light .panel-header p,
.patterns-panel.light .panel-header p {
  color: #718096;
}

/* ==================== SEARCH FORM ==================== */
.search-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.search-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.search-input-group label,
.section-label {
  font-size: 0.875rem;
  font-weight: 600;
}

.search-panel.dark .search-input-group label,
.search-panel.dark .section-label {
  color: #cbd5e0;
}

.search-panel.light .search-input-group label,
.search-panel.light .section-label {
  color: #4a5568;
}

.search-input {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  border: 1px solid;
  transition: all 0.2s;
}

.search-panel.dark .search-input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.search-panel.light .search-input {
  background: #ffffff;
  border-color: #e2e8f0;
  color: #1a202c;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.search-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.checkbox-group {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.search-panel.dark .checkbox-item {
  color: #cbd5e0;
}

.search-panel.light .checkbox-item {
  color: #4a5568;
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.search-actions {
  display: flex;
  gap: 1rem;
}

/* ==================== ERROR BANNER ==================== */
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  border: 2px solid;
}

.error-banner.dark {
  background: rgba(220, 38, 38, 0.15);
  border-color: #dc2626;
}

.error-banner.light {
  background: #fee2e2;
  border-color: #dc2626;
}

.error-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-content h3 {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.error-banner.dark .error-content h3 {
  color: #fca5a5;
}

.error-banner.light .error-content h3 {
  color: #dc2626;
}

.error-content p {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.error-banner.dark .error-content p {
  color: #fecaca;
}

.error-banner.light .error-content p {
  color: #991b1b;
}

.error-hint {
  font-size: 0.8rem;
  font-style: italic;
}

.error-banner.dark .error-hint {
  color: #fca5a5;
}

.error-banner.light .error-hint {
  color: #b91c1c;
}

.error-hint strong {
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.error-banner.dark .error-hint strong {
  color: #fee2e2;
}

.error-banner.light .error-hint strong {
  color: #7f1d1d;
}

.error-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.error-banner.dark .error-close {
  color: #fca5a5;
}

.error-banner.light .error-close {
  color: #dc2626;
}

.error-banner.dark .error-close:hover {
  background: rgba(220, 38, 38, 0.2);
}

.error-banner.light .error-close:hover {
  background: rgba(220, 38, 38, 0.1);
}

/* ==================== BUTTONS ==================== */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  border: 1px solid;
}

.search-panel.dark .btn-secondary,
.scan-panel.dark .btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #cbd5e0;
}

.search-panel.light .btn-secondary,
.scan-panel.light .btn-secondary {
  background: #f7fafc;
  border-color: #e2e8f0;
  color: #4a5568;
}

.search-panel.dark .btn-secondary:hover,
.scan-panel.dark .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.search-panel.light .btn-secondary:hover,
.scan-panel.light .btn-secondary:hover {
  background: #edf2f7;
}

/* ==================== FORMS ==================== */
.scan-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
}

.scan-panel.dark .form-group label {
  color: #cbd5e0;
}

.scan-panel.light .form-group label {
  color: #4a5568;
}

.input-number {
  width: 150px;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  border: 1px solid;
  transition: all 0.2s;
}

.scan-panel.dark .input-number {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.scan-panel.light .input-number {
  background: #ffffff;
  border-color: #e2e8f0;
  color: #1a202c;
}

.input-number:focus {
  outline: none;
  border-color: #667eea;
}

/* ==================== RESULTS ==================== */
.search-results,
.scan-results {
  margin-top: 2rem;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid;
}

.search-panel.dark .search-results,
.scan-panel.dark .scan-results {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

.search-panel.light .search-results,
.scan-panel.light .scan-results {
  background: #f7fafc;
  border-color: #e2e8f0;
}

.search-results h3,
.scan-results h3 {
  font-size: 1.25rem;
  margin: 0 0 1rem 0;
}

.search-panel.dark .search-results h3,
.scan-panel.dark .scan-results h3 {
  color: #fff;
}

.search-panel.light .search-results h3,
.scan-panel.light .scan-results h3 {
  color: #1a202c;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid;
  transition: all 0.2s;
}

.search-panel.dark .result-item {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #cbd5e0;
}

.search-panel.light .result-item {
  background: #ffffff;
  border-color: #e2e8f0;
  color: #4a5568;
}

.search-panel.dark .result-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.search-panel.light .result-item:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
}

.result-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.result-title {
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
}

.search-panel.dark .result-title {
  color: #fff;
}

.search-panel.light .result-title {
  color: #1a202c;
}

.result-title:hover {
  text-decoration: underline;
}

.result-type {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.search-panel.dark .result-type {
  background: rgba(102, 126, 234, 0.2);
  color: #a5b4fc;
}

.search-panel.light .result-type {
  background: #dbeafe;
  color: #1e40af;
}

.result-path,
.result-preview,
.result-description {
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.search-panel.dark .result-path,
.search-panel.dark .result-preview,
.search-panel.dark .result-description {
  color: #94a3b8;
}

.search-panel.light .result-path,
.search-panel.light .result-preview,
.search-panel.light .result-description {
  color: #64748b;
}

.result-meta {
  margin-top: 0.5rem;
  font-size: 0.75rem;
}

.search-panel.dark .result-meta {
  color: #64748b;
}

.search-panel.light .result-meta {
  color: #94a3b8;
}

/* ==================== FILE CARDS (OneDrive Scan) ==================== */
.result-file-card {
  border-radius: 8px;
  margin-bottom: 1rem;
  border: 1px solid;
  overflow: hidden;
}

.scan-panel.dark .result-file-card {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.scan-panel.light .result-file-card {
  background: #ffffff;
  border-color: #e2e8f0;
}

.file-header {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid;
}

.scan-panel.dark .file-header {
  background: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.scan-panel.light .file-header {
  background: #f7fafc;
  border-bottom-color: #e2e8f0;
}

.file-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  display: block;
  margin-bottom: 0.25rem;
}

.scan-panel.dark .file-name {
  color: #fff;
}

.scan-panel.light .file-name {
  color: #1a202c;
}

.file-name:hover {
  text-decoration: underline;
}

.file-path {
  font-size: 0.75rem;
}

.scan-panel.dark .file-path {
  color: #94a3b8;
}

.scan-panel.light .file-path {
  color: #64748b;
}

.file-size {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.scan-panel.dark .file-size {
  color: #64748b;
}

.scan-panel.light .file-size {
  color: #94a3b8;
}

.file-patterns {
  padding: 1rem;
}

.pattern-match {
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.scan-panel.dark .pattern-match {
  background: rgba(220, 38, 38, 0.1);
  border-left-color: #dc2626;
}

.scan-panel.light .pattern-match {
  background: #fee2e2;
  border-left-color: #dc2626;
}

.pattern-match:last-child {
  margin-bottom: 0;
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.pattern-type {
  font-weight: 600;
}

.scan-panel.dark .pattern-type {
  color: #fca5a5;
}

.scan-panel.light .pattern-type {
  color: #dc2626;
}

.pattern-severity {
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.scan-panel.dark .severity-critical {
  background: rgba(220, 38, 38, 0.2);
  color: #fca5a5;
}

.scan-panel.light .severity-critical {
  background: #dc2626;
  color: #ffffff;
}

.scan-panel.dark .severity-high {
  background: rgba(249, 115, 22, 0.2);
  color: #fdba74;
}

.scan-panel.light .severity-high {
  background: #f97316;
  color: #ffffff;
}

.scan-panel.dark .severity-medium {
  background: rgba(234, 179, 8, 0.2);
  color: #fde047;
}

.scan-panel.light .severity-medium {
  background: #eab308;
  color: #ffffff;
}

.scan-panel.dark .severity-low {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.scan-panel.light .severity-low {
  background: #22c55e;
  color: #ffffff;
}

.pattern-content {
  word-break: break-all;
  line-height: 1.6;
}

.scan-panel.dark .pattern-content {
  color: #e2e8f0;
}

.scan-panel.light .pattern-content {
  color: #475569;
}

.pattern-line {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.scan-panel.dark .pattern-line {
  color: #64748b;
}

.scan-panel.light .pattern-line {
  color: #94a3b8;
}

/* ==================== PATTERNS LIST ==================== */
.patterns-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.pattern-category {
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid;
}

.patterns-panel.dark .pattern-category {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

.patterns-panel.light .pattern-category {
  background: #f7fafc;
  border-color: #e2e8f0;
}

.pattern-category h3 {
  font-size: 1.1rem;
  margin: 0 0 1rem 0;
}

.patterns-panel.dark .pattern-category h3 {
  color: #fff;
}

.patterns-panel.light .pattern-category h3 {
  color: #1a202c;
}

.pattern-category ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.pattern-category li {
  padding: 0.5rem 0;
  font-size: 0.9rem;
  border-bottom: 1px solid;
}

.patterns-panel.dark .pattern-category li {
  color: #cbd5e0;
  border-bottom-color: rgba(255, 255, 255, 0.05);
}

.patterns-panel.light .pattern-category li {
  color: #4a5568;
  border-bottom-color: #e2e8f0;
}

.pattern-category li:last-child {
  border-bottom: none;
}

/* ==================== EMPTY STATE ==================== */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.scan-panel.dark .empty-state {
  color: #94a3b8;
}

.scan-panel.light .empty-state {
  color: #64748b;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.25rem;
  margin: 0 0 0.5rem 0;
}

.scan-panel.dark .empty-state h3 {
  color: #cbd5e0;
}

.scan-panel.light .empty-state h3 {
  color: #475569;
}

.empty-state p {
  font-size: 0.9rem;
  margin: 0;
}

/* ==================== FINDINGS LIST (OneDrive Results) ==================== */
.file-meta {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: flex;
  gap: 0.5rem;
}

.scan-panel.dark .file-meta {
  color: #94a3b8;
}

.scan-panel.light .file-meta {
  color: #64748b;
}

.findings-list {
  padding: 1rem;
}

.finding-item {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 8px;
  border-left: 3px solid;
}

.scan-panel.dark .finding-item {
  background: rgba(220, 38, 38, 0.1);
  border-left-color: #dc2626;
}

.scan-panel.light .finding-item {
  background: #fee2e2;
  border-left-color: #dc2626;
}

.finding-item:last-child {
  margin-bottom: 0;
}

.finding-header {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.severity-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.severity-high {
  background: #dc2626;
  color: #fff;
}

.severity-medium {
  background: #f59e0b;
  color: #fff;
}

.severity-low {
  background: #10b981;
  color: #fff;
}

.pattern-name {
  font-size: 0.875rem;
  font-weight: 600;
}

.scan-panel.dark .pattern-name {
  color: #fca5a5;
}

.scan-panel.light .pattern-name {
  color: #991b1b;
}

.finding-context {
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  max-width: 100%;
}

.scan-panel.dark .finding-context {
  background: rgba(0, 0, 0, 0.3);
}

.scan-panel.light .finding-context {
  background: rgba(0, 0, 0, 0.05);
}

.finding-context code {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  display: block;
}

.scan-panel.dark .finding-context code {
  color: #fee2e2;
}

.scan-panel.light .finding-context code {
  color: #7f1d1d;
}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {
  .search-view {
    padding: 1rem;
  }

  .page-header {
    padding: 1.5rem;
  }

  .header-text h1 {
    font-size: 1.5rem;
  }

  .tabs-container {
    gap: 0.25rem;
    padding: 0.25rem;
  }

  .tab-button {
    padding: 0.75rem;
  }

  .search-panel,
  .scan-panel,
  .patterns-panel,
  .teams-scanner-wrapper {
    padding: 1.5rem;
  }

  .patterns-list {
    grid-template-columns: 1fr;
  }

  .checkbox-group {
    flex-direction: column;
    gap: 0.75rem;
  }

  .search-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
