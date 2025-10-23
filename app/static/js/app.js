const socket = io();

let currentTaskId = null;
let taskDetailModal = null;

document.addEventListener('DOMContentLoaded', function() {
    taskDetailModal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
    
    initializeSocketListeners();
    loadTaskHistory();
    loadStats();
    
    document.getElementById('taskForm').addEventListener('submit', handleTaskSubmit);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadTaskHistory();
        loadStats();
    });
    document.getElementById('downloadScriptBtn').addEventListener('click', handleDownloadScript);
    
    const headlessToggle = document.getElementById('headlessToggle');
    const headlessLabel = document.getElementById('headlessLabel');
    
    headlessToggle.addEventListener('change', function() {
        if (this.checked) {
            headlessLabel.innerHTML = '<i class="bi bi-eye-slash"></i> Headless';
        } else {
            headlessLabel.innerHTML = '<i class="bi bi-eye"></i> Headful';
        }
    });
    
    setInterval(loadStats, 10000);
});

function initializeSocketListeners() {
    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });
    
    socket.on('task_created', (data) => {
        console.log('Task created:', data);
        currentTaskId = data.task_id;
        addExecutionMessage('info', `Task #${data.task_id} created`);
        addExecutionMessage('primary', `Instruction: ${data.instruction}`);
    });
    
    socket.on('task_update', (data) => {
        console.log('Task update:', data);
        addExecutionMessage('info', `Task #${data.id} status: ${data.status}`);
        if (data.status === 'running') {
            addExecutionMessage('primary', 'Executing with browser-use AI agent...');
        }
    });
    
    socket.on('step_update', (data) => {
        console.log('Step update:', data);
        const statusClass = data.status === 'success' ? 'success' : 
                          data.status === 'healed' ? 'warning' : 
                          data.status === 'failed' ? 'danger' : 'secondary';
        
        let message = `Step ${data.step_number}: ${data.action_type}`;
        if (data.healing_source) {
            message += ` (healed via ${data.healing_source})`;
        }
        
        addExecutionMessage(statusClass, message);
    });
    
    socket.on('healing_attempt', (data) => {
        console.log('Healing attempt:', data);
        addExecutionMessage('warning', 
            `Attempting ${data.source} healing (retry ${data.retry}/${data.max_retries})...`
        );
    });
    
    socket.on('healing_fallback', (data) => {
        console.log('Healing fallback:', data);
        addExecutionMessage('info', 
            `Falling back from ${data.from} to ${data.to} healing`
        );
    });
    
    socket.on('healing_event', (data) => {
        console.log('Healing event:', data);
        const statusClass = data.success ? 'success' : 'danger';
        const statusText = data.success ? 'successful' : 'failed';
        addExecutionMessage(statusClass, 
            `${data.healing_source} healing ${statusText} (${data.healing_time?.toFixed(2)}s)`
        );
    });
    
    socket.on('task_complete', (data) => {
        console.log('Task complete:', data);
        if (data.success) {
            addExecutionMessage('success', `Task #${data.task_id} completed successfully!`);
            if (data.script_path) {
                addExecutionMessage('info', `Generated Playwright script: ${data.script_path}`);
            }
        } else {
            addExecutionMessage('danger', `Task #${data.task_id} failed: ${data.error}`);
        }
        
        loadTaskHistory();
        loadStats();
        
        document.getElementById('executeBtn').disabled = false;
        document.getElementById('executeBtn').innerHTML = 
            '<i class="bi bi-lightning-charge"></i> Execute with Healing';
    });
    
    socket.on('task_error', (data) => {
        console.error('Task error:', data);
        addExecutionMessage('danger', `Error in task #${data.task_id}: ${data.error}`);
        
        document.getElementById('executeBtn').disabled = false;
        document.getElementById('executeBtn').innerHTML = 
            '<i class="bi bi-lightning-charge"></i> Execute with Healing';
    });
    
    socket.on('error', (data) => {
        console.error('Server error:', data);
        addExecutionMessage('danger', `Error: ${data.message}`);
    });
}

function updateConnectionStatus(connected) {
    const statusBadge = document.getElementById('connectionStatus');
    if (connected) {
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'Connected';
    } else {
        statusBadge.className = 'badge bg-danger';
        statusBadge.textContent = 'Disconnected';
    }
}

function handleTaskSubmit(e) {
    e.preventDefault();
    
    const instruction = document.getElementById('instruction').value.trim();
    const headless = document.getElementById('headlessToggle').checked;
    
    if (!instruction) {
        alert('Please enter an instruction');
        return;
    }
    
    clearExecutionMonitor();
    
    socket.emit('execute_task', { 
        instruction: instruction,
        headless: headless
    });
    
    document.getElementById('executeBtn').disabled = true;
    document.getElementById('executeBtn').innerHTML = 
        '<span class="spinner-border spinner-border-sm me-2"></span>Executing...';
}

function clearExecutionMonitor() {
    const monitor = document.getElementById('executionMonitor');
    monitor.innerHTML = '';
}

