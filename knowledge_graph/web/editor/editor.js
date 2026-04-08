/**
 * 知识库编辑器 JavaScript
 * 实现表单处理、YAML 生成和 API 通信
 */

// 全局状态
let currentTags = [];
let isEditing = false;
let currentImportMode = 'quick'; // 'quick' or 'deep'
let deepImportData = null; // 存储深度导入的数据

// DOM 元素
const form = document.getElementById('editorForm');
const yamlPreview = document.getElementById('yamlPreview');
const tagInput = document.getElementById('tagInput');
const tagsInput = document.getElementById('tagsInput');
const statusText = document.getElementById('statusText');
const statusDot = document.getElementById('statusDot');
const toast = document.getElementById('toast');
const loadingOverlay = document.getElementById('loadingOverlay');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadExistingEntities();
    setupEventListeners();
    setupUploadHandlers();
    updatePreview();
});

// 设置事件监听
function setupEventListeners() {
    // 表单字段变化时更新预览
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', updatePreview);
    });
    
    // 标签输入
    tagInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag(tagInput.value.trim());
            tagInput.value = '';
        }
    });
    
    // 表单提交
    form.addEventListener('submit', handleSubmit);
}

// 加载现有实体列表
async function loadExistingEntities() {
    try {
        const response = await fetch('http://localhost:8000/stats');
        const data = await response.json();
        
        // 获取所有实体
        const entitiesResponse = await fetch('http://localhost:8000/search?q=*&k=100');
        const entities = await entitiesResponse.json();
        
        const list = document.getElementById('existingList');
        list.innerHTML = '';
        
        // 按类型分组
        const byType = {};
        entities.results?.forEach(entity => {
            const type = entity.entity_type || 'unknown';
            if (!byType[type]) byType[type] = [];
            byType[type].push(entity);
        });
        
        // 渲染列表
        Object.keys(byType).sort().forEach(type => {
            byType[type].forEach(entity => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span class="icon">${getTypeIcon(type)}</span>
                    <span>${entity.name}</span>
                    <span class="type-badge">${type}</span>
                `;
                li.onclick = () => loadEntity(entity.id);
                list.appendChild(li);
            });
        });
        
    } catch (error) {
        console.error('加载实体列表失败:', error);
        showStatus('无法加载实体列表', 'error');
    }
}

// 获取类型图标
function getTypeIcon(type) {
    const icons = {
        'assay': '🧪',
        'tool': '🔧',
        'step': '📋',
        'concept': '💡',
        'stage': '📊',
        'issue': '⚠️',
        'resource': '📚'
    };
    return icons[type] || '📄';
}

// 添加标签
function addTag(tag) {
    if (!tag || currentTags.includes(tag)) return;
    
    currentTags.push(tag);
    renderTags();
    updatePreview();
}

// 移除标签
function removeTag(tag) {
    currentTags = currentTags.filter(t => t !== tag);
    renderTags();
    updatePreview();
}

// 渲染标签
function renderTags() {
    // 清除现有标签（保留输入框）
    const existingTags = tagsInput.querySelectorAll('.tag');
    existingTags.forEach(tag => tag.remove());
    
    // 添加标签
    currentTags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag';
        tagEl.innerHTML = `
            ${tag}
            <button onclick="removeTag('${tag}')">×</button>
        `;
        tagsInput.insertBefore(tagEl, tagInput);
    });
}

// 生成 YAML
function generateYAML() {
    const id = document.getElementById('entityId').value.trim();
    const name = document.getElementById('entityName').value.trim();
    const type = document.getElementById('entityType').value;
    const difficulty = document.getElementById('difficulty').value;
    const description = document.getElementById('description').value.trim();
    const detailedExplanation = document.getElementById('detailedExplanation').value.trim();
    
    if (!id || !name || !type || !description) {
        return '# 请填写必填字段...';
    }
    
    let yaml = `# ${name}\n`;
    yaml += `id: ${id}\n`;
    yaml += `name: ${name}\n`;
    yaml += `type: ${type.slice(0, -1)}\n`; // 去掉复数 s
    yaml += `description: >\n`;
    yaml += `  ${description.replace(/\n/g, '\n  ')}\n`;
    yaml += `difficulty: ${difficulty}\n`;
    
    if (currentTags.length > 0) {
        yaml += `tags:\n`;
        currentTags.forEach(tag => {
            yaml += `  - ${tag}\n`;
        });
    }
    
    if (detailedExplanation) {
        yaml += `\ndetailed_explanation: >\n`;
        yaml += `  ${detailedExplanation.replace(/\n/g, '\n  ')}\n`;
    }
    
    return yaml;
}

// 更新预览
function updatePreview() {
    yamlPreview.textContent = generateYAML();
}

// 处理表单提交
async function handleSubmit(e) {
    e.preventDefault();
    
    const yaml = generateYAML();
    if (yaml.startsWith('# 请填写')) {
        showToast('请填写所有必填字段', 'error');
        return;
    }
    
    showLoading(true);
    showStatus('正在保存...', 'saving');
    
    try {
        // 发送到 API
        const response = await fetch('http://localhost:8000/api/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                yaml: yaml,
                entityType: document.getElementById('entityType').value,
                entityId: document.getElementById('entityId').value.trim()
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('✅ 保存成功！知识库已更新', 'success');
            showStatus('保存成功', 'success');
            
            // 刷新实体列表
            await loadExistingEntities();
            
            // 清空表单（如果是新建）
            if (!isEditing) {
                resetForm();
            }
        } else {
            throw new Error(result.error || '保存失败');
        }
        
    } catch (error) {
        console.error('保存失败:', error);
        showToast(`❌ 保存失败: ${error.message}`, 'error');
        showStatus('保存失败', 'error');
    } finally {
        showLoading(false);
    }
}

// 加载实体（编辑模式）
async function loadEntity(entityId) {
    try {
        const response = await fetch(`http://localhost:8000/entity?id=${entityId}`);
        const data = await response.json();
        
        if (!data) {
            showToast('实体不存在', 'error');
            return;
        }
        
        // 填充表单
        document.getElementById('entityId').value = data.id;
        document.getElementById('entityName').value = data.name || data.metadata?.name || '';
        document.getElementById('entityType').value = data.entity_type + 's';
        document.getElementById('difficulty').value = data.difficulty || 'intermediate';
        document.getElementById('description').value = data.metadata?.original_data?.description || '';
        document.getElementById('detailedExplanation').value = data.metadata?.original_data?.detailed_explanation || '';
        
        // 填充标签
        currentTags = data.tags || data.metadata?.tags || [];
        renderTags();
        
        // 更新状态
        isEditing = true;
        updatePreview();
        showStatus(`正在编辑: ${data.name}`, 'success');
        
    } catch (error) {
        console.error('加载实体失败:', error);
        showToast('加载实体失败', 'error');
    }
}

// 重置表单
function resetForm() {
    form.reset();
    currentTags = [];
    renderTags();
    isEditing = false;
    updatePreview();
    showStatus('准备就绪', 'success');
}

// 仅预览
function previewOnly() {
    updatePreview();
    showToast('预览已更新', 'success');
}

// 显示状态
function showStatus(text, type) {
    statusText.textContent = text;
    statusDot.className = 'status-dot';
    if (type) {
        statusDot.classList.add(type);
    }
}

// 显示 Toast
function showToast(message, type) {
    const icon = type === 'success' ? '✓' : '✗';
    document.getElementById('toastIcon').textContent = icon;
    document.getElementById('toastMessage').textContent = message;
    
    toast.className = 'toast show ' + type;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 显示/隐藏加载
function showLoading(show) {
    loadingOverlay.classList.toggle('show', show);
}

// 监听窗口关闭提醒
window.addEventListener('beforeunload', (e) => {
    if (document.getElementById('entityId').value) {
        e.preventDefault();
        e.returnValue = '有未保存的更改，确定要离开吗？';
    }
});

// ========== 文件上传功能 ==========

function setupUploadHandlers() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('fileInput');
    
    // 导入模式切换
    document.querySelectorAll('.import-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.import-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentImportMode = tab.dataset.mode;
            updateImportDescription();
        });
    });
    
    // 点击上传
    dropzone.addEventListener('click', () => fileInput.click());
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    // 拖拽处理
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (isValidFileType(file)) {
                handleFileUpload(file);
            } else {
                showToast('❌ 不支持的文件格式，请上传 PDF、TXT 或 Markdown 文件', 'error');
            }
        }
    });
}

