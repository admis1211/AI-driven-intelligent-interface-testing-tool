const API_BASE = window.location.origin;

let sessionId = null;
let currentSessionId = null;
window.apiKey = localStorage.getItem('openai_api_key') || '';

const elements = {
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    documentList: document.getElementById('documentList'),
    useContext: document.getElementById('useContext'),
    apiKeyBtn: document.getElementById('apiKeyBtn'),
    apiKeyModal: document.getElementById('apiKeyModal'),
    apiKeyInput: document.getElementById('apiKeyInput'),
    apiBaseInput: document.getElementById('apiBaseInput'),
    modelNameInput: document.getElementById('modelNameInput'),
    temperatureInput: document.getElementById('temperatureInput'),
    saveApiKey: document.getElementById('saveApiKey'),
    loadApiConfig: document.getElementById('loadApiConfig'),
    newChatBtn: document.getElementById('newChatBtn'),
    clearDocsBtn: document.getElementById('clearDocsBtn'),
    toastContainer: document.getElementById('toastContainer'),
    addMonitorBtn: document.getElementById('addMonitorBtn'),
    monitorList: document.getElementById('monitorList'),
    monitorModal: document.getElementById('monitorModal'),
    monitorModalClose: document.getElementById('monitorModalClose'),
    cancelMonitorBtn: document.getElementById('cancelMonitorBtn'),
    saveMonitorBtn: document.getElementById('saveMonitorBtn'),
    monitorName: document.getElementById('monitorName'),
    monitorUrl: document.getElementById('monitorUrl'),
    monitorMethod: document.getElementById('monitorMethod'),
    monitorFrequency: document.getElementById('monitorFrequency'),
    docCount: document.getElementById('docCount')
};

elements.apiKeyInput.value = apiKey;

document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
    btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`view-${view}`).classList.add('active');
    });
});

elements.sendBtn.addEventListener('click', sendMessage);
elements.messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

elements.messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
elements.fileInput.addEventListener('change', handleFileUpload);

elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.classList.remove('drag-over');
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
        elements.fileInput.files = e.dataTransfer.files;
        handleFileUpload({ target: { files: e.dataTransfer.files } });
    }
});

elements.apiKeyBtn.addEventListener('click', () => {
    elements.apiKeyModal.classList.add('active');
});

elements.saveApiKey.addEventListener('click', async () => {
    const apiKeyVal = elements.apiKeyInput.value.trim();
    const apiBase = elements.apiBaseInput.value.trim();
    const modelName = elements.modelNameInput.value.trim();
    const temperature = parseFloat(elements.temperatureInput.value) || 0.7;

    try {
        const response = await fetch(`${API_BASE}/api/config/api`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKeyVal || null,
                api_base: apiBase || null,
                model_name: modelName || null,
                temperature: temperature
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            window.apiKey = apiKeyVal;
            localStorage.setItem('openai_api_key', apiKeyVal);
            localStorage.setItem('openai_api_base', apiBase);
            localStorage.setItem('openai_model_name', modelName);
            localStorage.setItem('openai_temperature', temperature.toString());
            
            elements.apiKeyModal.classList.remove('active');
            showToast('配置保存成功！', 'success');
        } else {
            showToast('保存配置失败: ' + (data.detail || '未知错误'), 'error');
        }
    } catch (error) {
        showToast('保存配置失败: ' + error.message, 'error');
    }
});

