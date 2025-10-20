// Main application JavaScript
const instructionInput = document.getElementById('instruction-input');
const executeBtn = document.getElementById('execute-btn');
const resetBtn = document.getElementById('reset-btn');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');

// Execute instruction
executeBtn.addEventListener('click', async () => {
    const instruction = instructionInput.value.trim();
    
    if (!instruction) {
        showStatus('error', 'Please enter an instruction');
        return;
    }
    
    // Disable button and show spinner
    setExecuting(true);
    showStatus('processing', 'AI is processing your instruction...');
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ instruction }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', `Completed in ${data.iterations} iteration(s)`);
            displayResults(data);
        } else {
            showStatus('error', `Error: ${data.error || 'Unknown error'}`);
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
        const response = await fetch('/api/reset', {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('success', 'Agent reset successfully');
            resultsDiv.innerHTML = '';
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
        messageEl.className = 'final-message';
        messageEl.textContent = data.message;
        resultsDiv.appendChild(messageEl);
    }
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
    statusEl.textContent = step.success ? 'Success' : 'Failed';
    
    headerEl.appendChild(numberEl);
    headerEl.appendChild(statusEl);
    
    const toolEl = document.createElement('div');
    toolEl.className = 'step-tool';
    toolEl.textContent = `Tool: ${step.tool}`;
    
    const argsEl = document.createElement('div');
    argsEl.className = 'step-args';
    argsEl.textContent = JSON.stringify(step.arguments, null, 2);
    
    stepEl.appendChild(headerEl);
    stepEl.appendChild(toolEl);
    stepEl.appendChild(argsEl);
    
    if (step.error) {
        const errorEl = document.createElement('div');
        errorEl.className = 'step-error';
        errorEl.style.color = '#721c24';
        errorEl.style.marginTop = '10px';
        errorEl.textContent = `Error: ${step.error}`;
        stepEl.appendChild(errorEl);
    } else if (step.result) {
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
            console.log('Application is healthy and connected to MCP server');
        } else {
            showStatus('error', 'MCP server is not accessible. Please ensure it is running.');
        }
    } catch (error) {
        showStatus('error', 'Failed to connect to the application');
    }
});
