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
            
            document.getElementById('generated-script').innerHTML = '<div style="color: var(--text-secondary);">Waiting for automation to start...</div>';
            document.getElementById('execution-logs').innerHTML = '<div style="color: var(--text-secondary);">Connecting to automation server...</div>';
            
            let stepLogs = [];
            
            try {
                const apiKey = localStorage.getItem('api_key');
                
                // Use Server-Sent Events for real-time streaming
                const payload = {
                    instruction: instruction,
                    engine: currentEngine,
                    headless: currentMode === 'headless'
                };
                
                // Create SSE connection
                const url = '/api/execute/stream';
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(apiKey ? {'X-API-Key': apiKey} : {})
                    },
                    body: JSON.stringify(payload)
                });
                
                // Handle non-OK HTTP responses before entering streaming loop
                if (!response.ok) {
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = {error: 'Unknown error', message: 'Failed to get error details'};
                    }
                    
                    document.getElementById('generated-script').innerHTML = 
                        `<div style="color: var(--text-secondary);">No script generated</div>`;
                    
                    let errorMessage = '';
                    if (response.status === 401 || response.status === 403) {
                        errorMessage = '🔒 Authentication Error<br>Please provide a valid API key.';
                    } else if (response.status === 429) {
                        errorMessage = '⏱️ Rate Limit Exceeded<br>' + (errorData.message || 'Too many requests. Please try again later.');
                    } else {
                        errorMessage = `❌ ${errorData.error || 'Error'}<br>${errorData.message || 'An unexpected error occurred'}`;
                    }
                    
                    document.getElementById('execution-logs').innerHTML = 
                        `<div style="color: var(--error-text);">${errorMessage}</div>`;
                    return;
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (!line.trim() || !line.startsWith('data: ')) continue;
                        
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            // Handle different event types from SSE stream
                            if (data.type === 'start') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">${data.message || 'Starting automation...'}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'init') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">⚙️  ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'browser_init') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">🌐 ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'agent_create') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">🤖 ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'execution_start') {
                                stepLogs.push(`<div style="color: var(--text-secondary); margin: 3px 0;">▶️  ${data.data.message}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                            } else if (data.type === 'step') {
                                stepLogs.push(`<div style="color: var(--success-text); margin: 3px 0;">✓ Step ${data.data.step_number}/${data.data.total_steps}: ${data.data.action}</div>`);
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                // Auto-scroll to bottom
                                const logsElement = document.getElementById('execution-logs');
                                logsElement.scrollTop = logsElement.scrollHeight;
                            } else if (data.type === 'done') {
                                const result = data.result;
                                // Display generated Playwright code if available
                                if (result.playwright_code) {
                                    document.getElementById('generated-script').innerHTML = 
                                        `<pre style="color: var(--success-text); margin: 0; white-space: pre-wrap; font-size: 0.85rem;">${result.playwright_code}</pre>`;
                                } else {
                                    document.getElementById('generated-script').innerHTML = 
                                        `<div style="color: var(--text-secondary);">No script generated for this automation</div>`;
                                }
                                
                                // Add final summary
                                stepLogs.push(`<div style="color: var(--success-text); margin-top: 10px; font-weight: bold;">✅ Completed successfully in ${result.iterations || 0} steps</div>`);
                                if (result.final_result) {
                                    stepLogs.push(`<div style="color: var(--success-text); margin-top: 5px;">Result: ${result.final_result}</div>`);
                                }
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                break;
                            } else if (data.type === 'error') {
                                document.getElementById('generated-script').innerHTML = 
                                    `<div style="color: var(--text-secondary);">No script generated due to error</div>`;
                                
                                stepLogs.push(`<div style="color: var(--error-text); font-weight: bold; margin-top: 10px;">❌ ${data.error || 'Execution failed'}</div>`);
                                if (data.message) {
                                    stepLogs.push(`<pre style="color: var(--error-text); margin: 5px 0; white-space: pre-wrap; font-size: 0.85rem;">${data.message}</pre>`);
                                }
                                document.getElementById('execution-logs').innerHTML = stepLogs.join('');
                                break;
                            }
                        } catch (parseError) {
                            console.error('Failed to parse SSE data:', parseError);
                        }
                    }
                }
            } catch (error) {
                console.error('Execution error:', error);
                document.getElementById('generated-script').innerHTML = 
                    `<div style="color: var(--text-secondary);">No script generated due to network error</div>`;
                document.getElementById('execution-logs').innerHTML = 
                    `<div style="color: var(--error-text);">❌ Network Error<br>Failed to execute automation: ${error.message}</div>`;
            } finally {
                isExecuting = false;
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<span>▶️</span> Execute Automation';
            }
        });
    }
});
