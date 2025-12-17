<template>
  <div :class="['cap-view', { 'dark': isDark }]">
    <!-- Header -->
    <div :class="['view-header', { 'dark': isDark }]">
      <div class="header-content">
        <h1 :class="{ 'dark': isDark }">
          <svg class="header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
            <path d="M12 16V12M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Conditional Access Policies
        </h1>
        <p :class="['subtitle', { 'dark': isDark }]">Enumerate and analyze Azure AD Conditional Access Policies</p>
      </div>
      <div class="header-actions">
        <button @click="fetchPolicies" :disabled="loading" :class="['btn', 'btn-primary', { 'dark': isDark }]">
          <svg v-if="!loading" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2"/>
            <path d="M12 7V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Loading...' : 'Fetch Policies' }}
        </button>
        <button @click="fetchNamedLocations" :disabled="loading || !policies.length" :class="['btn', 'btn-secondary', { 'dark': isDark }]">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2Z" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="9" r="2.5" stroke="currentColor" stroke-width="2"/>
          </svg>
          Named Locations
        </button>
        <button @click="fetchSummary" :disabled="loading || !policies.length" :class="['btn', 'btn-secondary', { 'dark': isDark }]">
          Summary
        </button>
      </div>
    </div>

    <!-- Warnings Banner -->
    <div v-if="warnings.length" class="warnings-banner">
      <div v-for="(warning, index) in warnings" :key="index" :class="['warning-item', { 'dark': isDark }]">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <div class="warning-content">
          <strong>{{ warning.type === 'scope_missing' ? 'Missing Scope' : 'Warning' }}:</strong>
          {{ warning.message }}
          <span v-if="warning.hint" class="warning-hint">{{ warning.hint }}</span>
        </div>
        <button @click="dismissWarning(index)" class="warning-dismiss">×</button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" :class="['error-message', { 'dark': isDark }]">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
        <path d="M12 8V12M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <div>
        <strong>Error:</strong> {{ error }}
        <p v-if="errorHint" class="error-hint">{{ errorHint }}</p>
      </div>
    </div>

    <!-- Named Locations Panel -->
    <div v-if="namedLocations && namedLocations.length" :class="['named-locations-panel', { 'dark': isDark }]">
      <div class="panel-header">
        <h2 :class="{ 'dark': isDark }">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2Z" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="9" r="2.5" stroke="currentColor" stroke-width="2"/>
          </svg>
          Named Locations ({{ namedLocations.length }})
        </h2>
        <button @click="namedLocations = null" :class="['btn', 'btn-sm', { 'dark': isDark }]">Close</button>
      </div>
      
      <div class="locations-grid">
        <div v-for="location in namedLocations" :key="location.id" :class="['location-card', { 'dark': isDark }]">
          <div :class="['location-header', { 'dark': isDark }]">
            <h3 :class="{ 'dark': isDark }">{{ location.displayName }}</h3>
            <div class="location-badges">
              <span :class="['trust-badge', location.isTrusted ? 'trusted' : 'untrusted']">
                {{ location.isTrusted ? '✓ Trusted' : '✗ Untrusted' }}
              </span>
              <span :class="['type-badge', { 'dark': isDark }]">{{ location.locationType === 'country' ? '🌍 Country' : '🌐 IP' }}</span>
            </div>
          </div>
          
          <div class="location-details">
            <!-- Apply to Unknown Country -->
            <div class="detail-row">
              <span :class="['detail-label', { 'dark': isDark }]">Apply to unknown country:</span>
              <span :class="['detail-value', location.applyToUnknownCountry ? 'yes' : 'no']">
                {{ location.applyToUnknownCountry ? 'Yes' : 'No' }}
              </span>
            </div>
            
            <!-- IP Ranges -->
            <div v-if="location.ipRanges && location.ipRanges.length" class="detail-row">
              <span :class="['detail-label', { 'dark': isDark }]">IP Ranges:</span>
              <div class="ip-ranges">
                <code v-for="ip in location.ipRanges" :key="ip" :class="['ip-range', { 'dark': isDark }]">{{ ip }}</code>
              </div>
            </div>
            
            <!-- Countries -->
            <div v-if="location.countriesAndRegions && location.countriesAndRegions.length" class="detail-row">
              <span :class="['detail-label', { 'dark': isDark }]">Country ISO Codes:</span>
              <div class="country-codes">
                <span v-for="code in location.countriesAndRegions" :key="code" :class="['country-code', { 'dark': isDark }]">{{ code }}</span>
              </div>
            </div>
            
            <!-- Categories -->
            <div v-if="location.categories && location.categories.length && location.categories[0]" class="detail-row">
              <span :class="['detail-label', { 'dark': isDark }]">Categories:</span>
              <div class="categories">
                <span v-for="cat in location.categories" :key="cat" :class="['category-tag', { 'dark': isDark }]">{{ cat }}</span>
              </div>
            </div>
            
            <!-- Associated Policies -->
            <div v-if="location.associatedPolicies && location.associatedPolicies.length" class="detail-row associated-policies">
              <span :class="['detail-label', { 'dark': isDark }]">Associated Policies ({{ location.associatedPolicies.length }}):</span>
              <div class="policies-list">
                <div v-for="policy in location.associatedPolicies" :key="policy.id" :class="['associated-policy', { 'dark': isDark }]">
                  <span :class="['policy-name', { 'dark': isDark }]">{{ policy.name }}</span>
                  <span :class="['direction-badge', policy.direction]">{{ policy.direction }}</span>
                </div>
              </div>
            </div>
            <div v-else class="detail-row">
              <span :class="['detail-label', { 'dark': isDark }]">Associated Policies:</span>
              <span :class="['no-policies', { 'dark': isDark }]">None</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Panel -->
    <div v-if="summary" :class="['summary-panel', { 'dark': isDark }]">
      <h2 :class="{ 'dark': isDark }">Security Summary</h2>
      <div class="summary-grid">
        <div :class="['summary-card', { 'dark': isDark }]">
          <div :class="['summary-value', { 'dark': isDark }]">{{ summary.total_policies }}</div>
          <div :class="['summary-label', { 'dark': isDark }]">Total Policies</div>
        </div>
        <div :class="['summary-card', 'enabled', { 'dark': isDark }]">
          <div class="summary-value">{{ summary.enabled_policies }}</div>
          <div :class="['summary-label', { 'dark': isDark }]">Enabled</div>
        </div>
        <div :class="['summary-card', 'disabled', { 'dark': isDark }]">
          <div class="summary-value">{{ summary.disabled_policies }}</div>
          <div :class="['summary-label', { 'dark': isDark }]">Disabled</div>
        </div>
        <div :class="['summary-card', 'mfa', { 'dark': isDark }]">
          <div class="summary-value">{{ summary.mfa_required_policies }}</div>
          <div :class="['summary-label', { 'dark': isDark }]">Require MFA</div>
        </div>
      </div>

      <div class="severity-section">
        <h3 :class="{ 'dark': isDark }">Policy Risk Levels</h3>
        <div class="severity-bars">
          <div class="severity-bar high" :style="{ width: getSeverityWidth('high') }">
            <span>High: {{ summary.severity_counts.high }}</span>
          </div>
          <div class="severity-bar medium" :style="{ width: getSeverityWidth('medium') }">
            <span>Medium: {{ summary.severity_counts.medium }}</span>
          </div>
          <div class="severity-bar low" :style="{ width: getSeverityWidth('low') }">
            <span>Low: {{ summary.severity_counts.low }}</span>
          </div>
        </div>
      </div>

      <div v-if="summary.coverage_gaps && summary.coverage_gaps.length" class="gaps-section">
        <h3 :class="{ 'dark': isDark }">Coverage Gaps</h3>
        <div v-for="gap in summary.coverage_gaps" :key="gap.type" :class="['gap-item', { 'dark': isDark }]">
          <span :class="['gap-severity', gap.severity || 'info']">{{ gap.severity || 'INFO' }}</span>
          {{ gap.message }}
        </div>
      </div>

      <div v-if="summary.all_bypass_opportunities && summary.all_bypass_opportunities.length" class="bypass-section">
        <h3 :class="{ 'dark': isDark }">Bypass Opportunities ({{ summary.all_bypass_opportunities.length }})</h3>
        <div v-for="(bypass, index) in summary.all_bypass_opportunities" :key="index" :class="['bypass-item', { 'dark': isDark }]">
          <div class="bypass-header">
            <span class="bypass-type">{{ bypass.type }}</span>
            <span :class="['bypass-policy', { 'dark': isDark }]">{{ bypass.policy_name }}</span>
          </div>
          <div :class="['bypass-message', { 'dark': isDark }]">{{ bypass.message }}</div>
          <div :class="['bypass-technique', { 'dark': isDark }]">
            <strong>Technique:</strong> {{ bypass.technique }}
          </div>
        </div>
      </div>

      <button @click="summary = null" :class="['btn', 'btn-sm', { 'dark': isDark }]">Close Summary</button>
    </div>

    <!-- Policies List -->
    <div v-if="policies.length" :class="['policies-container', { 'dark': isDark }]">
      <div :class="['policies-header', { 'dark': isDark }]">
        <h2 :class="{ 'dark': isDark }">Policies ({{ policies.length }})</h2>
        <div class="filter-controls">
          <select v-model="stateFilter" :class="{ 'dark': isDark }">
            <option value="">All States</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
            <option value="report">Report Only</option>
          </select>
          <select v-model="severityFilter" :class="{ 'dark': isDark }">
            <option value="">All Severities</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>
      </div>

      <div class="policies-list">
        <div 
          v-for="policy in filteredPolicies" 
          :key="policy.id" 
          :class="['policy-card', { expanded: expandedPolicy === policy.id, 'dark': isDark }]"
        >
          <div :class="['policy-header-row', { 'dark': isDark }]" @click="togglePolicy(policy.id)">
            <div class="policy-info">
              <h3 :class="{ 'dark': isDark }">{{ policy.displayName }}</h3>
              <div class="policy-meta">
                <span :class="['state-badge', policy.state.toLowerCase()]">
                  {{ policy.state }}
                </span>
                <span :class="['severity-badge', policy.analysis.severity]">
                  {{ policy.analysis.severity.toUpperCase() }}
                </span>
                <span v-if="policy.analysis.bypass_opportunities.length" class="bypass-count">
                  {{ policy.analysis.bypass_opportunities.length }} bypass(es)
                </span>
              </div>
            </div>
            <svg :class="['expand-icon', { rotated: expandedPolicy === policy.id, 'dark': isDark }]" viewBox="0 0 24 24" fill="none">
              <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>

          <div v-if="expandedPolicy === policy.id" :class="['policy-details', { 'dark': isDark }]">
            <!-- Grant Controls -->
            <div :class="['detail-section', { 'dark': isDark }]">
              <h4 :class="{ 'dark': isDark }">Grant Controls</h4>
              <div class="controls-list">
                <span 
                  v-for="control in policy.grantControls.builtInControls" 
                  :key="control"
                  :class="['control-badge', { 'dark': isDark }]"
                >
                  {{ control }}
                </span>
                <span v-if="!policy.grantControls.builtInControls.length" :class="['no-data', { 'dark': isDark }]">
                  No grant controls
                </span>
              </div>
              <div v-if="policy.grantControls.operator" :class="['operator', { 'dark': isDark }]">
                Operator: {{ policy.grantControls.operator }}
              </div>
            </div>

            <!-- Conditions -->
            <div :class="['detail-section', { 'dark': isDark }]">
              <h4 :class="{ 'dark': isDark }">Conditions</h4>
              
              <!-- Applications -->
              <div class="condition-group">
                <h5 :class="{ 'dark': isDark }">Applications</h5>
                <div v-if="policy.conditions.applications.includeAllApps" class="condition-value">
                  <span class="tag all">All Applications</span>
                </div>
                <div v-else>
                  <div class="condition-row">
                    <span :class="['label', { 'dark': isDark }]">Include:</span>
                    <span 
                      v-for="app in policy.conditions.applications.includeApplications" 
                      :key="app.id"
                      :class="['tag', { 'dark': isDark }]"
                      :title="app.id"
                    >
                      {{ app.name }}
                    </span>
                    <span v-if="!policy.conditions.applications.includeApplications.length" :class="['no-data', { 'dark': isDark }]">None</span>
                  </div>
                  <div v-if="policy.conditions.applications.excludeApplications.length" class="condition-row">
                    <span :class="['label', { 'dark': isDark }]">Exclude:</span>
                    <span 
                      v-for="app in policy.conditions.applications.excludeApplications" 
                      :key="app.id"
                      class="tag exclude"
                      :title="app.id"
                    >
                      {{ app.name }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Users -->
              <div class="condition-group">
                <h5 :class="{ 'dark': isDark }">Users & Groups</h5>
                <div class="condition-row">
                  <span :class="['label', { 'dark': isDark }]">Include:</span>
                  <span v-if="policy.conditions.users.includeUsers.allUsers" class="tag all">All Users</span>
                  <span v-if="policy.conditions.users.includeUsers.allGuestUsers" :class="['tag', { 'dark': isDark }]">All Guest Users</span>
                  <span v-if="!hasIncludeUsers(policy)" :class="['no-data', { 'dark': isDark }]">None</span>
                </div>
                
                <!-- Users list -->
                <div v-if="policy.conditions.users.includeUsers.users && policy.conditions.users.includeUsers.users.length && !policy.conditions.users.includeUsers.allUsers" :class="['members-list', { 'dark': isDark }]">
                  <div :class="['members-category', { 'dark': isDark }]">
                    <span class="category-icon">👤</span>
                    <span class="category-label">Users ({{ policy.conditions.users.includeUsers.users.length }}):</span>
                  </div>
                  <div class="members-items">
                    <span 
                      v-for="user in policy.conditions.users.includeUsers.users" 
                      :key="user.id"
                      :class="['member-tag', 'user-tag', { 'unresolved': isUnresolved(user), 'dark': isDark }]"
                      :title="user.id"
                    >
                      {{ user.upn || user.displayName }}
                    </span>
                  </div>
                </div>
                
                <!-- Groups list -->
                <div v-if="policy.conditions.users.includeUsers.groups && policy.conditions.users.includeUsers.groups.length" :class="['members-list', { 'dark': isDark }]">
                  <div :class="['members-category', { 'dark': isDark }]">
                    <span class="category-icon">👥</span>
                    <span class="category-label">Groups ({{ policy.conditions.users.includeUsers.groups.length }}):</span>
                  </div>
                  <div class="members-items">
                    <span 
                      v-for="group in policy.conditions.users.includeUsers.groups" 
                      :key="group.id"
                      :class="['member-tag', 'group-tag', { 'unresolved': isUnresolved(group), 'dark': isDark }]"
                      :title="group.id"
                    >
                      {{ group.displayName }}
                    </span>
                  </div>
                </div>
                
                <!-- Roles list -->
                <div v-if="policy.conditions.users.includeUsers.roles && policy.conditions.users.includeUsers.roles.length" :class="['members-list', { 'dark': isDark }]">
                  <div :class="['members-category', { 'dark': isDark }]">
                    <span class="category-icon">🔑</span>
                    <span class="category-label">Roles ({{ policy.conditions.users.includeUsers.roles.length }}):</span>
                  </div>
                  <div class="members-items">
                    <span 
                      v-for="role in policy.conditions.users.includeUsers.roles" 
                      :key="role.id"
                      :class="['member-tag', 'role-tag', { 'dark': isDark }]"
                      :title="role.id"
                    >
                      {{ role.displayName }}
                    </span>
                  </div>
                </div>
                
                <!-- Exclusions -->
                <div v-if="hasUserExclusions(policy)" :class="['exclusions-section', { 'dark': isDark }]">
                  <div class="condition-row exclude-row">
                    <span class="label">Exclude:</span>
                  </div>
                  
                  <!-- Excluded Users -->
                  <div v-if="policy.conditions.users.excludeUsers.users && policy.conditions.users.excludeUsers.users.length" :class="['members-list', { 'dark': isDark }]">
                    <div :class="['members-category', { 'dark': isDark }]">
                      <span class="category-icon">👤</span>
                      <span class="category-label">Users ({{ policy.conditions.users.excludeUsers.users.length }}):</span>
                    </div>
                    <div class="members-items">
                      <span 
                        v-for="user in policy.conditions.users.excludeUsers.users" 
                        :key="user.id"
                        :class="['member-tag', 'exclude-tag', { 'unresolved': isUnresolved(user) }]"
                        :title="user.id"
                      >
                        {{ user.upn || user.displayName }}
                      </span>
                    </div>
                  </div>
                  
                  <!-- Excluded Groups -->
                  <div v-if="policy.conditions.users.excludeUsers.groups && policy.conditions.users.excludeUsers.groups.length" :class="['members-list', { 'dark': isDark }]">
                    <div :class="['members-category', { 'dark': isDark }]">
                      <span class="category-icon">👥</span>
                      <span class="category-label">Groups ({{ policy.conditions.users.excludeUsers.groups.length }}):</span>
                    </div>
                    <div class="members-items">
                      <span 
                        v-for="group in policy.conditions.users.excludeUsers.groups" 
                        :key="group.id"
                        :class="['member-tag', 'exclude-tag', { 'unresolved': isUnresolved(group) }]"
                        :title="group.id"
                      >
                        {{ group.displayName }}
                      </span>
                    </div>
                  </div>
                  
                  <!-- Excluded Roles -->
                  <div v-if="policy.conditions.users.excludeUsers.roles && policy.conditions.users.excludeUsers.roles.length" :class="['members-list', { 'dark': isDark }]">
                    <div :class="['members-category', { 'dark': isDark }]">
                      <span class="category-icon">🔑</span>
                      <span class="category-label">Roles ({{ policy.conditions.users.excludeUsers.roles.length }}):</span>
                    </div>
                    <div class="members-items">
                      <span 
                        v-for="role in policy.conditions.users.excludeUsers.roles" 
                        :key="role.id"
                        :class="['member-tag', 'exclude-tag']"
                        :title="role.id"
                      >
                        {{ role.displayName }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Platforms -->
              <div v-if="policy.conditions.platforms.includePlatforms.length" class="condition-group">
                <h5 :class="{ 'dark': isDark }">Platforms</h5>
                <div class="condition-row">
                  <span 
                    v-for="platform in policy.conditions.platforms.includePlatforms" 
                    :key="platform"
                    :class="['tag', { 'dark': isDark }]"
                  >
                    {{ platform }}
                  </span>
                </div>
              </div>

              <!-- Locations -->
              <div v-if="policy.conditions.locations.includeLocations.length || policy.conditions.locations.excludeLocations.length" class="condition-group">
                <h5 :class="{ 'dark': isDark }">Locations</h5>
                <div v-if="policy.conditions.locations.includeLocations.length" class="condition-row">
                  <span :class="['label', { 'dark': isDark }]">Include:</span>
                  <span 
                    v-for="loc in policy.conditions.locations.includeLocations" 
                    :key="loc.id || loc" 
                    :class="['tag', 'location-tag', { 'unresolved': isLocationUnresolved(loc), 'dark': isDark }]"
                    :title="loc.id || loc"
                  >
                    {{ loc.displayName || loc }}
                  </span>
                </div>
                <div v-if="policy.conditions.locations.excludeLocations.length" class="condition-row">
                  <span :class="['label', { 'dark': isDark }]">Exclude:</span>
                  <span 
                    v-for="loc in policy.conditions.locations.excludeLocations" 
                    :key="loc.id || loc" 
                    :class="['tag', 'exclude', { 'unresolved': isLocationUnresolved(loc) }]"
                    :title="loc.id || loc"
                  >
                    {{ loc.displayName || loc }}
                  </span>
                </div>
              </div>

              <!-- Client App Types -->
              <div v-if="policy.conditions.clientAppTypes.length" class="condition-group">
                <h5 :class="{ 'dark': isDark }">Client App Types</h5>
                <div class="condition-row">
                  <span v-for="type in policy.conditions.clientAppTypes" :key="type" :class="['tag', { 'dark': isDark }]">
                    {{ type }}
                  </span>
                </div>
              </div>

              <!-- Risk Levels -->
              <div v-if="policy.conditions.signInRiskLevels.length || policy.conditions.userRiskLevels.length" class="condition-group">
                <h5 :class="{ 'dark': isDark }">Risk Levels</h5>
                <div v-if="policy.conditions.signInRiskLevels.length" class="condition-row">
                  <span :class="['label', { 'dark': isDark }]">Sign-in Risk:</span>
                  <span v-for="risk in policy.conditions.signInRiskLevels" :key="risk" class="tag risk">
                    {{ risk }}
                  </span>
                </div>
                <div v-if="policy.conditions.userRiskLevels.length" class="condition-row">
                  <span :class="['label', { 'dark': isDark }]">User Risk:</span>
                  <span v-for="risk in policy.conditions.userRiskLevels" :key="risk" class="tag risk">
                    {{ risk }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Session Controls -->
            <div v-if="hasSessionControls(policy)" :class="['detail-section', { 'dark': isDark }]">
              <h4 :class="{ 'dark': isDark }">Session Controls</h4>
              <div v-if="policy.sessionControls.signInFrequency" :class="['session-control', { 'dark': isDark }]">
                <strong>Sign-in Frequency:</strong> 
                {{ policy.sessionControls.signInFrequency.value }} {{ policy.sessionControls.signInFrequency.type }}
              </div>
              <div v-if="policy.sessionControls.persistentBrowser" :class="['session-control', { 'dark': isDark }]">
                <strong>Persistent Browser:</strong> 
                {{ policy.sessionControls.persistentBrowser.mode }}
              </div>
              <div v-if="policy.sessionControls.cloudAppSecurity" :class="['session-control', { 'dark': isDark }]">
                <strong>Cloud App Security:</strong> 
                {{ policy.sessionControls.cloudAppSecurity.cloudAppSecurityType }}
              </div>
            </div>

            <!-- Analysis -->
            <div :class="['detail-section', 'analysis', { 'dark': isDark }]">
              <h4 :class="{ 'dark': isDark }">Security Analysis</h4>
              
              <div v-if="policy.analysis.findings.length" class="findings">
                <div v-for="(finding, index) in policy.analysis.findings" :key="index" :class="['finding', finding.type]">
                  {{ finding.message }}
                </div>
              </div>

              <div v-if="policy.analysis.bypass_opportunities.length" class="bypass-opportunities">
                <h5 :class="{ 'dark': isDark }">Potential Bypass Opportunities</h5>
                <div v-for="(bypass, index) in policy.analysis.bypass_opportunities" :key="index" :class="['bypass-item', { 'dark': isDark }]">
                  <div class="bypass-type-badge">{{ bypass.type }}</div>
                  <div class="bypass-content">
                    <div :class="['bypass-msg', { 'dark': isDark }]">{{ bypass.message }}</div>
                    <div :class="['bypass-tech', { 'dark': isDark }]"><strong>Technique:</strong> {{ bypass.technique }}</div>
                  </div>
                </div>
              </div>

              <div v-if="!policy.analysis.findings.length && !policy.analysis.bypass_opportunities.length" class="no-issues">
                No significant security concerns identified
              </div>
            </div>

            <!-- Metadata -->
            <div :class="['detail-section', 'metadata', { 'dark': isDark }]">
              <div :class="['meta-item', { 'dark': isDark }]">
                <span class="label">Policy ID:</span>
                <code :class="{ 'dark': isDark }">{{ policy.id }}</code>
              </div>
              <div v-if="policy.createdDateTime" :class="['meta-item', { 'dark': isDark }]">
                <span class="label">Created:</span>
                {{ formatDate(policy.createdDateTime) }}
              </div>
              <div v-if="policy.modifiedDateTime" :class="['meta-item', { 'dark': isDark }]">
                <span class="label">Modified:</span>
                {{ formatDate(policy.modifiedDateTime) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !policies.length && !error" :class="['empty-state', { 'dark': isDark }]">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
        <path d="M9 9L15 15M15 9L9 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <h3 :class="{ 'dark': isDark }">No Policies Loaded</h3>
      <p>Click "Fetch Policies" to enumerate Conditional Access Policies from the tenant</p>
      <p class="note">Requires a token with refresh token for FOCI exchange</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'CAPView',
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
      errorHint: null,
      policies: [],
      summary: null,
      namedLocations: null,
      warnings: [],
      expandedPolicy: null,
      stateFilter: '',
      severityFilter: '',
      tenantId: null
    };
  },
  computed: {
    filteredPolicies() {
      return this.policies.filter(policy => {
        if (this.stateFilter) {
          const state = policy.state.toLowerCase();
          if (this.stateFilter === 'enabled' && state !== 'enabled') return false;
          if (this.stateFilter === 'disabled' && state !== 'disabled') return false;
          if (this.stateFilter === 'report' && !state.includes('report')) return false;
        }
        
        if (this.severityFilter && policy.analysis.severity !== this.severityFilter) {
          return false;
        }
        
        return true;
      });
    }
  },
  methods: {
    async fetchPolicies() {
      this.loading = true;
      this.error = null;
      this.errorHint = null;
      this.summary = null;
      this.namedLocations = null;
      this.warnings = [];
      
      try {
        const response = await axios.get('/api/cap/policies');
        
        if (response.data.success) {
          this.policies = response.data.policies;
          this.tenantId = response.data.tenant_id;
          
          // Handle warnings from backend
          if (response.data.warnings && response.data.warnings.length) {
            this.warnings = response.data.warnings;
          }
        } else {
          this.error = response.data.error;
          this.errorHint = response.data.hint;
        }
      } catch (err) {
        if (err.response && err.response.data) {
          this.error = err.response.data.error || 'Failed to fetch policies';
          this.errorHint = err.response.data.hint;
        } else {
          this.error = err.message || 'Network error';
        }
      } finally {
        this.loading = false;
      }
    },
    
    async fetchNamedLocations() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/api/cap/named-locations');
        
        if (response.data.success) {
          this.namedLocations = response.data.locations;
          // Close summary if open
          this.summary = null;
        } else {
          this.error = response.data.error;
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchSummary() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/api/cap/summary');
        
        if (response.data.success) {
          this.summary = response.data.summary;
          // Close named locations if open
          this.namedLocations = null;
        } else {
          this.error = response.data.error;
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message;
      } finally {
        this.loading = false;
      }
    },
    
    togglePolicy(policyId) {
      this.expandedPolicy = this.expandedPolicy === policyId ? null : policyId;
    },
    
    dismissWarning(index) {
      this.warnings.splice(index, 1);
    },
    
    isUnresolved(item) {
      // Check if the displayName looks like a truncated GUID
      if (!item || !item.displayName) return false;
      return item.displayName.endsWith('...');
    },
    
    isLocationUnresolved(loc) {
      if (!loc) return false;
      // Check for unresolved indicator
      if (loc.resolved === false) return true;
      if (typeof loc === 'string') return false;
      return loc.displayName && (loc.displayName.startsWith('📍') || loc.displayName.endsWith('...'));
    },
    
    hasIncludeUsers(policy) {
      const include = policy.conditions.users.includeUsers;
      return include.allUsers || 
             include.allGuestUsers ||
             (include.users && include.users.length) || 
             (include.groups && include.groups.length) || 
             (include.roles && include.roles.length);
    },
    
    hasUserExclusions(policy) {
      const exclude = policy.conditions.users.excludeUsers;
      return (exclude.users && exclude.users.length) || 
             (exclude.groups && exclude.groups.length) || 
             (exclude.roles && exclude.roles.length);
    },
    
    hasSessionControls(policy) {
      return policy.sessionControls && 
             (policy.sessionControls.signInFrequency || 
              policy.sessionControls.persistentBrowser || 
              policy.sessionControls.cloudAppSecurity);
    },
    
    getSeverityWidth(severity) {
      if (!this.summary) return '0%';
      const total = this.summary.total_policies || 1;
      const count = this.summary.severity_counts[severity] || 0;
      return `${Math.max((count / total) * 100, count > 0 ? 10 : 0)}%`;
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleString();
    }
  }
};
</script>

<style scoped>
.cap-view {
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
}

.cap-view.dark {
  background: #1a1a2e;
  color: #e2e8f0;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.view-header.dark {
  border-bottom-color: #374151;
}

.header-content h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 1.75rem;
  color: #1f2937;
}

.header-content h1.dark {
  color: #f1f5f9;
}

.header-icon {
  width: 32px;
  height: 32px;
  color: #6366f1;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 0.95rem;
}

.subtitle.dark {
  color: #9ca3af;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  background: #6366f1;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #4f46e5;
}

.btn-primary.dark {
  background: #818cf8;
}

.btn-primary.dark:hover:not(:disabled) {
  background: #6366f1;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary.dark {
  background: #374151;
  color: #e2e8f0;
  border-color: #4b5563;
}

.btn-secondary.dark:hover:not(:disabled) {
  background: #4b5563;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.btn-sm.dark {
  background: #374151;
  color: #e2e8f0;
  border: 1px solid #4b5563;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Warnings Banner */
.warnings-banner {
  margin-bottom: 20px;
}

.warning-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #fefce8;
  border: 1px solid #fef08a;
  border-radius: 8px;
  margin-bottom: 8px;
}

.warning-item.dark {
  background: #422006;
  border-color: #854d0e;
}

.warning-item svg {
  width: 20px;
  height: 20px;
  color: #ca8a04;
  flex-shrink: 0;
  margin-top: 2px;
}

.warning-content {
  flex: 1;
  font-size: 0.9rem;
  color: #854d0e;
}

.warning-item.dark .warning-content {
  color: #fef3c7;
}

.warning-hint {
  display: block;
  margin-top: 4px;
  font-size: 0.85rem;
  color: #a16207;
}

.warning-item.dark .warning-hint {
  color: #fcd34d;
}

.warning-dismiss {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #ca8a04;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.warning-dismiss:hover {
  color: #854d0e;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-bottom: 20px;
}

.error-message.dark {
  background: #450a0a;
  border-color: #991b1b;
  color: #fca5a5;
}

.error-message svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.error-hint {
  margin: 8px 0 0;
  font-size: 0.9rem;
  color: #991b1b;
}

.error-message.dark .error-hint {
  color: #fecaca;
}

/* Named Locations Panel */
.named-locations-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.named-locations-panel.dark {
  background: #1e293b;
  border-color: #374151;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.panel-header h2.dark {
  color: #f1f5f9;
}

.panel-header h2 svg {
  width: 24px;
  height: 24px;
  color: #6366f1;
}

.locations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.location-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.location-card.dark {
  background: #0f172a;
  border-color: #374151;
}

.location-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.location-header.dark {
  border-bottom-color: #374151;
}

.location-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
}

