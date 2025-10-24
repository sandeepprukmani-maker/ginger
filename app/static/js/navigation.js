document.addEventListener('DOMContentLoaded', () => {
    updateActiveNav();
    setupSmoothNavigation();
    
    async function checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            const statusDot = document.getElementById('connection-status');
            const connectionText = document.getElementById('connection-text');
            
            if (data.status === 'healthy') {
                statusDot.classList.remove('disconnected');
                connectionText.textContent = 'GPT-5 Enabled';
            } else {
                statusDot.classList.add('disconnected');
                connectionText.textContent = 'Disconnected';
            }
        } catch (error) {
            console.error('Health check failed:', error);
            const statusDot = document.getElementById('connection-status');
            if (statusDot) {
                statusDot.classList.add('disconnected');
            }
        }
    }
    
    checkHealth();
    setInterval(checkHealth, 30000);
});

function updateActiveNav() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        item.classList.remove('active');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            item.classList.add('active');
        }
    });
}

function setupSmoothNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', async (e) => {
            e.preventDefault();
            const href = item.getAttribute('href');
            
            if (href === window.location.pathname) {
                return;
            }
            
            const mainContent = document.querySelector('.main-content');
            if (!mainContent) return;
            
            mainContent.classList.add('page-transition');
            
            await new Promise(resolve => setTimeout(resolve, 150));
            
            try {
                const response = await fetch(href);
                const html = await response.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('.main-content');
                
                if (newContent) {
                    mainContent.innerHTML = newContent.innerHTML;
                    
                    window.history.pushState({}, '', href);
                    updateActiveNav();
                    
                    const scripts = newContent.querySelectorAll('script');
                    scripts.forEach(script => {
                        if (script.src) {
                            const newScript = document.createElement('script');
                            newScript.src = script.src;
                            document.body.appendChild(newScript);
                        } else if (script.textContent) {
                            try {
                                eval(script.textContent);
                            } catch (error) {
                                console.error('Error executing script:', error);
                            }
                        }
                    });
                    
                    await new Promise(resolve => setTimeout(resolve, 50));
                    mainContent.classList.remove('page-transition');
                }
            } catch (error) {
                console.error('Navigation error:', error);
                window.location.href = href;
            }
        });
    });
}

window.addEventListener('popstate', () => {
    location.reload();
});
