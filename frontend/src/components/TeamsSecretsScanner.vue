<template>
  <div :class="['teams-secrets-scanner', isDark ? 'dark' : 'light']">
    <!-- Scan Panel -->
    <div :class="['scan-panel', isDark ? 'dark' : 'light']">
      <div class="panel-header">
        <h2>🔐 Teams Secrets Scanner</h2>
        <p>Advanced pattern detection for credentials, API keys, and secrets in Teams conversations</p>
      </div>

      <div class="scan-form">
        <div class="form-group">
          <label>Max Conversations:</label>
          <input 
            v-model.number="scanOptions.maxConversations" 
            type="number"
            min="10"
            max="200"
            :disabled="isScanning"
            class="input-number"
          />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input 
              v-model="scanOptions.skipEmpty" 
              type="checkbox"
              :disabled="isScanning"
            />
            <span>Skip Empty Chats</span>
          </label>
        </div>

        <button @click="toggleScan" class="btn btn-primary" :disabled="!canScan && !isScanning">
          <span v-if="isScanning">⏹️ Stop Scan</span>
          <span v-else>🔍 Start Scan</span>
        </button>
      </div>
    </div>

    <!-- Error Banner (when token scope is wrong) -->
    <transition name="fade-slide">
      <div v-if="scanError" :class="['error-banner', isDark ? 'dark' : 'light']">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
          <h3>Authentication Error</h3>
          <p>{{ scanError }}</p>
          <p class="error-hint">Please authenticate with an Access Token that has audience <strong>https://api.spaces.skype.com</strong> and appropriate scopes for Teams API.</p>
        </div>
        <button @click="scanError = null" class="error-close">✕</button>
      </div>
    </transition>

    <!-- Progress Section (shown during scan) -->
    <transition name="fade-slide">
      <div v-if="isScanning || scanCompleted" :class="['progress-card', isDark ? 'dark' : 'light']">
        <div class="card-header">
          <h2>📊 Scan Progress</h2>
          <span v-if="scanCompleted" class="badge badge-success">✓ Completed</span>
          <span v-else class="badge badge-info pulse">● Scanning</span>
        </div>
        <div class="card-body">
          <!-- Progress Bar -->
          <div class="progress-container">
            <div class="progress-bar-wrapper">
              <div 
                class="progress-bar-fill" 
                :style="{ width: progress.percent + '%' }"
                :class="{ 'complete': scanCompleted }"
              ></div>
            </div>
            <span class="progress-text">{{ progress.percent }}%</span>
          </div>

          <!-- Stats Grid -->
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon">📁</div>
              <div class="stat-content">
                <div class="stat-value">{{ progress.scanned }} / {{ progress.total }}</div>
                <div class="stat-label">Conversations</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon">💬</div>
              <div class="stat-content">
                <div class="stat-value">{{ progress.messages.toLocaleString() }}</div>
                <div class="stat-label">Messages Scanned</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon">🔑</div>
              <div class="stat-content">
                <div class="stat-value">{{ progress.secrets }}</div>
                <div class="stat-label">Secrets Found</div>
              </div>
            </div>
            
            <div class="stat-item" v-if="isScanning">
              <div class="stat-icon">⏳</div>
              <div class="stat-content">
                <div class="stat-value current-conv">{{ progress.currentConversation }}</div>
                <div class="stat-label">Current Chat</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Results Section -->
    <transition name="fade-slide">
      <div v-if="results.length > 0" :class="['results-card', isDark ? 'dark' : 'light']">
        <div class="card-header">
          <h2>🎯 Detected Secrets ({{ filteredResults.length }})</h2>
          <button @click="exportResults" class="btn btn-secondary btn-sm">
            <span>📥 Export JSON</span>
          </button>
        </div>

        <!-- Filters -->
        <div class="filters-bar">
          <div class="filter-group">
            <label>Severity</label>
            <select v-model="filterSeverity" class="filter-select">
              <option value="">All Severities</option>
              <option value="critical">🔴 Critical</option>
              <option value="high">🟠 High</option>
              <option value="medium">🟡 Medium</option>
              <option value="low">🟢 Low</option>
            </select>
          </div>

          <div class="filter-group">
            <label>Secret Type</label>
            <select v-model="filterType" class="filter-select">
              <option value="">All Types</option>
              <option v-for="type in uniqueTypes" :key="type" :value="type">
                {{ type }}
              </option>
            </select>
          </div>

          <button v-if="filterSeverity || filterType" @click="clearFilters" class="btn-clear-filters">
            ✕ Clear Filters
          </button>
        </div>

        <!-- Results Table -->
        <div class="results-table-wrapper">
          <table class="results-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Type</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Entropy</th>
                <th>Conversation</th>
                <th>Sender</th>
                <th>Time</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="secret in paginatedResults" 
                :key="secret.id"
                :class="'severity-row-' + secret.severity"
              >
                <td>
                  <span :class="'severity-badge severity-' + secret.severity">
                    {{ getSeverityIcon(secret.severity) }} {{ secret.severity.toUpperCase() }}
                  </span>
                </td>
                <td class="type-cell">
                  <span class="type-badge">{{ secret.secret_type }}</span>
                </td>
                <td class="value-cell">
                  <div class="secret-value-container">
                    <code class="secret-value">
                      {{ isRevealed((currentPage - 1) * itemsPerPage + index) ? secret.value : secret.redacted_value }}
                    </code>
                    <button 
                      @click="toggleReveal((currentPage - 1) * itemsPerPage + index)" 
                      class="btn-reveal" 
                      :title="isRevealed((currentPage - 1) * itemsPerPage + index) ? 'Hide' : 'Reveal'"
                    >
                      {{ isRevealed((currentPage - 1) * itemsPerPage + index) ? '🙈' : '👁️' }}
                    </button>
                  </div>
                </td>
                <td class="confidence-cell">
                  <div class="confidence-bar-container">
                    <div 
                      class="confidence-bar" 
                      :style="{ width: (secret.confidence * 100) + '%' }"
                      :class="getConfidenceClass(secret.confidence)"
                    ></div>
                    <span class="confidence-text">{{ (secret.confidence * 100).toFixed(0) }}%</span>
                  </div>
                </td>
                <td class="entropy-cell">
                  <span class="entropy-value">{{ secret.entropy.toFixed(1) }}</span>
                </td>
                <td class="conversation-cell">
                  <span class="conversation-name" :title="secret.conversation_name">
                    {{ truncate(secret.conversation_name, 30) }}
                  </span>
                </td>
                <td class="sender-cell">{{ truncate(secret.sender, 20) }}</td>
                <td class="time-cell">{{ formatTime(secret.timestamp) }}</td>
                <td class="actions-cell">
                  <button @click="viewContext(secret)" class="btn-action" title="View Full Context">
                    💬
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button 
            @click="currentPage--" 
            :disabled="currentPage === 1"
            class="btn-pagination"
          >
            ← Previous
          </button>
          <span class="pagination-info">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          <button 
            @click="currentPage++" 
            :disabled="currentPage === totalPages"
            class="btn-pagination"
          >
            Next →
          </button>
        </div>
      </div>
    </transition>

    <!-- Empty State (before first scan) -->
    <div v-if="!isScanning && !scanCompleted && results.length === 0 && !scanError" :class="['scan-panel', isDark ? 'dark' : 'light']">
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>No Scan Results Yet</h3>
        <p>Start a scan to detect secrets and credentials in your Teams conversations</p>
      </div>
    </div>

    <!-- Context Viewer Modal -->
    <transition name="modal-fade">
      <div v-if="showContextModal" class="modal-overlay" @click.self="closeContext">
        <div class="modal-container">
          <div class="modal-header">
            <h3>💬 Message Context</h3>
            <button @click="closeContext" class="btn-close">✕</button>
          </div>
          
          <div class="modal-body">
            <div class="context-info">
              <div class="info-row">
                <span class="info-label">Conversation:</span>
                <span class="info-value">{{ selectedSecret?.conversation_name }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Sender:</span>
                <span class="info-value">{{ selectedSecret?.sender }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Time:</span>
                <span class="info-value">{{ formatTime(selectedSecret?.timestamp) }}</span>
              </div>
            </div>

            <div class="context-messages">
              <div class="context-section">
                <div class="context-label">Before:</div>
                <div class="context-text">{{ selectedSecret?.context_before || 'N/A' }}</div>
              </div>
              
              <div class="context-section highlight">
                <div class="context-label">🔑 Secret Found:</div>
                <div class="context-text">
                  <div class="secret-value-container">
                    <code class="secret-highlight">
                      {{ revealedInModal ? selectedSecret?.value : selectedSecret?.redacted_value }}
                    </code>
                    <button 
                      @click="toggleModalReveal" 
                      class="btn-reveal btn-reveal-modal" 
                      :title="revealedInModal ? 'Hide' : 'Reveal'"
                    >
                      {{ revealedInModal ? '🙈 Hide' : '👁️ Reveal' }}
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="context-section">
                <div class="context-label">After:</div>
                <div class="context-text">{{ selectedSecret?.context_after || 'N/A' }}</div>
              </div>
            </div>

            <div class="secret-details">
              <div class="detail-item">
                <span class="detail-label">Type:</span>
                <span class="type-badge">{{ selectedSecret?.secret_type }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Confidence:</span>
                <span class="detail-value">{{ (selectedSecret?.confidence * 100).toFixed(0) }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Entropy:</span>
                <span class="detail-value">{{ selectedSecret?.entropy.toFixed(2) }}</span>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button @click="closeContext" class="btn btn-secondary">Close</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'TeamsSecretsScanner',
  
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  
  data() {
    return {
      // Scan state
      isScanning: false,
      scanCompleted: false,
      currentScanId: null,
      pollInterval: null,
      
      // Scan options
      scanOptions: {
        maxConversations: 100,
        skipEmpty: true
      },
      
      // Progress data
      progress: {
        total: 0,
        scanned: 0,
        messages: 0,
        secrets: 0,
        currentConversation: '',
        percent: 0
      },
      
      // Results
      results: [],
      
      // Error handling
      scanError: null,
      
      // Filters
      filterSeverity: '',
      filterType: '',
      
      // Pagination
      currentPage: 1,
      itemsPerPage: 20,
      
      // Modal
      showContextModal: false,
      selectedSecret: null,
      revealedSecrets: new Set(), // Track which secrets are revealed in table
      revealedInModal: false, // Track if modal secret is revealed
      
      // Loading
      loading: false,
      loadingMessage: ''
    };
  },
  
  computed: {
    canScan() {
      // Check if active token exists (you may need to implement this check)
      return true;
    },
    
    filteredResults() {
      let filtered = this.results;
      
      if (this.filterSeverity) {
        filtered = filtered.filter(s => s.severity === this.filterSeverity);
      }
      
      if (this.filterType) {
        filtered = filtered.filter(s => s.secret_type === this.filterType);
      }
      
      return filtered;
    },
    
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.filteredResults.slice(start, end);
    },
    
    totalPages() {
      return Math.ceil(this.filteredResults.length / this.itemsPerPage);
    },
    
    uniqueTypes() {
      return [...new Set(this.results.map(s => s.secret_type))].sort();
    }
  },
  
  methods: {
    async startScan() {
      try {
        this.loading = true;
        this.loadingMessage = 'Starting scan...';
        
        const response = await axios.post('/api/search/teams/scan/start', {
          max_conversations: this.scanOptions.maxConversations,
          skip_empty: this.scanOptions.skipEmpty
        });
        
        // Check for error even if success is true (backend may return both)
        if (response.data.error) {
          this.scanError = response.data.error;
          return;
        }
        
        if (response.data.success) {
          this.currentScanId = response.data.scan_id;
          this.isScanning = true;
          this.scanCompleted = false;
          this.results = [];
          this.progress = {
            total: 0,
            scanned: 0,
            messages: 0,
            secrets: 0,
            currentConversation: '',
            percent: 0
          };
          
          // Start polling for progress
          this.startPolling();
        } else {
          // Show error in banner
          this.scanError = response.data.error || 'Failed to start scan';
        }
      } catch (error) {
        console.error('Start scan error:', error);
        // Show error in banner instead of alert
        const errorMsg = error.response?.data?.error || error.message;
        this.scanError = errorMsg;
      } finally {
        this.loading = false;
      }
    },
    
    async stopScan() {
      if (!this.currentScanId) return;
      
      try {
        await axios.post(`/api/search/teams/scan/stop/${this.currentScanId}`);
        this.stopPolling();
        this.isScanning = false;
      } catch (error) {
        console.error('Stop scan error:', error);
        alert('Error stopping scan: ' + (error.response?.data?.error || error.message));
      }
    },
    
    toggleScan() {
      if (this.isScanning) {
        this.stopScan();
      } else {
        // Clear previous errors
        this.scanError = null;
        this.startScan();
      }
    },
    
    startPolling() {
      this.pollInterval = setInterval(async () => {
        await this.fetchProgress();
        
        // If scan completed or error, stop polling
        if (this.progress.status === 'completed' || this.progress.status === 'error') {
          this.stopPolling();
          this.isScanning = false;
          
          // Only set scanCompleted if status is 'completed' (not error)
          if (this.progress.status === 'completed') {
            this.scanCompleted = true;
            await this.fetchResults();
          }
          // If error, scanError should already be set by fetchProgress
        }
      }, 2000); // Poll every 2 seconds
    },
    
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    
    async fetchProgress() {
      if (!this.currentScanId) return;
      
      try {
        const response = await axios.get(`/api/search/teams/scan/progress/${this.currentScanId}`);
        
        // Check for errors first
        if (response.data.error) {
          this.scanError = response.data.error;
          this.stopPolling();
          this.isScanning = false;
          return;
        }
        
        if (response.data.success) {
          const prog = response.data.progress;
          this.progress = {
            total: prog.total_conversations,
            scanned: prog.scanned_conversations,
            messages: prog.total_messages,
            secrets: prog.secrets_found,
            currentConversation: prog.current_conversation_name,
            percent: prog.percent,
            status: response.data.status
          };
          
          // Check if scan completed with error status
          if (response.data.status === 'error' && prog.error_message) {
            this.scanError = prog.error_message;
            this.stopPolling();
            this.isScanning = false;
          }
        }
      } catch (error) {
        console.error('Fetch progress error:', error);
        this.scanError = error.response?.data?.error || 'Error fetching scan progress';
        this.stopPolling();
        this.isScanning = false;
      }
    },
    
    async fetchResults() {
      if (!this.currentScanId) return;
      
      try {
        this.loading = true;
        this.loadingMessage = 'Loading results...';
        
        const response = await axios.get(`/api/search/teams/scan/results/${this.currentScanId}`);
        
        if (response.data.success) {
          this.results = response.data.secrets;
        }
      } catch (error) {
        console.error('Fetch results error:', error);
        alert('Error loading results: ' + (error.response?.data?.error || error.message));
      } finally {
        this.loading = false;
      }
    },
    
    async exportResults() {
      if (!this.currentScanId) return;
      
      try {
        const response = await axios.get(`/api/search/teams/scan/export/${this.currentScanId}`);
        
        if (response.data.success) {
          // Download as JSON
          const dataStr = JSON.stringify(response.data.export, null, 2);
          const dataBlob = new Blob([dataStr], { type: 'application/json' });
          const url = URL.createObjectURL(dataBlob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `teams-secrets-scan-${this.currentScanId}.json`;
          link.click();
          URL.revokeObjectURL(url);
        }
      } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting results: ' + (error.response?.data?.error || error.message));
      }
    },
    
    viewContext(secret) {
      this.selectedSecret = secret;
      this.showContextModal = true;
      this.revealedInModal = false; // Reset reveal state when opening modal
    },
    
    closeContext() {
      this.showContextModal = false;
      this.selectedSecret = null;
      this.revealedInModal = false;
    },
    
    toggleReveal(index) {
      // Toggle reveal state for a specific secret in the table
      if (this.revealedSecrets.has(index)) {
        this.revealedSecrets.delete(index);
      } else {
        this.revealedSecrets.add(index);
      }
      // Force Vue to update
      this.revealedSecrets = new Set(this.revealedSecrets);
    },
    
    toggleModalReveal() {
      // Toggle reveal state in modal
      this.revealedInModal = !this.revealedInModal;
    },
    
    isRevealed(index) {
      return this.revealedSecrets.has(index);
    },
    
    clearFilters() {
      this.filterSeverity = '';
      this.filterType = '';
      this.currentPage = 1;
    },
    
    getSeverityIcon(severity) {
      const icons = {
        critical: '🔴',
        high: '🟠',
        medium: '🟡',
        low: '🟢'
      };
      return icons[severity] || '⚪';
    },
    
    getConfidenceClass(confidence) {
      if (confidence >= 0.9) return 'confidence-high';
      if (confidence >= 0.7) return 'confidence-medium';
      return 'confidence-low';
    },
    
    truncate(text, length) {
      if (!text) return 'N/A';
      return text.length > length ? text.substring(0, length) + '...' : text;
    },
    
    formatTime(timestamp) {
      if (!timestamp) return 'N/A';
      try {
        const date = new Date(timestamp);
        return date.toLocaleString();
      } catch {
        return timestamp;
      }
    }
  },
  
  beforeUnmount() {
    this.stopPolling();
  }
};
</script>

<style scoped>
/* ==================== BASE ==================== */
.teams-secrets-scanner {
  padding: 0;
  width: 100%;
}

/* ==================== SCAN PANEL ==================== */
.scan-panel {
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid;
}

.scan-panel.dark {
  background: #1f2937;
  border-color: rgba(255, 255, 255, 0.1);
}

.scan-panel.light {
  background: #ffffff;
  border-color: #e2e8f0;
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

.scan-panel.dark .panel-header h2 {
  color: #fff;
}

.scan-panel.light .panel-header h2 {
  color: #1a202c;
}

.panel-header p {
  font-size: 0.9rem;
  margin: 0;
}

.scan-panel.dark .panel-header p {
  color: #a0aec0;
}

.scan-panel.light .panel-header p {
  color: #718096;
}

/* ==================== FORMS ==================== */
.scan-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
}

.scan-panel.dark .checkbox-label {
  color: #cbd5e0;
}

.scan-panel.light .checkbox-label {
  color: #4a5568;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
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

.dark .btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #cbd5e0;
}

.light .btn-secondary {
  background: #f7fafc;
  border-color: #e2e8f0;
  color: #4a5568;
}

.dark .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.light .btn-secondary:hover {
  background: #edf2f7;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

/* ==================== CARDS ==================== */
.progress-card,
.results-card {
  border-radius: 12px;
  margin-bottom: 2rem;
  border: 1px solid;
}

.progress-card.dark,
.results-card.dark {
  background: rgba(37, 41, 54, 0.8);
  backdrop-filter: blur(10px);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.progress-card.light,
.results-card.light {
  background: #ffffff;
  border-color: #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-card.dark .card-header,
.results-card.dark .card-header {
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.progress-card.light .card-header,
.results-card.light .card-header {
  border-bottom-color: #e2e8f0;
}

.card-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.progress-card.dark .card-header h2,
.results-card.dark .card-header h2 {
  color: #fff;
}

.progress-card.light .card-header h2,
.results-card.light .card-header h2 {
  color: #1a202c;
}

.card-body {
  padding: 1.5rem;
}

/* ==================== BADGES ==================== */
.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.badge-info {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ==================== PROGRESS ==================== */
.progress-container {
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bar-wrapper {
  flex: 1;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
}

.progress-card.dark .progress-bar-wrapper {
  background: rgba(255, 255, 255, 0.1);
}

.progress-card.light .progress-bar-wrapper {
  background: #e2e8f0;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  border-radius: 6px;
}

.progress-bar-fill.complete {
  background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
}

.progress-text {
  font-size: 0.875rem;
  font-weight: 600;
  min-width: 45px;
  text-align: right;
}

.progress-card.dark .progress-text {
  color: #cbd5e0;
}

.progress-card.light .progress-text {
  color: #4a5568;
}

/* ==================== STATS ==================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
}

.progress-card.dark .stat-item {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.progress-card.light .stat-item {
  background: #f7fafc;
  border-color: #e2e8f0;
}

.stat-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.progress-card.dark .stat-value {
  color: #fff;
}

.progress-card.light .stat-value {
  color: #1a202c;
}

.stat-value.current-conv {
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-label {
  font-size: 0.75rem;
}

.progress-card.dark .stat-label {
  color: #94a3b8;
}

.progress-card.light .stat-label {
  color: #64748b;
}

/* ==================== FILTERS ==================== */
.filters-bar {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.results-card.dark .filters-bar {
  background: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.results-card.light .filters-bar {
  background: #f7fafc;
  border-bottom-color: #e2e8f0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.results-card.dark .filter-group label {
  color: #94a3b8;
}

.results-card.light .filter-group label {
  color: #64748b;
}

.filter-select,
.filter-input {
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;
  border: 1px solid;
  min-width: 150px;
}

.results-card.dark .filter-select,
.results-card.dark .filter-input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.results-card.light .filter-select,
.results-card.light .filter-input {
  background: #ffffff;
  border-color: #e2e8f0;
  color: #1a202c;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #667eea;
}

/* ==================== RESULTS LIST ==================== */
.results-list {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 600px;
  overflow-y: auto;
}

.secret-item {
  border-radius: 8px;
  border: 1px solid;
  overflow: hidden;
  transition: all 0.2s;
}

.results-card.dark .secret-item {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

.results-card.light .secret-item {
  background: #f7fafc;
  border-color: #e2e8f0;
}

.results-card.dark .secret-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
}

.results-card.light .secret-item:hover {
  background: #ffffff;
  border-color: #cbd5e0;
}

.secret-header {
  padding: 1rem;
  border-bottom: 1px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-card.dark .secret-header {
  background: rgba(255, 255, 255, 0.02);
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.results-card.light .secret-header {
  background: #edf2f7;
  border-bottom-color: #e2e8f0;
}

.secret-type {
  font-weight: 700;
  font-size: 1rem;
}

.results-card.dark .secret-type {
  color: #fca5a5;
}

.results-card.light .secret-type {
  color: #dc2626;
}

.severity-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.severity-critical {
  background: rgba(220, 38, 38, 0.2);
  color: #fca5a5;
}

.light .severity-critical {
  background: #dc2626;
  color: #ffffff;
}

.severity-high {
  background: rgba(249, 115, 22, 0.2);
  color: #fdba74;
}

.light .severity-high {
  background: #f97316;
  color: #ffffff;
}

.severity-medium {
  background: rgba(234, 179, 8, 0.2);
  color: #fde047;
}

.light .severity-medium {
  background: #eab308;
  color: #ffffff;
}

.severity-low {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.light .severity-low {
  background: #22c55e;
  color: #ffffff;
}

.secret-body {
  padding: 1rem;
}

.secret-content {
  padding: 1rem;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  word-break: break-all;
  margin-bottom: 1rem;
  border-left: 3px solid;
}

.results-card.dark .secret-content {
  background: rgba(220, 38, 38, 0.1);
  border-left-color: #dc2626;
  color: #e2e8f0;
}

.results-card.light .secret-content {
  background: #fee2e2;
  border-left-color: #dc2626;
  color: #475569;
}

.secret-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.results-card.dark .meta-label {
  color: #94a3b8;
}

.results-card.light .meta-label {
  color: #64748b;
}

.meta-value {
  font-size: 0.875rem;
}

.results-card.dark .meta-value {
  color: #cbd5e0;
}

.results-card.light .meta-value {
  color: #4a5568;
}

.meta-value a {
  text-decoration: none;
}

.results-card.dark .meta-value a {
  color: #93c5fd;
}

.results-card.light .meta-value a {
  color: #3b82f6;
}

.meta-value a:hover {
  text-decoration: underline;
}

/* ==================== TRANSITIONS ==================== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {
  .scan-panel {
    padding: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .filters-bar {
    padding: 1rem;
  }

  .filter-group {
    flex: 1;
    min-width: 120px;
  }

  .secret-meta {
    grid-template-columns: 1fr;
  }

  .results-list {
    max-height: 400px;
  }
}
</style>