.location-header h3.dark {
  color: #f1f5f9;
}

.location-badges {
  display: flex;
  gap: 6px;
}

.trust-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.trust-badge.trusted {
  background: #d1fae5;
  color: #065f46;
}

.trust-badge.untrusted {
  background: #fee2e2;
  color: #991b1b;
}

.type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  background: #e0e7ff;
  color: #3730a3;
}

.type-badge.dark {
  background: #312e81;
  color: #c7d2fe;
}

.location-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
}

.detail-label.dark {
  color: #9ca3af;
}

.detail-value {
  font-size: 0.85rem;
  color: #374151;
}

.detail-value.yes {
  color: #059669;
}

.detail-value.no {
  color: #6b7280;
}

.ip-ranges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ip-range {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.ip-range.dark {
  background: #374151;
  color: #e2e8f0;
}

.country-codes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.country-code {
  background: #dbeafe;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.country-code.dark {
  background: #1e3a5f;
  color: #93c5fd;
}

.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-tag {
  background: #fef3c7;
  color: #92400e;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.category-tag.dark {
  background: #78350f;
  color: #fde68a;
}

.associated-policies .policies-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 4px;
}

.associated-policy {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 6px 10px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.associated-policy.dark {
  background: #1e293b;
  border-color: #374151;
}

.policy-name {
  font-size: 0.85rem;
  color: #374151;
}

.policy-name.dark {
  color: #e2e8f0;
}

.direction-badge {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.direction-badge.include {
  background: #d1fae5;
  color: #065f46;
}

.direction-badge.exclude {
  background: #fecaca;
  color: #991b1b;
}

.no-policies {
  font-size: 0.85rem;
  color: #9ca3af;
  font-style: italic;
}

.no-policies.dark {
  color: #6b7280;
}

.summary-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.summary-panel.dark {
  background: #1e293b;
  border-color: #374151;
}

.summary-panel h2 {
  margin: 0 0 20px;
  font-size: 1.25rem;
  color: #1f2937;
}

.summary-panel h2.dark {
  color: #f1f5f9;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.summary-card.dark {
  background: #0f172a;
}

.summary-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
}

.summary-value.dark {
  color: #f1f5f9;
}

.summary-label {
  font-size: 0.85rem;
  color: #6b7280;
  margin-top: 4px;
}

.summary-label.dark {
  color: #9ca3af;
}

.summary-card.enabled .summary-value { color: #059669; }
.summary-card.disabled .summary-value { color: #dc2626; }
.summary-card.mfa .summary-value { color: #6366f1; }

.severity-section {
  margin-bottom: 24px;
}

.severity-section h3 {
  font-size: 1rem;
  margin: 0 0 12px;
  color: #374151;
}

.severity-section h3.dark {
  color: #e2e8f0;
}

.severity-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.severity-bar {
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 0.85rem;
  font-weight: 500;
  color: white;
  min-width: fit-content;
  transition: width 0.3s ease;
}

.severity-bar.high { background: #dc2626; }
.severity-bar.medium { background: #f59e0b; }
.severity-bar.low { background: #6366f1; }

.gaps-section, .bypass-section {
  margin-bottom: 24px;
}

.gaps-section h3, .bypass-section h3 {
  font-size: 1rem;
  margin: 0 0 12px;
  color: #374151;
}

.gaps-section h3.dark, .bypass-section h3.dark {
  color: #e2e8f0;
}

.gap-item {
  padding: 12px;
  background: #fef3c7;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.gap-item.dark {
  background: #78350f;
  color: #fef3c7;
}

.gap-severity {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 8px;
  text-transform: uppercase;
}

.gap-severity.critical { background: #dc2626; color: white; }
.gap-severity.high { background: #f59e0b; color: white; }
.gap-severity.info { background: #6366f1; color: white; }

.bypass-item {
  background: #f3f4f6;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.bypass-item.dark {
  background: #0f172a;
}

.bypass-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.bypass-type {
  background: #6366f1;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.bypass-policy {
  font-size: 0.85rem;
  color: #6b7280;
}

.bypass-policy.dark {
  color: #9ca3af;
}

.bypass-message {
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.bypass-message.dark {
  color: #e2e8f0;
}

.bypass-technique {
  font-size: 0.85rem;
  color: #374151;
  background: white;
  padding: 8px;
  border-radius: 4px;
}

.bypass-technique.dark {
  background: #1e293b;
  color: #e2e8f0;
}

.policies-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.policies-container.dark {
  background: #1e293b;
  border-color: #374151;
}

.policies-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.policies-header.dark {
  background: #0f172a;
  border-bottom-color: #374151;
}

.policies-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #1f2937;
}

.policies-header h2.dark {
  color: #f1f5f9;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.filter-controls select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.85rem;
  background: white;
}

.filter-controls select.dark {
  background: #374151;
  border-color: #4b5563;
  color: #e2e8f0;
}

.policies-list {
  max-height: 70vh;
  overflow-y: auto;
}

.policy-card {
  border-bottom: 1px solid #e5e7eb;
}

.policy-card.dark {
  border-bottom-color: #374151;
}

.policy-card:last-child {
  border-bottom: none;
}

.policy-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.2s;
}

.policy-header-row:hover {
  background: #f9fafb;
}

.policy-header-row.dark:hover {
  background: #0f172a;
}

.policy-info h3 {
  margin: 0 0 8px;
  font-size: 1rem;
  color: #1f2937;
}

.policy-info h3.dark {
  color: #f1f5f9;
}

.policy-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.state-badge, .severity-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.state-badge.enabled { background: #d1fae5; color: #065f46; }
.state-badge.disabled { background: #fee2e2; color: #991b1b; }
.state-badge.enabledforreportingbutnotenforced { background: #fef3c7; color: #92400e; }

.severity-badge.high { background: #fee2e2; color: #dc2626; }
.severity-badge.medium { background: #fef3c7; color: #d97706; }
.severity-badge.low { background: #dbeafe; color: #1d4ed8; }
.severity-badge.info { background: #f3f4f6; color: #6b7280; }

.bypass-count {
  font-size: 0.75rem;
  color: #dc2626;
  font-weight: 500;
}

.expand-icon {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  transition: transform 0.2s;
}

.expand-icon.dark {
  color: #6b7280;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.policy-details {
  padding: 20px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.policy-details.dark {
  background: #0f172a;
  border-top-color: #374151;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-section.dark {
  border-bottom-color: #374151;
}

.detail-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detail-section h4 {
  margin: 0 0 12px;
  font-size: 0.95rem;
  color: #374151;
}

.detail-section h4.dark {
  color: #e2e8f0;
}

.controls-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.control-badge {
  background: #dbeafe;
  color: #1e40af;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}

.control-badge.dark {
  background: #1e3a5f;
  color: #93c5fd;
}

.operator {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #6b7280;
}

.operator.dark {
  color: #9ca3af;
}

.condition-group {
  margin-bottom: 16px;
}

.condition-group:last-child {
  margin-bottom: 0;
}

.condition-group h5 {
  margin: 0 0 8px;
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 600;
}

.condition-group h5.dark {
  color: #9ca3af;
}

.condition-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.condition-row .label {
  font-size: 0.8rem;
  color: #6b7280;
  min-width: 60px;
}

.condition-row .label.dark {
  color: #9ca3af;
}

.tag {
  background: #e5e7eb;
  color: #374151;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.tag.dark {
  background: #374151;
  color: #e2e8f0;
}

.tag.all {
  background: #6366f1;
  color: white;
}

.tag.exclude {
  background: #fecaca;
  color: #991b1b;
}

.tag.risk {
  background: #fef3c7;
  color: #92400e;
}

.tag.location-tag {
  background: #e0e7ff;
  color: #3730a3;
}

.tag.location-tag.dark {
  background: #312e81;
  color: #c7d2fe;
}

/* Unresolved items styling */
.unresolved {
  border: 1px dashed #9ca3af !important;
  background: #f3f4f6 !important;
  color: #6b7280 !important;
  font-style: italic;
}

.no-data {
  font-size: 0.85rem;
  color: #9ca3af;
  font-style: italic;
}

.no-data.dark {
  color: #6b7280;
}

.members-list {
  margin: 8px 0;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.members-list.dark {
  background: #1e293b;
  border-color: #374151;
}

.members-category {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 0.8rem;
  color: #6b7280;
}

.members-category.dark {
  color: #9ca3af;
}

.category-icon {
  font-size: 0.9rem;
}

.category-label {
  font-weight: 500;
}

.members-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.member-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: default;
}

.member-tag.user-tag {
  background: #dbeafe;
  color: #1e40af;
}

.member-tag.user-tag.dark {
  background: #1e3a5f;
  color: #93c5fd;
}

.member-tag.group-tag {
  background: #d1fae5;
  color: #065f46;
}

.member-tag.group-tag.dark {
  background: #064e3b;
  color: #6ee7b7;
}

.member-tag.role-tag {
  background: #fef3c7;
  color: #92400e;
}

.member-tag.role-tag.dark {
  background: #78350f;
  color: #fde68a;
}

.member-tag.exclude-tag {
  background: #fecaca;
  color: #991b1b;
}

.exclusions-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}

.exclusions-section.dark {
  border-top-color: #374151;
}

.exclude-row {
  margin-bottom: 8px;
}

.exclude-row .label {
  color: #dc2626;
  font-weight: 500;
}

.session-control {
  font-size: 0.9rem;
  margin-bottom: 8px;
  color: #374151;
}

.session-control.dark {
  color: #e2e8f0;
}

.detail-section.analysis {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.detail-section.analysis.dark {
  background: #1e293b;
  border-color: #374151;
}

.findings {
  margin-bottom: 16px;
}

.finding {
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.finding.warning {
  background: #fef3c7;
  color: #92400e;
}

.finding.info {
  background: #dbeafe;
  color: #1e40af;
}

.bypass-opportunities h5 {
  margin: 0 0 12px;
  font-size: 0.9rem;
  color: #dc2626;
}

.bypass-opportunities h5.dark {
  color: #f87171;
}

.bypass-opportunities .bypass-item {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.bypass-type-badge {
  background: #fee2e2;
  color: #dc2626;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  height: fit-content;
}

.bypass-content {
  flex: 1;
}

.bypass-msg {
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.bypass-msg.dark {
  color: #e2e8f0;
}

.bypass-tech {
  font-size: 0.85rem;
  color: #6b7280;
}

.bypass-tech.dark {
  color: #9ca3af;
}

.no-issues {
  color: #059669;
  font-size: 0.9rem;
}

.detail-section.metadata {
  background: white;
  padding: 12px;
  border-radius: 6px;
}

.detail-section.metadata.dark {
  background: #1e293b;
}

.meta-item {
  font-size: 0.85rem;
  margin-bottom: 6px;
  color: #6b7280;
}

.meta-item.dark {
  color: #9ca3af;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.meta-item .label {
  font-weight: 500;
  margin-right: 8px;
}

.meta-item code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.meta-item code.dark {
  background: #374151;
  color: #e2e8f0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-state.dark {
  color: #9ca3af;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px;
  color: #374151;
}

.empty-state h3.dark {
  color: #e2e8f0;
}

.empty-state p {
  margin: 0 0 8px;
}

.empty-state .note {
  font-size: 0.85rem;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .btn {
    flex: 1;
    justify-content: center;
    min-width: 120px;
  }
  
  .policies-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .filter-controls {
    width: 100%;
  }
  
  .filter-controls select {
    flex: 1;
  }
  
  .locations-grid {
    grid-template-columns: 1fr;
  }
}
</style>
