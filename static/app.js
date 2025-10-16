let currentExecutionId = null;
let currentTestPlan = null;

function fillPrompt(text) {
    document.getElementById('promptInput').value = text;
}

async function runAutomation() {
    const prompt = document.getElementById('promptInput').value.trim();
    
    if (!prompt) {
        alert('Please enter a prompt describing what you want to automate');
        return;
    }
    
    const headless = document.getElementById('headlessMode').checked;
    const browser = document.getElementById('browserSelect').value;
    
    showLoading(true);
    
    try {
        // Convert prompt to test plan
        const convertResponse = await fetch('/api/convert-prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, browser, headless })
        });
        
        if (!convertResponse.ok) {
            throw new Error('Failed to convert prompt to test plan');
        }
        
        const { test_plan } = await convertResponse.json();
        currentTestPlan = test_plan;
        
        // Execute the test plan
        const executeResponse = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(test_plan)
        });
        
        if (!executeResponse.ok) {
            throw new Error('Failed to execute automation');
        }
        
        const result = await executeResponse.json();
        currentExecutionId = result.execution_id;
        
        // Poll for execution completion
        await pollExecution(currentExecutionId);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error running automation: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function pollExecution(executionId) {
    const maxAttempts = 60;
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`/api/executions/${executionId}`);
            const report = await response.json();
            
            if (report.status === 'completed' || report.status === 'failed') {
                displayResults(report);
                return;
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
        } catch (error) {
            console.error('Polling error:', error);
            attempts++;
        }
    }
    
    alert('Execution timeout - please check the execution manually');
}

function displayResults(report) {
    document.getElementById('resultsSection').style.display = 'block';
    
    const statusIndicator = document.getElementById('statusIndicator');
    statusIndicator.className = `status ${report.status}`;
    statusIndicator.textContent = report.status === 'completed' ? '✅ Automation Completed Successfully!' : '❌ Automation Failed';
    
    const details = document.getElementById('executionDetails');
    details.innerHTML = `
        <h3>Execution Summary</h3>
        <div class="detail-item">
            <span>Test Plan:</span>
            <span>${report.test_plan_name}</span>
        </div>
        <div class="detail-item">
            <span>Total Steps:</span>
            <span>${report.steps.length}</span>
        </div>
        <div class="detail-item">
            <span>Successful Steps:</span>
            <span>${report.steps.filter(s => s.status === 'success').length}</span>
        </div>
        <div class="detail-item">
            <span>Failed Steps:</span>
            <span>${report.steps.filter(s => s.status === 'failed').length}</span>
        </div>
        <div class="detail-item">
            <span>Duration:</span>
            <span>${calculateDuration(report.start_time, report.end_time)}</span>
        </div>
    `;
    
    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '<h3>Steps:</h3>' + report.steps.map(step => `
        <div class="step-card ${step.status}">
            <div class="step-header">
                <strong>Step ${step.step_number}: ${step.action}</strong>
                <span class="step-status ${step.status}">${step.status}</span>
            </div>
            <p>${step.description}</p>
            ${step.error_message ? `<p style="color: #dc3545; margin-top: 8px;">Error: ${step.error_message}</p>` : ''}
        </div>
    `).join('');
    
    document.querySelector('.prompt-section').style.display = 'none';
}

function calculateDuration(start, end) {
    if (!end) return 'N/A';
    const duration = Math.round((new Date(end) - new Date(start)) / 1000);
    return `${duration} seconds`;
}

async function downloadPlaywrightCode() {
    if (!currentExecutionId) return;
    
    try {
        const response = await fetch(`/api/generate-code/${currentExecutionId}`);
        const { code } = await response.json();
        
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'automation.py';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Error downloading code: ' + error.message);
    }
}

async function viewTestPlan() {
    if (!currentTestPlan) return;
    
    const blob = new Blob([JSON.stringify(currentTestPlan, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'test_plan.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function newAutomation() {
    currentExecutionId = null;
    currentTestPlan = null;
    document.getElementById('resultsSection').style.display = 'none';
    document.querySelector('.prompt-section').style.display = 'block';
    document.getElementById('promptInput').value = '';
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    document.getElementById('runButton').disabled = show;
}

// Event listeners
document.getElementById('runButton').addEventListener('click', runAutomation);
document.getElementById('downloadCodeButton').addEventListener('click', downloadPlaywrightCode);
document.getElementById('viewTestPlanButton').addEventListener('click', viewTestPlan);
document.getElementById('newAutomationButton').addEventListener('click', newAutomation);
