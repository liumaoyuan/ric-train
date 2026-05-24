<template>
  <div class="chat-container">
    <!-- 会话侧边栏 -->
    <div class="session-sidebar" :class="{ collapsed: !showSidebar }">
      <div class="sidebar-header">
        <el-button type="primary" :icon="Plus" @click="handleNewSession" class="new-chat-btn">
          {{ showSidebar ? '新对话' : '' }}
        </el-button>
      </div>
      <div class="session-list" v-loading="loadingSessions">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          class="session-item"
          :class="{ active: currentSessionId === s.session_id }"
          @click="switchSession(s.session_id)"
        >
          <div class="session-title">{{ s.title || '新对话' }}</div>
          <div class="session-time">{{ formatTime(s.updated_at) }}</div>
          <el-icon class="session-delete" @click.stop="handleDeleteSession(s.session_id)">
            <Delete />
          </el-icon>
        </div>
        <el-empty v-if="sessions.length === 0 && !loadingSessions" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main" @click="showSidebar = true">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef" id="message-list">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">AI</div>
          <h2>你好，我是小餐</h2>
          <p>你的连锁餐饮 AI 助手，我可以帮你：</p>
          <div class="suggestions">
            <div class="suggestion-item" @click="sendQuickQuestion('上个月营业额是多少？')">
              📊 查询营业数据
            </div>
            <div class="suggestion-item" @click="sendQuickQuestion('公司考勤制度有哪些规定？')">
              📋 公司制度问答
            </div>
            <div class="suggestion-item" @click="sendQuickQuestion('酸辣土豆丝的制作工艺是什么？')">
              🍳 菜品知识查询
            </div>
            <div class="suggestion-item" @click="sendQuickQuestion('最近餐饮行业有什么新趋势？')">
              🔍 行业资讯搜索
            </div>
          </div>
        </div>

        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="msg.role"
        >
          <div class="message-avatar">
            {{ msg.role === 'user' ? 'U' : 'AI' }}
          </div>
          <div class="message-content">
            <div class="message-bubble" v-if="msg.role === 'user'">
              {{ msg.content }}
            </div>
            <div class="message-bubble assistant" v-else>
              <div v-if="msg.isStreaming && !msg.content" class="streaming-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-if="msg.content" v-html="renderMarkdown(msg.content)"></div>
            </div>
            <div class="message-time" v-if="msg.time">{{ formatTime(msg.time) }}</div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入你的问题..."
            resize="none"
            @keydown.enter.prevent="handleSend"
            :disabled="isProcessing"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="isProcessing"
            :disabled="!inputText.trim() || isProcessing"
            @click="handleSend"
            class="send-btn"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import {
  Plus, Delete, Promotion,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import {
  askQuestionStream,
  getSessions,
  createSession,
  deleteSession,
  getSessionHistory,
} from '../../api/chat'

const showSidebar = ref(true)
const sessions = ref([])
const currentSessionId = ref('')
const messages = ref([])
const inputText = ref('')
const isProcessing = ref(false)
const loadingSessions = ref(false)
const messageListRef = ref(null)

marked.setOptions({
  breaks: true,
  gfm: true,
})

function renderMarkdown(text) {
  if (!text) return ''
  try {
    // 压缩连续换行：2个以上换行压缩为2个，避免多余段落间距
    const processed = text.replace(/\n{3,}/g, '\n\n')
    return marked.parse(processed)
  } catch {
    return text
  }
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  try {
    const d = new Date(timeStr)
    const now = new Date()
    const diff = now - d
    if (diff < 86400000) {
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  } catch {
    return timeStr
  }
}

async function loadSessions() {
  loadingSessions.value = true
  try {
    const res = await getSessions()
    sessions.value = res.data || []
    if (sessions.value.length > 0 && !currentSessionId.value) {
      currentSessionId.value = sessions.value[0].session_id
      await loadHistory()
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  } finally {
    loadingSessions.value = false
  }
}

async function loadHistory() {
  if (!currentSessionId.value) {
    messages.value = []
    return
  }
  try {
    const res = await getSessionHistory(currentSessionId.value)
    messages.value = (res.data || []).map(m => ({
      role: m.role,
      content: m.content,
      time: null,
      isStreaming: false,
    }))
    await scrollToBottom()
  } catch (e) {
    console.error('加载历史失败:', e)
    messages.value = []
  }
}

async function switchSession(sessionId) {
  if (isProcessing.value) return
  currentSessionId.value = sessionId
  await loadHistory()
}

async function handleNewSession() {
  if (isProcessing.value) return
  try {
    const res = await createSession({ title: '新对话' })
    const newSession = res.data
    sessions.value.unshift({
      session_id: newSession.session_id,
      title: newSession.title || '新对话',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    currentSessionId.value = newSession.session_id
    messages.value = []
  } catch (e) {
    ElMessage.error('创建会话失败')
  }
}

async function handleDeleteSession(sessionId) {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await deleteSession(sessionId)
    ElMessage.success('删除成功')
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value[0]?.session_id || ''
      await loadHistory()
    }
  } catch {
    // user cancelled
  }
}

function sendQuickQuestion(text) {
  inputText.value = text
  handleSend()
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isProcessing.value) return

  inputText.value = ''
  isProcessing.value = true

  messages.value.push({
    role: 'user',
    content: text,
    time: new Date().toISOString(),
    isStreaming: false,
  })

  const assistantMsg = reactive({
    role: 'assistant',
    content: '',
    time: new Date().toISOString(),
    isStreaming: true,
  })
  messages.value.push(assistantMsg)
  await scrollToBottom()

  let streamContent = ''

  const abort = askQuestionStream(
    {
      question: text,
      session_id: currentSessionId.value || undefined,
      is_stream: true,
    },
    (data) => {
      if (data.type === 'content') {
        streamContent += data.content
        assistantMsg.content = streamContent
        scrollToBottom()
      } else if (data.type === 'reasoning') {
        streamContent += data.content
        assistantMsg.content = streamContent
        scrollToBottom()
      } else if (data.type === 'start') {
        if (data.session_id && !currentSessionId.value) {
          currentSessionId.value = data.session_id
          loadSessions()
        }
      }
    },
    (error) => {
      assistantMsg.content = error || '请求失败，请重试'
      assistantMsg.isStreaming = false
      isProcessing.value = false
    },
    () => {
      assistantMsg.isStreaming = false
      isProcessing.value = false
      assistantMsg.time = new Date().toISOString()
      if (messages.value.length === 2) {
        loadSessions()
      }
    },
  )
}

async function scrollToBottom() {
  await nextTick()
  const container = messageListRef.value
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 100px);
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.session-sidebar {
  width: 260px;
  min-width: 260px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transition: width 0.3s, min-width 0.3s;
}

.session-sidebar.collapsed {
  width: 0;
  min-width: 0;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.new-chat-btn {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  margin-bottom: 2px;
  transition: background 0.2s;
}

.session-item:hover {
  background: #f0f5ff;
}

.session-item.active {
  background: #e6f0ff;
}

.session-title {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 20px;
}

.session-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.session-delete {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: none;
  color: #999;
  font-size: 14px;
}

.session-item:hover .session-delete {
  display: block;
}

.session-delete:hover {
  color: #f56c6c;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.welcome {
  text-align: center;
  padding-top: 80px;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #409EFF, #337ecc);
  color: #fff;
  font-size: 28px;
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.welcome h2 {
  font-size: 22px;
  color: #333;
  margin: 0 0 8px;
}

.welcome p {
  color: #888;
  margin: 0 0 24px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.suggestion-item {
  padding: 10px 18px;
  border: 1px solid #e4e7ed;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
  background: #fafafa;
}

.suggestion-item:hover {
  border-color: #409EFF;
  color: #409EFF;
  background: #f0f5ff;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: flex-start;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: bold;
  flex-shrink: 0;
}

.message-row.user .message-avatar {
  background: #409EFF;
  color: #fff;
}

.message-row.assistant .message-avatar {
  background: linear-gradient(135deg, #67C23A, #5daf34);
  color: #fff;
}

.message-content {
  max-width: 75%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
  white-space: normal;
}

.message-row.user .message-bubble {
  background: #409EFF;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .message-bubble {
  background: #f5f7fa;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-bubble :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  margin: 8px 0;
}

.message-bubble :deep(code) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.message-bubble :deep(p) {
  margin: 0;
}

.message-bubble :deep(ul), .message-bubble :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.message-bubble :deep(h1), .message-bubble :deep(h2), .message-bubble :deep(h3) {
  margin: 8px 0 4px;
}

.message-bubble :deep(h3) {
  font-size: 16px;
}

.message-bubble :deep(blockquote) {
  border-left: 3px solid #409EFF;
  padding-left: 12px;
  color: #666;
  margin: 4px 0;
}

.message-bubble :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-bubble :deep(th), .message-bubble :deep(td) {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  text-align: left;
}

.message-bubble :deep(th) {
  background: #f0f0f0;
  font-weight: 600;
}

.message-time {
  font-size: 11px;
  color: #bbb;
  margin-top: 4px;
  text-align: right;
}

.streaming-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}

.dot {
  width: 6px;
  height: 6px;
  background: #909399;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 16px 24px 20px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
}

.send-btn {
  height: 60px;
  border-radius: 8px;
  padding: 0 24px;
  flex-shrink: 0;
}
</style>