function isValidFileType(file) {
    const validTypes = [
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/octet-stream'
    ];
    const validExtensions = ['.pdf', '.txt', '.md', '.docx'];
    
    const isValidMime = validTypes.includes(file.type);
    const isValidExt = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
    );
    
    return isValidMime || isValidExt;
}

function updateImportDescription() {
    const desc = document.getElementById('importDescription');
    const hint = document.getElementById('uploadHint');
    
    if (currentImportMode === 'quick') {
        desc.textContent = '自动提取实体并构建知识库，适合批量处理';
        desc.style.borderLeftColor = 'var(--accent-blue)';
        hint.textContent = '支持 PDF、TXT、Markdown 格式';
    } else {
        desc.textContent = '先与 AI 讨论文献要点，确认后再写入知识库 (推荐)';
        desc.style.borderLeftColor = 'var(--accent-purple)';
        hint.textContent = '支持 PDF、TXT、Markdown 格式 - 符合 llm-wiki 思想';
    }
}

async function handleFileUpload(file) {
    const isPDF = file.name.toLowerCase().endsWith('.pdf');
    const isText = file.name.toLowerCase().match(/\.(txt|md)$/);
    
    if (!isPDF && !isText) {
        showToast('❌ 暂不支持的文件格式', 'error');
        return;
    }
    
    if (currentImportMode === 'deep') {
        // 深度导入模式
        await startDeepImport(file, isPDF);
    } else {
        // 快速导入模式
        if (isPDF) {
            await uploadPDF(file);
        } else {
            await uploadText(file);
        }
    }
}

