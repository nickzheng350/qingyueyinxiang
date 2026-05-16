<template>
  <div class="dialogue-container">
    <!-- 侧边对话历史 -->
    <aside class="dialogue-sidebar glass-card">
      <div class="sidebar-header">
        <h3 class="sidebar-title">{{ lang === 'zh' ? '对话列表' : 'Dialogues' }}</h3>
        <button class="new-chat-btn" @click="createNewDialogue">
          <span>➕</span>
          <span>{{ lang === 'zh' ? '新对话' : 'New Chat' }}</span>
        </button>
      </div>
      <div class="dialogue-list">
        <div
          v-for="dialogue in dialogues"
          :key="dialogue.id"
          class="dialogue-item"
          :class="{ active: currentDialogue?.id === dialogue.id }"
          @click="selectDialogue(dialogue.id)"
        >
          <div class="dialogue-icon">💬</div>
          <div class="dialogue-info">
            <div class="dialogue-title">{{ dialogue.title }}</div>
            <div class="dialogue-time">{{ formatTime(dialogue.updatedAt) }}</div>
          </div>
          <button class="delete-btn" @click.stop="deleteDialogue(dialogue.id)">🗑️</button>
        </div>
        <div v-if="dialogues.length === 0" class="empty-list">
          <span>📭</span>
          <p>{{ lang === 'zh' ? '暂无对话' : 'No dialogues yet' }}</p>
        </div>
      </div>
    </aside>

    <!-- 主对话区域 -->
    <main class="dialogue-main glass-card">
      <!-- 顶部Tab栏 -->
      <div class="module-tabs">
        <div 
          class="module-tab" 
          :class="{ active: activeTab === 'chat' }"
          @click="switchTab('chat')"
        >
          <span>💬</span>
          <span>{{ lang === 'zh' ? '对话' : 'Chat' }}</span>
        </div>
        <div 
          class="module-tab" 
          :class="{ active: activeTab === 'history' }"
          @click="switchTab('history')"
        >
          <span>📜</span>
          <span>{{ lang === 'zh' ? '历史记录' : 'History' }}</span>
        </div>
      </div>

      <!-- 对话Tab内容 -->
      <div v-if="activeTab === 'chat'">
        <!-- 欢迎状态 -->
        <div v-if="!dialogueStore.currentDialogue" class="welcome-state">
          <div class="welcome-icon">✨</div>
          <h2>{{ lang === 'zh' ? '欢迎使用清悦印象' : 'Welcome to QingYue YinXiang' }}</h2>
          <p>{{ lang === 'zh' ? '选择对话或创建新对话开始' : 'Select a dialogue or create a new one to start' }}</p>
          <button class="start-btn" @click="createNewDialogue">
            <span>🚀</span>
            {{ lang === 'zh' ? '开始新对话' : 'Start New Chat' }}
          </button>
        </div>

        <!-- 对话区域 -->
        <div v-else class="chat-area">
          <div class="messages-container">
            <div
              v-for="(msg, idx) in dialogueStore.currentDialogue?.messages || []"
              :key="msg.id || idx"
              class="message"
              :class="msg.role"
            >
              <div class="message-avatar">{{ getAvatar(msg.role) }}</div>
              <div class="message-bubble">
                <div class="message-role">{{ getRoleLabel(msg.role) }}</div>
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-area">
            <!-- 功能开关 -->
            <div class="feature-tags">
              <span class="tag" :class="{ active: smartRouting }" @click="smartRouting = !smartRouting">
                🔀 {{ lang === 'zh' ? '智能路由' : 'Smart' }}
              </span>
              <span class="tag" :class="{ active: contextEnabled }" @click="contextEnabled = !contextEnabled">
                📎 {{ lang === 'zh' ? '上下文' : 'Context' }}
              </span>
              <span class="tag" :class="{ active: processInsert }" @click="processInsert = !processInsert">
                ⚙️ {{ lang === 'zh' ? '进程' : 'Process' }}
              </span>
            </div>

            <!-- 输入框 -->
            <div class="input-row">
              <div class="input-wrapper">
                <textarea
                  v-model="inputText"
                  class="input-box"
                  :placeholder="lang === 'zh' ? '输入消息...' : 'Type a message...'"
                  @keydown.enter.exact.prevent="sendMessage"
                  rows="1"
                ></textarea>
              </div>
              <button class="voice-btn" @click="toggleVoice" :class="{ recording: isRecording }">
                <span v-if="isRecording">⏹️</span>
                <span v-else>🎤</span>
              </button>
              <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim()">
                <span>➤</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史记录Tab内容 -->
      <div v-if="activeTab === 'history'">
        <div class="history-area">
          <div class="history-header">
            <h3>{{ lang === 'zh' ? '对话历史记录' : 'Dialogue History' }}</h3>
          </div>
          <div class="history-list">
            <div
              v-for="dialogue in optimizedDialogues"
              :key="dialogue.id"
              class="history-item"
              @click="selectDialogue(dialogue.id)"
            >
              <div class="history-icon">📋</div>
              <div class="history-info">
                <div class="history-title">{{ dialogue.title }}</div>
                <div class="history-meta">
                  <span>{{ dialogue.messages.length }} {{ lang === 'zh' ? '条消息' : 'messages' }}</span>
                  <span>{{ shouldOptimizeFormatting ? dialogue.formattedTime : formatTime(dialogue.updatedAt) }}</span>
                </div>
              </div>
              <div class="history-preview">{{ dialogue.messages[0]?.content.slice(0, 30) }}...</div>
            </div>
            <div v-if="dialogueStore.dialogues.length === 0" class="empty-history">
              <span>📭</span>
              <p>{{ lang === 'zh' ? '暂无历史记录' : 'No history yet' }}</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDialogueStore } from '@/stores/dialogueStore'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const dialogueStore = useDialogueStore()
