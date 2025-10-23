// Main application JavaScript
const instructionInput = document.getElementById('instruction-input');
const executeBtn = document.getElementById('execute-btn');
const resetBtn = document.getElementById('reset-btn');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const engineSelect = document.getElementById('engine-select');
const headlessToggle = document.getElementById('headless-toggle');
const statusBadge = document.getElementById('status-badge');
const currentEngineDisplay = document.getElementById('current-engine');
const currentModeDisplay = document.getElementById('current-mode');

// Update footer display when engine or mode changes
function updateFooterDisplay() {
    const engineText = engineSelect.value === 'browser_use' ? 'Browser-Use' : 'Playwright MCP';
    const modeText = headlessToggle.checked ? 'Headless' : 'Headful';
    
    currentEngineDisplay.textContent = engineText;
    currentModeDisplay.textContent = modeText;
}

// Initialize
engineSelect.addEventListener('change', updateFooterDisplay);
headlessToggle.addEventListener('change', updateFooterDisplay);
updateFooterDisplay();

// Execute instruction
executeBtn.addEventListener('click', async () => {
    const instruction = instructionInput.value.trim();
    const engine = engineSelect.value;
    const headless = headlessToggle.checked;
    
    if (!instruction) {
        showStatus('error', 'Please enter an instruction');
        return;
    }
    
    // Disable button and show spinner
    setExecuting(true);
    showStatus('processing', 'AI is processing your instruction...');
    showStatusBadge('running', 'Processing...');
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                instruction,
                engine,
                headless
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', `✅ Completed in ${data.iterations} iteration(s) using ${data.engine}`);
            showStatusBadge('success', 'Completed');
            displayResults(data);
        } else {
            showStatus('error', `❌ Error: ${data.error || 'Unknown error'}`);
            showStatusBadge('error', 'Failed');
            if (data.steps && data.steps.length > 0) {
                displayResults(data);
            }
        }
        
    } catch (error) {
        showStatus('error', `❌ Failed to execute: ${error.message}`);
        showStatusBadge('error', 'Failed');
    } finally {
        setExecuting(false);
    }
});

// Reset agent
resetBtn.addEventListener('click', async () => {
    if (!confirm('Reset the agent? This will clear the conversation history and browser state.')) {
        return;
    }
    
    const engine = engineSelect.value;
    
    try {
        const response = await fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ engine }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', '✅ Agent reset successfully');
            showStatusBadge('', '');
            resultsDiv.innerHTML = '<div class="empty-state"><div class="empty-icon">🚀</div><p>Enter an instruction and click Execute to begin automation</p></div>';
            instructionInput.value = '';
        } else {
            showStatus('error', `❌ Failed to reset: ${data.error}`);
        }
        
    } catch (error) {
        showStatus('error', `❌ Failed to reset: ${error.message}`);
    }
});

// Example buttons
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        instructionInput.value = btn.dataset.instruction;
        instructionInput.focus();
    });
});

// Allow Enter key to execute (Shift+Enter for new line)
instructionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executeBtn.click();
    }
});

// Helper functions
function setExecuting(executing) {
    executeBtn.disabled = executing;
    const btnText = executeBtn.querySelector('.btn-text');
    const spinner = executeBtn.querySelector('.spinner');
    
    if (executing) {
        btnText.textContent = 'Executing...';
        spinner.style.display = 'inline-block';
    } else {
        btnText.textContent = 'Execute';
        spinner.style.display = 'none';
    }
}

function showStatus(type, message) {
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
}

function showStatusBadge(type, text) {
    statusBadge.className = `status-badge ${type}`;
    statusBadge.textContent = text;
    statusBadge.style.display = text ? 'block' : 'none';
}

function displayResults(data) {
    const steps = data.steps || [];
    
    // Display steps
    steps.forEach((step, index) => {
        const stepEl = createStepElement(step, index + 1);
        resultsDiv.appendChild(stepEl);
    });
    
    // Display final message if available
    if (data.message) {
        const messageEl = document.createElement('div');
        messageEl.style.cssText = 'background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 16px; border-radius: 8px; margin-top: 16px; font-weight: 500; color: #0c4a6e;';
        messageEl.innerHTML = `<strong>Final Result:</strong> ${data.message}`;
        resultsDiv.appendChild(messageEl);
    }
    
    // Display engine info
    const engineInfo = document.createElement('div');
    engineInfo.style.cssText = 'margin-top: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px; font-size: 0.9rem; color: #666;';
    engineInfo.innerHTML = `<strong>Engine:</strong> ${data.engine || 'unknown'} | <strong>Mode:</strong> ${data.headless ? 'Headless' : 'Headful'}`;
    resultsDiv.appendChild(engineInfo);
}

function createStepElement(step, number) {
    const stepEl = document.createElement('div');
    stepEl.className = 'step';
    
    const headerEl = document.createElement('div');
    headerEl.className = 'step-header';
    
    const numberEl = document.createElement('span');
    numberEl.className = 'step-number';
    numberEl.textContent = `Step ${number}`;
    
    const statusEl = document.createElement('span');
    statusEl.className = `step-status ${step.success ? 'success' : 'error'}`;
    statusEl.textContent = step.success ? '✓ Success' : '✗ Failed';
    
    headerEl.appendChild(numberEl);
    headerEl.appendChild(statusEl);
    
    const toolEl = document.createElement('div');
    toolEl.className = 'step-tool';
    toolEl.textContent = `🔧 Tool: ${step.tool}`;
    
    const argsEl = document.createElement('div');
    argsEl.className = 'step-args';
    argsEl.textContent = JSON.stringify(step.arguments, null, 2);
    
    stepEl.appendChild(headerEl);
    stepEl.appendChild(toolEl);
    stepEl.appendChild(argsEl);
    
    if (step.error) {
        const errorEl = document.createElement('div');
        errorEl.className = 'step-error';
        errorEl.textContent = `❌ Error: ${step.error}`;
        stepEl.appendChild(errorEl);
    } else if (step.result) {
        const resultEl = document.createElement('details');
        resultEl.style.marginTop = '10px';
        
        const summary = document.createElement('summary');
        summary.textContent = '📄 View Result';
        summary.style.cursor = 'pointer';
        summary.style.color = '#667eea';
        summary.style.fontWeight = '600';
        
        const resultContent = document.createElement('pre');
        resultContent.style.background = '#f8f9fa';
        resultContent.style.padding = '10px';
        resultContent.style.borderRadius = '6px';
        resultContent.style.marginTop = '10px';
        resultContent.style.fontSize = '0.85rem';
        resultContent.style.overflow = 'auto';
        resultContent.textContent = JSON.stringify(step.result, null, 2);
        
        resultEl.appendChild(summary);
        resultEl.appendChild(resultContent);
        stepEl.appendChild(resultEl);
    }
    
    return stepEl;
}

// Check health on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('Application is healthy and ready');
        } else {
            showStatus('error', 'Server error. Please refresh the page.');
        }
    } catch (error) {
        showStatus('error', 'Failed to connect to the application');
    }
});
