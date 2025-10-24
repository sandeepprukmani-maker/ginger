let currentMode = 'headful';
let currentEngine = 'browser_use';
let isExecuting = false;

document.addEventListener('DOMContentLoaded', () => {
    const headlessBtn = document.getElementById('headless-btn');
    const headfulBtn = document.getElementById('headful-btn');
    const browserUseBtn = document.getElementById('browser-use-btn');
    const playwrightMcpBtn = document.getElementById('playwright-mcp-btn');
    const executeBtn = document.getElementById('execute-automation');
    const promptTextarea = document.getElementById('automation-prompt');
    
    if (headlessBtn) {
        headlessBtn.addEventListener('click', () => {
            currentMode = 'headless';
            headlessBtn.classList.add('active');
            headfulBtn.classList.remove('active');
        });
    }
    
    if (headfulBtn) {
        headfulBtn.addEventListener('click', () => {
            currentMode = 'headful';
            headfulBtn.classList.add('active');
            headlessBtn.classList.remove('active');
        });
    }
    
    if (browserUseBtn) {
        browserUseBtn.addEventListener('click', () => {
            currentEngine = 'browser_use';
            browserUseBtn.classList.add('active');
            playwrightMcpBtn.classList.remove('active');
        });
    }
    
    if (playwrightMcpBtn) {
        playwrightMcpBtn.addEventListener('click', () => {
            currentEngine = 'playwright_mcp';
            playwrightMcpBtn.classList.add('active');
            browserUseBtn.classList.remove('active');
        });
    }
    
    if (executeBtn) {
        executeBtn.addEventListener('click', async () => {
            if (isExecuting) return;
            
            const instruction = promptTextarea.value.trim();
            if (!instruction) {
                alert('Please enter an automation instruction');
                return;
            }
            
            isExecuting = true;
            executeBtn.disabled = true;
            executeBtn.innerHTML = '<span class="spinner"></span> Executing...';
            
            document.getElementById('generated-script').innerHTML = '<div style="color: var(--text-secondary);">Generating script...</div>';
            document.getElementById('execution-logs').innerHTML = '<div style="color: var(--text-secondary);">Executing...</div>';
            
            try {
                const headers = {
                    'Content-Type': 'application/json',
                };
                
                const apiKey = localStorage.getItem('api_key');
                if (apiKey) {
                    headers['X-API-Key'] = apiKey;
                }
                
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({
                        instruction: instruction,
                        engine: currentEngine,
                        headless: currentMode === 'headless'
                    }),
                });
                
                const data = await response.json();
                
                if (response.status === 401 || response.status === 403) {
                    document.getElementById('generated-script').innerHTML = 
                        `<div style="color: var(--error-text);">🔒 Authentication Error</div>`;
                    document.getElementById('execution-logs').innerHTML = 
                        `<div style="color: var(--error-text);">Please provide a valid API key. ${data.message || ''}</div>`;
                } else if (data.success) {
                    document.getElementById('generated-script').innerHTML = 
                        `<pre style="color: var(--success-text); margin: 0; white-space: pre-wrap; font-size: 0.85rem;">${JSON.stringify(data, null, 2)}</pre>`;
                    document.getElementById('execution-logs').innerHTML = 
                        `<div style="color: var(--success-text);">✅ Completed successfully in ${data.iterations || 0} iterations</div>`;
                } else {
                    document.getElementById('generated-script').innerHTML = 
                        `<div style="color: var(--error-text);">❌ ${data.error || 'Execution failed'}</div>`;
                    document.getElementById('execution-logs').innerHTML = 
                        `<pre style="color: var(--error-text); margin: 0; white-space: pre-wrap; font-size: 0.85rem;">${data.message || 'No details available'}</pre>`;
                }
            } catch (error) {
                console.error('Execution error:', error);
                document.getElementById('generated-script').innerHTML = 
                    `<div style="color: var(--error-text);">❌ Network error: ${error.message}</div>`;
                document.getElementById('execution-logs').innerHTML = 
                    `<div style="color: var(--error-text);">Failed to execute automation</div>`;
            } finally {
                isExecuting = false;
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<span>▶️</span> Execute Automation';
            }
        });
    }
});