elements.loadApiConfig.addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_BASE}/api/config/api`);
        const data = await response.json();
        
        if (response.ok) {
            elements.apiBaseInput.value = data.api_base || '';
            elements.modelNameInput.value = data.model_name || '';
            elements.temperatureInput.value = data.temperature || 0.7;
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
});

document.querySelector('#apiKeyModal .modal-close').addEventListener('click', () => {
    elements.apiKeyModal.classList.remove('active');
});

elements.apiKeyModal.addEventListener('click', (e) => {
    if (e.target === elements.apiKeyModal) {
        elements.apiKeyModal.classList.remove('active');
    }
});

elements.newChatBtn.addEventListener('click', () => {
    sessionId = null;
    elements.chatMessages.innerHTML = '';
    addMessage('ai', `<p>你好！我是 <strong>Ralph Loop</strong>，你的 AI 接口测试助手。</p>
        <p>我可以帮助你：</p>
        <ul>
            <li>📄 解析接口文档 (Pdf, Word, PPT)</li>
            <li>🧪 生成接口测试用例</li>
            <li>🔍 实时监控接口状态</li>
            <li>💬 智能问答测试相关问题</li>
        </ul>
        <div class="message-time">今天</div>`);
});

elements.clearDocsBtn.addEventListener('click', async () => {
    if (confirm('确定要清除所有文档吗？')) {
        try {
            const response = await fetch(`${API_BASE}/api/documents/`, {
                method: 'DELETE'
            });
            const data = await response.json();
            showToast(data.message, 'success');
            loadDocuments();
        } catch (error) {
            showToast('清除文档失败: ' + error.message, 'error');
        }
    }
});

if (elements.addMonitorBtn) {
    elements.addMonitorBtn.addEventListener('click', function() {
        elements.monitorModal.classList.add('active');
    });
}

if (elements.monitorModalClose) {
    elements.monitorModalClose.addEventListener('click', function() {
        elements.monitorModal.classList.remove('active');
    });
}

if (elements.cancelMonitorBtn) {
    elements.cancelMonitorBtn.addEventListener('click', function() {
        elements.monitorModal.classList.remove('active');
    });
}

if (elements.monitorModal) {
    elements.monitorModal.addEventListener('click', function(e) {
        if (e.target === elements.monitorModal) {
            elements.monitorModal.classList.remove('active');
        }
    });
}

if (elements.saveMonitorBtn) {
    elements.saveMonitorBtn.addEventListener('click', addMonitor);
}

async function loadMonitors() {
    try {
        var response = await fetch(API_BASE + '/api/monitor/list');
        var data = await response.json();
        
        if (data.configs.length === 0) {
            elements.monitorList.innerHTML = '<div class="empty-state"><svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><p>暂无监控</p><span>添加接口进行实时监控</span></div>';
            return;
        }
        
        elements.monitorList.innerHTML = '';
        
        for (var monitor of data.configs) {
            var lastCheck = '';
            var responseTime = '';
            var statusCode = '';
            
            try {
                var historyResp = await fetch(API_BASE + '/api/monitor/history/' + monitor.id + '?limit=1');
                var historyData = await historyResp.json();
                
                if (historyData.history && historyData.history.length > 0) {
                    var last = historyData.history[0];
                    var checkDate = new Date(last.checked_at);
                    lastCheck = checkDate.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    responseTime = (last.response_time * 1000).toFixed(0);
                    statusCode = last.status_code;
                }
            } catch (e) {
                console.error('获取历史记录失败:', e);
            }
            
            var item = document.createElement('div');
            item.className = 'monitor-item';
            item.innerHTML = '<div class="monitor-status-indicator" id="status-' + monitor.id + '"></div>' +
                '<div class="monitor-info"><div class="monitor-name">' + monitor.name + '</div><div class="monitor-url">' + monitor.method + ' ' + monitor.url + '</div>' +
                '<div class="monitor-meta">' +
                    '<span class="monitor-frequency">' + (monitor.frequency || 60) + '秒</span>' +
                    (responseTime ? '<span class="monitor-response">' + responseTime + 'ms</span>' : '') +
                    (statusCode ? '<span class="monitor-status-code ' + (statusCode >= 400 ? 'error' : 'success') + '">' + statusCode + '</span>' : '') +
                    (lastCheck ? '<span class="monitor-last-check">' + lastCheck + '</span>' : '') +
                '</div></div>' +
                '<button class="monitor-delete-btn" data-id="' + monitor.id + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
            elements.monitorList.appendChild(item);
        }

        document.querySelectorAll('.monitor-delete-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var id = this.dataset.id;
                if (confirm('确定要删除此监控吗？')) {
                    deleteMonitor(id);
                }
            });
        });

        data.configs.forEach(function(monitor) {
            checkMonitorStatus(monitor.id);
        });

    } catch (error) {
        console.error('加载监控列表失败:', error);
    }
}

async function checkMonitorStatus(monitorId) {
    try {
        var response = await fetch(API_BASE + '/api/monitor/stats/' + monitorId + '?hours=1');
        var stats = await response.json();
        
        var statusEl = document.getElementById('status-' + monitorId);
        if (statusEl) {
            if (stats.total_checks === 0) {
                statusEl.className = 'monitor-status-indicator status-unknown';
            } else if (stats.uptime_percentage >= 99) {
                statusEl.className = 'monitor-status-indicator status-online';
            } else if (stats.uptime_percentage >= 90) {
                statusEl.className = 'monitor-status-indicator status-warning';
            } else {
                statusEl.className = 'monitor-status-indicator status-offline';
            }
        }
    } catch (error) {
        console.error('获取监控状态失败:', error);
    }
}

async function addMonitor() {
    var name = elements.monitorName.value.trim();
    var url = elements.monitorUrl.value.trim();
    var method = elements.monitorMethod.value;
    var frequency = parseInt(elements.monitorFrequency.value) || 60;

    if (!name || !url) {
        showToast('请填写接口名称和地址', 'warning');
        return;
    }

    try {
        var response = await fetch(API_BASE + '/api/monitor/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name, url: url, method: method, frequency: frequency
            })
        });

        if (response.ok) {
            showToast('监控添加成功！', 'success');
            elements.monitorModal.classList.remove('active');
            elements.monitorName.value = '';
            elements.monitorUrl.value = '';
            elements.monitorMethod.value = 'GET';
            elements.monitorFrequency.value = 60;
            
            var result = await response.json();
            var newConfigId = result.id;
            
            await loadMonitors();
            
            setTimeout(async function() {
                try {
                    await fetch(API_BASE + '/api/monitor/check/' + newConfigId, { method: 'POST' });
                    await loadMonitors();
                } catch(e) {
                    console.error('立即检查失败:', e);
                }
            }, 1500);
        } else {
            var data = await response.json();
            showToast('添加失败: ' + (data.detail || '未知错误'), 'error');
        }
    } catch (error) {
        showToast('添加失败: ' + error.message, 'error');
    }
}

async function deleteMonitor(monitorId) {
    try {
        var response = await fetch(API_BASE + '/api/monitor/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config_id: monitorId })
        });

        if (response.ok) {
            showToast('监控删除成功', 'success');
            loadMonitors();
        } else {
            showToast('删除失败', 'error');
        }
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

setInterval(function() {
    refreshMonitorStatusOnly();
}, 5000);

function refreshMonitorStatusOnly() {
    var ids = document.querySelectorAll('.monitor-status-indicator');
    if (ids.length === 0) return;
    
    var idList = Array.from(ids).map(el => el.id.replace('status-', ''));
    
    Promise.all(idList.map(function(id) {
        return fetch(API_BASE + '/api/monitor/history/' + id + '?limit=1')
            .then(r => r.json())
            .then(data => ({ id: id, data: data }));
    })).then(function(results) {
        results.forEach(function(result) {
            var statusEl = document.getElementById('status-' + result.id);
            var itemEl = statusEl ? statusEl.closest('.monitor-item') : null;
            
            if (itemEl && result.data.history && result.data.history.length > 0) {
                var last = result.data.history[0];
                var checkDate = new Date(last.checked_at);
                var lastCheckStr = checkDate.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                var lastCheckEl = itemEl.querySelector('.monitor-last-check');
                var responseEl = itemEl.querySelector('.monitor-response');
                var statusCodeEl = itemEl.querySelector('.monitor-status-code');
                
                if (lastCheckEl) lastCheckEl.textContent = lastCheckStr;
                if (responseEl) responseEl.textContent = (last.response_time * 1000).toFixed(0) + 'ms';
                if (statusCodeEl) {
                    statusCodeEl.textContent = last.status_code;
                    statusCodeEl.className = 'monitor-status-code ' + (last.status_code >= 400 ? 'error' : 'success');
                }
                
                if (statusEl) {
                    statusEl.className = 'monitor-status-indicator ' + (last.success ? 'status-online' : 'status-offline');
                }
            }
        });
    }).catch(function(err) {
        console.error('刷新状态失败:', err);
    });
}

async function checkAllMonitorStatus() {
    refreshMonitorStatusOnly();
}

function getSelectedDocuments() {
    const checkboxes = document.querySelectorAll('#documentList input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message) {
        showToast('请输入消息内容', 'warning');
        return;
    }

    if (!window.apiKey) {
        showToast('请先设置 API Key', 'warning');
        elements.apiKeyModal.classList.add('active');
        elements.sendBtn.disabled = false;
        return;
    }

    addMessage('user', message);
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    elements.sendBtn.disabled = true;

    const loadingMessage = addMessage('ai', '<div class="loading"><div class="spinner"></div><span class="thinking-text">正在思考...</span></div>');

    const selectedDocs = getSelectedDocuments();
    const useContext = elements.useContext.checked;

    try {
        const requestBody = {
            message: message,
            session_id: sessionId,
            use_context: useContext
        };
        
        if (useContext && selectedDocs.length > 0) {
            requestBody.selected_documents = selectedDocs;
        }

        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.apiKey}`
            },
            body: JSON.stringify(requestBody)
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let sources = null;
        
        const messageContentEl = loadingMessage.querySelector('.message-content');
        if (messageContentEl) {
            messageContentEl.innerHTML = '<div class="streaming-content"></div>';
        }
        const streamingContent = loadingMessage.querySelector('.streaming-content') || messageContentEl;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'chunk') {
                            fullResponse += data.content;
                            if (streamingContent) {
                                streamingContent.innerHTML = formatResponse(fullResponse);
                            }
                        } else if (data.type === 'done') {
                            sessionId = data.session_id;
                            sources = data.sources;
                        } else if (data.type === 'error') {
                            throw new Error(data.content);
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

        loadingMessage.remove();
        
        const now = new Date();
        const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        
        let content = `<div class="streaming-content">${formatResponse(fullResponse)}</div>`;
        
        if (sources && sources.length > 0) {
            content += `<div class="sources"><h4>📄 参考文档:</h4>`;
            sources.forEach((source, i) => {
                content += `<div class="source-item">${i + 1}. ${source.page_content}</div>`;
            });
            content += `</div>`;
        }
        
        content += `<div class="message-time">${timeStr}</div>`;
        
        addMessage('ai', content);
    } catch (error) {
        loadingMessage.remove();
        addMessage('ai', `<p style="color: #EF4444;">发送消息失败: ${error.message}</p><div class="message-time">${new Date().toLocaleTimeString()}</div>`);
    }

    elements.sendBtn.disabled = false;
    elements.messageInput.focus();
}

