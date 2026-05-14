<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">🔌 {{ lang === 'zh' ? '插件中心' : 'Plugin Center' }}</div>
        <div class="card-subtitle">{{ lang === 'zh' ? '管理插件和MCP连接' : 'Manage plugins and MCP connections' }}</div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <el-button @click="fetchPlugins">🔄 {{ lang === 'zh' ? '刷新' : 'Refresh' }}</el-button>
      </div>
    </div>

    <!-- Tab切换 -->
    <div class="plugin-tabs">
      <button
        class="plugin-tab"
        :class="{ active: activeTab === 'enabled' }"
        @click="activeTab = 'enabled'"
      >
        ✅ {{ lang === 'zh' ? '已启用' : 'Enabled' }} ({{ enabledPlugins.length }})
      </button>
      <button
        class="plugin-tab"
        :class="{ active: activeTab === 'disabled' }"
        @click="activeTab = 'disabled'"
      >
        ⏸️ {{ lang === 'zh' ? '未启用' : 'Disabled' }} ({{ disabledPlugins.length }})
      </button>
      <button
        class="plugin-tab"
        :class="{ active: activeTab === 'mcp' }"
        @click="activeTab = 'mcp'"
      >
        🔗 MCP {{ lang === 'zh' ? '链接' : 'Links' }} ({{ mcpLinks.length }})
      </button>
    </div>

    <!-- 已启用/未启用插件列表 -->
    <div v-if="activeTab !== 'mcp'" class="plugin-grid">
      <div v-for="plugin in currentPlugins" :key="plugin.id" class="plugin-card">
        <div class="plugin-header">
          <div class="plugin-icon">🔌</div>
          <div class="plugin-info">
            <div class="plugin-name">{{ lang === 'zh' ? plugin.name : plugin.nameEn }}</div>
            <div class="plugin-version">v{{ plugin.version }}</div>
          </div>
          <div class="plugin-status" :class="plugin.enabled ? 'enabled' : 'disabled'">
            {{ plugin.enabled ? 'ON' : 'OFF' }}
          </div>
        </div>
        <div class="plugin-desc">{{ plugin.description }}</div>
        <div class="plugin-meta">
          <span class="plugin-author">👤 {{ plugin.author }}</span>
          <span class="plugin-category">🏷️ {{ plugin.category }}</span>
        </div>
        <div v-if="plugin.dependencies.length" class="plugin-deps">
          <span class="deps-label">{{ lang === 'zh' ? '依赖:' : 'Deps:' }}</span>
          <span v-for="dep in plugin.dependencies" :key="dep" class="dep-tag">{{ dep }}</span>
        </div>
        <div class="plugin-actions">
          <el-button
            size="small"
            :type="plugin.enabled ? '' : 'primary'"
            @click="togglePlugin(plugin.id)"
          >
            {{ plugin.enabled ? (lang === 'zh' ? '禁用' : 'Disable') : (lang === 'zh' ? '启用' : 'Enable') }}
          </el-button>
          <el-button size="small" @click="showDetail(plugin)">
            {{ lang === 'zh' ? '详情' : 'Details' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- MCP链接 -->
    <div v-else class="mcp-section">
      <div class="mcp-header">
        <h3>🔗 MCP {{ lang === 'zh' ? '模型上下文协议链接' : 'Model Context Protocol Links' }}</h3>
        <el-button type="primary" @click="showAddMCPDialog = true">
          ➕ {{ lang === 'zh' ? '添加链接' : 'Add Link' }}
        </el-button>
      </div>

      <div class="mcp-list">
        <div v-for="link in mcpLinks" :key="link.id" class="mcp-card">
          <div class="mcp-status-indicator" :class="link.status"></div>
          <div class="mcp-info">
            <div class="mcp-name">{{ link.name }}</div>
            <div class="mcp-url">{{ link.url }}</div>
            <div class="mcp-meta">
              <span class="mcp-status-text">{{ getStatusText(link.status) }}</span>
              <span v-if="link.lastSync" class="mcp-sync">
                {{ lang === 'zh' ? '同步于' : 'Synced' }}: {{ formatTime(link.lastSync) }}
              </span>
            </div>
          </div>
          <div class="mcp-actions">
            <el-button
              size="small"
              @click="syncMCPLink(link.id)"
              :disabled="link.status === 'connected'"
            >
              🔄 {{ lang === 'zh' ? '同步' : 'Sync' }}
            </el-button>
            <el-button size="small" type="danger" @click="removeMCPLink(link.id)">
              🗑️
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 插件详情对话框 -->
    <div v-if="showDetailDialog" class="dialog-overlay" @click.self="showDetailDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '插件详情' : 'Plugin Details' }}</h3>
        <div v-if="selectedPlugin" class="detail-content">
          <div class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '名称' : 'Name' }}:</span>
            <span>{{ lang === 'zh' ? selectedPlugin.name : selectedPlugin.nameEn }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '版本' : 'Version' }}:</span>
            <span>{{ selectedPlugin.version }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '作者' : 'Author' }}:</span>
            <span>{{ selectedPlugin.author }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '分类' : 'Category' }}:</span>
            <span>{{ selectedPlugin.category }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '描述' : 'Description' }}:</span>
            <span>{{ selectedPlugin.description }}</span>
          </div>
          <div v-if="selectedPlugin.dependencies.length" class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '依赖' : 'Dependencies' }}:</span>
            <span>{{ selectedPlugin.dependencies.join(', ') }}</span>
          </div>
          <div v-if="selectedPlugin.installedAt" class="detail-row">
            <span class="detail-label">{{ lang === 'zh' ? '安装时间' : 'Installed' }}:</span>
            <span>{{ formatTime(selectedPlugin.installedAt) }}</span>
          </div>
        </div>
        <div class="dialog-actions">
          <el-button @click="showDetailDialog = false">{{ lang === 'zh' ? '关闭' : 'Close' }}</el-button>
        </div>
      </div>
    </div>

    <!-- 添加MCP链接对话框 -->
    <div v-if="showAddMCPDialog" class="dialog-overlay" @click.self="showAddMCPDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '添加MCP链接' : 'Add MCP Link' }}</h3>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '名称' : 'Name' }}</label>
          <input v-model="newMCP.name" type="text" />
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? 'URL' }}:</label>
          <input v-model="newMCP.url" type="text" placeholder="https://api.example.com" />
        </div>
        <div class="dialog-actions">
          <el-button @click="showAddMCPDialog = false">{{ lang === 'zh' ? '取消' : 'Cancel' }}</el-button>
          <el-button type="primary" @click="addNewMCPLink">{{ lang === 'zh' ? '添加' : 'Add' }}</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePluginStore } from '@/stores/pluginStore'
