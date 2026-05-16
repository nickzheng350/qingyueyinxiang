<script setup lang="ts">import { ref, onMounted, computed } from 'vue';
import initWasmModule, { init_wasm, install_skill, list_skills, get_skill, enable_skill, disable_skill, uninstall_skill } from '@/wasm/skill_engine.js';
import { useThemeStore } from '@/stores/theme';
const themeStore = useThemeStore();
// 类型定义
interface Skill {
 id: string;
 name: string;
 description: string;
 version: string;
 author: string;
 enabled: boolean;
 installed_at: string;
}
interface InstallProgress {
 skillId: string;
 percentage: number;
 status: 'pending' | 'downloading' | 'extracting' | 'installing' | 'completed' | 'error';
 message: string;
}
interface ErrorInfo {
 code: string;
 message: string;
 timestamp: string;
}
// 状态
const wasmReady = ref(false);
const wasmLoading = ref(false);
const wasmError = ref<ErrorInfo | null>(null);
// 文件上传
const selectedFile = ref<File | null>(null);
const fileError = ref<string>('');
// 技能安装
const installing = ref(false);
const installProgress = ref<InstallProgress | null>(null);
const installResult = ref<{
 success: boolean;
 message: string;
} | null>(null);
// 技能列表
const skills = ref<Skill[]>([]);
const skillsLoading = ref(false);
const activeTab = ref<'list' | 'install'>('list');
// 选中的技能
const selectedSkill = ref<Skill | null>(null);
const skillDetailLoading = ref(false);
// 计算属性
const hasSkills = computed(() => skills.value.length > 0);
// 当前语言
const lang = computed(() => themeStore.language);
// 本地化消息
const messages = computed(() => ({
 // WASM 初始化相关
 wasmLoading: lang.value === 'zh' ? '正在初始化 WASM 技能引擎...' : 'Initializing WASM skill engine...',
 wasmInitFailed: lang.value === 'zh' ? 'WASM 初始化失败' : 'WASM initialization failed',
 wasmLoadFailed: lang.value === 'zh' ? 'WASM 模块加载失败' : 'WASM module load failed',
 networkError: lang.value === 'zh' ? '网络请求失败，请检查网络连接' : 'Network request failed, please check your network connection',
 retry: lang.value === 'zh' ? '重试' : 'Retry',
 // 技能列表相关
 skillList: lang.value === 'zh' ? '技能列表' : 'Skill List',
 installSkill: lang.value === 'zh' ? '安装技能' : 'Install Skill',
 noSkills: lang.value === 'zh' ? '暂无技能' : 'No skills',
 noSkillsHint: lang.value === 'zh' ? '请切换到「安装技能」标签页安装新技能' : 'Please switch to the "Install Skill" tab to install new skills',
 // 技能状态
 enabled: lang.value === 'zh' ? '已启用' : 'Enabled',
 disabled: lang.value === 'zh' ? '已禁用' : 'Disabled',
 // 操作按钮
 enable: lang.value === 'zh' ? '启用' : 'Enable',
 disable: lang.value === 'zh' ? '禁用' : 'Disable',
 uninstall: lang.value === 'zh' ? '卸载' : 'Uninstall',
 confirmUninstall: lang.value === 'zh' ? '确定要卸载此技能吗？' : 'Are you sure you want to uninstall this skill?',
 // 文件上传
 selectFile: lang.value === 'zh' ? '选择 .tar.gz 文件' : 'Select .tar.gz file',
 invalidExtension: lang.value === 'zh' ? '请选择 .tar.gz 或 .tgz 格式的技能包' : 'Please select a .tar.gz or .tgz skill package',
 fileSizeError: (size: string) => lang.value === 'zh' ? `文件大小不能超过 50MB，当前大小: ${size}` : `File size cannot exceed 50MB, current size: ${size}`,
 selectedFile: (name: string, size: string) => lang.value === 'zh' ? `✅ 已选择: ${name} (${size})` : `✅ Selected: ${name} (${size})`,
 installButton: lang.value === 'zh' ? '安装技能' : 'Install Skill',
 installing: lang.value === 'zh' ? '安装中...' : 'Installing...',
 // 安装进度
 pending: lang.value === 'zh' ? '待处理' : 'Pending',
 downloading: lang.value === 'zh' ? '下载中' : 'Downloading',
 extracting: lang.value === 'zh' ? '解压中' : 'Extracting',
 installingStatus: lang.value === 'zh' ? '安装中' : 'Installing',
 completed: lang.value === 'zh' ? '已完成' : 'Completed',
 error: lang.value === 'zh' ? '错误' : 'Error',
 // 安装结果
 installSuccess: lang.value === 'zh' ? '技能安装成功' : 'Skill installed successfully',
 installFailed: lang.value === 'zh' ? '技能安装失败' : 'Skill installation failed',
 unknownError: lang.value === 'zh' ? '安装过程中发生未知错误' : 'An unknown error occurred during installation',
 // 技能详情
 skillDetail: lang.value === 'zh' ? '技能详情' : 'Skill Detail',
 skillName: lang.value === 'zh' ? '技能名称' : 'Skill Name',
 skillId: lang.value === 'zh' ? '技能 ID' : 'Skill ID',
 description: lang.value === 'zh' ? '描述' : 'Description',
 version: lang.value === 'zh' ? '版本' : 'Version',
 author: lang.value === 'zh' ? '作者' : 'Author',
 status: lang.value === 'zh' ? '状态' : 'Status',
 installedAt: lang.value === 'zh' ? '安装时间' : 'Installed At',
 close: lang.value === 'zh' ? '关闭' : 'Close',
 // 提示信息
 hint: lang.value === 'zh' ? '提示：技能包必须是 .tar.gz 或 .tgz 格式，最大支持 50MB。' : 'Note: Skill package must be .tar.gz or .tgz format, maximum 50MB.',
}));
// 初始化 WASM
async function initializeWasm() {
 if (wasmReady.value)
 return;
 wasmLoading.value = true;
 wasmError.value = null;
 try {
 console.time('WASM 初始化');
 console.log('📦 正在加载 WASM 模块...');
 // 先加载 WASM 模块
 await initWasmModule();
 console.log('📦 WASM 模块加载完成');
 // 然后初始化技能引擎
 await init_wasm();
 console.timeEnd('WASM 初始化');
 wasmReady.value = true;
 console.log('✅ WASM 技能引擎初始化完成');
 await loadSkills();
 }
 catch (error) {
 console.error('❌ WASM 初始化失败:', error);
 const err = error instanceof Error ? error : null;
 let errorCode = 'WASM_INIT_FAILED';
 let errorMessage = messages.value.wasmLoadFailed;
 
 // 判断错误类型
 if (err) {
 if (err.message.includes('fetch') || err.message.includes('network')) {
 errorCode = 'NETWORK_ERROR';
 errorMessage = messages.value.networkError;
 } else if (err.message.includes('init_wasm')) {
 errorCode = 'WASM_INIT_ERROR';
 errorMessage = lang.value === 'zh' ? 'WASM 引擎初始化失败' : 'WASM engine initialization failed';
 } else if (err.message.includes('undefined')) {
 errorCode = 'MODULE_NOT_LOADED';
 errorMessage = lang.value === 'zh' ? 'WASM 模块未正确加载' : 'WASM module not loaded properly';
 } else {
 errorMessage = err.message;
 }
 }
 
 wasmError.value = {
 code: errorCode,
 message: errorMessage,
 timestamp: new Date().toISOString()
 };
 }
 finally {
 wasmLoading.value = false;
 }
}
// 加载技能列表
async function loadSkills() {
 if (!wasmReady.value)
 return;
 skillsLoading.value = true;
 try {
 const result = await list_skills();
 skills.value = Array.isArray(result) ? result : [];
 console.log('📋 技能列表已加载:', skills.value.length);
 }
 catch (error) {
 console.error('❌ 加载技能列表失败:', error);
 }
 finally {
 skillsLoading.value = false;
 }
}
// 文件选择处理
function handleFileSelect(event: Event) {
 const target = event.target as HTMLInputElement;
 const file = target.files?.[0];
 if (!file) {
 selectedFile.value = null;
 fileError.value = '';
 return;
 }
 // 文件类型验证
 const validExtensions = ['.tar.gz', '.tgz'];
 const isValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
 if (!isValidExtension) {
 fileError.value = '请选择 .tar.gz 或 .tgz 格式的技能包';
 selectedFile.value = null;
 return;
 }
 // 文件大小验证（最大 50MB）
 const maxSize = 50 * 1024 * 1024;
 if (file.size > maxSize) {
 fileError.value = `文件大小不能超过 50MB，当前大小: ${formatFileSize(file.size)}`;
 selectedFile.value = null;
 return;
 }
 fileError.value = '';
 selectedFile.value = file;
 console.log('📁 已选择文件:', file.name, formatFileSize(file.size));
}
// 格式化文件大小
function formatFileSize(bytes: number): string {
 if (bytes < 1024)
 return `${bytes} B`;
 if (bytes < 1024 * 1024)
 return `${(bytes / 1024).toFixed(2)} KB`;
 return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
// 安装技能
async function handleInstall() {
 if (!wasmReady.value || !selectedFile.value || installing.value)
 return;
 installing.value = true;
 installProgress.value = {
 skillId: `skill_${Date.now()}`,
 percentage: 0,
 status: 'pending',
 message: '准备安装...'
 };
 installResult.value = null;
 try {
 // 读取文件为 Uint8Array
 const arrayBuffer = await selectedFile.value.arrayBuffer();
 const tarData = new Uint8Array(arrayBuffer);
 // 模拟进度更新
 const progressInterval = setInterval(() => {
 if (installProgress.value && installProgress.value.percentage < 90) {
 installProgress.value.percentage += Math.floor(Math.random() * 15) + 5;
 if (installProgress.value.percentage >= 30 && installProgress.value.percentage < 60) {
 installProgress.value.status = 'downloading';
 installProgress.value.message = '正在下载...';
 }
 else if (installProgress.value.percentage >= 60 && installProgress.value.percentage < 85) {
 installProgress.value.status = 'extracting';
 installProgress.value.message = '正在解压...';
 }
 else if (installProgress.value.percentage >= 85) {
 installProgress.value.status = 'installing';
 installProgress.value.message = '正在安装...';
 }
 }
 }, 300);
 // 执行安装
 console.time('技能安装');
 const result = await install_skill(`skill_${Date.now()}`, tarData);
 console.timeEnd('技能安装');
 clearInterval(progressInterval);
 // 更新进度为完成
 installProgress.value.percentage = 100;
 installProgress.value.status = 'completed';
 installProgress.value.message = '安装完成';
 // 处理结果
 if (result && result.success !== undefined) {
 installResult.value = {
 success: result.success,
 message: result.message || (result.success ? '技能安装成功' : '技能安装失败')
 };
 if (result.success) {
 console.log('✅ 技能安装成功:', result);
 await loadSkills();
 }
 else {
 console.error('❌ 技能安装失败:', result.message);
 }
 }
 else {
 installResult.value = {
 success: true,
 message: '技能安装成功'
 };
 await loadSkills();
 }
 }
 catch (error) {
 console.error('❌ 安装技能时发生错误:', error);
 if (installProgress.value) {
 installProgress.value.status = 'error';
 installProgress.value.message = error instanceof Error ? error.message : '安装失败';
 }
 installResult.value = {
 success: false,
 message: error instanceof Error ? error.message : '安装过程中发生未知错误'
 };
 }
 finally {
 installing.value = false;
 // 3秒后清除进度
 setTimeout(() => {
 installProgress.value = null;
 }, 3000);
 }
}
// 获取技能详情
async function getSkillDetail(skillId: string) {
 if (!wasmReady.value)
 return;
 skillDetailLoading.value = true;
 try {
 const result = await get_skill(skillId);
 selectedSkill.value = result as Skill;
 console.log('📄 技能详情:', selectedSkill.value);
 }
 catch (error) {
 console.error('❌ 获取技能详情失败:', error);
 }
 finally {
 skillDetailLoading.value = false;
 }
}
// 启用技能
async function handleEnable(skillId: string) {
 if (!wasmReady.value)
 return;
 try {
 await enable_skill(skillId);
 console.log('✅ 技能已启用:', skillId);
 await loadSkills();
 }
 catch (error) {
 console.error('❌ 启用技能失败:', error);
 }
}
// 禁用技能
async function handleDisable(skillId: string) {
 if (!wasmReady.value)
 return;
 try {
 await disable_skill(skillId);
 console.log('❌ 技能已禁用:', skillId);
 await loadSkills();
 }
 catch (error) {
 console.error('❌ 禁用技能失败:', error);
 }
}
// 卸载技能
async function handleUninstall(skillId: string) {
 if (!wasmReady.value || !confirm('确定要卸载此技能吗？'))
 return;
 try {
 await uninstall_skill(skillId);
 console.log('🗑️ 技能已卸载:', skillId);
 await loadSkills();
 if (selectedSkill.value?.id === skillId) {
 selectedSkill.value = null;
 }
 }
 catch (error) {
 console.error('❌ 卸载技能失败:', error);
 }
}
// 关闭详情弹窗
function closeDetail() {
 selectedSkill.value = null;
}
// 获取状态文本
function getStatusText(status: string): string {
 const statusMap: Record<string, string> = {
 pending: '待处理',
 downloading: '下载中',
 extracting: '解压中',
 installing: '安装中',
 completed: '已完成',
 error: '错误'
 };
 return statusMap[status] || status;
}
// 获取状态样式类
function getStatusClass(status: string): string {
 const classMap: Record<string, string> = {
 pending: 'text-gray-500',
 downloading: 'text-blue-500',
 extracting: 'text-yellow-500',
 installing: 'text-green-500',
 completed: 'text-green-600',
 error: 'text-red-500'
 };
 return classMap[status] || 'text-gray-500';
}
onMounted(() => {
 initializeWasm();
});
</script>

<template>
  <div class="skill-wasm-manager">
    <!-- WASM 初始化状态 -->
    <div v-if="!wasmReady" class="mb-6">
      <div v-if="wasmLoading" class="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
        <svg class="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="text-blue-700">{{ messages.wasmLoading }}</span>
      </div>
      
      <div v-else-if="wasmError" class="p-4 bg-red-50 rounded-lg border border-red-200">
        <div class="flex items-start gap-3">
          <svg class="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <p class="text-red-800 font-medium">{{ messages.wasmInitFailed }}</p>
            <p class="text-red-600 text-sm mt-1">{{ wasmError.message }}</p>
            <button @click="initializeWasm" class="mt-2 text-sm text-red-600 hover:text-red-700 underline">
              {{ messages.retry }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div v-if="wasmReady" class="space-y-6">
      <!-- 标签切换 -->
      <div class="flex gap-4 border-b border-gray-200">
        <button
          @click="activeTab = 'list'"
          :class="[
            'px-4 py-2 font-medium text-sm transition-colors border-b-2 -mb-px',
            activeTab === 'list' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ messages.skillList }}
          <span v-if="skills.length" class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
            {{ skills.length }}
          </span>
        </button>
        <button
          @click="activeTab = 'install'"
          :class="[
            'px-4 py-2 font-medium text-sm transition-colors border-b-2 -mb-px',
            activeTab === 'install' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ messages.installSkill }}
        </button>
      </div>

      <!-- 技能列表 -->
      <div v-if="activeTab === 'list'" class="space-y-4">
        <div v-if="skillsLoading" class="flex justify-center py-8">
          <svg class="animate-spin h-6 w-6 text-gray-400" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        <div v-else-if="!hasSkills" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
          </svg>
          <h3 class="mt-4 text-lg font-medium text-gray-900">{{ messages.noSkills }}</h3>
          <p class="mt-2 text-gray-500">{{ messages.noSkillsHint }}</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="skill in skills"
            :key="skill.id"
            class="bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors cursor-pointer"
            @click="getSkillDetail(skill.id)"
          >
            <div class="flex items-start justify-between">
              <div>
                <h4 class="font-medium text-gray-900">{{ skill.name }}</h4>
                <p class="text-sm text-gray-500 mt-1">{{ skill.description }}</p>
              </div>
              <span
                :class="[
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  skill.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ skill.enabled ? messages.enabled : messages.disabled }}
              </span>
            </div>
            <div class="mt-3 flex items-center gap-4 text-xs text-gray-500">
              <span>{{ skill.version }}</span>
              <span>{{ skill.author }}</span>
            </div>
            <div class="mt-3 flex gap-2">
              <button
                @click.stop="skill.enabled ? handleDisable(skill.id) : handleEnable(skill.id)"
                class="px-3 py-1 text-xs font-medium rounded-md transition-colors"
                :class="skill.enabled ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' : 'bg-green-100 text-green-700 hover:bg-green-200'"
              >
                {{ skill.enabled ? messages.disable : messages.enable }}
              </button>
              <button
                @click.stop="handleUninstall(skill.id)"
                class="px-3 py-1 text-xs font-medium rounded-md bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
              >
                {{ messages.uninstall }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 安装技能 -->
      <div v-if="activeTab === 'install'" class="max-w-2xl">
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">{{ messages.installSkill }}</h3>
          
          <!-- 文件选择 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ messages.selectFile }}</label>
            <input
              type="file"
              accept=".tar.gz,.tgz"
              @change="handleFileSelect"
              class="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p v-if="fileError" class="mt-2 text-sm text-red-600">{{ fileError }}</p>
            <p v-if="selectedFile" class="mt-2 text-sm text-green-600">
              {{ messages.selectedFile(selectedFile.name, formatFileSize(selectedFile.size)) }}
            </p>
          </div>

          <!-- 安装按钮 -->
          <button
            @click="handleInstall"
            :disabled="!selectedFile || installing"
            class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="installing">{{ messages.installing }}</span>
            <span v-else>{{ messages.installButton }}</span>
          </button>

          <!-- 安装进度 -->
          <div v-if="installProgress" class="mt-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700">{{ getStatusText(installProgress.status) }}</span>
              <span :class="['text-sm font-medium', getStatusClass(installProgress.status)]">
                {{ installProgress.percentage }}%
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="[
                  installProgress.status === 'error' ? 'bg-red-500' :
                  installProgress.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                ]"
                :style="{ width: `${installProgress.percentage}%` }"
              ></div>
            </div>
            <p class="mt-2 text-sm text-gray-500">{{ installProgress.message }}</p>
          </div>

          <!-- 安装结果 -->
          <div
            v-if="installResult"
            :class="[
              'mt-4 p-4 rounded-lg border',
              installResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            ]"
          >
            <div class="flex items-center gap-3">
              <svg
                v-if="installResult.success"
                class="h-5 w-5 text-green-500"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <svg
                v-else
                class="h-5 w-5 text-red-500"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
              </svg>
              <span :class="['font-medium', installResult.success ? 'text-green-800' : 'text-red-800']">
                {{ installResult.message }}
              </span>
            </div>
          </div>

          <!-- 提示信息 -->
          <div class="mt-4 p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-600">
              {{ messages.hint }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 技能详情弹窗 -->
    <Teleport to="body">
      <div
        v-if="selectedSkill"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="closeDetail"
      >
        <div class="bg-white rounded-xl shadow-xl max-w-lg w-full">
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="text-lg font-semibold text-gray-900">{{ messages.skillDetail }}</h3>
            <button
              @click="closeDetail"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
          
          <div v-if="skillDetailLoading" class="p-8 flex justify-center">
            <svg class="animate-spin h-6 w-6 text-gray-400" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          
          <div v-else class="p-4 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-500">{{ messages.skillName }}</label>
              <p class="text-gray-900">{{ selectedSkill.name }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500">{{ messages.skillId }}</label>
              <p class="text-gray-900 font-mono text-sm">{{ selectedSkill.id }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500">{{ messages.description }}</label>
              <p class="text-gray-900">{{ selectedSkill.description }}</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-500">{{ messages.version }}</label>
                <p class="text-gray-900">{{ selectedSkill.version }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500">{{ messages.author }}</label>
                <p class="text-gray-900">{{ selectedSkill.author }}</p>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500">{{ messages.status }}</label>
              <span
                :class="[
                  'px-2 py-1 text-xs font-medium rounded-full',
                  selectedSkill.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ selectedSkill.enabled ? messages.enabled : messages.disabled }}
              </span>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500">{{ messages.installTime }}</label>
              <p class="text-gray-900 text-sm">{{ selectedSkill.installed_at }}</p>
            </div>
          </div>
          
          <div class="flex gap-3 p-4 border-t">
            <button
              @click="closeDetail"
              class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {{ messages.close }}
            </button>
            <button
              @click="selectedSkill.enabled ? handleDisable(selectedSkill.id) : handleEnable(selectedSkill.id)"
              class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors"
              :class="selectedSkill.enabled ? 'bg-yellow-600 text-white hover:bg-yellow-700' : 'bg-green-600 text-white hover:bg-green-700'"
            >
              {{ selectedSkill.enabled ? messages.disable : messages.enable }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.skill-wasm-manager {
  min-height: 400px;
}
</style>