function formatResponse(text) {
    if (typeof marked !== 'undefined') {
        let html = marked.parse(text);
        if (typeof DOMPurify !== 'undefined') {
            html = DOMPurify.sanitize(html);
        }
        return html;
    }
    return text.replace(/\n/g, '<br>');
}

function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${type === 'ai' 
                    ? '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>'
                    : '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'
                }
            </svg>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTo({
        top: elements.chatMessages.scrollHeight,
        behavior: 'smooth'
    });
    
    return messageDiv;
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showToast('正在上传 ' + file.name + '...', 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/documents/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast(`上传成功！已索引 ${data.document_count} 个文档`, 'success');
            loadDocuments();
            loadDocumentsForDefect();
            loadDocumentsForTestcase();
        } else {
            throw new Error(data.detail || '上传失败');
        }
    } catch (error) {
        showToast('上传失败: ' + error.message, 'error');
    }

    event.target.value = '';
}

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/api/documents/`);
        const data = await response.json();
        
        if (elements.docCount) {
            elements.docCount.textContent = `${data.documents.length} 个文档`;
        }
        
        elements.documentList.innerHTML = '';
        
        if (data.documents.length === 0) {
            elements.documentList.innerHTML = `
                <div class="empty-state">
                    <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <p>暂无文档</p>
                    <span>上传接口文档开始使用</span>
                </div>`;
            return;
        }
        
        data.documents.forEach((doc, index) => {
            const item = document.createElement('div');
            item.className = 'document-item';
            item.style.animationDelay = `${index * 0.05}s`;
            item.innerHTML = `
                <label class="doc-checkbox">
                    <input type="checkbox" value="${doc.filename}" checked>
                    <span class="checkmark"></span>
                </label>
                <div class="document-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                </div>
                <span class="filename" title="${doc.filename}">${doc.filename}</span>
                <button class="delete-btn" data-filename="${doc.filename}" aria-label="删除文档">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            `;
            elements.documentList.appendChild(item);
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const filename = e.currentTarget.dataset.filename;
                await deleteDocument(filename);
            });
        });
    } catch (error) {
        console.error('加载文档列表失败:', error);
    }
}

async function deleteDocument(filename) {
    try {
        const response = await fetch(`${API_BASE}/api/documents/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('文档删除成功', 'success');
            loadDocuments();
            loadDocumentsForDefect();
            loadDocumentsForTestcase();
        } else {
            showToast('删除失败', 'error');
        }
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconSvg = type === 'success' 
        ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
        : type === 'error'
        ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        : '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
    
    toast.innerHTML = `
        ${iconSvg}
        <span class="toast-message">${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    toast.addEventListener('click', () => {
        toast.remove();
    });
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 4000);
}

// ========================================
// Agent Testing Functions
// ========================================
let currentTestId = null;

async function runAgentTest() {
    const endpointUrl = document.getElementById('agentEndpointUrl').value.trim();
    const method = document.getElementById('agentMethod').value;
    const expectedStatus = parseInt(document.getElementById('agentExpectedStatus').value) || 200;
    
    if (!endpointUrl) {
        showToast('请输入接口地址', 'error');
        return;
    }
    
    const runBtn = document.getElementById('runAgentTestBtn');
    const progressSection = document.getElementById('agentProgress');
    const progressBar = document.getElementById('agentProgressBar');
    const progressText = document.getElementById('agentProgressText');
    const resultsContainer = document.getElementById('agentResults');
    
    runBtn.disabled = true;
    runBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>测试中...';
    progressSection.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = '正在启动测试...';
    
    resultsContainer.innerHTML = '';
    
    try {
        const response = await fetch('/api/agent/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_ids: [],
                endpoint_url: endpointUrl,
                method: method,
                expected_status: expectedStatus,
                test_scenarios: ['正常请求', '空参数', '超长参数', '特殊字符']
            })
        });
        
        if (!response.ok) {
            throw new Error('测试请求失败');
        }
        
        const result = await response.json();
        currentTestId = result.test_id;
        
        progressBar.style.width = '100%';
        progressText.textContent = result.message;
        
        await loadAgentTestReport(result.test_id);
        
    } catch (error) {
        showToast('测试失败: ' + error.message, 'error');
        progressSection.classList.add('hidden');
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>开始测试';
    }
}

async function loadAgentTestReport(testId) {
    const resultsContainer = document.getElementById('agentResults');
    
    try {
        const response = await fetch(`/api/agent/test/${testId}/report`);
        if (!response.ok) {
            throw new Error('获取报告失败');
        }
        
        const report = await response.json();
        
        let html = `
            <div class="agent-summary">
                <div class="agent-summary-title">测试结果汇总</div>
                <div class="agent-summary-stats">
                    <div class="agent-stat">
                        <span class="agent-stat-value success">${report.passed_tests}</span>
                        <span class="agent-stat-label">通过</span>
                    </div>
                    <div class="agent-stat">
                        <span class="agent-stat-value failed">${report.failed_tests}</span>
                        <span class="agent-stat-label">失败</span>
                    </div>
                    <div class="agent-stat">
                        <span class="agent-stat-value rate">${report.pass_rate.toFixed(1)}%</span>
                        <span class="agent-stat-label">通过率</span>
                    </div>
                </div>
        `;
        
        if (report.suggestions && report.suggestions.length > 0) {
            html += `
                <div class="agent-suggestions">
                    <div class="agent-suggestions-title">修复建议</div>
                    ${report.suggestions.map(s => `<div class="agent-suggestion-item">${s}</div>`).join('')}
                </div>
            `;
        }
        
        html += '</div>';
        
        report.results.forEach(result => {
            const statusClass = result.passed ? 'passed' : 'failed';
            const statusText = result.passed ? '通过' : '失败';
            const statusValueClass = result.passed ? 'status-success' : 'status-error';
            
            html += `
                <div class="test-result-card">
                    <div class="test-result-header">
                        <span class="test-scenario-name">${result.scenario}</span>
                        <span class="test-status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <div class="test-result-details">
                        <div class="test-detail-item">
                            <span class="test-detail-label">状态码</span>
                            <span class="test-detail-value ${statusValueClass}">${result.response_status}</span>
                        </div>
                        <div class="test-detail-item">
                            <span class="test-detail-label">响应时间</span>
                            <span class="test-detail-value">${result.response_time.toFixed(2)}s</span>
                        </div>
                        <div class="test-detail-item">
                            <span class="test-detail-label">请求方法</span>
                            <span class="test-detail-value">${result.request_method}</span>
                        </div>
                    </div>
                    ${result.error ? `<div class="test-error-message">${result.error}</div>` : ''}
                </div>
            `;
        });
        
        resultsContainer.innerHTML = html;
        
    } catch (error) {
        showToast('加载报告失败: ' + error.message, 'error');
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <p>加载报告失败</p>
                <span>${error.message}</span>
            </div>
        `;
    }
}

