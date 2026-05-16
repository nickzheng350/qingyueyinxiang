// === 页面导航 ===
function showTab(tabId) {
    const tabs = ['dashboard', 'market', 'skills', 'generative', 'workflow', 'files', 'hardware', 'tasks', 'prompt', 'api', 'system'];
    tabs.forEach(id => {
        const tab = document.getElementById(id + '-tab');
        if (tab) {
            tab.classList.remove('active');
        }
    });
    
    const activeTab = document.getElementById(tabId + '-tab');
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    document.querySelector(`[onclick="showTab('${tabId}')"]`)?.classList.add('active');
    
    const titles = {
        dashboard: '控制台',
        market: '技能市场',
        skills: '技能中心',
        generative: '生成式功能',
        workflow: '工作流水线',
        files: '文件管理',
        hardware: '硬件配置',
        tasks: '任务管理',
        prompt: '提示词管理',
        api: 'API设置',
        system: '系统设置'
    };
    document.querySelector('.page-title')?.setTextContent(titles[tabId] || '控制台');
}

// === 仪表盘 ===
function loadDashboardData() {
    updateSystemStats();
    loadRecentTasks();
}

function updateSystemStats() {
    const stats = [
        { id: 'cpu-value', label: 'cpu', min: 20, max: 80 },
        { id: 'memory-value', label: 'memory', min: 30, max: 70 },
        { id: 'gpu-value', label: 'gpu', min: 10, max: 90 },
        { id: 'storage-value', label: 'storage', min: 40, max: 60 }
    ];
    
    stats.forEach(stat => {
        const value = Math.floor(Math.random() * (stat.max - stat.min + 1)) + stat.min;
        const el = document.getElementById(stat.id);
        if (el) el.textContent = value + '%';
        
        const progress = document.querySelector(`.progress-fill.${stat.label}`);
        if (progress) progress.style.width = value + '%';
    });
}

function loadRecentTasks() {
    const tasks = [
        { id: 'T001', name: '模型训练任务', status: 'running', progress: 67, time: '5分钟前' },
        { id: 'T002', name: '数据处理', status: 'success', progress: 100, time: '15分钟前' },
        { id: 'T003', name: '图片生成批量任务', status: 'pending', progress: 0, time: '30分钟前' },
        { id: 'T004', name: '音频合成', status: 'error', progress: 34, time: '1小时前' }
    ];
    
    const tbody = document.querySelector('#recent-tasks tbody');
    if (tbody) {
        tbody.innerHTML = tasks.map(task => `
            <tr>
                <td>${task.id}</td>
                <td>${task.name}</td>
                <td><span class="status-badge status-${task.status}">${getStatusText(task.status)}</span></td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill ${task.status === 'success' ? 'memory' : task.status === 'running' ? 'cpu' : 'gpu'}" style="width: ${task.progress}%"></div>
                    </div>
                </td>
                <td>${task.time}</td>
            </tr>
        `).join('');
    }
}

function getStatusText(status) {
    const texts = { running: '运行中', success: '已完成', pending: '等待中', error: '失败' };
    return texts[status] || status;
}

