<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">🤖 {{ lang === 'zh' ? '模型配置' : 'Model Configuration' }}</div>
        <div class="card-subtitle">{{ lang === 'zh' ? '管理AI模型和API设置' : 'Manage AI models and API settings' }}</div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn-primary" @click="showAddModelDialog = true">➕ {{ lang === 'zh' ? '添加模型' : 'Add Model' }}</button>
        <button class="btn-secondary" @click="fetchModels">🔄 {{ lang === 'zh' ? '刷新' : 'Refresh' }}</button>
      </div>
    </div>

    <!-- 功能类型筛选 -->
    <div class="function-tabs">
      <button
        class="function-tab"
        :class="{ active: activeFunction === 'all' }"
        @click="activeFunction = 'all'"
      >
        🌐 {{ lang === 'zh' ? '全部' : 'All' }}
      </button>
      <button
        v-for="ft in functionTypes"
        :key="ft.id"
        class="function-tab"
        :class="{ active: activeFunction === ft.id }"
        @click="activeFunction = ft.id"
      >
        {{ ft.icon }} {{ lang === 'zh' ? ft.name : ft.nameEn }}
      </button>
    </div>

    <!-- 提供商标签 -->
    <div class="provider-section">
      <div class="provider-tabs">
        <button
          class="provider-tab"
          :class="{ active: !activeProvider }"
          @click="activeProvider = ''"
        >
          {{ lang === 'zh' ? '全部提供商' : 'All Providers' }}
        </button>
        <button
          v-for="p in providers"
          :key="p.id"
          class="provider-tab"
          :class="{ active: activeProvider === p.id }"
          @click="activeProvider = p.id"
        >
          <span class="provider-logo">{{ p.logo }}</span>
          {{ lang === 'zh' ? p.name : p.nameEn }}
          <span class="provider-category">{{ p.category === 'official' ? '☁️' : '💻' }}</span>
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-num">{{ models.length }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '模型总数' : 'Total Models' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-num">{{ enabledCount }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '已启用' : 'Enabled' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🟢</div>
        <div class="stat-info">
          <div class="stat-num">{{ onlineCount }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '在线' : 'Online' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">☁️</div>
        <div class="stat-info">
          <div class="stat-num">{{ officialCount }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '官方兼容' : 'Official' }}</div>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="model-grid">
      <div v-for="model in filteredModels" :key="model.id" class="model-card">
        <div class="model-header">
          <div class="model-provider-logo">{{ getProviderLogo(model.provider) }}</div>
          <div class="model-info">
            <div class="model-name">{{ model.name }}</div>
            <div class="model-provider">{{ getProviderName(model.provider) }}</div>
          </div>
          <div class="model-status" :class="model.status">
            <span class="status-dot"></span>
            {{ getStatusText(model.status) }}
          </div>
        </div>

        <div class="model-meta">
          <div class="meta-item">
            <span class="meta-label">{{ lang === 'zh' ? '功能' : 'Function' }}:</span>
            <span class="meta-value">{{ getFunctionName(model.functionType) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">{{ lang === 'zh' ? '类型' : 'Type' }}:</span>
            <span class="meta-value">{{ model.category }}</span>
          </div>
        </div>

        <div class="model-config">
          <div v-for="(value, key) in model.config" :key="key" class="config-item">
            <span class="config-key">{{ key }}:</span>
            <span class="config-value">{{ value }}</span>
          </div>
        </div>

        <div class="model-actions">
          <div class="toggle-switch" :class="{ active: model.enabled }" @click="toggleModel(model.id)">
            <span class="toggle-label">{{ model.enabled ? (lang === 'zh' ? '启用' : 'ON') : (lang === 'zh' ? '禁用' : 'OFF') }}</span>
            <div class="toggle-track">
              <div class="toggle-thumb"></div>
            </div>
          </div>
          <button class="btn-config" @click="editModel(model)">
            {{ lang === 'zh' ? '配置' : 'Config' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 添加模型对话框 -->
    <div v-if="showAddModelDialog" class="dialog-overlay" @click.self="showAddModelDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '添加模型' : 'Add Model' }}</h3>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '模型ID' : 'Model ID' }}</label>
          <input v-model="newModel.id" type="text" placeholder="gpt-4o" />
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '模型名称' : 'Model Name' }}</label>
          <input v-model="newModel.name" type="text" placeholder="GPT-4o" />
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '提供商' : 'Provider' }}</label>
          <select v-model="newModel.provider">
            <option v-for="p in providers" :key="p.id" :value="p.id">
              {{ p.logo }} {{ lang === 'zh' ? p.name : p.nameEn }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '功能类型' : 'Function Type' }}</label>
          <select v-model="newModel.functionType">
            <option v-for="ft in functionTypes" :key="ft.id" :value="ft.id">
              {{ ft.icon }} {{ lang === 'zh' ? ft.name : ft.nameEn }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? 'API Key' : 'API Key' }}</label>
          <input v-model="newModel.apiKey" type="password" />
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? 'Base URL (可选)' : 'Base URL (Optional)' }}</label>
          <input v-model="newModel.baseUrl" type="text" placeholder="https://api.openai.com/v1" />
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="showAddModelDialog = false">{{ lang === 'zh' ? '取消' : 'Cancel' }}</button>
          <button class="btn-primary" @click="addNewModel">{{ lang === 'zh' ? '添加' : 'Add' }}</button>
        </div>
      </div>
    </div>

    <!-- 编辑模型对话框 -->
    <div v-if="showEditModelDialog" class="dialog-overlay" @click.self="showEditModelDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '配置模型' : 'Configure Model' }}</h3>
        <div v-if="selectedModel" class="form-content">
          <div class="form-group">
            <label>{{ lang === 'zh' ? '模型名称' : 'Model Name' }}</label>
            <input v-model="selectedModel.name" type="text" readonly />
          </div>
          <div class="form-group">
            <label>{{ lang === 'zh' ? 'API Key' : 'API Key' }}</label>
            <input v-model="editConfig.apiKey" type="password" />
          </div>
          <div class="form-group">
            <label>{{ lang === 'zh' ? 'Base URL' : 'Base URL' }}</label>
            <input v-model="editConfig.baseUrl" type="text" />
          </div>
          <div v-for="(value, key) in selectedModel.config" :key="key" class="form-group">
            <label>{{ key }}</label>
            <input v-model="editConfig[key]" type="text" />
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="showEditModelDialog = false">{{ lang === 'zh' ? '取消' : 'Cancel' }}</button>
          <button class="btn-primary" @click="saveModelConfig">{{ lang === 'zh' ? '保存' : 'Save' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useModelStore } from '@/stores/modelStore'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const modelStore = useModelStore()
const themeStore = useThemeStore()
const { providers, models, loading, activeProvider, activeFunction, functionTypes } = storeToRefs(modelStore)
const { language: lang } = storeToRefs(themeStore)

const showAddModelDialog = ref(false)
const showEditModelDialog = ref(false)
const selectedModel = ref<any>(null)
const newModel = ref({
  id: '',
  name: '',
  provider: 'openai',
  functionType: 'text',
  apiKey: '',
  baseUrl: '',
})
const editConfig = ref<Record<string, string>>({})

const filteredModels = computed(() => {
  let result = models.value
  if (activeProvider.value) {
    result = modelStore.getModelsByProvider(activeProvider.value)
  }
  if (activeFunction.value !== 'all') {
    result = result.filter(m => m.functionType === activeFunction.value)
  }
  return result
})

const enabledCount = computed(() => models.value.filter(m => m.enabled).length)
const onlineCount = computed(() => models.value.filter(m => m.status === 'online').length)
const officialCount = computed(() => {
  const official = providers.value.filter(p => p.category === 'official').map(p => p.id)
  return models.value.filter(m => official.includes(m.provider)).length
})

function fetchModels() {
  modelStore.fetchModels()
}

function getProviderLogo(providerId: string) {
  const p = providers.value.find(p => p.id === providerId)
  return p?.logo || '🤖'
}

function getProviderName(providerId: string) {
  const p = providers.value.find(p => p.id === providerId)
  if (!p) return providerId
  return lang.value === 'zh' ? p.name : p.nameEn
}

function getFunctionName(functionType: string) {
  const ft = functionTypes.value.find(f => f.id === functionType)
  if (!ft) return functionType
  return lang.value === 'zh' ? ft.name : ft.nameEn
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    online: lang.value === 'zh' ? '在线' : 'Online',
    offline: lang.value === 'zh' ? '离线' : 'Offline',
    error: lang.value === 'zh' ? '错误' : 'Error',
  }
  return texts[status] || status
}

