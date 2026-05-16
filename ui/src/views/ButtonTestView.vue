<template>
  <div class="button-test-container">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">🔘 按钮样式测试</div>
          <div class="card-subtitle">查看所有按钮类型和状态</div>
        </div>
      </div>

      <!-- 基础按钮类型 -->
      <div class="section">
        <h3 class="section-title">基础按钮类型</h3>
        <div class="button-grid">
          <div class="button-item">
            <button class="btn btn-primary">Primary Button</button>
            <span class="button-label">btn-primary</span>
          </div>
          <div class="button-item">
            <button class="btn btn-secondary">Secondary Button</button>
            <span class="button-label">btn-secondary</span>
          </div>
          <div class="button-item">
            <button class="btn btn-outline">Outline Button</button>
            <span class="button-label">btn-outline</span>
          </div>
          <div class="button-item">
            <button class="btn btn-danger">Danger Button</button>
            <span class="button-label">btn-danger</span>
          </div>
        </div>
      </div>

      <!-- 尺寸变体 -->
      <div class="section">
        <h3 class="section-title">尺寸变体</h3>
        <div class="button-grid">
          <div class="button-item">
            <button class="btn btn-primary btn-sm">Small</button>
            <span class="button-label">btn-sm</span>
          </div>
          <div class="button-item">
            <button class="btn btn-primary">Default</button>
            <span class="button-label">default</span>
          </div>
          <div class="button-item">
            <button class="btn btn-primary btn-lg">Large</button>
            <span class="button-label">btn-lg</span>
          </div>
        </div>
      </div>

      <!-- 状态 -->
      <div class="section">
        <h3 class="section-title">按钮状态</h3>
        <div class="button-grid">
          <div class="button-item">
            <button class="btn btn-primary btn-loading">Loading...</button>
            <span class="button-label">btn-loading</span>
          </div>
          <div class="button-item">
            <button class="btn btn-primary" disabled>Disabled</button>
            <span class="button-label">disabled</span>
          </div>
          <div class="button-item">
            <button class="btn btn-config">Config Button</button>
            <span class="button-label">btn-config</span>
          </div>
          <div class="button-item">
            <button class="btn btn-text">Text Button</button>
            <span class="button-label">btn-text</span>
          </div>
        </div>
      </div>

      <!-- 按钮组 -->
      <div class="section">
        <h3 class="section-title">按钮组</h3>
        <div class="button-group-demo">
          <div class="btn-group">
            <button class="btn active">Tab 1</button>
            <button class="btn">Tab 2</button>
            <button class="btn">Tab 3</button>
          </div>
        </div>
      </div>

      <!-- 图标按钮 -->
      <div class="section">
        <h3 class="section-title">图标按钮</h3>
        <div class="button-grid">
          <div class="button-item">
            <button class="btn btn-icon btn-primary">📋</button>
            <span class="button-label">btn-icon</span>
          </div>
          <div class="button-item">
            <button class="btn btn-icon-lg btn-primary">⚙️</button>
            <span class="button-label">btn-icon-lg</span>
          </div>
          <div class="button-item">
            <button class="btn btn-icon btn-secondary">🔍</button>
            <span class="button-label">secondary</span>
          </div>
          <div class="button-item">
            <button class="btn btn-icon btn-outline">✨</button>
            <span class="button-label">outline</span>
          </div>
        </div>
      </div>

      <!-- 组合按钮 -->
      <div class="section">
        <h3 class="section-title">组合按钮</h3>
        <div class="button-grid">
          <div class="button-item">
            <button class="btn btn-primary btn-sm">✓ Confirm</button>
            <span class="button-label">small + icon</span>
          </div>
          <div class="button-item">
            <button class="btn btn-danger btn-sm">🗑️ Delete</button>
            <span class="button-label">danger + small</span>
          </div>
          <div class="button-item">
            <button class="btn btn-secondary btn-lg">📁 Browse Files</button>
            <span class="button-label">large + icon</span>
          </div>
          <div class="button-item">
            <button class="btn btn-outline btn-sm">✏️ Edit</button>
            <span class="button-label">outline + small</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 按钮测试页面
</script>

<style scoped>
.button-test-container {
  padding: 2rem;
}

.card {
  background: linear-gradient(145deg, var(--bg-card), var(--bg-dark));
  border-radius: 16px;
  border: 1px solid var(--border);
  padding: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--bg-hover);
  border-radius: 8px;
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.button-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--bg-hover);
  border-radius: 8px;
}

.button-label {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.button-group-demo {
  padding: 1rem;
  background: var(--bg-hover);
  border-radius: 8px;
  display: flex;
  justify-content: center;
}
</style>