function addExecutionMessage(type, message) {
    const monitor = document.getElementById('executionMonitor');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type} mb-2 py-2`;
    messageDiv.innerHTML = `
        <small class="text-muted">${new Date().toLocaleTimeString()}</small> - ${message}
    `;
    
    monitor.appendChild(messageDiv);
    monitor.scrollTop = monitor.scrollHeight;
}

async function loadTaskHistory() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        if (data.success) {
            renderTaskHistory(data.tasks);
        } else {
            console.error('Failed to load tasks:', data.error);
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function renderTaskHistory(tasks) {
    const tbody = document.getElementById('taskHistory');
    
    if (tasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No tasks yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = tasks.map(task => {
        const statusBadge = getStatusBadge(task.status);
        const createdAt = new Date(task.created_at).toLocaleString();
        
        return `
            <tr onclick="showTaskDetail(${task.id})">
                <td>${task.id}</td>
                <td>
                    <div class="text-truncate" style="max-width: 300px;" title="${task.instruction}">
                        ${task.instruction}
                    </div>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <span class="badge bg-info">${task.successful_steps}/${task.total_steps}</span>
                </td>
                <td>
                    ${task.healed_steps > 0 ? `<span class="badge bg-warning">${task.healed_steps}</span>` : '-'}
                </td>
                <td><small>${createdAt}</small></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); showTaskDetail(${task.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-secondary">Pending</span>',
        'running': '<span class="badge bg-primary">Running</span>',
        'completed': '<span class="badge bg-success">Completed</span>',
        'failed': '<span class="badge bg-danger">Failed</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
}

async function showTaskDetail(taskId) {
    currentTaskId = taskId;
    
    const modalBody = document.getElementById('taskDetailContent');
    modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    taskDetailModal.show();
    
    try {
        const [taskResponse, logsResponse, healingResponse] = await Promise.all([
            fetch(`/api/tasks/${taskId}`),
            fetch(`/api/tasks/${taskId}/logs`),
            fetch(`/api/tasks/${taskId}/healing`)
        ]);
        
        const taskData = await taskResponse.json();
        const logsData = await logsResponse.json();
        const healingData = await healingResponse.json();
        
        if (taskData.success) {
            renderTaskDetail(taskData.task, logsData.logs || [], healingData.healing_events || []);
        } else {
            modalBody.innerHTML = '<div class="alert alert-danger">Failed to load task details</div>';
        }
    } catch (error) {
        console.error('Error loading task details:', error);
        modalBody.innerHTML = '<div class="alert alert-danger">Error loading task details</div>';
    }
}

function renderTaskDetail(task, logs, healingEvents) {
    const modalBody = document.getElementById('taskDetailContent');
    
    const html = `
        <div class="mb-3">
            <h6>Task #${task.id}</h6>
            <p class="mb-2"><strong>Instruction:</strong> ${task.instruction}</p>
            <p class="mb-2"><strong>Status:</strong> ${getStatusBadge(task.status)}</p>
            <p class="mb-2"><strong>Created:</strong> ${new Date(task.created_at).toLocaleString()}</p>
            ${task.completed_at ? `<p class="mb-2"><strong>Completed:</strong> ${new Date(task.completed_at).toLocaleString()}</p>` : ''}
            ${task.error_message ? `<p class="mb-2"><strong>Error:</strong> <span class="text-danger">${task.error_message}</span></p>` : ''}
        </div>
        
        <div class="mb-3">
            <h6>Progress</h6>
            <div class="row">
                <div class="col-4 text-center">
                    <div class="h4">${task.total_steps}</div>
                    <small class="text-muted">Total Steps</small>
                </div>
                <div class="col-4 text-center">
                    <div class="h4 text-success">${task.successful_steps}</div>
                    <small class="text-muted">Successful</small>
                </div>
                <div class="col-4 text-center">
                    <div class="h4 text-warning">${task.healed_steps}</div>
                    <small class="text-muted">Healed</small>
                </div>
            </div>
        </div>
        
        ${logs.length > 0 ? `
            <div class="mb-3">
                <h6>Action Logs</h6>
                ${logs.map(log => `
                    <div class="action-log-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <span class="step-number">Step ${log.step_number}</span>
                                <span class="badge bg-secondary ms-2">${log.action_type}</span>
                                ${log.healing_source ? `<span class="badge bg-warning ms-1">Healed via ${log.healing_source}</span>` : ''}
                            </div>
                            <span class="badge ${log.status === 'success' || log.status === 'healed' ? 'bg-success' : 'bg-danger'}">
                                ${log.status}
                            </span>
                        </div>
                        ${log.url ? `<div class="mt-1"><small class="text-muted">URL: ${log.url}</small></div>` : ''}
                        ${log.error_message ? `<div class="mt-1 text-danger"><small>${log.error_message}</small></div>` : ''}
                    </div>
                `).join('')}
            </div>
        ` : ''}
        
        ${healingEvents.length > 0 ? `
            <div class="mb-3">
                <h6>Healing Events</h6>
                ${healingEvents.map(event => `
                    <div class="healing-event ${event.success ? 'success' : 'failed'}">
                        <div class="d-flex justify-content-between">
                            <strong>${event.healing_source}</strong>
                            <span class="badge ${event.success ? 'bg-success' : 'bg-danger'}">
                                ${event.success ? 'Success' : 'Failed'}
                            </span>
                        </div>
                        <small class="text-muted">
                            Time: ${event.healing_time?.toFixed(2)}s | 
                            ${new Date(event.timestamp).toLocaleString()}
                        </small>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
    
    modalBody.innerHTML = html;
}

async function handleDownloadScript() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/tasks/${currentTaskId}/generate-script`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = `/api/tasks/${currentTaskId}/download-script`;
        } else {
            alert('Failed to generate script: ' + data.error);
        }
    } catch (error) {
        console.error('Error downloading script:', error);
        alert('Error downloading script');
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalTasks').textContent = data.stats.tasks.total;
            document.getElementById('completedTasks').textContent = data.stats.tasks.completed;
            
            const totalHealed = data.stats.healing.browser_use + data.stats.healing.mcp;
            document.getElementById('healedSteps').textContent = totalHealed;
            document.getElementById('totalHealings').textContent = data.stats.healing.total_events;
            
            document.getElementById('browserUseCount').textContent = data.stats.healing.browser_use;
            document.getElementById('mcpCount').textContent = data.stats.healing.mcp;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}
