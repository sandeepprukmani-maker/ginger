// Main application JavaScript
const instructionInput = document.getElementById('instruction-input');
const executeBtn = document.getElementById('execute-btn');
const resetBtn = document.getElementById('reset-btn');
const engineSelect = document.getElementById('engine-select');
const headlessToggle = document.getElementById('headless-toggle');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const engineInfo = document.getElementById('engine-info');

let lastExecution = null;

// Execute instruction
executeBtn.addEventListener('click', async () => {
    const instruction = instructionInput.value.trim();
    
    if (!instruction) {
        showStatus('error', 'Please enter an instruction');
        return;
    }
    
    const engineMode = engineSelect.value;
    const headless = headlessToggle.checked;
    
    setExecuting(true);
    showStatus('processing', 'AI is processing your instruction...');
    resultsDiv.innerHTML = '';
    engineInfo.style.display = 'none';
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                instruction,
                engine_mode: engineMode,
                headless: headless
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', data.message || 'Task completed successfully');
            displayEngineInfo(data);
            displayResults(data);
            lastExecution = {
                instruction: instruction,
                steps: data.steps
            };
            showExportButton();
        } else {
            showStatus('error', `Error: ${data.error || 'Unknown error'}`);
            if (data.engine_used) {
                displayEngineInfo(data);
            }
            if (data.steps && data.steps.length > 0) {
                displayResults(data);
            }
        }
        
    } catch (error) {
        showStatus('error', `Failed to execute: ${error.message}`);
    } finally {
        setExecuting(false);
    }
});

// Reset agent
resetBtn.addEventListener('click', async () => {
    if (!confirm('Reset the agent? This will clear the conversation history.')) {
        return;
    }
    
    try {
        const engineMode = engineSelect.value === 'auto' ? null : engineSelect.value;
        
        const response = await fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ engine_mode: engineMode }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', 'Agent reset successfully');
            resultsDiv.innerHTML = '';
            engineInfo.style.display = 'none';
            instructionInput.value = '';
        } else {
            showStatus('error', `Failed to reset: ${data.error}`);
        }
        
    } catch (error) {
        showStatus('error', `Failed to reset: ${error.message}`);
    }
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

function displayEngineInfo(data) {
    if (!data.engine_used) return;
    
    const icon = data.engine_used === 'browser-use' ? '🚀' : '🎭';
    const engineName = data.engine_used === 'browser-use' ? 'Browser-use' : 'Playwright MCP';
    let infoHTML = `${icon} <strong>Engine used:</strong> ${engineName}`;
    
    if (data.fallback_occurred) {
        infoHTML += ` <span style="color: #f59e0b; font-weight: 600;">(⚠️ Fallback occurred)</span>`;
    }
    
    engineInfo.innerHTML = infoHTML;
    engineInfo.style.display = 'block';
}

function displayResults(data) {
    const steps = data.steps || [];
    
    steps.forEach((step, index) => {
        const stepEl = createStepElement(step, step.step_number || index + 1);
        resultsDiv.appendChild(stepEl);
    });
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
    statusEl.className = `step-status ${step.success !== false ? 'success' : 'error'}`;
    statusEl.textContent = step.success !== false ? 'Success' : 'Failed';
    
    headerEl.appendChild(numberEl);
    headerEl.appendChild(statusEl);
    
    const toolEl = document.createElement('div');
    toolEl.className = 'step-tool';
    toolEl.textContent = `Tool: ${step.tool || 'unknown'}`;
    
    stepEl.appendChild(headerEl);
    stepEl.appendChild(toolEl);
    
    if (step.arguments && Object.keys(step.arguments).length > 0) {
        const argsEl = document.createElement('div');
        argsEl.className = 'step-args';
        argsEl.textContent = JSON.stringify(step.arguments, null, 2);
        stepEl.appendChild(argsEl);
    }
    
    if (step.error) {
        const errorEl = document.createElement('div');
        errorEl.className = 'step-error';
        errorEl.style.color = '#721c24';
        errorEl.style.marginTop = '10px';
        errorEl.textContent = `Error: ${step.error}`;
        stepEl.appendChild(errorEl);
    } else if (step.result && Object.keys(step.result).length > 0) {
        const resultEl = document.createElement('details');
        resultEl.style.marginTop = '10px';
        
        const summary = document.createElement('summary');
        summary.textContent = 'View Result';
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
        
        const resultText = typeof step.result === 'string' ? step.result : JSON.stringify(step.result, null, 2);
        resultContent.textContent = resultText;
        
        resultEl.appendChild(summary);
        resultEl.appendChild(resultContent);
        stepEl.appendChild(resultEl);
    }
    
    return stepEl;
}

