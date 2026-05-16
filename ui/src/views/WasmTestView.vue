<template>
  <div class="wasm-test-view">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">⚡ WASM 技能引擎测试</div>
          <div class="card-subtitle">测试 WASM 模块的初始化、技能上传和安装流程</div>
        </div>
      </div>

      <!-- 简单测试组件 -->
      <SimpleWasmTest />

      <!-- 完整技能管理器 -->
      <div class="manager-section">
        <h4>🎯 完整技能管理器</h4>
        <SkillWasmManager />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SimpleWasmTest from '@/components/SimpleWasmTest.vue'
import SkillWasmManager from '@/components/SkillWasmManager.vue'
</script>

<style scoped>
.wasm-test-view {
  min-height: 100vh;
  padding: 1rem;
}

.card {
  background: linear-gradient(145deg, var(--bg-card), var(--bg-dark));
  border-radius: 16px;
  border: 1px solid var(--border);
  padding: 1.75rem;
}

.card-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.card-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.manager-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.manager-section h4 {
  margin-bottom: 1rem;
}
</style>
