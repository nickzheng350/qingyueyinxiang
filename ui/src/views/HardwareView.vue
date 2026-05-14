<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">⚙️ 硬件配置评估</div><div class="card-subtitle">企业级硬件资源管理</div></div>
      <span class="tier-badge tier-development">开发环境</span>
    </div>
    <div class="grid-2" style="margin-bottom: 1.5rem;">
      <div class="hardware-item"><div class="hardware-title">💻 CPU</div><div class="hardware-info">{{ cpuInfo }}</div></div>
      <div class="hardware-item"><div class="hardware-title">🧠 内存</div><div class="hardware-info">{{ memoryInfo }}</div></div>
      <div class="hardware-item"><div class="hardware-title">🎮 GPU</div><div class="hardware-info">{{ gpuInfo }}</div></div>
      <div class="hardware-item"><div class="hardware-title">📦 存储</div><div class="hardware-info">{{ storageInfo }}</div></div>
    </div>
    <div class="card-header"><div class="card-title">📊 硬件层级推荐</div></div>
    <div class="grid-auto">
      <div v-for="tier in tiers" :key="tier.id" class="tier-card" @click="selectTier(tier.id)">
        <div style="font-size: 2rem; margin-bottom: 1rem;">{{ tier.icon }}</div>
        <div class="tier-name">{{ tier.name }}</div>
        <div class="tier-desc">{{ tier.desc }}</div>
        <div :class="`tier-badge tier-${tier.id}`" style="margin-top: 1rem;">{{ tier.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const cpuInfo = ref('Intel i7-12700K × 12核 @ 3.6GHz')
const memoryInfo = ref('32 GB DDR5 3600MHz')
const gpuInfo = ref('无独立GPU (开发环境)')
const storageInfo = ref('1 TB NVMe SSD')
const tiers = [
  { id: 'development', icon: '💻', name: '开发环境', desc: '适合开发测试，4核CPU，16GB内存', label: '入门级' },
  { id: 'small', icon: '📱', name: '小型部署', desc: '适合小型团队，8核CPU，32GB内存', label: '小型' },
  { id: 'medium', icon: '💼', name: '中型部署', desc: '适合中型企业，16核CPU，64GB内存，1×GPU', label: '中型' },
  { id: 'large', icon: '🏢', name: '大型部署', desc: '适合大型企业，32核CPU，128GB内存，2×GPU', label: '大型' },
  { id: 'enterprise', icon: '🏆', name: '企业级部署', desc: '高可用集群，64核CPU，256GB内存，4×GPU', label: '企业级' },
  { id: 'cluster', icon: '☁️', name: '集群部署', desc: '多节点集群，自动扩缩容，多GPU', label: '集群' },
]
function selectTier(id: string) { console.log('tier:', id) }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
.hardware-item { background: var(--bg-dark); border-radius: 12px; padding: 1.25rem; }
.hardware-title { font-weight: 600; margin-bottom: 0.5rem; }
.hardware-info { color: var(--text-secondary); font-size: 0.85rem; }
.grid-auto { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; }
.tier-card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; padding: 1.75rem; border: 1px solid var(--border); cursor: pointer; transition: all 0.4s; }
.tier-card:hover { border-color: var(--primary); transform: translateY(-4px); }
.tier-name { font-size: 1.1rem; font-weight: 600; }
.tier-desc { color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem; }
.tier-badge { padding: 0.375rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
.tier-development { background: color-mix(in srgb, var(--text-secondary) 20%, transparent); color: var(--text-secondary); }
.tier-small { background: color-mix(in srgb, var(--primary) 20%, transparent); color: white; }
.tier-medium { background: color-mix(in srgb, var(--secondary) 20%, transparent); color: var(--secondary); }
.tier-large { background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning); }
.tier-enterprise { background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); }
.tier-cluster { background: color-mix(in srgb, var(--danger) 20%, transparent); color: var(--danger); }
</style>