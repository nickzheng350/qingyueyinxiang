#!/bin/bash
# Rust 技能引擎 WASM 构建脚本
# 集成到 Vue 项目构建流程

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RUST_ENGINE_DIR="$PROJECT_ROOT/rust-skill-engine"
UI_DIR="$PROJECT_ROOT/ui"
WASM_OUTPUT_DIR="$UI_DIR/src/wasm"

echo "=========================================="
echo "  Rust 技能引擎 WASM 构建"
echo "=========================================="
echo ""

# 检查依赖
check_dependencies() {
    echo "1. 检查依赖..."
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ 错误：未找到 cargo，请先安装 Rust"
        echo "   安装地址：https://rustup.rs/"
        exit 1
    fi
    
    if ! command -v wasm-pack &> /dev/null; then
        echo "   安装 wasm-pack..."
        curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
    fi
    
    echo "   ✅ 依赖检查通过"
    echo "      - cargo: $(cargo --version)"
    echo "      - wasm-pack: $(wasm-pack --version)"
}

# 创建输出目录
setup_output_dir() {
    echo ""
    echo "2. 创建输出目录..."
    
    mkdir -p "$WASM_OUTPUT_DIR"
    echo "   输出目录：$WASM_OUTPUT_DIR"
}

# 构建 WASM
build_wasm() {
    echo ""
    echo "3. 构建 WASM..."
    
    cd "$RUST_ENGINE_DIR"
    
    # 构建 WASM (针对 web 优化)
    wasm-pack build --target web --release
    
    echo "   ✅ WASM 构建完成"
}

# 复制 WASM 文件到 Vue 项目
copy_wasm_files() {
    echo ""
    echo "4. 复制文件到 Vue 项目..."
    
    # 复制 .wasm 文件
    cp "$RUST_ENGINE_DIR/pkg/skill_engine_bg.wasm" "$WASM_OUTPUT_DIR/"
    
    # 复制 JS 绑定
    cp "$RUST_ENGINE_DIR/pkg/skill_engine.js" "$WASM_OUTPUT_DIR/"
    cp "$RUST_ENGINE_DIR/pkg/skill_engine.d.ts" "$WASM_OUTPUT_DIR/"
    
    # 创建 index.js 方便导入
    cat > "$WASM_OUTPUT_DIR/index.js" << 'EOF'
// WASM 模块自动加载器
import init, * as wasm from './skill_engine.js'

let initialized = false

export async function initWasm() {
  if (initialized) return
  await init()
  initialized = true
}

export * from './skill_engine.js'
export default wasm
EOF
    
    echo "   ✅ 文件复制完成"
    echo "      - skill_engine_bg.wasm"
    echo "      - skill_engine.js"
    echo "      - skill_engine.d.ts"
    echo "      - index.js"
}

# 更新 Vue 项目配置
update_vue_config() {
    echo ""
    echo "5. 更新 Vue 项目配置..."
    
    # 检查 vite.config.ts 是否需要配置 WASM 支持
    if [ -f "$UI_DIR/vite.config.ts" ]; then
        if ! grep -q "wasm" "$UI_DIR/vite.config.ts"; then
            echo "   添加 WASM 支持到 vite.config.ts..."
            
            # 备份原文件
            cp "$UI_DIR/vite.config.ts" "$UI_DIR/vite.config.ts.bak"
            
            # 添加 WASM 配置（如果不存在）
            cat >> "$UI_DIR/vite.config.ts" << 'EOF'

// WASM 支持配置
export default defineConfig({
  // ... 其他配置
  optimizeDeps: {
    exclude: ['@/wasm/skill_engine_bg.wasm']
  },
  assetsInclude: ['**/*.wasm']
})
EOF
            echo "   ✅ Vite 配置已更新"
        else
            echo "   ℹ️  Vite 已配置 WASM 支持"
        fi
    fi
}