async function uploadPDF(file) {
    showUploadProgress(true);
    updateUploadStage('正在读取 PDF 文件...', 10);
    
    try {
        // 获取 AI 设置
        const settings = getAISettings();
        if (!settings.apiKey) {
            showToast('⚠️ 请先在设置页面配置 OpenAI API Key', 'error');
            showUploadProgress(false);
            return;
        }
        
        const formData = new FormData();
        formData.append('pdf', file);
        formData.append('apiBase', settings.apiBase || 'https://api.openai-proxy.org');
        formData.append('apiKey', settings.apiKey);
        formData.append('model', settings.model || 'gpt-4.1-mini');
        
        updateUploadStage('正在使用 AI 分析文献内容...', 30);
        
        const response = await fetch('http://localhost:8000/api/process-pdf', {
            method: 'POST',
            body: formData
        });
        
        updateUploadStage('正在处理响应...', 80);
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateUploadStage('✅ 完成！正在刷新列表...', 100);
            showToast(`✅ 成功提取 ${result.entity_count} 个实体！`, 'success');
            
            // 刷新实体列表
            await loadExistingEntities();
            
            // 显示结果概要
            if (result.entities && result.entities.length > 0) {
                showEntitySummary(result.entities);
            }
            
            // 开始轮询构建状态
            pollBuildStatus();
        } else {
            throw new Error(result.error || '处理失败');
        }
        
    } catch (error) {
        console.error('PDF 上传失败:', error);
        showToast(`❌ 上传失败: ${error.message}`, 'error');
    } finally {
        setTimeout(() => showUploadProgress(false), 1500);
    }
}

