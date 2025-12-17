<template>
  <div class="container mx-auto px-4 py-6">
    <div :class="[bgPrimary, borderPrimary, 'rounded-lg shadow-md border']">
      <!-- Header -->
      <div :class="[borderPrimary, 'border-b p-6']">
        <div class="flex items-center justify-between">
          <div>
            <h1 :class="[textPrimary, 'text-2xl font-bold']">Microsoft Teams</h1>
            <p :class="[textSecondary, 'mt-1']">Chats, Teams and Channels</p>
          </div>
          
          <!-- API Toggle -->
          <div :class="[bgSecondary, 'flex items-center space-x-3 rounded-lg p-2']">
            <button
              @click="apiMode = 'graph'"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
                apiMode === 'graph'
                  ? [bgPrimary, 'text-blue-400 shadow-sm']
                  : [textSecondary, 'hover:text-blue-400']
              ]"
            >
              📊 Graph API
            </button>
            <button
              @click="apiMode = 'skype'"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
                apiMode === 'skype'
                  ? [bgPrimary, 'text-green-400 shadow-sm']
                  : [textSecondary, 'hover:text-green-400']
              ]"
            >
              💬 Skype API
            </button>
          </div>
        </div>
        
        <!-- API Info Banner -->
        <div v-if="apiMode === 'skype'" :class="[isDark ? 'bg-green-900/30 border-green-700' : 'bg-green-100 border-green-300', 'mt-4 p-3 border rounded-lg']">
          <p :class="[isDark ? 'text-green-300' : 'text-green-800', 'text-sm']">
            <i class="fas fa-info-circle mr-2"></i>
            <strong>Skype API Mode:</strong> Uses Skype backend (no Chat.Read scope required). Requires Access Token for <code :class="[isDark ? 'bg-green-900/50' : 'bg-green-200', 'px-1 rounded']">https://api.spaces.skype.com</code>
          </p>
        </div>
        <div v-else :class="[isDark ? 'bg-blue-900/30 border-blue-700' : 'bg-blue-100 border-blue-300', 'mt-4 p-3 border rounded-lg']">
          <p :class="[isDark ? 'text-blue-300' : 'text-blue-800', 'text-sm']">
            <i class="fas fa-info-circle mr-2"></i>
            <strong>Graph API Mode:</strong> Standard Microsoft Graph API. Requires Chat.Read scope.
          </p>
        </div>
      </div>

      <!-- Tabs -->
      <div :class="[borderPrimary, 'border-b']">
        <nav class="flex -mb-px">
          <button
            @click="activeTab = 'chats'"
            :class="[
              'py-4 px-6 font-medium text-sm border-b-2 transition-colors',
              activeTab === 'chats'
                ? 'border-blue-500 text-blue-400'
                : ['border-transparent', textSecondary, isDark ? 'hover:text-white hover:border-gray-600' : 'hover:text-gray-900 hover:border-gray-400']
            ]"
          >
            <i class="fas fa-comments mr-2"></i>
            Chats
          </button>
          <button
            @click="activeTab = 'teams'"
            :class="[
              'py-4 px-6 font-medium text-sm border-b-2 transition-colors',
              activeTab === 'teams'
                ? 'border-blue-500 text-blue-400'
                : ['border-transparent', textSecondary, isDark ? 'hover:text-white hover:border-gray-600' : 'hover:text-gray-900 hover:border-gray-400']
            ]"
          >
            <i class="fas fa-users mr-2"></i>
            Teams & Channels
          </button>
        </nav>
      </div>

      <!-- Chats Tab -->
      <div v-show="activeTab === 'chats'" class="p-6">
        <!-- Loading -->
        <div v-if="loadingChats" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p :class="[textSecondary, 'mt-2']">Loading chats...</p>
        </div>

        <!-- Error -->
        <div v-else-if="chatsError" :class="[isDark ? 'bg-red-900/30 border-red-700 text-red-300' : 'bg-red-100 border-red-300 text-red-800', 'border rounded-lg p-4']">
          <p><i class="fas fa-exclamation-circle mr-2"></i>{{ chatsError }}</p>
        </div>

        <!-- Chats List -->
        <div v-else-if="(apiMode === 'graph' && chats.length > 0) || (apiMode === 'skype' && skypeConversations.length > 0)" class="space-y-3">
          <!-- Graph API Chats -->
          <div
            v-if="apiMode === 'graph'"
            v-for="chat in chats"
            :key="chat.id"
            @click="openChat(chat)"
            :class="[
              borderPrimary,
              isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
              'border rounded-lg p-4 cursor-pointer transition-colors'
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center">
                  <i :class="[isDark ? 'text-gray-500' : 'text-gray-400', 'fas fa-comment-dots mr-2']"></i>
                  <h3 :class="[textPrimary, 'font-medium']">
                    {{ getChatTitle(chat) }}
                  </h3>
                </div>
                <p :class="[textSecondary, 'text-sm mt-1']" v-if="chat.lastMessagePreview">
                  {{ chat.lastMessagePreview.content.substring(0, 150) }}...
                </p>
                <div :class="[isDark ? 'text-gray-500' : 'text-gray-500', 'flex items-center mt-2 text-xs']">
                  <span v-if="chat.lastMessagePreview">
                    {{ formatDate(chat.lastMessagePreview.createdDateTime) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Skype API Conversations -->
          <div
            v-if="apiMode === 'skype'"
            v-for="conv in skypeConversations"
            :key="conv.id"
            @click="openSkypeConversation(conv)"
            :class="[
              borderPrimary,
              isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
              'border rounded-lg p-4 cursor-pointer transition-colors'
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center">
                  <i class="fas fa-comment-dots text-green-500 mr-2"></i>
                  <h3 :class="[textPrimary, 'font-medium']">
                    {{ getSkypeConvTitle(conv) }}
                  </h3>
                </div>
                <p :class="[textSecondary, 'text-sm mt-1']" v-if="conv.lastMessage">
                  {{ stripHtml(conv.lastMessage.content).substring(0, 150) }}...
                </p>
                <div class="flex items-center mt-2 text-xs text-gray-500">
                  <span v-if="conv.lastMessage">
                    {{ formatDate(conv.lastMessage.originalarrivaltime) }}
                  </span>
                  <span :class="[isDark ? 'bg-green-900/50 text-green-300' : 'bg-green-200 text-green-800', 'ml-2 px-2 py-0.5 rounded-full text-xs']">
                    Skype API
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No Chats -->
        <div v-else :class="[textSecondary, 'text-center py-8']">
          <i class="fas fa-comments text-4xl mb-3"></i>
          <p>No chats found</p>
        </div>
      </div>

      <!-- Teams Tab -->
      <div v-show="activeTab === 'teams'" class="p-6">
        <!-- Loading -->
        <div v-if="loadingTeams" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p :class="[textSecondary, 'mt-2']">Loading teams...</p>
        </div>

        <!-- Error -->
        <div v-else-if="teamsError" :class="[isDark ? 'bg-red-900/30 border-red-700 text-red-300' : 'bg-red-100 border-red-300 text-red-800', 'border rounded-lg p-4']">
          <p><i class="fas fa-exclamation-circle mr-2"></i>{{ teamsError }}</p>
        </div>

        <!-- Teams List -->
        <div v-else-if="teams.length > 0" class="space-y-4">
          <div
            v-for="team in teams"
            :key="team.id"
            :class="[borderPrimary, 'border rounded-lg']"
          >
            <!-- Team Header -->
            <div
              @click="toggleTeam(team.id)"
              :class="[
                isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
                'p-4 cursor-pointer transition-colors flex items-center justify-between'
              ]"
            >
              <div class="flex items-center">
                <i class="fas fa-users text-blue-500 mr-3"></i>
                <div>
                  <h3 :class="[textPrimary, 'font-medium']">{{ team.displayName }}</h3>
                  <p :class="[textSecondary, 'text-sm']" v-if="team.description">{{ team.description }}</p>
                </div>
              </div>
              <i
                :class="[
                  'fas transition-transform',
                  textSecondary,
                  expandedTeams.includes(team.id) ? 'fa-chevron-up' : 'fa-chevron-down'
                ]"
              ></i>
            </div>

            <!-- Channels (collapsed by default) -->
            <div v-show="expandedTeams.includes(team.id)" :class="[borderPrimary, isDark ? 'bg-gray-900/50' : 'bg-gray-50', 'border-t p-4']">
              <!-- Loading Channels -->
              <div v-if="loadingChannels[team.id]" class="text-center py-4">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <p :class="[textSecondary, 'text-sm mt-2']">Loading channels...</p>
              </div>

              <!-- Channels List -->
              <div v-else-if="teamChannels[team.id] && teamChannels[team.id].length > 0" class="space-y-2">
                <div
                  v-for="channel in teamChannels[team.id]"
                  :key="channel.id"
                  @click="openChannel(team, channel)"
                  :class="[
                    bgSecondary,
                    borderPrimary,
                    isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200',
                    'border rounded p-3 cursor-pointer transition-colors'
                  ]"
                >
                  <div class="flex items-center">
                    <i :class="[isDark ? 'text-gray-500' : 'text-gray-400', 'fas fa-hashtag mr-2']"></i>
                    <span :class="[textPrimary, 'font-medium']">{{ channel.displayName }}</span>
                  </div>
                  <p :class="[textSecondary, 'text-sm mt-1']" v-if="channel.description">
                    {{ channel.description }}
                  </p>
                </div>
              </div>

              <!-- No Channels -->
              <div v-else :class="[textSecondary, 'text-center py-4 text-sm']">
                <p>No channels found</p>
              </div>
            </div>
          </div>
        </div>

        <!-- No Teams -->
        <div v-else :class="[textSecondary, 'text-center py-8']">
          <i class="fas fa-users text-4xl mb-3"></i>
          <p>No teams found</p>
        </div>
      </div>
    </div>

    <!-- Chat/Channel Messages Modal -->
    <div
      v-if="selectedChat || selectedChannel || selectedConversation"
      class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4"
      @click.self="closeMessages"
    >
      <div :class="[bgPrimary, borderPrimary, 'rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col border']">
        <!-- Modal Header -->
        <div :class="[borderPrimary, 'border-b p-4 flex items-center justify-between']">
          <div>
            <h2 :class="[textPrimary, 'text-xl font-bold']">
              {{ selectedChat ? getChatTitle(selectedChat) : selectedConversation ? getSkypeConvTitle(selectedConversation) : selectedChannel?.displayName }}
            </h2>
            <p :class="[textSecondary, 'text-sm']" v-if="selectedChannel">
              {{ selectedTeam?.displayName }}
            </p>
            <p class="text-sm text-green-400" v-if="selectedConversation">
              <i class="fas fa-check-circle mr-1"></i> Skype API
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 1rem;">
            <!-- Refresh Button -->
            <button
              @click="refreshMessages"
              :disabled="loadingMessages"
              style="color: #9CA3AF; background: transparent; border: none; cursor: pointer; padding: 0.5rem; font-size: 1.125rem; min-width: 40px;"
              title="Refresh messages"
            >
              <span :style="{ display: 'inline-block', transform: loadingMessages ? 'rotate(360deg)' : 'none', transition: 'transform 0.5s' }">🔄</span>
            </button>
            <!-- Close Button -->
            <button
              @click="closeMessages"
              style="color: #9CA3AF; background: transparent; border: none; cursor: pointer; padding: 0.5rem; font-size: 1.25rem; min-width: 40px;"
            >
              <span>✖</span>
            </button>
          </div>
        </div>

        <!-- Messages Container -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <!-- Loading Messages -->
          <div v-if="loadingMessages" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p :class="[textSecondary, 'mt-2']">Loading messages...</p>
          </div>

          <!-- Messages List -->
          <div v-else-if="messages.length > 0" class="space-y-3">
            <!-- Modern message bubbles for Skype API and Graph API chats -->
            <template v-if="(apiMode === 'skype' && selectedConversation) || (apiMode === 'graph' && selectedChat)">
              <div
                v-for="message in messages"
                :key="message.id"
                :class="[
                  'flex gap-2',
                  message.isFromMe ? 'justify-end' : 'justify-start'
                ]"
              >
                <!-- Avatar (only for others) -->
                <div 
                  v-if="!message.isFromMe"
                  class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                  :style="{ backgroundColor: getAvatarColor(message.from || message.id) }"
                >
                  {{ getInitials(getMessageSenderName(message)) }}
                </div>

                <!-- Message Bubble -->
                <div 
                  class="max-w-[70%] rounded-2xl px-4 py-2"
                  :class="message.isFromMe ? 'bg-blue-600 text-white rounded-tr-sm' : [isDark ? 'bg-gray-700 text-gray-100' : 'bg-gray-200 text-gray-900', 'rounded-tl-sm']"
                >
                  <!-- Sender name (for others) -->
                  <div v-if="!message.isFromMe" class="text-xs opacity-75 mb-1 font-medium">
                    {{ getMessageSenderName(message) }}
                  </div>
                  
                  <!-- Message content -->
                  <div class="text-sm break-words" v-html="renderMessageContent(message)"></div>
                  
                  <!-- Link Preview Card (Teams-style) -->
                  <div v-if="message.linkPreviews && message.linkPreviews.length > 0" class="mt-2">
                    <div 
                      v-for="(preview, idx) in message.linkPreviews" 
                      :key="idx"
                      class="border border-gray-600 rounded-lg overflow-hidden bg-gray-800 hover:bg-gray-750 transition-colors cursor-pointer"
                      @click="openUrl(preview.url)"
                    >
                      <!-- Preview Image -->
                      <img 
                        v-if="preview.preview.previewurl" 
                        :src="preview.preview.previewurl" 
                        :alt="preview.preview.title"
                        class="w-full h-32 object-cover"
                        @error="$event.target.style.display='none'"
                      />
                      
                      <!-- Preview Content -->
                      <div class="p-3">
                        <div class="text-sm font-medium text-white mb-1">
                          {{ preview.preview.title }}
                        </div>
                        <div class="text-xs text-gray-400">
                          {{ preview.preview.description }}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Timestamp -->
                  <div class="text-xs opacity-75 mt-1">
                    {{ formatMessageTime(getMessageDateTime(message)) }}
                  </div>
                </div>
              </div>
            </template>

            <!-- Channel messages (keep old style) -->
            <template v-else>
              <div
                v-for="message in messages"
                :key="message.id"
                class="border border-gray-700 rounded-lg p-4"
              >
                <div class="flex items-start">
                  <div class="flex-1">
                    <div class="flex items-center mb-2">
                      <span class="font-medium text-white">
                        {{ getMessageSenderName(message) }}
                      </span>
                      <span class="text-xs text-gray-500 ml-2">
                        {{ formatDate(getMessageDateTime(message)) }}
                      </span>
                    </div>
                    <div
                      class="text-gray-300"
                      v-html="getMessageContent(message)"
                    ></div>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- No Messages -->
          <div v-else :class="[textSecondary, 'text-center py-8']">
            <i class="fas fa-comments text-4xl mb-3"></i>
            <p>No messages</p>
          </div>
        </div>

        <!-- Send Message Form -->
        <div :class="[borderPrimary, 'border-t p-4']">
          <div class="flex space-x-2">
            <input
              v-model="newMessage"
              type="text"
              placeholder="Type a message..."
              :class="[
                isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
                'flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
              ]"
              @keyup.enter="sendMessage"
            />
            <button
              @click="sendMessage"
              :disabled="!newMessage.trim() || sendingMessage"
              :class="[
                sendingMessage || !newMessage.trim() ? (isDark ? 'bg-gray-600' : 'bg-gray-400') : 'bg-blue-600 hover:bg-blue-700',
                'px-6 py-2 text-white rounded-lg disabled:cursor-not-allowed transition-colors flex items-center gap-2'
              ]"
            >
              <i class="fas fa-paper-plane" v-if="!sendingMessage"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              <span>{{ sendingMessage ? 'Sending...' : 'Send' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'TeamsView',
  
  props: {
    isDark: {
      type: Boolean,
      default: true
    }
  },
  
  data() {
    return {
      activeTab: 'chats',
      apiMode: 'skype', // Default to Skype API (no scope required)
      
      // Chats
      chats: [],
      loadingChats: false,
      chatsError: null,
      
      // Teams
      teams: [],
      loadingTeams: false,
      teamsError: null,
      expandedTeams: [],
      
      // Channels
      teamChannels: {},
      loadingChannels: {},
      
      // Messages
      selectedChat: null,
      selectedChannel: null,
      selectedTeam: null,
      messages: [],
      loadingMessages: false,
      newMessage: '',
      sendingMessage: false,
      currentUserId: null,  // Current user ID for "You" detection
      
      // Skype API
      skypeConversations: [],
      selectedConversation: null
    };
  },
  
  computed: {
    // Dynamic theme classes
    bgPrimary() {
      return this.isDark ? 'bg-gray-800' : 'bg-white';
    },
    bgSecondary() {
      return this.isDark ? 'bg-gray-700' : 'bg-gray-100';
    },
    bgTertiary() {
      return this.isDark ? 'bg-gray-900' : 'bg-gray-50';
    },
    textPrimary() {
      return this.isDark ? 'text-white' : 'text-gray-900';
    },
    textSecondary() {
      return this.isDark ? 'text-gray-400' : 'text-gray-600';
    },
    textTertiary() {
      return this.isDark ? 'text-gray-300' : 'text-gray-700';
    },
    borderPrimary() {
      return this.isDark ? 'border-gray-700' : 'border-gray-300';
    },
    borderSecondary() {
      return this.isDark ? 'border-gray-600' : 'border-gray-400';
    }
  },
  
  mounted() {
    this.loadChats();
    this.loadTeams();
  },
  
  watch: {
    apiMode() {
      // Reload chats when API mode changes
      this.loadChats();
    }
  },
  
  methods: {
    showToast(message, type = 'info') {
      // Simple toast implementation
      console.log(`[TOAST ${type.toUpperCase()}]:`, message);
      
      // You can replace this with a proper toast library later
      // For now, just use alert for critical errors
      if (type === 'error' && message.includes('scope permissions')) {
        alert(`❌ Missing Permissions\n\n${message}\n\nYou need a token with ChatMessage.Send or Chat.ReadWrite scope to send messages.`);
      } else if (type === 'success') {
        console.log('✅', message);
      } else if (type === 'error') {
        console.error('❌', message);
      }
    },
    
    async loadChats() {
      if (this.apiMode === 'skype') {
        return this.loadSkypeConversations();
      }
      
      this.loadingChats = true;
      this.chatsError = null;
      
      try {
        const response = await axios.get('http://localhost:5000/api/teams/chats');
        this.chats = response.data.chats || [];
      } catch (error) {
        console.error('Error loading chats:', error);
        this.chatsError = error.response?.data?.error || 'Failed to load chats';
      } finally {
        this.loadingChats = false;
      }
    },
    
    async loadSkypeConversations() {
      this.loadingChats = true;
      this.chatsError = null;
      
      try {
        const response = await axios.get('http://localhost:5000/api/teams/skype/conversations');
        
        if (response.data.success) {
          this.skypeConversations = response.data.conversations || [];
        } else {
          this.chatsError = response.data.error || 'Failed to load Skype conversations';
        }
      } catch (error) {
        console.error('Error loading Skype conversations:', error);
        this.chatsError = error.response?.data?.error || 'Failed to load conversations. Ensure active token is for api.spaces.skype.com';
      } finally {
        this.loadingChats = false;
      }
    },
    
    async loadTeams() {
      this.loadingTeams = true;
      this.teamsError = null;
      
      try {
        const response = await axios.get('http://localhost:5000/api/teams/teams');
        this.teams = response.data.teams || [];
      } catch (error) {
        console.error('Error loading teams:', error);
        this.teamsError = error.response?.data?.error || 'Failed to load teams';
      } finally {
        this.loadingTeams = false;
      }
    },
    
    async toggleTeam(teamId) {
      const index = this.expandedTeams.indexOf(teamId);
      
      if (index > -1) {
        this.expandedTeams.splice(index, 1);
      } else {
        this.expandedTeams.push(teamId);
        
        // Load channels if not already loaded
        if (!this.teamChannels[teamId]) {
          await this.loadChannels(teamId);
        }
      }
    },
    
    async loadChannels(teamId) {
      this.loadingChannels[teamId] = true;
      
      try {
        const response = await axios.get(`http://localhost:5000/api/teams/teams/${teamId}/channels`);
        this.teamChannels[teamId] = response.data.channels || [];
      } catch (error) {
        console.error('Error loading channels:', error);
        this.teamChannels[teamId] = [];
      } finally {
        this.loadingChannels[teamId] = false;
      }
    },
    
    async openChat(chat) {
      this.selectedChat = chat;
      this.selectedChannel = null;
      this.selectedTeam = null;
      this.messages = [];
      this.newMessage = '';
      
      await this.loadChatMessages(chat.id);
    },
    
    async openChannel(team, channel) {
      this.selectedChannel = channel;
      this.selectedTeam = team;
      this.selectedChat = null;
      this.messages = [];
      this.newMessage = '';
      
      await this.loadChannelMessages(team.id, channel.id);
    },
    
    async loadChatMessages(chatId) {
      console.log('[TeamsView] Loading messages for chat:', chatId);
      this.loadingMessages = true;
      
      // FAILSAFE: Force loading to false after 10 seconds NO MATTER WHAT
      const failsafeTimeout = setTimeout(() => {
        console.error('[TeamsView] FAILSAFE TIMEOUT - Forcing loading to false');
        this.loadingMessages = false;
        this.showToast('Request timeout - server not responding', 'error');
      }, 10000);
      
      try {
        console.log('[TeamsView] Sending request to backend...');
        
        // Create timeout promise
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('REQUEST_TIMEOUT')), 8000);
        });
        
        // Create request promise
        const requestPromise = axios.get(`http://localhost:5000/api/teams/chats/${chatId}/messages`);
        
        // Race between timeout and request
        const response = await Promise.race([requestPromise, timeoutPromise]);
        
        console.log('[TeamsView] Response received:', response.status);
        
        const messages = response.data.messages || response.data.value || response.data || [];
        
        // Save current user ID for "You" detection
        if (response.data.current_user_id) {
          this.currentUserId = response.data.current_user_id;
          console.log('[TeamsView] Current user ID:', this.currentUserId);
        }
        
        // Messages already have isFromMe flag from backend
        this.messages = messages;
        
        console.log('[TeamsView] Messages loaded:', this.messages.length);
        
        if (this.messages.length === 0) {
          this.showToast('No messages found in this chat', 'error');
        }
      } catch (error) {
        console.error('[TeamsView] Error loading chat messages:', error);
        this.messages = [];
        
        if (error.message === 'REQUEST_TIMEOUT') {
          this.showToast('Request timeout (8s) - backend not responding', 'error');
        } else if (error.response) {
          const errorMsg = error.response.data?.error || 'Server error';
          this.showToast(`Failed: ${errorMsg} (${error.response.status})`, 'error');
        } else if (error.request) {
          this.showToast('Backend not responding - check Flask is running on port 5000', 'error');
        } else {
          this.showToast('Error: ' + error.message, 'error');
        }
      } finally {
        clearTimeout(failsafeTimeout);  // Clear failsafe if we finished normally
        this.loadingMessages = false;
        console.log('[TeamsView] loadingMessages set to false');
      }
    },
    
    async loadChannelMessages(teamId, channelId) {
      console.log('[TeamsView] Loading channel messages:', teamId, channelId);
      this.loadingMessages = true;
      
      // FAILSAFE: Force loading to false after 10 seconds NO MATTER WHAT
      const failsafeTimeout = setTimeout(() => {
        console.error('[TeamsView] FAILSAFE TIMEOUT - Forcing loading to false');
        this.loadingMessages = false;
        this.showToast('Request timeout - server not responding', 'error');
      }, 10000);
      
      try {
        console.log('[TeamsView] Sending request to backend...');
        
        // Create timeout promise
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('REQUEST_TIMEOUT')), 8000);
        });
        
        // Create request promise
        const requestPromise = axios.get(
          `http://localhost:5000/api/teams/teams/${teamId}/channels/${channelId}/messages`
        );
        
        // Race between timeout and request
        const response = await Promise.race([requestPromise, timeoutPromise]);
        
        console.log('[TeamsView] Response received:', response.status);
        this.messages = response.data.messages || response.data.value || response.data || [];
        console.log('[TeamsView] Messages loaded:', this.messages.length);
        
        if (this.messages.length === 0) {
          this.showToast('No messages found in this channel', 'error');
        }
      } catch (error) {
        console.error('[TeamsView] Error loading channel messages:', error);
        this.messages = [];
        
        if (error.message === 'REQUEST_TIMEOUT') {
          this.showToast('Request timeout (8s) - backend not responding', 'error');
        } else if (error.response) {
          const errorMsg = error.response.data?.error || 'Server error';
          this.showToast(`Failed: ${errorMsg} (${error.response.status})`, 'error');
        } else if (error.request) {
          this.showToast('Backend not responding - check Flask on port 5000', 'error');
        } else {
          this.showToast('Error: ' + error.message, 'error');
        }
      } finally {
        clearTimeout(failsafeTimeout);
        this.loadingMessages = false;
        console.log('[TeamsView] loadingMessages set to false');
      }
    },
    
    async sendMessage() {
      if (!this.newMessage.trim() || this.sendingMessage) return;
      
      this.sendingMessage = true;
      
      try {
        if (this.selectedConversation && this.apiMode === 'skype') {
          // Send via Skype API
          await axios.post('http://localhost:5000/api/teams/skype/conversations/send', {
            conversation_link: this.selectedConversation.messages,
            content: this.newMessage
          });
          
          this.showToast('Message sent!', 'success');
          this.newMessage = '';
          
          // Reload messages (bypass cache)
          await this.loadSkypeConversationMessages(this.selectedConversation.messages);
          
        } else if (this.selectedChat) {
          // Send to Graph API chat
          const messageData = {
            content: this.newMessage,
            contentType: 'text'
          };
          
          await axios.post(
            `http://localhost:5000/api/teams/chats/${this.selectedChat.id}/messages`,
            messageData
          );
          
          this.showToast('Message sent!', 'success');
          this.newMessage = '';
          
          // Force reload messages with cache bypass
          const timestamp = Date.now();
          const response = await axios.get(
            `http://localhost:5000/api/teams/chats/${this.selectedChat.id}/messages?load_all=true&_nocache=${timestamp}`
          );
          
          const messages = response.data.messages || response.data.value || [];
          if (response.data.current_user_id) {
            this.currentUserId = response.data.current_user_id;
          }
          this.messages = messages;
          console.log('[TeamsView] Messages reloaded after send:', messages.length);
          
        } else if (this.selectedChannel) {
          // Send to Graph API channel
          const messageData = {
            content: this.newMessage,
            contentType: 'html'
          };
          
          await axios.post(
            `http://localhost:5000/api/teams/teams/${this.selectedTeam.id}/channels/${this.selectedChannel.id}/messages`,
            messageData
          );
          
          this.showToast('Message sent!', 'success');
          this.newMessage = '';
          
          // Reload messages
          await this.loadChannelMessages(this.selectedTeam.id, this.selectedChannel.id);
        }
        
      } catch (error) {
        console.error('Error sending message:', error);
        this.showToast('Failed to send message: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.sendingMessage = false;
      }
    },
    
    closeMessages() {
      this.selectedChat = null;
      this.selectedChannel = null;
      this.selectedTeam = null;
      this.selectedConversation = null;
      this.messages = [];
      this.newMessage = '';
    },
    
    refreshMessages() {
      console.log('[TeamsView] Manual refresh triggered');
      
      if (this.selectedChat) {
        console.log('[TeamsView] Refreshing chat messages');
        this.loadChatMessages(this.selectedChat.id);
      } else if (this.selectedChannel && this.selectedTeam) {
        console.log('[TeamsView] Refreshing channel messages');
        this.loadChannelMessages(this.selectedTeam.id, this.selectedChannel.id);
      } else if (this.selectedConversation) {
        console.log('[TeamsView] Refreshing Skype conversation messages');
        this.loadSkypeConversationMessages(this.selectedConversation.messages);
      }
    },
    
    getChatTitle(chat) {
      if (chat.topic) {
        return chat.topic;
      }
      
      if (chat.members && chat.members.length > 0) {
        const memberNames = chat.members
          .filter(m => m.displayName)
          .map(m => m.displayName)
          .join(', ');
        return memberNames || 'Unnamed Chat';
      }
      
      return 'Unnamed Chat';
    },
    
    getSkypeConvTitle(conv) {
      // Use extracted contact name from messages
      if (conv.contactName) {
        return conv.contactName;
      }
      
      // Try threadProperties
      if (conv.threadProperties && conv.threadProperties.topic) {
        return conv.threadProperties.topic;
      }
      
      // Fallback to conversation ID (shortened)
      if (conv.id) {
        // Show only last part after @ for readability
        const parts = conv.id.split('@');
        if (parts.length > 1) {
          return parts[0].substring(0, 30) + '...';
        }
        return conv.id.substring(0, 30) + '...';
      }
      
      return 'Unnamed Conversation';
    },
    
    stripHtml(html) {
      if (!html) return '';
      const tmp = document.createElement('div');
      tmp.innerHTML = html;
      return tmp.textContent || tmp.innerText || '';
    },
    
    async openSkypeConversation(conv) {
      this.selectedConversation = conv;
      this.selectedChat = null;
      this.selectedChannel = null;
      this.messages = [];
      this.newMessage = '';
      
      await this.loadSkypeConversationMessages(conv.messages);
    },
    
    async loadSkypeConversationMessages(conversationLink) {
      console.log('[TeamsView] Loading Skype messages:', conversationLink);
      this.loadingMessages = true;
      
      // FAILSAFE: Force loading to false after 10 seconds NO MATTER WHAT
      const failsafeTimeout = setTimeout(() => {
        console.error('[TeamsView] FAILSAFE TIMEOUT - Forcing loading to false');
        this.loadingMessages = false;
        this.showToast('Request timeout - server not responding', 'error');
      }, 10000);
      
      try {
        console.log('[TeamsView] Sending Skype API request...');
        
        // Create timeout promise
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('REQUEST_TIMEOUT')), 8000);
        });
        
        // Create request promise
        const requestPromise = axios.post('http://localhost:5000/api/teams/skype/conversations/messages', {
          conversation_link: conversationLink
        });
        
        // Race between timeout and request
        const response = await Promise.race([requestPromise, timeoutPromise]);
        
        console.log('[TeamsView] Skype response received:', response.status);
        
        if (response.data.success) {
          // Filter out system messages and enrich with parsed data
          this.messages = (response.data.messages || [])
            .filter(msg => {
              // Skip system messages (ThreadActivity/*)
              const msgType = msg.messagetype || '';
              return !msgType.startsWith('ThreadActivity/');
            })
            .map(msg => {
              // Add isFromMe flag
              if (msg.isFromMe === undefined) {
                const from = msg.from || '';
                const displayName = msg.imdisplayname || '';
                msg.isFromMe = displayName.includes('SpecterPortal') || 
                               from.includes('SpecterPortal') ||
                               displayName === 'You';
              }
              
              // Parse properties.links for preview cards
              msg.linkPreviews = [];
              if (msg.properties && msg.properties.links) {
                try {
                  const links = JSON.parse(msg.properties.links);
                  msg.linkPreviews = links.filter(link => 
                    link.previewenabled && link.preview
                  );
                } catch (e) {
                  // Ignore parse errors
                }
              }
              
              return msg;
            });
          
          // Extract contact name from messages (the person who is NOT me)
          if (this.selectedConversation && this.messages.length > 0) {
            for (const msg of this.messages) {
              if (!msg.isFromMe && msg.imdisplayname) {
                this.selectedConversation.contactName = msg.imdisplayname;
                break;
              }
            }
          }
          
          console.log('[TeamsView] Skype messages loaded:', this.messages.length);
          
          if (this.messages.length === 0) {
            this.showToast('No messages found in this conversation', 'error');
          }
        } else {
          this.messages = [];
          this.showToast('Failed: ' + (response.data.error || 'Unknown error'), 'error');
        }
      } catch (error) {
        console.error('[TeamsView] Error loading Skype messages:', error);
        this.messages = [];
        
        if (error.message === 'REQUEST_TIMEOUT') {
          this.showToast('Request timeout (8s) - backend not responding', 'error');
        } else if (error.response) {
          const errorMsg = error.response.data?.error || 'Server error';
          this.showToast(`Failed: ${errorMsg} (${error.response.status})`, 'error');
        } else if (error.request) {
          this.showToast('Backend not responding - check Flask on port 5000', 'error');
        } else {
          this.showToast('Error: ' + error.message, 'error');
        }
      } finally {
        clearTimeout(failsafeTimeout);
        this.loadingMessages = false;
        console.log('[TeamsView] loadingMessages set to false');
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString();
    },
    
    getMessageSenderName(message) {
      // Show "You" for own messages
      if (message.isFromMe) {
        return 'You';
      }
      
      // Skype API messages (has imdisplayname)
      if (message.imdisplayname) {
        return message.imdisplayname;
      }
      // Graph API messages (has from.user.displayName)
      if (message.from && message.from.user && message.from.user.displayName) {
        return message.from.user.displayName;
      }
      // Fallback - ALWAYS return string, never object
      return 'Unknown';
    },
    
    getMessageDateTime(message) {
      // Skype API (originalarrivaltime)
      if (message.originalarrivaltime) {
        return message.originalarrivaltime;
      }
      // Graph API (createdDateTime)
      if (message.createdDateTime) {
        return message.createdDateTime;
      }
      return null;
    },
    
    getMessageContent(message) {
      // Skype API (content directly)
      if (message.content && !message.body) {
        return message.content;
      }
      // Graph API (body.content)
      if (message.body && message.body.content) {
        return message.body.content;
      }
      return '';
    },
    
    getInitials(name) {
      if (!name || typeof name !== 'string') return '?';
      const words = name.split(' ').filter(w => w.length > 0);
      if (words.length === 0) return '?';
      if (words.length === 1) return words[0].substring(0, 2).toUpperCase();
      return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    },
    
    getAvatarColor(id) {
      if (!id) return '#6B7280';
      const colors = [
        '#3B82F6', '#10B981', '#8B5CF6', '#EC4899',
        '#F59E0B', '#EF4444', '#6366F1', '#14B8A6'
      ];
      let hash = 0;
      for (let i = 0; i < id.length; i++) {
        hash = id.charCodeAt(i) + ((hash << 5) - hash);
      }
      return colors[Math.abs(hash) % colors.length];
    },
    
    formatMessageTime(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    
    renderMessageContent(message) {
      if (!message) return '';
      
      // Get content from either Skype API (content) or Graph API (body.content)
      let html = '';
      if (message.content) {
        html = message.content;
      } else if (message.body && message.body.content) {
        html = message.body.content;
      } else {
        return '';
      }
      
      // Parse HTML
      const div = document.createElement('div');
      div.innerHTML = html;
      
      // Remove all links to emea.ng.msg.teams.microsoft.com (contacts metadata - Skype API)
      const links = div.querySelectorAll('a[href*="emea.ng.msg.teams.microsoft.com"]');
      links.forEach(link => link.remove());
      
      // Remove links that are just URLs without preview (already showing preview card)
      if (message.linkPreviews && message.linkPreviews.length > 0) {
        const previewUrls = message.linkPreviews.map(p => p.url);
        const allLinks = div.querySelectorAll('a');
        allLinks.forEach(link => {
          const href = link.getAttribute('href');
          if (href && previewUrls.some(url => href.includes(url) || url.includes(href))) {
            link.remove();
          }
        });
      }
      
      // Remove standalone contact URLs from text nodes (Skype API specific)
      const textNodes = [];
      const walker = document.createTreeWalker(div, NodeFilter.SHOW_TEXT);
      let node;
      while (node = walker.nextNode()) {
        textNodes.push(node);
      }
      textNodes.forEach(textNode => {
        let text = textNode.nodeValue;
        // Remove contact URLs
        text = text.replace(/https:\/\/emea\.ng\.msg\.teams\.microsoft\.com\/v1\/users\/ME\/contacts\/[^\s]*/g, '');
        // Remove orgid chains
        text = text.replace(/\d{13,}:orgid:[a-f0-9-]+(:orgid:[a-f0-9-]+)*/gi, '');
        textNode.nodeValue = text;
      });
      
      // Fix images to use proxy for ASM images (Skype API specific)
      const images = div.querySelectorAll('img');
      images.forEach(img => {
        const src = img.getAttribute('src');
        
        if (src) {
          // If it's an ASM Skype image, proxy it
          if (src.includes('asm.skype.com')) {
            const proxiedUrl = `http://localhost:5000/api/teams/skype/proxy/image?url=${encodeURIComponent(src)}`;
            img.setAttribute('src', proxiedUrl);
          }
          // If it's a Graph API image, proxy it
          else if (src.includes('graph.microsoft.com')) {
            const proxiedUrl = `http://localhost:5000/api/teams/proxy/image?url=${encodeURIComponent(src)}`;
            img.setAttribute('src', proxiedUrl);
          }
          
          // Style all images
          img.style.maxWidth = '400px';
          img.style.maxHeight = '300px';
          img.style.borderRadius = '8px';
          img.style.marginTop = '8px';
          img.style.display = 'block';
          img.style.cursor = 'pointer';
          
          // Add error handling
          img.setAttribute('onerror', "this.style.display='none'");
          
          // If no alt text, add one
          if (!img.getAttribute('alt')) {
            img.setAttribute('alt', 'Image');
          }
        }
      });
      
      // Clean up empty elements
      html = div.innerHTML;
      html = html.replace(/<p>\s*<\/p>/g, '');
      html = html.replace(/<div>\s*<\/div>/g, '');
      html = html.replace(/\n\s*\n+/g, '\n');
      html = html.trim();
      
      return html;
    },
    
    openUrl(url) {
      if (url) {
        window.open(url, '_blank');
      }
    }
  }
};
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