document.getElementById('runAgentTestBtn')?.addEventListener('click', runAgentTest);

// ==================== 缺陷预测模块 ====================

let uploadedDocList = [];

async function loadDocumentsForDefect() {
    const docList = document.getElementById('defectDocList');
    if (!docList) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        const data = await response.json();
        
        uploadedDocList = data.documents || [];
        
        if (uploadedDocList.length === 0) {
            docList.innerHTML = '<div class="text-muted">暂无已上传的文档，请先上传文档</div>';
            return;
        }
        
        docList.innerHTML = uploadedDocList.map(doc => `
            <label class="defect-doc-checkbox">
                <input type="checkbox" value="${doc.filename}">
                <span class="checkmark"></span>
                <span class="filename">${doc.filename}</span>
            </label>
        `).join('');
    } catch (error) {
        console.error('加载文档列表失败:', error);
        docList.innerHTML = '<div class="text-muted">加载文档失败</div>';
    }
}

async function runDefectPredict() {
    console.log('runDefectPredict started');
    const docCheckboxes = document.querySelectorAll('#defectDocList input[type="checkbox"]:checked');
    const selectedDocs = Array.from(docCheckboxes).map(cb => cb.value);
    console.log('Selected docs:', selectedDocs);
    
    if (selectedDocs.length === 0) {
        showToast('请至少选择一个文档', 'warning');
        return;
    }
    
    const endpointUrl = document.getElementById('defectEndpointUrl')?.value?.trim() || '';
    const method = document.getElementById('defectMethod')?.value || 'GET';
    console.log('Endpoint:', endpointUrl, 'Method:', method);
    
    const progressDiv = document.getElementById('defectProgress');
    const progressBar = document.getElementById('defectProgressBar');
    const progressText = document.getElementById('defectProgressText');
    const resultsDiv = document.getElementById('defectResults');
    
    progressDiv.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = '正在分析文档...';
    resultsDiv.innerHTML = '';
    
    console.log('Making API call...');
    
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress > 90) progress = 90;
        progressBar.style.width = progress + '%';
    }, 500);
    
    try {
        console.log('Fetching API...');
        let response;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);
        
        try {
            response = await fetch(`${API_BASE}/api/defect/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    document_ids: selectedDocs,
                    endpoint_url: endpointUrl || null,
                    method: method
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchErr) {
            clearTimeout(timeoutId);
            console.error('Fetch error:', fetchErr);
            if (fetchErr.name === 'AbortError') {
                throw new Error('请求超时，请重试');
            }
            throw fetchErr;
        }
        console.log('Response status:', response.status);
        
        const result = await response.json();
        console.log('Response data:', result);
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        progressText.textContent = '分析完成';
        
        if (result.report_id) {
            await loadDefectReport(result.report_id);
        } else {
            throw new Error(result.detail || '预测失败');
        }
        
    } catch (error) {
        clearInterval(progressInterval);
        progressDiv.classList.add('hidden');
        showToast('缺陷预测失败: ' + error.message, 'error');
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <p>预测失败</p>
                <span>${error.message}</span>
            </div>
        `;
    }
}