const themeStore = useThemeStore()
const router = useRouter()
const route = useRoute()
const { dialogues, currentDialogue } = storeToRefs(dialogueStore)
const { language: lang } = storeToRefs(themeStore)

const inputText = ref('')
const isRecording = ref(false)
const smartRouting = ref(true)
const contextEnabled = ref(true)
const processInsert = ref(false)
// 根据当前路由初始化 activeTab
const activeTab = ref<'chat' | 'history'>('chat')
// 标志位：防止路由监听覆盖手动设置
const isManualTabChange = ref(false)
// 防抖标志：防止快速连续点击
const isSelecting = ref(false)

// 性能监控：数据量超过阈值时自动优化
const shouldOptimizeFormatting = computed(() => {
  const count = dialogueStore.dialogues.length
  // 当数据量超过 100 条时启用优化
  if (count > 100) {
    console.warn(`[Performance] Dialogue count exceeds 100 (${count}), automatic optimization enabled`)
  }
  return count > 100
})

// 优化后的对话列表，缓存格式化时间
const optimizedDialogues = computed(() => {
  if (!shouldOptimizeFormatting.value) {
    return dialogueStore.dialogues
  }
  return dialogueStore.dialogues.map(dialogue => ({
    ...dialogue,
    formattedTime: formatTime(dialogue.updatedAt)
  }))
})

// 初始化 activeTab
function updateActiveTabFromRoute() {
  const shouldBeHistory = route.path.includes('history')
  activeTab.value = shouldBeHistory ? 'history' : 'chat'
}

// 根据路由自动切换Tab
watch(() => route.path, (newPath) => {
  if (!isManualTabChange.value) {
    updateActiveTabFromRoute()
  } else {
    isManualTabChange.value = false
  }
}, { immediate: true })

function switchTab(tab: 'chat' | 'history') {
  activeTab.value = tab
  if (tab === 'chat') {
    router.push('/dialogue')
  } else {
    router.push('/dialogue/history')
  }
}

function getAvatar(role: string) {
  const avatars: Record<string, string> = {
    user: '👤',
    assistant: '🤖',
    skill: '⚡',
    system: '⚙️',
  }
  return avatars[role] || '❓'
}

function getRoleLabel(role: string) {
  const labels: Record<string, { zh: string; en: string }> = {
    user: { zh: '用户', en: 'User' },
    assistant: { zh: 'AI助手', en: 'AI Assistant' },
    skill: { zh: '技能调用', en: 'Skill Call' },
    system: { zh: '系统', en: 'System' },
  }
  return lang.value === 'zh' ? labels[role]?.zh : labels[role]?.en || role
}

function formatTime(time: string) {
  const d = new Date(time)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return lang.value === 'zh' ? '刚刚' : 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}${lang.value === 'zh' ? '分钟前' : 'm ago'}`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}${lang.value === 'zh' ? '小时前' : 'h ago'}`
  return d.toLocaleDateString()
}

