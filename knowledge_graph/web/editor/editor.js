/**
 * 知识库编辑器 JavaScript
 * 实现表单处理、YAML 生成和 API 通信
 */

// 全局状态
let currentTags = [];
let isEditing = false;

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