function toggleModel(id: string) {
  try {
    modelStore.toggleModel(id)
  } catch (e) {
    console.error('[Model] Error toggling model:', e)
  }
}

function editModel(model: any) {
  selectedModel.value = model
  editConfig.value = { ...model.config }
  showEditModelDialog.value = true
}

function saveModelConfig() {
  if (selectedModel.value) {
    modelStore.updateModelConfig(selectedModel.value.id, editConfig.value)
  }
  showEditModelDialog.value = false
}

function addNewModel() {
  try {
    const config: Record<string, string> = {}
    if (newModel.value.apiKey) config.apiKey = newModel.value.apiKey
    if (newModel.value.baseUrl) config.baseUrl = newModel.value.baseUrl

    modelStore.addModel({
      id: newModel.value.id,
      name: newModel.value.name,
      provider: newModel.value.provider,
      functionType: newModel.value.functionType,
      category: newModel.value.functionType,
      config,
      status: 'offline',
      enabled: true,
    })

    showAddModelDialog.value = false
    newModel.value = { id: '', name: '', provider: 'openai', functionType: 'text', apiKey: '', baseUrl: '' }
  } catch (e) {
    console.error('[Model] Error adding model:', e)
  }
}

onMounted(() => {
  try {
    modelStore.fetchModels()
  } catch (e) {
    console.error('[Model] Error fetching models:', e)
  }
})
</script>

