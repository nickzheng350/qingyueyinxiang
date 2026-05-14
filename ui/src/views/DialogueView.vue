<template>
  <div class="dialogue-container">
    <!-- 侧边对话历史 -->
    <aside class="dialogue-sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewDialogue">
          <span>➕</span> {{ lang === 'zh' ? '新对话' : 'New Chat' }}
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
          <div class="dialogue-title">{{ dialogue.title }}</div>
          <div class="dialogue-meta">
            <span class="dialogue-time">{{ formatTime(dialogue.updatedAt) }}</span>
            <button class="delete-btn" @click.stop="deleteDialogue(dialogue.id)">🗑️</button>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主对话区域 -->
    <main class="dialogue-main">
      <div v-if="!currentDialogue" class="empty-state">
        <div class="empty-icon">💬</div>
        <h2>{{ lang === 'zh' ? '开始新对话' : 'Start a New Conversation' }}</h2>
        <p>{{ lang === 'zh' ? '选择一个对话或创建新对话' : 'Select a conversation or create a new one' }}</p>
      </div>

      <div v-else class="chat-area">
        <div class="messages-container">
          <div
            v-for="msg in currentDialogue.messages"
            :key="msg.id"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">{{ msg.role === 'user' ? '👤' : msg.role === 'skill' ? '⚡' : '🤖' }}</div>
            <div class="message-content">
              <div class="message-role">{{ getRoleLabel(msg.role) }}</div>
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="feature-tags">
            <span class="tag" :class="{ active: smartRouting }" @click="smartRouting = !smartRouting">
              🔀 {{ lang === 'zh' ? '智能路由' : 'Smart Route' }}
            </span>
            <span class="tag" :class="{ active: contextEnabled }" @click="contextEnabled = !contextEnabled">
              📎 {{ lang === 'zh' ? '上下文' : 'Context' }}
            </span>
            <span class="tag" :class="{ active: processInsert }" @click="processInsert = !processInsert">
              ⚙️ {{ lang === 'zh' ? '进程插入' : 'Process Insert' }}
            </span>
          </div>
          <div class="input-row">
            <textarea
              v-model="inputText"
              class="input-box"
              :placeholder="lang === 'zh' ? '输入消息...' : 'Type a message...'"
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button class="voice-btn" @click="toggleVoice" :class="{ recording: isRecording }">
              {{ isRecording ? '⏹️' : '🎤' }}
            </button>
            <button class="send-btn" @click="sendMessage">➤</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDialogueStore } from '@/stores/dialogueStore'
import { useThemeStore } from '@/stores/themeStore'
import { storeToRefs } from 'pinia'

const dialogueStore = useDialogueStore()
const themeStore = useThemeStore()
const { dialogues, currentDialogue } = storeToRefs(dialogueStore)
const { language: lang } = storeToRefs(themeStore)

const inputText = ref('')
const isRecording = ref(false)
const smartRouting = ref(true)
const contextEnabled = ref(true)
const processInsert = ref(false)

function getRoleLabel(role: string) {
  const labels: Record<string, string> = {
    user: lang.value === 'zh' ? '用户' : 'User',
    assistant: 'AI助手',
    skill: lang.value === 'zh' ? '技能调用' : 'Skill Call',
  }
  return labels[role] || role
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
  dialogueStore.selectDialogue(id)
}

function deleteDialogue(id: string) {
  dialogueStore.deleteDialogue(id)
}

function sendMessage() {
  if (!inputText.value.trim()) return
  dialogueStore.addMessage('user', inputText.value)
  const userMsg = inputText.value
  inputText.value = ''

  // 模拟AI回复
  setTimeout(() => {
    dialogueStore.addMessage(
      'assistant',
      lang.value === 'zh'
        ? `收到您的消息："${userMsg.slice(0, 30)}${userMsg.length > 30 ? '...' : ''}"。我正在分析并准备回复...`
        : `Got your message: "${userMsg.slice(0, 30)}${userMsg.length > 30 ? '...' : ''}". Analyzing and preparing response...`
    )
  }, 800)
}

function toggleVoice() {
  isRecording.value = !isRecording.value
}

onMounted(() => {
  dialogueStore.fetchDialogues()
})
</script>

<style scoped>
.dialogue-container {
  display: flex;
  height: calc(100vh - 120px);
  gap: 1.5rem;
}

.dialogue-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
}

.new-chat-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border: none;
  border-radius: 10px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s;
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.dialogue-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.dialogue-item {
  padding: 0.875rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 0.25rem;
}

.dialogue-item:hover {
  background: var(--bg-hover);
}

.dialogue-item.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.1));
  border-left: 3px solid var(--primary);
}

.dialogue-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dialogue-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
}

.dialogue-item:hover .delete-btn {
  opacity: 1;
}

.dialogue-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h2 {
  margin-bottom: 0.5rem;
  color: var(--text-primary);
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
  padding: 1.5rem;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message-role {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.message.user .message-role {
  text-align: right;
}

.message-text {
  background: var(--bg-dark);
  padding: 1rem 1.25rem;
  border-radius: 16px;
  line-height: 1.6;
}

.message.user .message-text {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
}

.message.skill .message-text {
  border-left: 3px solid var(--warning);
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.message.user .message-time {
  text-align: right;
}

.input-area {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background: var(--bg-dark);
}

.feature-tags {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.tag {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.3s;
}

.tag.active {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border-color: transparent;
}

.input-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.input-box {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.875rem 1rem;
  color: var(--text-primary);
  resize: none;
  min-height: 48px;
  max-height: 120px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s;
}

.input-box:focus {
  border-color: var(--primary);
}

.voice-btn, .send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
  transition: all 0.3s;
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

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.send-btn {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
}

.send-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}
</style>
