<template>
  <div class="app-container">
    <AppSidebar />
    <main class="main-content" :class="{ 'full-width': sidebarCollapsed }">
      <AppHeader />
      <div class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'

const sidebarCollapsed = ref(false)
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  margin-left: 280px;
  min-height: 100vh;
  transition: margin-left 0.3s;
}

.main-content.full-width {
  margin-left: 0;
}

.content-area {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>