<style scoped>
.card { 
  background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); 
  border-radius: 16px; 
  border: 1px solid var(--border); 
  padding: 1.75rem; 
  color: var(--text-primary);
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.btn-primary {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--primary) 30%, transparent);
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: var(--primary);
}

.btn-config {
  padding: 0.35rem 0.75rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.3s;
}

.btn-config:hover {
  border-color: var(--primary);
}

.function-tabs, .provider-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
.function-tab, .provider-tab { 
  padding: 0.5rem 1rem; 
  border-radius: 8px; 
  border: 1px solid var(--border); 
  background: var(--bg-hover); 
  cursor: pointer; 
  transition: all 0.3s; 
  font-size: 0.85rem;
  color: var(--text-primary);
}
.function-tab:hover, .provider-tab:hover { border-color: var(--primary); }
.function-tab.active, .provider-tab.active { 
  background: linear-gradient(135deg, var(--primary), var(--secondary)); 
  color: white; 
  border-color: transparent; 
}
.provider-logo { margin-right: 0.25rem; }
.provider-category { margin-left: 0.25rem; opacity: 0.7; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.stat-card { background: var(--bg-hover); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; }
.stat-icon { font-size: 1.5rem; }
.stat-num { font-size: 1.5rem; font-weight: bold; color: var(--text-primary); }
.stat-label { font-size: 0.8rem; color: var(--text-secondary); }

.model-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
.model-card { 
  background: var(--bg-hover); 
  border-radius: 12px; 
  padding: 1.25rem; 
  transition: all 0.3s; 
  border: 1px solid var(--border);
}
.model-card:hover { border-color: var(--primary); transform: translateY(-2px); }
.model-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.model-provider-logo { font-size: 2rem; }
.model-info { flex: 1; }
.model-name { font-weight: 600; color: var(--text-primary); }
.model-provider { font-size: 0.8rem; color: var(--text-secondary); }
.model-status { 
  display: flex; 
  align-items: center; 
  gap: 0.5rem; 
  padding: 0.25rem 0.75rem; 
  border-radius: 20px; 
  font-size: 0.75rem; 
}
.model-status.online { background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); }
.model-status.offline { background: color-mix(in srgb, var(--danger) 20%, transparent); color: var(--danger); }
.model-status.error { background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.model-meta { display: flex; gap: 1.5rem; margin-bottom: 1rem; font-size: 0.85rem; }
.meta-label { color: var(--text-secondary); }
.meta-value { color: var(--text-primary); }
.model-config { background: var(--bg-dark); border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; }
.config-item { display: flex; gap: 0.5rem; font-size: 0.8rem; margin-bottom: 0.25rem; }
.config-key { color: var(--text-secondary); }
.config-value { color: var(--text-primary); font-family: monospace; }
.model-actions { display: flex; justify-content: space-between; align-items: center; }

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.toggle-switch.active {
  color: var(--success);
}

.toggle-track {
  width: 40px;
  height: 20px;
  background: var(--bg-dark);
  border-radius: 10px;
  position: relative;
  transition: all 0.3s;
}

.toggle-switch.active .toggle-track {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s;
}

.toggle-switch.active .toggle-thumb {
  left: 22px;
}

.toggle-label {
  width: 24px;
}

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { 
  background: var(--bg-card); 
  border-radius: 16px; 
  padding: 2rem; 
  width: 500px; 
  max-width: 90%; 
  border: 1px solid var(--border);
}
.dialog h3 { margin-bottom: 1.5rem; color: var(--text-primary); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); }
.form-group input, .form-group select { 
  width: 100%; 
  background: var(--bg-hover); 
  border: 1px solid var(--border); 
  border-radius: 8px; 
  padding: 0.75rem; 
  color: var(--text-primary); 
  outline: none; 
}
.form-group input:focus, .form-group select:focus { border-color: var(--primary); }
.form-group input::placeholder { color: var(--text-muted); }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem; }
</style>