async function uploadText(file) {
    showUploadProgress(true);
    updateUploadStage('正在读取文本文件...', 10);
    
    try {
        const text = await readFileAsText(file);
        
        // 检查内容长度
        if (text.length < 100) {
            throw new Error('文本内容过短，请提供更多内容以便提取实体');
        }
        
        // 获取 AI 设置
        const settings = getAISettings();
        if (!settings.apiKey) {
            showToast('⚠️ 请先在设置页面配置 OpenAI API Key', 'error');
            showUploadProgress(false);
            return;
        }
        
        updateUploadStage('正在使用 AI 分析笔记内容...', 30);
        
        // 调用文本处理 API
        const response = await fetch('http://localhost:8000/api/process-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                filename: file.name,
                apiBase: settings.apiBase || 'https://api.openai-proxy.org',
                apiKey: settings.apiKey,
                model: settings.model || 'gpt-4.1-mini'
            })
        });
        
        updateUploadStage('正在处理响应...', 80);
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateUploadStage('✅ 完成！正在刷新列表...', 100);
            showToast(`✅ 成功提取 ${result.entity_count} 个实体！`, 'success');
            
            // 刷新实体列表
            await loadExistingEntities();
            
            // 显示结果概要
            if (result.entities && result.entities.length > 0) {
                showEntitySummary(result.entities);
            }
            
            // 开始轮询构建状态
            pollBuildStatus();
        } else {
            throw new Error(result.error || '处理失败');
        }
        
    } catch (error) {
        console.error('文本上传失败:', error);
        showToast(`❌ 上传失败: ${error.message}`, 'error');
    } finally {
        setTimeout(() => showUploadProgress(false), 1500);
    }
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('读取文件失败'));
        reader.readAsText(file);
    });
}

function showUploadProgress(show) {
    const dropzone = document.getElementById('uploadDropzone');
    const progress = document.getElementById('uploadProgress');
    
    if (show) {
        dropzone.style.display = 'none';
        progress.style.display = 'block';
    } else {
        dropzone.style.display = 'block';
        progress.style.display = 'none';
        document.getElementById('fileInput').value = '';
    }
}

function updateUploadStage(stage, percent) {
    document.getElementById('uploadStage').textContent = stage;
    document.getElementById('uploadPercent').textContent = percent + '%';
    document.getElementById('progressFill').style.width = percent + '%';
}

function showEntitySummary(entities) {
    // 按类型分组统计
    const byType = {};
    entities.forEach(e => {
        byType[e.type] = (byType[e.type] || 0) + 1;
    });
    
    const summary = Object.entries(byType)
        .map(([type, count]) => `${type}: ${count}`)
        .join(', ');
    
    console.log('提取的实体:', summary);
}

async function pollBuildStatus() {
    // 等待一段时间后检查构建状态
    await new Promise(r => setTimeout(r, 5000));
    
    try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        
        if (response.ok) {
            showToast(`✅ 知识库构建完成！共 ${data.items} 个实体`, 'success');
            await loadExistingEntities(); // 再次刷新
        }
    } catch (e) {
        console.log('等待构建完成...');
    }
}