async function loadDefectReport(reportId) {
    const resultsDiv = document.getElementById('defectResults');
    const progressDiv = document.getElementById('defectProgress');
    
    try {
        const response = await fetch(`${API_BASE}/api/defect/report/${reportId}`);
        if (!response.ok) throw new Error('获取报告失败');
        
        const report = await response.json();
        
        progressDiv.classList.add('hidden');
        
        const defectsBySeverity = {
            high: report.defects.filter(d => d.severity === 'high'),
            medium: report.defects.filter(d => d.severity === 'medium'),
            low: report.defects.filter(d => d.severity === 'low')
        };
        
        const riskEmoji = report.risk_level === 'high' ? '🔴' : report.risk_level === 'medium' ? '🟡' : '🟢';
        
        let html = `
            <div class="defect-summary">
                <div class="defect-risk-badge ${report.risk_level}">
                    ${riskEmoji} 风险等级: ${report.risk_level.toUpperCase()}
                </div>
                <p class="defect-summary-text">${report.summary}</p>
            </div>
        `;
        
        ['high', 'medium', 'low'].forEach(severity => {
            const defects = defectsBySeverity[severity];
            if (defects.length === 0) return;
            
            html += `
                <div class="defect-category">
                    <div class="defect-category-header ${severity}">
                        ${severity === 'high' ? '⚠️ 高危缺陷' : severity === 'medium' ? '⚡ 中危缺陷' : '📝 低危缺陷'} (${defects.length})
                    </div>
                    <div class="defect-category-body">
            `;
            
            defects.forEach(defect => {
                html += `
                    <div class="defect-item-card">
                        <div class="defect-item-header">
                            <span class="defect-item-category">${defect.category}</span>
                            <span class="defect-item-severity ${defect.severity}">${defect.severity}</span>
                        </div>
                        <div class="defect-item-title">${defect.description}</div>
                        <div class="defect-item-location">📍 ${defect.location}</div>
                        <div class="defect-item-suggestion">💡 ${defect.suggestion}</div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        });
        
        if (report.test_focus && report.test_focus.length > 0) {
            html += `
                <div class="defect-test-focus">
                    <div class="defect-test-focus-title">📋 测试重点</div>
                    <div class="defect-test-focus-list">
                        ${report.test_focus.map(f => `<span class="test-focus-item">${f}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        resultsDiv.innerHTML = html;
        showToast('缺陷预测完成', 'success');
        
    } catch (error) {
        progressDiv.classList.add('hidden');
        showToast('加载报告失败: ' + error.message, 'error');
    }
}

// Wrapper to catch errors
function runDefectPredictWrapper() {
    console.log('runDefectPredictBtn clicked');
    try {
        runDefectPredict();
    } catch (e) {
        console.error('Error in runDefectPredict:', e);
        showToast('预测失败: ' + e.message, 'error');
    }
}

document.getElementById('runDefectPredictBtn')?.addEventListener('click', runDefectPredictWrapper);

// ==================== 测试用例模块 ====================

let testcaseGeneratedList = [];

async function loadDocumentsForTestcase() {
    const docList = document.getElementById('testcaseDocSelect');
    if (!docList) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        const data = await response.json();
        
        const docs = data.documents || [];
        
        if (docs.length === 0) {
            docList.innerHTML = '<div class="text-muted">暂无已上传的文档</div>';
            return;
        }
        
        docList.innerHTML = docs.map(doc => `
            <label class="defect-doc-checkbox">
                <input type="checkbox" value="${doc.filename}">
                <span class="checkmark"></span>
                <span class="filename">${doc.filename}</span>
            </label>
        `).join('');
    } catch (error) {
        console.error('加载文档列表失败:', error);
    }
}

async function generateTestcases() {
    const docCheckboxes = document.querySelectorAll('#testcaseDocSelect input[type="checkbox"]:checked');
    const selectedDocs = Array.from(docCheckboxes).map(cb => cb.value);
    
    // Note: Allow generating testcases without selecting documents
    // if (selectedDocs.length === 0) {
    //     showToast('请至少选择一个文档', 'warning');
    //     return;
    // }
    
    const endpointUrl = document.getElementById('testcaseEndpointUrl')?.value?.trim();
    const method = document.getElementById('testcaseMethod')?.value || 'GET';
    const count = parseInt(document.getElementById('testcaseCount')?.value) || 10;
    
    if (!endpointUrl) {
        showToast('请输入接口地址', 'warning');
        return;
    }
    
    // Note: document_ids can be empty, we allow generating testcases without documents
    
    const resultsDiv = document.getElementById('testcaseResults');
    const testcaseList = document.getElementById('testcaseList');
    const countDisplay = document.getElementById('testcaseCountDisplay');
    const generateBtn = document.getElementById('generateTestcaseBtn');
    
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> 生成中...';
    
    try {
        const response = await fetch(`${API_BASE}/api/testcase/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_ids: selectedDocs,
                endpoint_url: endpointUrl,
                method: method,
                count: count
            })
        });
        
        if (!response.ok) {
            throw new Error('生成失败');
        }
        
        const data = await response.json();
        testcaseGeneratedList = data.testcases || [];
        
        countDisplay.textContent = testcaseGeneratedList.length;
        
        if (testcaseGeneratedList.length === 0) {
            testcaseList.innerHTML = '<div class="empty-state"><p>未生成测试用例</p></div>';
        } else {
            testcaseList.innerHTML = testcaseGeneratedList.map((tc, idx) => `
                <div class="testcase-item">
                    <div class="testcase-item-header">
                        <span class="testcase-id">#${tc.id || idx + 1}</span>
                        <span class="testcase-name">${tc.name}</span>
                        <span class="testcase-priority priority-${tc.priority}">${tc.priority}</span>
                    </div>
                    <div class="testcase-item-body">
                        <div class="testcase-detail"><strong>方法:</strong> ${tc.method}</div>
                        <div class="testcase-detail"><strong>URL:</strong> ${tc.url}</div>
                        ${tc.params ? `<div class="testcase-detail"><strong>参数:</strong> <pre>${JSON.stringify(tc.params, null, 2)}</pre></div>` : ''}
                        ${tc.body ? `<div class="testcase-detail"><strong>请求体:</strong> <pre>${JSON.stringify(tc.body, null, 2)}</pre></div>` : ''}
                        <div class="testcase-detail"><strong>预期状态:</strong> ${tc.expected_status}</div>
                        ${tc.description ? `<div class="testcase-detail"><strong>描述:</strong> ${tc.description}</div>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        resultsDiv.style.display = 'block';
        showToast('生成完成', 'success');
        
    } catch (error) {
        console.error('生成测试用例失败:', error);
        showToast('生成失败: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> 生成测试用例';
    }
}

async function exportTestcases(format) {
    if (testcaseGeneratedList.length === 0) {
        showToast('没有可导出的测试用例', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/testcase/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testcaseGeneratedList)
        });
        
        if (!response.ok) {
            throw new Error('导出失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `testcases.${format === 'excel' ? 'xlsx' : format === 'postman' ? 'json' : 'json'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('导出成功', 'success');
        
    } catch (error) {
        console.error('导出失败:', error);
        showToast('导出失败: ' + error.message, 'error');
    }
}

document.getElementById('generateTestcaseBtn')?.addEventListener('click', generateTestcases);
document.getElementById('exportJsonBtn')?.addEventListener('click', () => exportTestcases('json'));
document.getElementById('exportExcelBtn')?.addEventListener('click', () => exportTestcases('excel'));
document.getElementById('exportPostmanBtn')?.addEventListener('click', () => exportTestcases('postman'));

// ==================== Session Management ====================

async function loadSessions() {
    const sessionsList = document.getElementById('sessionsList');
    if (!sessionsList) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/chat/sessions`);
        const data = await response.json();
        
        if (data.sessions && data.sessions.length > 0) {
            sessionsList.innerHTML = data.sessions.map(s => `
                <div class="session-item" data-session-id="${s.session_id}">
                    <div class="session-info">
                        <div class="session-date">${new Date(s.created_at).toLocaleString('zh-CN')}</div>
                        <div class="session-preview">${s.last_message || '新对话'}</div>
                    </div>
                    <button class="session-delete" title="删除会话">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            `).join('');
            
            sessionsList.querySelectorAll('.session-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (e.target.closest('.session-delete')) return;
                    const sid = item.dataset.sessionId;
                    loadSessionChat(sid);
                });
            });
            
            sessionsList.querySelectorAll('.session-delete').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const item = btn.closest('.session-item');
                    const sid = item.dataset.sessionId;
                    if (confirm('确定删除此会话？')) {
                        await deleteSession(sid);
                    }
                });
            });
        } else {
            sessionsList.innerHTML = '<div class="empty-state"><p>暂无历史会话</p></div>';
        }
    } catch (error) {
        console.error('加载会话失败:', error);
        sessionsList.innerHTML = '<div class="empty-state"><p>加载失败</p></div>';
    }
}

async function deleteSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/chat/session/${sessionId}/delete`, {
            method: 'DELETE'
        });
        if (response.ok) {
            showToast('会话已删除', 'success');
            loadSessions();
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                startNewChat();
            }
        }
    } catch (error) {
        console.error('删除会话失败:', error);
        showToast('删除失败', 'error');
    }
}

function loadSessionChat(sessionId) {
    currentSessionId = sessionId;
    sessionStorage.setItem('currentSessionId', sessionId);
    
    document.getElementById('sessionsSidebar')?.classList.remove('active');
    
    const chatMessages = document.getElementById('chatMessages');
    
    // Fetch session history from API
    fetch(`${API_BASE}/api/chat/session/${sessionId}/history`)
        .then(res => res.json())
        .then(data => {
            if (data.history && data.history.length > 0) {
                chatMessages.innerHTML = '';
                data.history.forEach(msg => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = msg.type === 'user' ? 'message message-user' : 'message message-ai';
                    
                    const avatar = msg.type === 'user' 
                        ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
                        : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>';
                    
                    msgDiv.innerHTML = `
                        <div class="message-avatar">${avatar}</div>
                        <div class="message-content">
                            <div class="message-text">${msg.content}</div>
                            <div class="message-time">历史消息</div>
                        </div>
                    `;
                    chatMessages.appendChild(msgDiv);
                });
            } else {
                chatMessages.innerHTML = '<div class="message message-system">暂无历史消息，请继续对话</div>';
            }
        })
        .catch(err => {
            console.error('加载历史失败:', err);
            chatMessages.innerHTML = '<div class="message message-system">加载历史失败，请继续对话</div>';
        });
    
    showToast('会话已加载', 'success');
}

function startNewChat() {
    currentSessionId = null;
    sessionId = null;
    sessionStorage.removeItem('currentSessionId');
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="message message-ai">
                <div class="message-avatar">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <div class="message-content">
                    <p>你好！我是 <strong>Ralph Loop</strong>，你的 AI 接口测试助手。</p>
                    <p>我可以帮助你：</p>
                    <ul>
                        <li>📄 解析接口文档 (Pdf, Word, PPT)</li>
                        <li>🧪 生成接口测试用例</li>
                        <li>🔍 实时监控接口状态</li>
                        <li>💬 智能问答测试相关问题</li>
                    </ul>
                    <div class="message-time">今天</div>
                </div>
            </div>
        `;
    }
}

document.getElementById('historySessionsBtn')?.addEventListener('click', () => {
    document.getElementById('sessionsSidebar')?.classList.add('active');
    loadSessions();
});

document.getElementById('closeSessionsBtn')?.addEventListener('click', () => {
    document.getElementById('sessionsSidebar')?.classList.remove('active');
});

document.getElementById('newChatBtn')?.addEventListener('click', startNewChat);

// Click outside sidebar to close
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sessionsSidebar');
    const btn = document.getElementById('historySessionsBtn');
    if (sidebar && sidebar.classList.contains('active')) {
        if (!sidebar.contains(e.target) && !btn.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

const savedSessionId = sessionStorage.getItem('currentSessionId');
if (savedSessionId) {
    currentSessionId = savedSessionId;
}

loadDocuments();
loadMonitors();
loadDocumentsForDefect();
loadDocumentsForTestcase();
