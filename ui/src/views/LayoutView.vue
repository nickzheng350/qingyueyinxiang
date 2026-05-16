<template>
  <div class="app-container">
    <AppSidebar />
    <main class="main-content">
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
import AppSidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  margin-left: 196px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-area {
  flex: 1;
  padding: 1.5rem;
  width: 100%;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
  
  .content-area {
    padding: 1rem;
  }
}
</style>