function getAISettings() {
    try {
        const saved = localStorage.getItem('omicknowledge_settings');
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (e) {
        console.error('读取设置失败:', e);
    }
    return {};
}

// ========== 深度导入功能 (符合 llm-wiki 思想) ==========

let currentFileContent = '';
let currentFileName = '';
let discussionHistory = [];
let extractedEntities = [];
let isDiscussionPhase = true;

async function startDeepImport(file, isPDF) {
    showUploadProgress(true);
    updateUploadStage('正在读取文件内容...', 10);
    
    const settings = getAISettings();
    if (!settings.apiKey) {
        showToast('⚠️ 请先在设置页面配置 OpenAI API Key', 'error');
        showUploadProgress(false);
        return;
    }
    
    try {
        currentFileName = file.name;
        
        if (isPDF) {
            updateUploadStage('正在解析 PDF...', 30);
            currentFileContent = await extractPDFText(file);
        } else {
            currentFileContent = await readFileAsText(file);
        }
        
        updateUploadStage('准备对话界面...', 100);
        
        // 显示深度导入面板并开始对话
        showDeepImportPanelForDiscussion(file.name);
        
        // 添加初始消息
        addDiscussionMessage('ai', `文件 "${file.name}" 已加载。我会先对内容进行初步分析，然后我们可以一起讨论。\n\n你可以：\n- 问具体的问题\n- 讨论文献的核心贡献\n- 确认提取的要点\n- 输入 "确认" 进入实体提取阶段`);
        
    } catch (error) {
        console.error('深度导入失败:', error);
        showToast(`❌ 分析失败: ${error.message}`, 'error');
    } finally {
        setTimeout(() => showUploadProgress(false), 500);
    }
}

async function extractPDFText(file) {
    // 简化处理：实际项目中可能需要服务端解析 PDF
    // 这里我们假设 PDF 已经有文本内容
    return `[PDF 文件: ${file.name}]\n\n[请注意：此版本中 PDF 需要先转换为文本上传，或使用快速导入模式]`;
}

async function extractForDeepImport(content, filename, settings) {
    // 调用后端 API 提取结构化数据
    const response = await fetch('http://localhost:8000/api/extract-for-review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: content.substring(0, 10000), // 限制长度
            filename: filename,
            apiBase: settings.apiBase || 'https://api.openai-proxy.org',
            apiKey: settings.apiKey,
            model: settings.model || 'gpt-4.1-mini'
        })
    });
    
    if (!response.ok) {
        throw new Error('提取失败');
    }
    
    const result = await response.json();
    return result;
}

function showDeepImportPanelForDiscussion(filename) {
    // 隐藏上传区域，显示深度导入面板
    document.getElementById('uploadSection').style.display = 'none';
    const panel = document.getElementById('deepImportPanel');
    panel.style.display = 'block';
    
    // 显示对话阶段
    isDiscussionPhase = true;
    document.getElementById('discussionSection').style.display = 'block';
    document.getElementById('summarySection').style.display = 'none';
    document.getElementById('entitiesSection').style.display = 'none';
    document.getElementById('obsidianSection').style.display = 'none';
    document.getElementById('confirmBtn').style.display = 'none';
    document.getElementById('backBtn').style.display = 'none';
    
    // 填充文件名
    document.getElementById('sourceFilename').textContent = filename;
    
    // 清空对话历史
    discussionHistory = [];
    document.getElementById('discussionMessages').innerHTML = '';
    
    // 聚焦输入框
    setTimeout(() => document.getElementById('discussionInput').focus(), 100);
}