function showExportButton() {
    if (document.getElementById('export-btn')) return;
    
    const buttonGroup = document.querySelector('.button-group');
    const exportBtn = document.createElement('button');
    exportBtn.id = 'export-btn';
    exportBtn.className = 'btn btn-export';
    exportBtn.textContent = 'Export as Playwright';
    exportBtn.style.backgroundColor = '#10b981';
    
    exportBtn.addEventListener('click', async () => {
        if (!lastExecution) {
            showStatus('error', 'No execution to export');
            return;
        }
        
        try {
            const response = await fetch('/api/export-playwright', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(lastExecution),
            });
            
            const data = await response.json();
            
            if (data.success) {
                showExportModal(data.playwright_code, data.json_export);
            } else {
                showStatus('error', `Export failed: ${data.error}`);
            }
            
        } catch (error) {
            showStatus('error', `Export failed: ${error.message}`);
        }
    });
    
    buttonGroup.appendChild(exportBtn);
}

function showExportModal(playwrightCode, jsonExport) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
    
    const content = document.createElement('div');
    content.style.cssText = 'background: white; padding: 30px; border-radius: 12px; max-width: 800px; max-height: 80vh; overflow: auto; width: 90%;';
    
    content.innerHTML = `
        <h2 style="margin-top: 0; color: #667eea;">Export Options</h2>
        
        <div style="margin-bottom: 20px;">
            <h3 style="color: #333;">Playwright Test Code:</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.85rem;">${escapeHtml(playwrightCode)}</pre>
            <button id="copy-code-btn" style="margin-top: 10px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">Copy Code</button>
            <button id="download-code-btn" style="margin-top: 10px; margin-left: 10px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">Download .spec.ts</button>
        </div>
        
        <div style="margin-bottom: 20px;">
            <h3 style="color: #333;">JSON Export (for replay):</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.85rem;">${escapeHtml(JSON.stringify(jsonExport, null, 2))}</pre>
            <button id="download-json-btn" style="margin-top: 10px; padding: 10px 20px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer;">Download JSON</button>
        </div>
        
        <button id="close-modal-btn" style="padding: 10px 20px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer;">Close</button>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    document.getElementById('copy-code-btn').addEventListener('click', () => {
        navigator.clipboard.writeText(playwrightCode);
        showStatus('success', 'Code copied to clipboard!');
    });
    
    document.getElementById('download-code-btn').addEventListener('click', () => {
        downloadFile('automation.spec.ts', playwrightCode);
        showStatus('success', 'Playwright code downloaded!');
    });
    
    document.getElementById('download-json-btn').addEventListener('click', () => {
        downloadFile('automation-steps.json', JSON.stringify(jsonExport, null, 2));
        showStatus('success', 'JSON export downloaded!');
    });
    
    document.getElementById('close-modal-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/engines');
        const data = await response.json();
        
        if (data.success && data.engines) {
            console.log('Available engines:', data.engines.map(e => e.name).join(', '));
        }
        
        const healthResponse = await fetch('/health');
        const healthData = await healthResponse.json();
        
        if (healthData.status === 'healthy') {
            console.log('Application is ready');
        } else {
            showStatus('error', 'Server error. Please refresh the page.');
        }
    } catch (error) {
        showStatus('error', 'Failed to connect to the application');
    }
});
