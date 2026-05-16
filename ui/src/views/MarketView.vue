<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">🏪 技能市场</div>
        <div class="card-subtitle">发现新技能，一键安装</div>
      </div>
      <button class="btn btn-secondary" @click="fetchMarket">🔄 刷新</button>
    </div>
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
      <el-input v-model="keyword" placeholder="搜索技能名称、描述或标签..." style="flex: 1;" @keyup.enter="search" />
      <button class="btn btn-primary" @click="search">🔍 搜索</button>
    </div>
    <div v-if="loading" style="text-align: center; padding: 3rem;"><span class="loading"></span></div>
    <div v-else class="grid-auto">
      <SkillCard v-for="s in displayedSkills" :key="s.id" :skill="s" @install="install" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import SkillCard from '@/components/SkillCard.vue'
import { useSkillStore } from '@/stores/skillStore'
import { storeToRefs } from 'pinia'

const store = useSkillStore()
const { market, loading } = storeToRefs(store)
const keyword = ref('')

const displayedSkills = computed(() => {
  if (!keyword.value) return market.value
  const k = keyword.value.toLowerCase()
  return market.value.filter(s => s.name.toLowerCase().includes(k) || s.description.toLowerCase().includes(k))
})

const mockMarket = [
  { id: 'm1', name: '代码审查', description: '自动审查代码质量', type: 'code', installed: false },
  { id: 'm2', name: '网页爬虫', description: '高效网页内容抓取', type: 'web', installed: false },
  { id: 'm3', name: '数据可视化', description: '图表生成与渲染', type: 'data', installed: false },
  { id: 'm4', name: 'OCR识别', description: '图像文字识别', type: 'ai', installed: false },
]

async function fetchMarket() {
  await store.fetchMarket()
  if (!market.value.length) market.value = mockMarket
}

function search() {
  // already reactive
}

async function install(skill: any) {
  try {
    // 调用后端安装接口
    const response = await client.post(`/skills/${skill.id}/install`)
    
    if (response.status === 'success') {
      skill.installed = true
      ElMessage.success(response.message || `${skill.name} 安装成功`)
    } else {
      ElMessage.error(response.message || `${skill.name} 安装失败`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || `${skill.name} 安装失败`)
  }
}

onMounted(fetchMarket)
</script>

<style scoped>
.card { 
  background: linear-gradient(145deg, var(--bg-card), var(--bg-dark));
  border-radius: 16px;
  border: 1px solid var(--border);
  padding: 1.75rem;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.grid-auto { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
</style>