function addDiscussionMessage(role, text) {
    const container = document.getElementById('discussionMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'ai' ? '🤖' : '👤';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    // 记录历史
    discussionHistory.push({role, text});
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function sendDiscussionMessage() {
    const input = document.getElementById('discussionInput');
    const text = input.value.trim();
    
    if (!text) return;
    
    // 显示用户消息
    addDiscussionMessage('user', text);
    input.value = '';
    
    // 检查是否确认
    if (text === '确认' || text.toLowerCase() === 'confirm') {
        await proceedToExtraction();
        return;
    }
    
    // 调用 API 进行对话
    try {
        const settings = getAISettings();
        const response = await fetch('http://localhost:8000/api/discuss', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: currentFileContent,
                filename: currentFileName,
                question: text,
                history: discussionHistory,
                apiBase: settings.apiBase || 'https://api.openai-proxy.org',
                apiKey: settings.apiKey,
                model: settings.model || 'gpt-4.1-mini'
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            addDiscussionMessage('ai', result.reply);
        } else {
            addDiscussionMessage('ai', '抱歉，处理你的问题时出现错误。请继续提问，或输入"确认"进入实体提取阶段。');
        }
    } catch (error) {
        console.error('对话失败:', error);
        addDiscussionMessage('ai', '网络连接有问题，但你仍然可以继续提问或输入"确认"进入下一步。');
    }
}

async function proceedToExtraction() {
    addDiscussionMessage('ai', '好的，我现在开始分析并提取实体。请稍等...');
    
    try {
        const settings = getAISettings();
        
        // 调用提取 API
        const response = await fetch('http://localhost:8000/api/extract-for-review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: currentFileContent,
                filename: currentFileName,
                apiBase: settings.apiBase || 'https://api.openai-proxy.org',
                apiKey: settings.apiKey,
                model: settings.model || 'gpt-4.1-mini'
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            extractedEntities = result.entities || [];
            
            // 转换到实体审核阶段
            isDiscussionPhase = false;
            
            document.getElementById('discussionSection').style.display = 'none';
            document.getElementById('summarySection').style.display = 'block';
            document.getElementById('entitiesSection').style.display = 'block';
            document.getElementById('backBtn').style.display = 'inline-flex';
            document.getElementById('confirmBtn').style.display = 'inline-flex';
            
            // 填充摘要
            document.getElementById('summaryTextarea').value = result.summary || '';
            
            // 检查交叉引用
            await checkCrossReferences(extractedEntities);
            
            // 渲染实体列表
            renderDeepImportEntities(extractedEntities);
            
            showToast(`✅ 已提取 ${extractedEntities.length} 个实体，请审核`, 'success');
        } else {
            throw new Error(result.error || '提取失败');
        }
    } catch (error) {
        console.error('提取失败:', error);
        addDiscussionMessage('ai', `提取失败: ${error.message}`);
    }
}

async function checkCrossReferences(entities) {
    const container = document.getElementById('crossReferencesInfo');
    container.innerHTML = '<p>正在检查与现有实体的关联...</p>';
    
    try {
        // 获取所有新实体的名称
        const newNames = entities.map(e => e.name).join(', ');
        
        const response = await fetch('http://localhost:8000/api/cross-reference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                entity_names: entities.map(e => e.name),
                descriptions: entities.map(e => e.description)
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.similarities && result.similarities.length > 0) {
            let html = '<h5 style="margin-bottom: 12px;">🔍 发现相关实体</h5>';
            result.similarities.forEach(sim => {
                html += `
                    <div class="cross-ref-item">
                        <span class="cross-ref-similarity">${Math.round(sim.score * 100)}%</span>
                        <span><strong>${escapeHtml(sim.new_entity)}</strong> ↔ ${escapeHtml(sim.existing_entity)}</span>
                    </div>
                `;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: var(--text-muted);">没有发现明显相关的现有实体</p>';
        }
    } catch (error) {
        console.error('交叉引用检查失败:', error);
        container.innerHTML = '<p style="color: var(--text-muted);">交叉引用检查完成</p>';
    }
}

function renderDeepImportEntities(entities) {
    const container = document.getElementById('deepImportEntities');
    container.innerHTML = '';
    
    entities.forEach((entity, index) => {
        const card = document.createElement('div');
        card.className = 'entity-edit-card';
        card.dataset.index = index;
        card.innerHTML = `
            <div class="entity-edit-header">
                <select class="entity-edit-type">
                    <option value="resources" ${entity.type === 'resources' ? 'selected' : ''}>文献</option>
                    <option value="tools" ${entity.type === 'tools' ? 'selected' : ''}>工具</option>
                    <option value="steps" ${entity.type === 'steps' ? 'selected' : ''}>方法</option>
                    <option value="concepts" ${entity.type === 'concepts' ? 'selected' : ''}>概念</option>
                </select>
                <input type="text" class="entity-edit-name" value="${escapeHtml(entity.name)}" placeholder="实体名称">
            </div>
            <textarea class="entity-edit-desc" rows="2" placeholder="描述">${escapeHtml(entity.description)}</textarea>
            <div class="entity-edit-actions">
                <button class="btn-icon" onclick="removeDeepImportEntity(${index})" title="删除">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

function addNewEntity() {
    const container = document.getElementById('deepImportEntities');
    const index = container.children.length;
    
    const card = document.createElement('div');
    card.className = 'entity-edit-card';
    card.dataset.index = index;
    card.innerHTML = `
        <div class="entity-edit-header">
            <select class="entity-edit-type">
                <option value="tools" selected>工具</option>
                <option value="steps">方法</option>
                <option value="concepts">概念</option>
                <option value="resources">文献</option>
            </select>
            <input type="text" class="entity-edit-name" placeholder="实体名称">
        </div>
        <textarea class="entity-edit-desc" rows="2" placeholder="描述"></textarea>
        <div class="entity-edit-actions">
            <button class="btn-icon" onclick="removeDeepImportEntity(${index})" title="删除">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
            </button>
        </div>
    `;
    container.appendChild(card);
}

function removeDeepImportEntity(index) {
    const cards = document.querySelectorAll('.entity-edit-card');
    if (cards[index]) {
        cards[index].remove();
    }
}

function backToDiscussion() {
    isDiscussionPhase = true;
    document.getElementById('discussionSection').style.display = 'block';
    document.getElementById('summarySection').style.display = 'none';
    document.getElementById('entitiesSection').style.display = 'none';
    document.getElementById('obsidianSection').style.display = 'none';
    document.getElementById('backBtn').style.display = 'none';
    document.getElementById('confirmBtn').style.display = 'none';
}

function cancelDeepImport() {
    // 重置界面
    document.getElementById('deepImportPanel').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'block';
    deepImportData = null;
    currentFileContent = '';
    currentFileName = '';
    discussionHistory = [];
    extractedEntities = [];
}

async function confirmDeepImport() {
    // 收集编辑后的数据
    const summary = document.getElementById('summaryTextarea').value;
    const filename = currentFileName;
    
    const entities = [];
    document.querySelectorAll('.entity-edit-card').forEach(card => {
        const type = card.querySelector('.entity-edit-type').value;
        const name = card.querySelector('.entity-edit-name').value;
        const description = card.querySelector('.entity-edit-desc').value;
        
        if (name && description) {
            entities.push({
                type: type,
                name: name,
                description: description,
                id: `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
            });
        }
    });
    
    if (entities.length === 0) {
        showToast('⚠️ 请至少添加一个实体', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        // 发送到后端保存
        const response = await fetch('http://localhost:8000/api/save-deep-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                summary: summary,
                entities: entities,
                discussion: discussionHistory
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // 显示 Obsidian 集成
            showObsidianIntegration(result.wiki_paths || []);
            
            showToast(`✅ 成功保存 ${entities.length} 个实体`, 'success');
            
            // 刷新实体列表
            await loadExistingEntities();
            
            // 保持面板打开显示 Obsidian 链接
            document.getElementById('entitiesSection').style.display = 'none';
            document.getElementById('obsidianSection').style.display = 'block';
            document.getElementById('confirmBtn').style.display = 'none';
            document.getElementById('backBtn').style.display = 'none';
            
            // 添加关闭按钮
            const closeBtn = document.createElement('button');
            closeBtn.className = 'btn btn-secondary';
            closeBtn.textContent = '完成';
            closeBtn.onclick = () => {
                cancelDeepImport();
                closeBtn.remove();
            };
            document.querySelector('.deep-import-actions').appendChild(closeBtn);
            
        } else {
            throw new Error(result.error || '保存失败');
        }
        
    } catch (error) {
        console.error('保存失败:', error);
        showToast(`❌ 保存失败: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function showObsidianIntegration(paths) {
    const container = document.getElementById('obsidianLinks');
    container.innerHTML = '';
    
    paths.forEach(path => {
        const link = document.createElement('a');
        link.className = 'obsidian-link';
        link.href = `obsidian://open?path=${encodeURIComponent(path)}`;
        link.target = '_blank';
        
        const filename = path.split('/').pop();
        link.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
            ${escapeHtml(filename)}
        `;
        
        container.appendChild(link);
    });
}