# 创建使用示例
create_usage_example() {
    echo ""
    echo "6. 创建使用示例..."
    
    cat > "$WASM_OUTPUT_DIR/README.md" << 'EOF'
# WASM 技能引擎使用指南

## 快速开始

### 1. 初始化 WASM

在 Vue 组件中初始化 WASM 模块：

```typescript
import { initWasm, install_skill } from '@/wasm'

// 在应用启动时初始化
await initWasm()
```

### 2. 使用技能安装功能

```typescript
import { install_skill } from '@/wasm'

async function handleInstall(skillId: string, tarPath: string) {
  try {
    const result = await install_skill(skillId, tarPath)
    console.log('安装成功:', result)
  } catch (error) {
    console.error('安装失败:', error)
  }
}
```

### 3. 在 Vue 组件中使用

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { initWasm, install_skill } from '@/wasm'

const loading = ref(false)
const progress = ref(0)

onMounted(async () => {
  await initWasm()
  console.log('WASM 初始化完成')
})

async function handleInstall() {
  loading.value = true
  try {
    const result = await install_skill('test_skill', '/path/to/file.tar.gz')
    console.log('安装完成:', result)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button @click="handleInstall" :disabled="loading">
    {{ loading ? '安装中...' : '安装技能' }}
  </button>
</template>
```

## API 参考

### initWasm()

初始化 WASM 模块，必须在调用其他函数前执行。

```typescript
await initWasm()
```

### install_skill(skillId: string, tarPath: string): Promise<Skill>

安装技能。

**参数:**
- `skillId`: 技能 ID
- `tarPath`: tar.gz 文件路径

**返回:**
- `Promise<Skill>`: 安装后的技能对象

### uninstall_skill(skillId: string): Promise<void>

卸载技能。

**参数:**
- `skillId`: 技能 ID

### list_skills(): Promise<Skill[]>

列出所有已安装的技能。

**返回:**
- `Promise<Skill[]>`: 技能列表

## 性能优化

### 1. 预加载 WASM

在应用启动时预加载：

```typescript
// main.ts
import { initWasm } from '@/wasm'

async function bootstrap() {
  await initWasm()
  createApp(App).mount('#app')
}

bootstrap()
```

### 2. 懒加载

按需加载 WASM 模块：

```typescript
const loadWasm = async () => {
  const wasm = await import('@/wasm')
  await wasm.initWasm()
  return wasm
}
```

## 故障排查

### WASM 加载失败

检查浏览器控制台是否有 CORS 错误，确保服务器正确配置 MIME 类型：

```
application/wasm
```

### 性能问题

使用 Chrome DevTools 的 Performance 面板分析 WASM 执行性能。

## 构建

重新构建 WASM:

```bash
./scripts/build_wasm.sh
```
EOF
    
    echo "   ✅ 使用示例已创建"
}

# 更新 package.json
update_package_json() {
    echo ""
    echo "7. 更新 package.json..."
    
    if [ -f "$UI_DIR/package.json" ]; then
        # 检查是否已有 wasm 脚本
        if ! grep -q '"build:wasm"' "$UI_DIR/package.json"; then
            echo "   添加 WASM 构建脚本..."
            
            # 使用 sed 添加脚本
            sed -i '/"scripts": {/a\
    "build:wasm": "../scripts/build_wasm.sh",' "$UI_DIR/package.json"
            
            echo "   ✅ package.json 已更新"
            echo "      运行：npm run build:wasm"
        else
            echo "   ℹ️  package.json 已包含 WASM 脚本"
        fi
    fi
}

# 显示构建统计
show_build_stats() {
    echo ""
    echo "8. 构建统计..."
    
    if [ -f "$WASM_OUTPUT_DIR/skill_engine_bg.wasm" ]; then
        WASM_SIZE=$(du -h "$WASM_OUTPUT_DIR/skill_engine_bg.wasm" | cut -f1)
        echo "   WASM 文件大小：$WASM_SIZE"
        
        JS_SIZE=$(du -h "$WASM_OUTPUT_DIR/skill_engine.js" | cut -f1)
        echo "   JS 绑定大小：$JS_SIZE"
        
        echo ""
        echo "   总大小：$(du -sh "$WASM_OUTPUT_DIR" | cut -f1)"
    fi
}

# 主函数
main() {
    check_dependencies
    setup_output_dir
    build_wasm
    copy_wasm_files
    update_vue_config
    create_usage_example
    update_package_json
    show_build_stats
    
    echo ""
    echo "=========================================="
    echo "  ✅ WASM 构建完成！"
    echo "=========================================="
    echo ""
    echo "下一步:"
    echo "  1. 在 Vue 组件中导入 WASM 模块"
    echo "  2. 调用 initWasm() 初始化"
    echo "  3. 使用 install_skill() 等函数"
    echo ""
    echo "示例:"
    echo "  import { initWasm, install_skill } from '@/wasm'"
    echo "  await initWasm()"
    echo "  const result = await install_skill('skill_id', 'path.tar.gz')"
}

main "$@"
