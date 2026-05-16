<template>
  <div class="stat-card">
    <div class="stat-icon" :class="color">{{ icon }}</div>
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div class="progress-bar">
      <div class="progress-fill" :class="color" :style="{ width: progress + '%' }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ icon: string; value: string; label: string; progress: number; color: string }>()
</script>

<style scoped>
.stat-card {
  background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.9));
  border-radius: 16px;
  padding: 1.75rem;
  border: 1px solid var(--border);
  transition: all 0.4s;
}
.stat-card:hover {
  border-color: var(--primary);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.cpu { background: rgba(59, 130, 246, 0.2); }
.memory { background: rgba(16, 185, 129, 0.2); }
.gpu { background: rgba(139, 92, 246, 0.2); }
.stat-value { font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }
.stat-label { font-size: 0.85rem; color: var(--text-secondary); }
.progress-bar {
  height: 8px;
  background: var(--bg-hover);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.75rem;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.progress-fill.cpu { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.progress-fill.memory { background: linear-gradient(90deg, var(--success), #34d399); }
.progress-fill.gpu { background: linear-gradient(90deg, var(--secondary), #a78bfa); }
</style>