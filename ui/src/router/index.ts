import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/views/LayoutView.vue'),
    children: [
      // 顶部Tab 1: 对话
      { path: 'dialogue', name: 'Dialogue', component: () => import('@/views/DialogueView.vue') },
      // 顶部Tab 2: 记忆
      { path: 'memory', name: 'Memory', component: () => import('@/views/MemoryView.vue') },
      // 顶部Tab 3: 技能
      { path: 'skills', name: 'Skills', component: () => import('@/views/SkillsView.vue') },
      // 顶部Tab 4: 插件
      { path: 'plugins', name: 'Plugins', component: () => import('@/views/PluginsView.vue') },
      // 顶部Tab 5: 工作流
      { path: 'workflow', name: 'Workflow', component: () => import('@/views/WorkflowView.vue') },
      // 顶部Tab 6: 模型
      { path: 'models', name: 'Models', component: () => import('@/views/ModelView.vue') },
      // 顶部Tab 7: 经验库
      { path: 'experience', name: 'Experience', component: () => import('@/views/ExperienceView.vue') },
      // 默认跳转到对话
      { path: '', redirect: '/dialogue' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'market', name: 'Market', component: () => import('@/views/MarketView.vue') },
      { path: 'generative', name: 'Generative', component: () => import('@/views/GenerativeView.vue') },
      { path: 'files', name: 'Files', component: () => import('@/views/FilesView.vue') },
      { path: 'hardware', name: 'Hardware', component: () => import('@/views/HardwareView.vue') },
      { path: 'tasks', name: 'Tasks', component: () => import('@/views/TasksView.vue') },
      { path: 'prompt', name: 'Prompt', component: () => import('@/views/PromptView.vue') },
      { path: 'api', name: 'Api', component: () => import('@/views/ApiView.vue') },
      { path: 'system', name: 'System', component: () => import('@/views/SystemView.vue') },
      { path: 'buttons', name: 'Buttons', component: () => import('@/views/ButtonTestView.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.onError((error) => {
  console.error('[Router] Navigation error:', error)
})

router.beforeEach((to, from, next) => {
  try {
    next()
  } catch (error) {
    console.error('[Router] Before each error:', error)
    next('/dialogue')
  }
})

router.afterEach((to, from) => {
  console.log('[Router] Navigated from', from.path, 'to', to.path)
})

export default router