// === 生成式功能 ===
function showGenTab(tab) {
    const tabs = ['text', 'image', 'audio', 'video'];
    tabs.forEach(t => {
        document.getElementById('gen-' + t).style.display = 'none';
    });
    document.getElementById('gen-' + tab).style.display = 'block';
    
    const buttons = document.querySelectorAll('.gen-tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[onclick="showGenTab('${tab}')"]`)?.classList.add('active');
}

async function generateText() {
    const input = document.getElementById('text-input');
    if (!input || !input.value.trim()) {
        alert('请输入内容');
        return;
    }
    
    const output = document.getElementById('text-output');
    if (output) {
        output.innerHTML = '<div style="text-align: center; padding: 3rem;"><span class="loading"></span><p style="margin-top: 1rem;">✨ AI 正在生成文本...</p></div>';
    }
    
    const type = document.getElementById('text-type').value;
    const settings = getApiSettings();
    
    let result = '';
    
    try {
        if (settings.apiKey && settings.apiUrl) {
            const prompts = {
                article: `请根据以下内容写一篇文章：${input.value}`,
                summary: `请总结以下内容：${input.value}`,
                translate: `请将以下内容翻译成中文：${input.value}`,
                rewrite: `请改写润色以下内容：${input.value}`,
                creative: `请根据以下主题进行创意写作：${input.value}`,
                email: `请根据以下内容写一封邮件：${input.value}`,
                code: `请根据以下需求生成代码：${input.value}`
            };
            
            if (settings.apiType === 'anthropic') {
                result = await callAnthropicWithKey(prompts[type] || prompts.article, settings.apiKey);
            } else {
                result = await callOpenAIWithKey(prompts[type] || prompts.article, settings.apiKey, settings.apiUrl, settings.defaultModel);
            }
        } else {
            const contents = {
                article: '这是一篇由AI生成的文章内容。文章涵盖了当前热门话题，提供了深入的分析和独到的见解。AI技术正在改变我们的生活方式，让创作变得更加高效和便捷。',
                summary: '本文简要总结了核心要点：人工智能正在快速发展，机器学习模型不断进步，自然语言处理能力大幅提升，未来前景广阔。',
                translate: 'Hello, this is an English text translated into Chinese. 你好，这是一段英文文本翻译成中文的结果。',
                rewrite: '原文经过AI润色改写后，表达更加流畅自然，逻辑更加清晰严谨，可读性得到显著提升。',
                creative: '在遥远的未来，人工智能与人类和谐共处，共同探索宇宙的奥秘。机器人艺术家创作着令人惊叹的作品，AI诗人吟诵着永恒的诗篇。',
                email: '尊敬的收件人：您好！\n\n感谢您的来信。关于您提出的问题，我们已经进行了深入研究，并将尽快给您答复。\n\n此致\n敬礼',
                code: 'def hello_world():\n    """AI生成的示例代码"""\n    print("Hello, World!")\n    return "Success"\n\nif __name__ == "__main__":\n    result = hello_world()\n    print(result)'
            };
            result = contents[type] || contents.article;
            await new Promise(resolve => setTimeout(resolve, 1500));
        }
        
        if (output) {
            output.innerHTML = `<p>${result}</p>`;
            const copyBtn = document.getElementById('copy-text-btn');
            if (copyBtn) copyBtn.disabled = false;
        }
    } catch (error) {
        if (output) {
            output.innerHTML = `<p style="color: var(--danger);">生成失败: ${error.message}</p>`;
        }
    }
}

function copyTextResult() {
    const output = document.getElementById('text-output');
    if (output) {
        navigator.clipboard.writeText(output.textContent).then(() => {
            const copyBtn = document.getElementById('copy-text-btn');
            if (copyBtn) {
                copyBtn.innerHTML = '✓ 已复制';
                setTimeout(() => {
                    copyBtn.innerHTML = '📋 复制';
                }, 2000);
            }
        }).catch(err => {
            alert('复制失败: ' + err.message);
        });
    }
}

function clearTextResult() {
    const output = document.getElementById('text-output');
    const input = document.getElementById('text-input');
    const copyBtn = document.getElementById('copy-text-btn');
    
    if (output) {
        output.innerHTML = `
            <div style="text-align: center; padding: 3rem;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📄</div>
                <p>生成的文本将显示在这里</p>
            </div>
        `;
    }
    if (input) {
        input.value = '';
    }
    if (copyBtn) {
        copyBtn.disabled = true;
    }
}

async function generateImage() {
    const promptInput = document.getElementById('image-prompt');
    if (!promptInput || !promptInput.value.trim()) {
        alert('请输入图像描述');
        return;
    }
    
    const output = document.getElementById('image-output');
    const style = document.getElementById('image-style').value || 'realistic';
    const count = parseInt(document.getElementById('image-count').value) || 1;
    
    if (output) {
        output.innerHTML = '<div style="text-align: center; padding: 2rem;"><span class="loading"></span><p style="margin-top: 1rem;">🎨 AI 正在生成图像...</p></div>';
    }
    
    const settings = getApiSettings();
    let html = '';
    
    try {
        if (settings.apiKey) {
            if (settings.apiType === 'stability') {
                for (let i = 0; i < count; i++) {
                    const imageData = await callStabilityWithKey(promptInput.value, settings.apiKey, style);
                    html += `<div style="position: relative; display: inline-block; width: 48%; margin: 0.5%;">
                        <img src="${imageData}" 
                             style="width: 100%; border-radius: 8px;" 
                             alt="生成的图像 ${i + 1}"/>
                    </div>`;
                }
            } else if (settings.apiType === 'replicate') {
                const replicateModel = 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b';
                const result = await callReplicateWithKey(replicateModel, {
                    prompt: promptInput.value,
                    num_outputs: count,
                    width: 1024,
                    height: 1024
                }, settings.apiKey);
                
                if (Array.isArray(result)) {
                    result.forEach((imageUrl, i) => {
                        html += `<div style="position: relative; display: inline-block; width: 48%; margin: 0.5%;">
                            <img src="${imageUrl}" 
                                 style="width: 100%; border-radius: 8px;" 
                                 alt="生成的图像 ${i + 1}"/>
                        </div>`;
                    });
                }
            }
        }
        
        if (!html) {
            const prompt = encodeURIComponent(promptInput.value);
            for (let i = 0; i < count; i++) {
                html += `<div style="position: relative; display: inline-block; width: 48%; margin: 0.5%;">
                    <img src="https://neeko-copilot.bytedance.net/api/text2image?prompt=${prompt}&seed=${Date.now() + i}&style=${style}" 
                         style="width: 100%; border-radius: 8px;" 
                         alt="生成的图像 ${i + 1}"/>
                </div>`;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        if (output) output.innerHTML = html;
    } catch (error) {
        if (output) {
            output.innerHTML = `<p style="color: var(--danger);">生成失败: ${error.message}</p>`;
        }
    }
}

async function generateAudio() {
    const promptInput = document.getElementById('audio-prompt');
    const style = document.getElementById('audio-style').value || 'ambient';
    const duration = document.getElementById('audio-duration').value || '30';
    const bpm = document.getElementById('audio-bpm').value || '100';
    
    const output = document.getElementById('audio-output');
    
    if (output) {
        output.innerHTML = '<div style="text-align: center; padding: 2rem;"><span class="loading"></span><p style="margin-top: 1rem;">🎵 AI 正在生成音频...</p></div>';
    }
    
    const styles = {
        ambient: '氛围音乐', classical: '古典音乐', electronic: '电子音乐',
        rock: '摇滚音乐', jazz: '爵士音乐', lofi: 'Lo-fi 嘻哈',
        cinematic: '电影配乐', nature: '自然音效'
    };
    
    const settings = getApiSettings();
    
    try {
        let audioUrl = '';
        
        if (settings.apiKey && settings.apiType === 'replicate') {
            const replicateModel = 'meta/musicgen:7be0f12c74a8ddb03b683343628dd57563bbf44ef565c2bdcc1ed210bd682fa1';
            const prompt = promptInput.value.trim() || `${styles[style] || style}音乐，${bpm} BPM`;
            const result = await callReplicateWithKey(replicateModel, {
                prompt: prompt,
                duration: parseInt(duration)
            }, settings.apiKey);
            
            if (Array.isArray(result) && result.length > 0) {
                audioUrl = result[0];
            }
        }
        
        if (!audioUrl) {
            audioUrl = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3';
            await new Promise(resolve => setTimeout(resolve, 1500));
        }
        
        if (output) {
            output.innerHTML = `
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎧</div>
                    ${promptInput && promptInput.value.trim() ? `<p style="margin-bottom: 0.5rem;"><strong>描述：</strong>${promptInput.value}</p>` : ''}
                    <p style="margin-bottom: 0.5rem;"><strong>风格：</strong>${styles[style] || style}</p>
                    <p style="margin-bottom: 0.5rem;"><strong>时长：</strong>${duration}秒</p>
                    <p style="margin-bottom: 1rem;"><strong>BPM：</strong>${bpm}</p>
                </div>
                <div style="width: 100%; margin-top: 1rem;">
                    <audio id="audio-player" controls style="width: 100%; max-width: 400px;">
                        <source src="${audioUrl}" type="audio/mp3">
                    
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                        <button class="btn btn-sm btn-secondary" onclick="downloadAudio('${audioUrl}')">⬇️ 下载</button>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        if (output) {
            output.innerHTML = `<p style="color: var(--danger);">生成失败: ${error.message}</p>`;
        }
    }
}

async function generateVideo() {
    const theme = document.getElementById('video-theme');
    const desc = document.getElementById('video-desc');
    
    if (!theme || !theme.value.trim()) {
        alert('请输入视频主题');
        return;
    }
    
    const output = document.getElementById('video-output');
    
    if (output) {
        output.innerHTML = '<div style="text-align: center; padding: 2rem;"><span class="loading"></span><p style="margin-top: 1rem;">🎬 AI 正在生成视频...</p></div>';
    }
    
    const settings = getApiSettings();
    
    try {
        let videoUrl = '';
        let videoGenerated = false;
        
        if (settings.apiKey && settings.apiType === 'replicate') {
            const replicateModel = 'anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351';
            const prompt = desc.value.trim() || theme.value;
            const result = await callReplicateWithKey(replicateModel, {
                prompt: prompt,
                num_frames: 24,
                num_inference_steps: 25,
                fps: 8
            }, settings.apiKey);
            
            if (Array.isArray(result) && result.length > 0) {
                videoUrl = result[0];
                videoGenerated = true;
            }
        } else {
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        if (output) {
            if (videoGenerated && videoUrl) {
                output.innerHTML = `
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🎥</div>
                        <p style="margin-bottom: 0.5rem;"><strong>主题：</strong>${theme.value}</p>
                        ${desc && desc.value.trim() ? `<p style="margin-bottom: 0.5rem;"><strong>描述：</strong>${desc.value}</p>` : ''}
                        <p style="margin-bottom: 1rem;"><strong>状态：</strong>视频生成完成</p>
                    </div>
                    <div style="width: 100%; margin-top: 1rem;">
                        <video id="video-player" controls style="width: 100%; max-height: 280px; border-radius: 8px;">
                            <source src="${videoUrl}" type="video/mp4">
                        </video>
                        <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                            <button class="btn btn-sm btn-secondary" onclick="document.getElementById('video-player').play()">▶️ 播放</button>
                            <button class="btn btn-sm btn-secondary" onclick="downloadVideo('${videoUrl}')">⬇️ 下载</button>
                        </div>
                    </div>
                `;
            } else {
                output.innerHTML = `
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🎥</div>
                        <p style="margin-bottom: 0.5rem;"><strong>主题：</strong>${theme.value}</p>
                        ${desc && desc.value.trim() ? `<p style="margin-bottom: 0.5rem;"><strong>描述：</strong>${desc.value}</p>` : ''}
                        <p style="margin-bottom: 1rem;"><strong>状态：</strong>视频生成完成</p>
                    </div>
                    <div style="width: 100%; margin-top: 1rem;">
                        <div style="width: 100%; max-height: 280px; border-radius: 8px; background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); display: flex; align-items: center; justify-content: center;">
                            <div style="text-align: center;">
                                <div style="font-size: 4rem; margin-bottom: 1rem;">🎬</div>
                                <p style="color: var(--text-secondary);">视频预览区域</p>
                                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">视频文件已生成</p>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                            <button class="btn btn-sm btn-secondary">▶️ 播放</button>
                            <button class="btn btn-sm btn-secondary">⬇️ 下载</button>
                        </div>
                    </div>
                `;
            }
        }
    } catch (error) {
        if (output) {
            output.innerHTML = `<p style="color: var(--danger);">生成失败: ${error.message}</p>`;
        }
    }
}

// === 工作流水线 ===
function createWorkflow() {
    alert('新建流水线功能即将开放！');
}

function loadWorkflow(type) {
    const workflows = {
        text: { name: '文本生成流水线', desc: '输入提示 → AI生成 → 内容优化 → 输出' },
        image: { name: '图像生成流水线', desc: '提示词 → 风格选择 → AI生成 → 后处理' },
        audio: { name: '音频生成流水线', desc: '文本转语音 → 音效合成 → 混音输出' },
        video: { name: '视频生成流水线', desc: '脚本生成 → 图像渲染 → 视频合成' },
        custom: { name: '自定义流水线', desc: '自由组合节点创建自定义流程' }
    };
    
    const workflow = workflows[type];
    if (workflow) {
        document.getElementById('workflow-name').textContent = workflow.name;
        document.getElementById('workflow-desc').textContent = workflow.desc;
        renderWorkflowNodes(type);
    }
}

function renderWorkflowNodes(type) {
    const nodes = {
        text: [{ id: 'input', label: '输入', icon: '📝' }, { id: 'gen', label: 'AI生成', icon: '✨' }, { id: 'optimize', label: '优化', icon: '⚡' }, { id: 'output', label: '输出', icon: '📄' }],
        image: [{ id: 'prompt', label: '提示词', icon: '💬' }, { id: 'style', label: '风格', icon: '🎨' }, { id: 'gen', label: '生成', icon: '🖼️' }, { id: 'post', label: '后处理', icon: '🔧' }],
        audio: [{ id: 'text', label: '文本', icon: '📝' }, { id: 'tts', label: '语音合成', icon: '🔊' }, { id: 'effect', label: '音效', icon: '🎵' }, { id: 'mix', label: '混音', icon: '🎧' }],
        video: [{ id: 'script', label: '脚本', icon: '📄' }, { id: 'render', label: '渲染', icon: '🎬' }, { id: 'edit', label: '剪辑', icon: '✂️' }, { id: 'export', label: '导出', icon: '📤' }],
        custom: [{ id: 'start', label: '开始', icon: '🚀' }, { id: 'node1', label: '节点1', icon: '🔹' }, { id: 'node2', label: '节点2', icon: '🔹' }, { id: 'end', label: '结束', icon: '🏁' }]
    };
    
    const container = document.getElementById('workflow-canvas');
    if (container && nodes[type]) {
        container.innerHTML = nodes[type].map((node, index) => `
            <div class="workflow-node" draggable="true" ondragstart="dragNode(event)">
                <div>${node.icon}</div>
                <div style="font-size: 0.85rem; margin-top: 0.25rem;">${node.label}</div>
                ${index < nodes[type].length - 1 ? '<div class="node-arrow">→</div>' : ''}
            </div>
        `).join('');
    }
}

function dragNode(event) {
    event.dataTransfer.setData('text', event.target.id);
}

function dropNode(event) {
    event.preventDefault();
    const data = event.dataTransfer.getData('text');
    const draggedElement = document.getElementById(data);
    if (draggedElement && event.target.classList.contains('workflow-canvas')) {
        event.target.appendChild(draggedElement);
    }
}

// === 文件管理 ===
function openUploadModal() {
    document.getElementById('upload-modal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('active');
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        const fileList = document.getElementById('upload-file-list');
        if (fileList) {
            fileList.innerHTML = Array.from(files).map(file => `
                <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-dark); border-radius: 4px; margin-bottom: 0.5rem;">
                    <span>${file.name}</span>
                    <span style="color: var(--text-secondary); font-size: 0.85rem;">${formatFileSize(file.size)}</span>
                </div>
            `).join('');
        }
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function uploadFiles() {
    const progress = document.getElementById('upload-progress');
    if (progress) {
        progress.style.width = '0%';
        let percent = 0;
        const interval = setInterval(() => {
            percent += Math.random() * 20;
            if (percent >= 100) {
                percent = 100;
                clearInterval(interval);
                setTimeout(() => {
                    closeModal('upload-modal');
                    alert('文件上传成功！');
                    loadFiles();
                }, 500);
            }
            progress.style.width = percent + '%';
        }, 300);
    }
}

function loadFiles() {
    const files = [
        { name: 'report.pdf', size: '2.4 MB', date: '2024-01-15', type: 'pdf' },
        { name: 'presentation.pptx', size: '15.6 MB', date: '2024-01-14', type: 'ppt' },
        { name: 'dataset.csv', size: '890 KB', date: '2024-01-13', type: 'csv' },
        { name: 'image_gallery.zip', size: '45.2 MB', date: '2024-01-12', type: 'zip' },
        { name: 'notes.txt', size: '12 KB', date: '2024-01-11', type: 'txt' }
    ];
    
    const tbody = document.querySelector('#file-table tbody');
    if (tbody) {
        tbody.innerHTML = files.map(file => `
            <tr>
                <td><span style="margin-right: 0.5rem;">${getFileIcon(file.type)}</span>${file.name}</td>
                <td>${file.size}</td>
                <td>${file.date}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" style="margin-right: 0.25rem;">⬇️ 下载</button>
                    <button class="btn btn-sm btn-danger">🗑️ 删除</button>
                </td>
            </tr>
        `).join('');
    }
}

function getFileIcon(type) {
    const icons = { pdf: '📄', ppt: '📊', csv: '📈', zip: '📦', txt: '📝', img: '🖼️', audio: '🎵', video: '🎬' };
    return icons[type] || '📁';
}

// === 硬件配置 ===
function selectTier(tier) {
    const tiers = {
        dev: { name: '开发版', cpu: '2核', memory: '4GB', gpu: '无', storage: '50GB', price: '免费' },
        small: { name: '小型', cpu: '4核', memory: '8GB', gpu: 'NVIDIA T4', storage: '100GB', price: '¥99/月' },
        medium: { name: '中型', cpu: '8核', memory: '16GB', gpu: 'NVIDIA A10G', storage: '200GB', price: '¥299/月' },
        large: { name: '大型', cpu: '16核', memory: '32GB', gpu: 'NVIDIA A100', storage: '500GB', price: '¥799/月' },
        enterprise: { name: '企业级', cpu: '32核', memory: '64GB', gpu: '2×NVIDIA A100', storage: '1TB', price: '¥1999/月' },
        cluster: { name: '集群', cpu: '64核+', memory: '128GB+', gpu: '4×NVIDIA H100', storage: '5TB+', price: '定制' }
    };
    
    const config = tiers[tier];
    if (config) {
        document.getElementById('tier-name').textContent = config.name;
        document.getElementById('tier-cpu').textContent = config.cpu;
        document.getElementById('tier-memory').textContent = config.memory;
        document.getElementById('tier-gpu').textContent = config.gpu;
        document.getElementById('tier-storage').textContent = config.storage;
        document.getElementById('tier-price').textContent = config.price;
    }
}

// === 任务管理 ===
function loadTasks() {
    const tasks = [
        { id: 'TASK-001', name: '模型训练 - ResNet50', status: 'running', progress: 45, type: 'training', submitted: '2024-01-15 09:30', eta: '预计 2小时' },
        { id: 'TASK-002', name: '数据预处理', status: 'success', progress: 100, type: 'data', submitted: '2024-01-15 08:00', eta: '已完成' },
        { id: 'TASK-003', name: '图片生成批量任务', status: 'pending', progress: 0, type: 'generation', submitted: '2024-01-15 10:00', eta: '等待中' },
        { id: 'TASK-004', name: '音频合成任务', status: 'error', progress: 23, type: 'generation', submitted: '2024-01-14 16:45', eta: '失败' },
        { id: 'TASK-005', name: '视频渲染', status: 'running', progress: 78, type: 'rendering', submitted: '2024-01-15 07:15', eta: '预计 30分钟' }
    ];
    
    const tbody = document.querySelector('#task-table tbody');
    if (tbody) {
        tbody.innerHTML = tasks.map(task => `
            <tr>
                <td>${task.id}</td>
                <td>${task.name}</td>
                <td><span class="status-badge status-${task.status}">${getStatusText(task.status)}</span></td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill ${task.status === 'success' ? 'memory' : task.status === 'running' ? 'cpu' : 'gpu'}" style="width: ${task.progress}%"></div>
                    </div>
                </td>
                <td>${task.submitted}</td>
                <td>${task.eta}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="viewTask('${task.id}')" style="margin-right: 0.25rem;">👁️ 查看</button>
                    ${task.status === 'running' ? `<button class="btn btn-sm btn-danger" onclick="stopTask('${task.id}')">⏹️ 停止</button>` : ''}
                </td>
            </tr>
        `).join('');
    }
}

function viewTask(taskId) {
    alert(`查看任务详情: ${taskId}\n\n功能开发中...`);
}

function stopTask(taskId) {
    if (confirm(`确定要停止任务 ${taskId} 吗？`)) {
        alert(`任务 ${taskId} 已停止`);
        loadTasks();
    }
}

// === 提示词管理 ===
function updatePreview() {
    const title = document.getElementById('prompt-title').value || '未命名提示词';
    const content = document.getElementById('prompt-content').value || '请输入提示词内容...';
    
    document.getElementById('prompt-preview-title').textContent = title;
    document.getElementById('prompt-preview-content').textContent = content;
}

function savePrompt() {
    const title = document.getElementById('prompt-title');
    const content = document.getElementById('prompt-content');
    
    if (!title.value.trim()) {
        alert('请输入提示词名称');
        return;
    }
    if (!content.value.trim()) {
        alert('请输入提示词内容');
        return;
    }
    
    alert(`提示词 "${title.value}" 已保存！`);
    loadPrompts();
}

function loadPrompts() {
    const prompts = [
        { id: 1, name: '产品描述生成器', category: '营销', updated: '2024-01-15' },
        { id: 2, name: '代码注释生成器', category: '开发', updated: '2024-01-14' },
        { id: 3, name: '创意写作助手', category: '写作', updated: '2024-01-13' },
        { id: 4, name: 'SEO标题生成器', category: '营销', updated: '2024-01-12' },
        { id: 5, name: '邮件回复模板', category: '办公', updated: '2024-01-11' }
    ];
    
    const list = document.getElementById('prompt-list');
    if (list) {
        list.innerHTML = prompts.map(prompt => `
            <div class="prompt-item" onclick="loadPrompt(${prompt.id})">
                <div>
                    <div style="font-weight: 500;">${prompt.name}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">${prompt.category} · ${prompt.updated}</div>
                </div>
                <div style="color: var(--text-muted);">→</div>
            </div>
        `).join('');
    }
}

function loadPrompt(id) {
    const prompts = {
        1: { title: '产品描述生成器', content: '请帮我为以下产品写一段吸引人的描述：\n\n产品名称：[输入产品名称]\n产品特点：[输入产品特点]\n目标受众：[输入目标受众]\n\n请生成一段专业、有吸引力的产品描述。' },
        2: { title: '代码注释生成器', content: '请为以下代码添加详细的注释：\n\n```\n[粘贴代码]\n```\n\n请解释代码的功能、关键逻辑和设计思路。' },
        3: { title: '创意写作助手', content: '请以"[主题]"为主题，写一篇创意短文。要求：\n- 富有想象力\n- 语言生动\n- 结构完整\n- 字数在300-500字之间' },
        4: { title: 'SEO标题生成器', content: '请为以下内容生成5个SEO友好的标题：\n\n内容主题：[输入主题]\n关键词：[输入关键词]\n\n要求：\n- 包含主要关键词\n- 吸引点击\n- 长度适中' },
        5: { title: '邮件回复模板', content: '请帮我回复以下邮件：\n\n[粘贴邮件内容]\n\n要求：\n- 专业礼貌\n- 清晰表达\n- 适当简洁' }
    };
    
    const prompt = prompts[id];
    if (prompt) {
        document.getElementById('prompt-title').value = prompt.title;
        document.getElementById('prompt-content').value = prompt.content;
        updatePreview();
    }
}

// === 技能市场 ===
function loadMarket() {
    const skills = [
        { id: 1, name: '智能文案助手', category: '写作', installs: 12580, rating: 4.8, desc: '基于AI的智能文案生成工具' },
        { id: 2, name: '图像风格转换', category: '图像', installs: 8920, rating: 4.6, desc: '将照片转换为不同艺术风格' },
        { id: 3, name: '语音合成引擎', category: '音频', installs: 6750, rating: 4.9, desc: '高质量多语言语音合成' },
        { id: 4, name: '数据分析师', category: '数据', installs: 4520, rating: 4.7, desc: '自动化数据分析和可视化' },
        { id: 5, name: '代码审查助手', category: '开发', installs: 3890, rating: 4.5, desc: 'AI驱动的代码审查工具' },
        { id: 6, name: '视频剪辑AI', category: '视频', installs: 5230, rating: 4.4, desc: '智能视频剪辑和编辑' },
        { id: 7, name: '翻译大师', category: '语言', installs: 15680, rating: 4.8, desc: '支持50+语言的智能翻译' },
        { id: 8, name: '创意灵感生成器', category: '创意', installs: 7820, rating: 4.6, desc: '激发创意灵感的AI工具' }
    ];
    
    const container = document.getElementById('market-skills');
    if (container) {
        container.innerHTML = skills.map(skill => `
            <div class="skill-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">${getSkillIcon(skill.category)}</div>
                <div class="skill-name">${skill.name}</div>
                <div class="skill-desc">${skill.desc}</div>
                <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">⭐ ${skill.rating} · ${skill.installs.toLocaleString()} 安装</span>
                    <button class="btn btn-sm btn-primary" onclick="installSkill(${skill.id})">➕ 安装</button>
                </div>
            </div>
        `).join('');
    }
}

function getSkillIcon(category) {
    const icons = { 写作: '✍️', 图像: '🖼️', 音频: '🎵', 数据: '📊', 开发: '💻', 视频: '🎬', 语言: '🌍', 创意: '💡' };
    return icons[category] || '✨';
}

function installSkill(id) {
    const button = event.target;
    button.innerHTML = '<span class="loading"></span> 安装中...';
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = '✓ 已安装';
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
    }, 1500);
}

// === 技能中心 ===
function loadSkills() {
    const skills = [
        { id: 1, name: '智能文案助手', status: 'enabled', category: '写作', updated: '2024-01-15' },
        { id: 2, name: '图像风格转换', status: 'enabled', category: '图像', updated: '2024-01-14' },
        { id: 3, name: '语音合成引擎', status: 'disabled', category: '音频', updated: '2024-01-13' },
        { id: 4, name: '数据分析师', status: 'enabled', category: '数据', updated: '2024-01-12' },
        { id: 5, name: '代码审查助手', status: 'enabled', category: '开发', updated: '2024-01-11' },
        { id: 6, name: '视频剪辑AI', status: 'disabled', category: '视频', updated: '2024-01-10' },
        { id: 7, name: '翻译大师', status: 'enabled', category: '语言', updated: '2024-01-09' },
        { id: 8, name: '创意灵感生成器', status: 'enabled', category: '创意', updated: '2024-01-08' }
    ];
    
    const container = document.getElementById('installed-skills');
    if (container) {
        container.innerHTML = skills.map(skill => `
            <div class="skill-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">${getSkillIcon(skill.category)}</div>
                <div class="skill-name">${skill.name}</div>
                <div class="skill-desc">${skill.category} · 更新于 ${skill.updated}</div>
                <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <span class="status-badge status-${skill.status === 'enabled' ? 'success' : 'pending'}">${skill.status === 'enabled' ? '已启用' : '已禁用'}</span>
                    <div style="display: flex; gap: 0.25rem;">
                        <button class="btn btn-sm btn-secondary" onclick="configureSkill(${skill.id})">⚙️ 配置</button>
                        <button class="btn btn-sm ${skill.status === 'enabled' ? 'btn-warning' : 'btn-success'}" onclick="toggleSkill(${skill.id})">
                            ${skill.status === 'enabled' ? '⏸️ 禁用' : '▶️ 启用'}
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

function configureSkill(id) {
    alert(`配置技能 ID: ${id}\n\n功能开发中...`);
}

function toggleSkill(id) {
    const button = event.target;
    if (button.textContent.includes('禁用')) {
        button.textContent = '▶️ 启用';
        button.classList.remove('btn-warning');
        button.classList.add('btn-success');
    } else {
        button.textContent = '⏸️ 禁用';
        button.classList.remove('btn-success');
        button.classList.add('btn-warning');
    }
}

// === 系统设置 ===
function saveSystemSettings() {
    const settings = {
        theme: document.getElementById('system-theme').value,
        language: document.getElementById('system-language').value,
        notifications: document.getElementById('system-notifications').checked,
        autoSave: document.getElementById('system-autosave').checked
    };
    
    alert(`系统设置已保存！\n\n主题: ${settings.theme}\n语言: ${settings.language}\n通知: ${settings.notifications ? '开启' : '关闭'}\n自动保存: ${settings.autoSave ? '开启' : '关闭'}`);
}

// === 系统信息刷新 ===
function refreshSystemInfo() {
    updateSystemStats();
    loadRecentTasks();
    loadTasks();
}

// === 初始化 ===
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadMarket();
    loadSkills();
    loadFiles();
    loadTasks();
    loadPrompts();
    loadApiSettings();
    
    const bpmSlider = document.getElementById('audio-bpm');
    const bpmValue = document.getElementById('bpm-value');
    if (bpmSlider && bpmValue) {
        bpmSlider.addEventListener('input', function() {
            bpmValue.textContent = this.value;
        });
    }
});



function getApiSettings() {
    const saved = localStorage.getItem('hydraflow_api_settings');
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch (e) {
            console.error('解析API设置失败:', e);
        }
    }
    return {};
}

function detectApiType(apiKey) {
    if (!apiKey) return null;
    
    if (apiKey.startsWith('sk-')) {
        if (apiKey.startsWith('sk-ant-')) {
            return { type: 'anthropic', name: 'Anthropic', icon: '🧠' };
        }
        return { type: 'openai', name: 'OpenAI', icon: '🤖' };
    } else if (apiKey.startsWith('r8_')) {
        return { type: 'replicate', name: 'Replicate', icon: '🎬' };
    } else if (apiKey.startsWith('hf_')) {
        return { type: 'huggingface', name: 'Hugging Face', icon: '🤗' };
    } else if (apiKey.startsWith('AIza')) {
        return { type: 'google', name: 'Google', icon: '🔍' };
    } else if (apiKey.startsWith('pk_')) {
        return { type: 'stability', name: 'Stability AI', icon: '🎨' };
    }
    return { type: 'custom', name: '自定义', icon: '⚙️' };
}

async function analyzeAndConnect() {
    const apiKey = document.getElementById('api-key').value;
    const apiUrl = document.getElementById('api-url').value;
    
    if (!apiKey.trim()) {
        alert('请输入API密钥');
        return;
    }
    
    const analysisResult = document.getElementById('api-analysis-result');
    const analysisIcon = document.getElementById('analysis-icon');
    const analysisTitle = document.getElementById('analysis-title');
    const analysisDesc = document.getElementById('analysis-desc');
    const analysisModels = document.getElementById('analysis-models');
    
    analysisResult.style.display = 'block';
    analysisIcon.textContent = '🔍';
    analysisTitle.textContent = '正在分析...';
    analysisDesc.textContent = '检测API类型并获取可用模型列表';
    analysisModels.innerHTML = '';
    
    const detectedType = detectApiType(apiKey);
    analysisIcon.textContent = detectedType.icon;
    analysisTitle.textContent = `已识别: ${detectedType.name}`;
    analysisDesc.textContent = `API类型: ${detectedType.type}`;
    
    try {
        let models = [];
        
        if (detectedType.type === 'openai' || detectedType.type === 'custom') {
            models = await fetchOpenAIModels(apiKey, apiUrl);
        } else if (detectedType.type === 'anthropic') {
            models = getAnthropicModels();
        } else if (detectedType.type === 'replicate') {
            models = await fetchReplicateModels(apiKey);
        } else if (detectedType.type === 'huggingface') {
            models = getHuggingFaceModels();
        } else if (detectedType.type === 'google') {
            models = await fetchGoogleModels(apiKey);
        } else if (detectedType.type === 'stability') {
            models = getStabilityModels();
        }
        
        if (models.length > 0) {
            displayModels(models, detectedType);
            saveApiConnection(apiKey, apiUrl, detectedType, models[0].id);
            showConnectionStatus('success', `✅ 连接成功！已识别 ${models.length} 个可用模型`);
        } else {
            showConnectionStatus('error', '❌ 未能获取模型列表，请检查API密钥和URL是否正确');
        }
    } catch (error) {
        showConnectionStatus('error', `❌ 连接失败: ${error.message}`);
        console.error('API连接错误:', error);
    }
}

async function fetchOpenAIModels(apiKey, baseUrl) {
    const response = await fetch(`${baseUrl}/models`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${apiKey}`
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.data && Array.isArray(data.data)) {
        return data.data.map(m => ({
            id: m.id,
            name: m.id,
            description: m.description || 'OpenAI模型'
        }));
    }
    return [];
}

function getAnthropicModels() {
    return [
        { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', description: '最强大的模型，适合复杂任务' },
        { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet', description: '平衡性能和速度' },
        { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', description: '最快的模型' },
        { id: 'claude-2.1', name: 'Claude 2.1', description: '支持200K上下文' }
    ];
}

async function fetchReplicateModels(apiKey) {
    const response = await fetch('https://api.replicate.com/v1/models', {
        method: 'GET',
        headers: {
            'Authorization': `Token ${apiKey}`
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.results && Array.isArray(data.results)) {
        return data.results.slice(0, 10).map(m => ({
            id: m.full_name,
            name: m.name,
            description: m.description || 'Replicate模型'
        }));
    }
    return [];
}

function getHuggingFaceModels() {
    return [
        { id: 'gpt2', name: 'GPT-2', description: 'OpenAI的GPT-2模型' },
        { id: 'bert-base-uncased', name: 'BERT Base', description: 'Google的BERT模型' },
        { id: 'meta-llama/Llama-2-7b-chat-hf', name: 'Llama 2 7B', description: 'Meta的开源大模型' },
        { id: 'stable-diffusion-v1-5', name: 'Stable Diffusion', description: '图像生成模型' }
    ];
}

async function fetchGoogleModels(apiKey) {
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
    
    if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.models && Array.isArray(data.models)) {
        return data.models.map(m => ({
            id: m.name.replace('models/', ''),
            name: m.displayName,
            description: m.description || 'Google模型'
        }));
    }
    return [];
}

function getStabilityModels() {
    return [
        { id: 'stable-diffusion-xl-1024-v1-0', name: 'Stable Diffusion XL', description: '高质量图像生成' },
        { id: 'stable-diffusion-v1-5', name: 'Stable Diffusion 1.5', description: '经典图像生成模型' },
        { id: 'sdxl-turbo', name: 'SDXL Turbo', description: '快速图像生成' }
    ];
}

function displayModels(models, apiType) {
    const analysisModels = document.getElementById('analysis-models');
    analysisModels.innerHTML = `
        <div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-secondary);">可用模型:</div>
        <div style="max-height: 300px; overflow-y: auto;">
            ${models.map((model, index) => `
                <div style="padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; background: var(--bg-primary); cursor: pointer; transition: all 0.2s;"
                     onclick="selectModel('${model.id}', '${model.name}', '${apiType.type}')"
                     id="model-${index}">
                    <div style="font-weight: 500;">${model.name}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">${model.id}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">${model.description}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function selectModel(modelId, modelName, apiType) {
    const apiKey = document.getElementById('api-key').value;
    const apiUrl = document.getElementById('api-url').value;
    
    saveApiConnection(apiKey, apiUrl, { type: apiType }, modelId);
    showConnectionStatus('success', `✅ 已选择模型: ${modelName}`);
    
    document.querySelectorAll('[id^="model-"]').forEach(el => {
        el.style.background = 'var(--bg-primary)';
    });
    event.target.style.background = 'var(--accent)';
}

function saveApiConnection(apiKey, apiUrl, apiType, defaultModel) {
    const settings = {
        apiKey: apiKey,
        apiUrl: apiUrl,
        apiType: apiType.type,
        apiTypeName: apiType.name,
        defaultModel: defaultModel
    };
    localStorage.setItem('hydraflow_api_settings', JSON.stringify(settings));
}

function showConnectionStatus(status, message) {
    const connectionStatus = document.getElementById('connection-status');
    const statusMessage = document.getElementById('status-message');
    
    connectionStatus.style.display = 'block';
    connectionStatus.style.background = status === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)';
    connectionStatus.style.border = status === 'success' ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)';
    
    statusMessage.innerHTML = `<p style="margin: 0;">${message}</p>`;
}

function saveApiSettings() {
    const apiKey = document.getElementById('api-key').value;
    const apiUrl = document.getElementById('api-url').value;
    const apiType = detectApiType(apiKey);
    
    const settings = {
        apiKey: apiKey,
        apiUrl: apiUrl,
        apiType: apiType.type,
        apiTypeName: apiType.name
    };
    
    localStorage.setItem('hydraflow_api_settings', JSON.stringify(settings));
    alert('API设置已保存！');
}

function loadApiSettings() {
    const settings = getApiSettings();
    
    if (settings.apiKey) {
        document.getElementById('api-key').value = settings.apiKey;
    }
    if (settings.apiUrl) {
        document.getElementById('api-url').value = settings.apiUrl;
    }
    
    if (settings.apiKey && settings.apiType) {
        const apiType = detectApiType(settings.apiKey);
        const analysisResult = document.getElementById('api-analysis-result');
        const analysisIcon = document.getElementById('analysis-icon');
        const analysisTitle = document.getElementById('analysis-title');
        const analysisDesc = document.getElementById('analysis-desc');
        
        if (analysisResult) {
            analysisResult.style.display = 'block';
            analysisIcon.textContent = apiType.icon;
            analysisTitle.textContent = `已识别: ${apiType.name}`;
            analysisDesc.textContent = `API类型: ${apiType.type} · 默认模型: ${settings.defaultModel || '未选择'}`;
        }
        
        showConnectionStatus('success', `✅ 已加载API设置 · ${apiType.name}`);
    }
}

function clearApiSettings() {
    localStorage.removeItem('hydraflow_api_settings');
    document.getElementById('api-key').value = '';
    document.getElementById('api-url').value = 'https://api.openai.com/v1';
    document.getElementById('api-analysis-result').style.display = 'none';
    document.getElementById('connection-status').style.display = 'none';
    alert('API设置已清除！');
}

// === 真实API调用函数（支持新格式）===
async function callOpenAIWithKey(prompt, apiKey, baseUrl, model = 'gpt-4') {
    const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: prompt }],
            max_tokens: 1000
        })
    });
    
    if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
    }
    
    const data = await response.json();
    return data.choices[0].message.content;
}

async function callAnthropicWithKey(prompt, apiKey) {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 1000,
            messages: [{ role: 'user', content: prompt }]
        })
    });
    
    if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
    }
    
    const data = await response.json();
    return data.content[0].text;
}

async function callReplicateWithKey(model, input, apiKey) {
    const response = await fetch('https://api.replicate.com/v1/predictions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${apiKey}`
        },
        body: JSON.stringify({
            version: model,
            input: input
        })
    });
    
    if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
    }
    
    let prediction = await response.json();
    
    while (prediction.status !== 'succeeded' && prediction.status !== 'failed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const statusResponse = await fetch(`https://api.replicate.com/v1/predictions/${prediction.id}`, {
            headers: { 'Authorization': `Token ${apiKey}` }
        });
        prediction = await statusResponse.json();
    }
    
    if (prediction.status === 'failed') {
        throw new Error('Replicate生成失败');
    }
    
    return prediction.output;
}