function createNewDialogue() {
  dialogueStore.createDialogue(lang.value === 'zh' ? '新对话' : 'New Chat')
}

function selectDialogue(id: string) {
  // 防止快速连续点击
  if (isSelecting.value) return
  isSelecting.value = true
  
  // 设置标志位，防止路由监听覆盖手动设置
  isManualTabChange.value = true
  
  // 切换到聊天视图
  activeTab.value = 'chat'
  
  // 选择对话
  dialogueStore.selectDialogue(id)
  
  // 跳转到对话路由
  router.replace({ name: 'Dialogue' })
  
  // 重置防抖标志
  setTimeout(() => {
    isSelecting.value = false
  }, 300)
}

function deleteDialogue(id: string) {
  dialogueStore.deleteDialogue(id)
}

function sendMessage() {
  if (!inputText.value.trim()) return
  dialogueStore.addMessage('user', inputText.value)
  const userMsg = inputText.value
  inputText.value = ''

  setTimeout(() => {
    dialogueStore.addMessage(
      'assistant',
      lang.value === 'zh'
        ? `收到您的消息。正在分析...`
        : `Got your message. Analyzing...`
    )
  }, 800)
}

function toggleVoice() {
  isRecording.value = !isRecording.value
}

onMounted(async () => {
  await dialogueStore.fetchDialogues()
})
</script>

<style scoped>
.dialogue-container {
  display: flex;
  gap: var(--space-lg);
  height: calc(100vh - 140px);
  margin-top: 80px;
}

.dialogue-sidebar {
  width: 210px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border);
}

.sidebar-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.new-chat-btn {
  width: 100%;
  padding: var(--space-md);
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  transition: all var(--transition-normal);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--primary) 30%, transparent);
}

.dialogue-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.dialogue-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: var(--space-xs);
}

.dialogue-item:hover {
  background: var(--bg-hover);
}

.dialogue-item.active {
  background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 15%, transparent), color-mix(in srgb, var(--secondary) 10%, transparent));
  border-left: 3px solid var(--primary);
}

.dialogue-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--bg-glass);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.dialogue-info {
  flex: 1;
  min-width: 0;
}

.dialogue-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.dialogue-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast);
  font-size: 0.875rem;
}

.dialogue-item:hover .delete-btn {
  opacity: 1;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--text-muted);
}

.empty-list span {
  font-size: 3rem;
  margin-bottom: var(--space-md);
}

.empty-list p {
  font-size: 0.875rem;
}

.dialogue-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.module-tabs {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border);
}

.module-tab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.module-tab.active {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.module-tab:hover:not(.active) {
  background: var(--bg-glass);
}

.welcome-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}

.welcome-icon {
  font-size: 4rem;
  margin-bottom: var(--space-lg);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-state h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: var(--space-sm);
  background: linear-gradient(90deg, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-state p {
  color: var(--text-secondary);
  margin-bottom: var(--space-xl);
}

.start-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border: none;
  border-radius: var(--radius-lg);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--primary) 30%, transparent);
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.message {
  display: flex;
  gap: var(--space-md);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-glass);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}

.message-bubble {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.message-role {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.message.user .message-role {
  text-align: right;
}

.message-text {
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--bg-glass);
  border: 1px solid var(--border);
  line-height: 1.6;
}

.message.user .message-text {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-color: transparent;
  color: white;
}

.message.skill .message-text {
  border-left: 3px solid var(--warning);
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.message.user .message-time {
  text-align: right;
}

.input-area {
  padding: var(--space-lg);
  border-top: 1px solid var(--border);
  background: var(--bg-glass);
}

.feature-tags {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px var(--space-sm);
  border-radius: 20px;
  font-size: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tag.active {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border-color: transparent;
}

.input-row {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;
}

.input-box {
  width: 100%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.9rem;
  resize: none;
  min-height: 48px;
  max-height: 120px;
  outline: none;
  transition: all var(--transition-fast);
}

.input-box:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 10%, transparent);
}

.voice-btn, .send-btn {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.voice-btn {
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.voice-btn.recording {
  background: var(--error);
  color: white;
  animation: pulse 1s infinite;
}

.send-btn {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--primary) 30%, transparent);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>