import { useThemeStore } from '@/stores/themeStore'
import { storeToRefs } from 'pinia'

const pluginStore = usePluginStore()
const themeStore = useThemeStore()
const { enabledPlugins, disabledPlugins, mcpLinks, loading, activeTab } = storeToRefs(pluginStore)
const { language: lang } = storeToRefs(themeStore)

const showDetailDialog = ref(false)
const showAddMCPDialog = ref(false)
const selectedPlugin = ref<any>(null)
const newMCP = ref({ name: '', url: '' })

const currentPlugins = computed(() => {
  return activeTab.value === 'enabled' ? enabledPlugins.value : disabledPlugins.value
})

function fetchPlugins() {
  pluginStore.fetchPlugins()
}

function togglePlugin(id: string) {
  pluginStore.togglePlugin(id)
}

function showDetail(plugin: any) {
  selectedPlugin.value = plugin
  showDetailDialog.value = true
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    connected: lang.value === 'zh' ? '已连接' : 'Connected',
    disconnected: lang.value === 'zh' ? '未连接' : 'Disconnected',
    error: lang.value === 'zh' ? '错误' : 'Error',
  }
  return texts[status] || status
}

function formatTime(time: string) {
  return new Date(time).toLocaleString()
}

function addNewMCPLink() {
  pluginStore.addMCPLink({ name: newMCP.value.name, url: newMCP.value.url })
  showAddMCPDialog.value = false
  newMCP.value = { name: '', url: '' }
}

function removeMCPLink(id: string) {
  pluginStore.removeMCPLink(id)
}

function syncMCPLink(id: string) {
  pluginStore.syncMCPLink(id)
}

onMounted(() => {
  pluginStore.fetchPlugins()
})
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.plugin-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.plugin-tab { padding: 0.5rem 1.25rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; }
.plugin-tab:hover { border-color: var(--primary); }
.plugin-tab.active { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }

.plugin-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
.plugin-card { background: var(--bg-dark); border-radius: 12px; padding: 1.25rem; transition: all 0.3s; }
.plugin-card:hover { border: 1px solid var(--primary); transform: translateY(-2px); }
.plugin-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; }
.plugin-icon { font-size: 2rem; }
.plugin-info { flex: 1; }
.plugin-name { font-weight: 600; }
.plugin-version { font-size: 0.75rem; color: var(--text-secondary); }
.plugin-status { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.plugin-status.enabled { background: rgba(74, 222, 128, 0.2); color: var(--success); }
.plugin-status.disabled { background: rgba(248, 113, 113, 0.2); color: var(--error); }
.plugin-desc { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.75rem; }
.plugin-meta { display: flex; gap: 1rem; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
.plugin-deps { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.deps-label { font-size: 0.75rem; color: var(--text-secondary); }
.dep-tag { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; background: rgba(99, 102, 241, 0.2); color: var(--primary); }
.plugin-actions { display: flex; gap: 0.5rem; }

.mcp-section {}
.mcp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.mcp-header h3 { font-size: 1rem; font-weight: 600; }
.mcp-list { display: flex; flex-direction: column; gap: 0.75rem; }
.mcp-card { background: var(--bg-dark); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; }
.mcp-status-indicator { width: 12px; height: 12px; border-radius: 50%; }
.mcp-status-indicator.connected { background: var(--success); box-shadow: 0 0 8px var(--success); }
.mcp-status-indicator.disconnected { background: var(--text-secondary); }
.mcp-status-indicator.error { background: var(--error); }
.mcp-info { flex: 1; }
.mcp-name { font-weight: 600; }
.mcp-url { font-size: 0.8rem; color: var(--text-secondary); margin: 0.25rem 0; }
.mcp-meta { display: flex; gap: 1rem; font-size: 0.75rem; }
.mcp-status-text { color: var(--text-secondary); }
.mcp-sync { color: var(--text-secondary); }
.mcp-actions { display: flex; gap: 0.5rem; }

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { background: var(--bg-card); border-radius: 16px; padding: 2rem; width: 500px; max-width: 90%; }
.dialog h3 { margin-bottom: 1.5rem; }
.detail-content { display: flex; flex-direction: column; gap: 0.75rem; }
.detail-row { display: flex; gap: 1rem; }
.detail-label { color: var(--text-secondary); min-width: 100px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); }
.form-group input { width: 100%; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; color: var(--text-primary); outline: none; }
.form-group input:focus { border-color: var(--primary); }
</style>