async function callStabilityWithKey(prompt, apiKey, style = 'realistic') {
    const response = await fetch('https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            text_prompts: [{ text: prompt }],
            cfg_scale: 7,
            height: 1024,
            width: 1024,
            steps: 30,
            samples: 1
        })
    });
    
    if (!response.ok) {
        throw new Error(`Stability AI错误: ${response.status}`);
    }
    
    const data = await response.json();
    return `data:image/png;base64,${data.artifacts[0].base64}`;
}

// === 下载功能 ===
function downloadAudio(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = `audio_${Date.now()}.mp3`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadVideo(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = `video_${Date.now()}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function testOpenAI(apiKey, baseUrl) {
    updateApiStatus('openai', 'testing');
    
    try {
        const response = await fetch(`${baseUrl}/models`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        if (response.ok) {
            updateApiStatus('openai', 'success');
        } else {
            updateApiStatus('openai', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('openai', 'error', '连接失败');
    }
}

async function testAnthropic(apiKey) {
    updateApiStatus('anthropic', 'testing');
    
    try {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'x-api-key': apiKey,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            body: JSON.stringify({
                model: 'claude-3-haiku-20240307',
                max_tokens: 10,
                messages: [{ role: 'user', content: 'Hi' }]
            })
        });
        
        if (response.ok) {
            updateApiStatus('anthropic', 'success');
        } else {
            updateApiStatus('anthropic', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('anthropic', 'error', '连接失败');
    }
}

async function testGoogle(apiKey) {
    updateApiStatus('google', 'testing');
    
    try {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
        
        if (response.ok) {
            updateApiStatus('google', 'success');
        } else {
            updateApiStatus('google', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('google', 'error', '连接失败');
    }
}

async function testStability(apiKey) {
    updateApiStatus('stability', 'testing');
    
    try {
        const response = await fetch('https://api.stability.ai/v1/user/account', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        if (response.ok) {
            updateApiStatus('stability', 'success');
        } else {
            updateApiStatus('stability', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('stability', 'error', '连接失败');
    }
}

async function testReplicate(apiKey) {
    updateApiStatus('replicate', 'testing');
    
    try {
        const response = await fetch('https://api.replicate.com/v1/collections', {
            method: 'GET',
            headers: {
                'Authorization': `Token ${apiKey}`
            }
        });
        
        if (response.ok) {
            updateApiStatus('replicate', 'success');
        } else {
            updateApiStatus('replicate', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('replicate', 'error', '连接失败');
    }
}

async function testHuggingFace(apiKey) {
    updateApiStatus('huggingface', 'testing');
    
    try {
        const response = await fetch('https://huggingface.co/api/whoami', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        if (response.ok) {
            updateApiStatus('huggingface', 'success');
        } else {
            updateApiStatus('huggingface', 'error', '认证失败');
        }
    } catch (error) {
        updateApiStatus('huggingface', 'error', '连接失败');
    }
}

function updateApiStatus(provider, status, message) {
    const element = document.getElementById(`status-${provider}`);
    if (!element) return;
    
    const badge = element.querySelector('.status-badge');
    if (!badge) return;
    
    badge.className = 'status-badge';
    
    switch (status) {
        case 'testing':
            badge.classList.add('status-running');
            badge.textContent = '测试中...';
            break;
        case 'success':
            badge.classList.add('status-success');
            badge.textContent = '✓ 连接成功';
            break;
        case 'error':
            badge.classList.add('status-error');
            badge.textContent = message || '✗ 连接失败';
            break;
        default:
            badge.classList.add('status-pending');
            badge.textContent = '未测试';
    }
}

function resetApiStatus() {
    const providers = ['openai', 'anthropic', 'google', 'stability', 'replicate', 'huggingface'];
    providers.forEach(provider => {
        updateApiStatus(provider, 'pending');
    });
}

// === 真实API调用函数 ===
async function callOpenAI(prompt, model = 'gpt-4') {
    const settings = getApiSettings();
    if (!settings.openai || !settings.openai.key) {
        throw new Error('OpenAI API Key未配置');
    }
    
    const response = await fetch(`${settings.openai.url}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${settings.openai.key}`
        },
        body: JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: prompt }],
            max_tokens: 1000
        })
    });
    
    if (!response.ok) {
        throw new Error(`OpenAI API错误: ${response.status}`);
    }
    
    const data = await response.json();
    return data.choices[0].message.content;
}

async function callAnthropic(prompt, model = 'claude-3-haiku-20240307') {
    const settings = getApiSettings();
    if (!settings.anthropic || !settings.anthropic.key) {
        throw new Error('Anthropic API Key未配置');
    }
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
            'x-api-key': settings.anthropic.key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        body: JSON.stringify({
            model: model,
            max_tokens: 1000,
            messages: [{ role: 'user', content: prompt }]
        })
    });
    
    if (!response.ok) {
        throw new Error(`Anthropic API错误: ${response.status}`);
    }
    
    const data = await response.json();
    return data.content[0].text;
}

async function callStabilityAI(prompt, style = 'realistic') {
    const settings = getApiSettings();
    if (!settings.stability || !settings.stability.key) {
        throw new Error('Stability AI Key未配置');
    }
    
    const response = await fetch('https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${settings.stability.key}`,
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            text_prompts: [{ text: prompt }],
            cfg_scale: 7,
            height: 1024,
            width: 1024,
            steps: 30,
            samples: 1
        })
    });
    
    if (!response.ok) {
        throw new Error(`Stability AI错误: ${response.status}`);
    }
    
    const data = await response.json();
    return `data:image/png;base64,${data.artifacts[0].base64}`;
}

async function callReplicate(model, input) {
    const settings = getApiSettings();
    if (!settings.replicate || !settings.replicate.key) {
        throw new Error('Replicate API Token未配置');
    }
    
    const response = await fetch(`https://api.replicate.com/v1/predictions`, {
        method: 'POST',
        headers: {
            'Authorization': `Token ${settings.replicate.key}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            version: model,
            input: input
        })
    });
    
    if (!response.ok) {
        throw new Error(`Replicate API错误: ${response.status}`);
    }
    
    const prediction = await response.json();
    
    while (prediction.status !== 'succeeded' && prediction.status !== 'failed') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const statusResponse = await fetch(`https://api.replicate.com/v1/predictions/${prediction.id}`, {
            headers: {
                'Authorization': `Token ${settings.replicate.key}`
            }
        });
        
        prediction.status = (await statusResponse.json()).status;
    }
    
    if (prediction.status === 'failed') {
        throw new Error('Replicate生成失败');
    }
    
    return prediction.output;
}
