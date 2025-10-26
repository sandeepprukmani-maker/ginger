let currentStories = [];

function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

async function analyzeEpic() {
    const epicKey = document.getElementById('epicKey').value.trim();
    const manualText = document.getElementById('manualText').value.trim();
    const confluencePageIdsInput = document.getElementById('confluencePageIds').value.trim();
    
    if (!epicKey && !manualText) {
        showAlert('Please provide either a Jira EPIC key or manual text', 'warning');
        return;
    }
    
    const confluencePageIds = confluencePageIdsInput 
        ? confluencePageIdsInput.split(',').map(id => id.trim()).filter(id => id)
        : [];
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/analyze-epic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                epic_key: epicKey,
                manual_text: manualText,
                confluence_page_ids: confluencePageIds
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze EPIC');
        }
        
        displayEpicSummary(data.epic_data);
        document.getElementById('epicSummary').style.display = 'block';
        document.getElementById('conversationSection').style.display = 'block';
        showAlert('EPIC analyzed successfully! Review the summary and generate stories.', 'success');
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function displayEpicSummary(epicData) {
    const summaryContent = document.getElementById('epicSummaryContent');
    let html = '';
    
    if (epicData.title) {
        html += `<h6><strong>Title:</strong> ${escapeHtml(epicData.title)}</h6>`;
    }
    
    if (epicData.description) {
        html += `<p><strong>Description:</strong><br>${escapeHtml(epicData.description).substring(0, 500)}${epicData.description.length > 500 ? '...' : ''}</p>`;
    }
    
    if (epicData.comments && epicData.comments.length > 0) {
        html += `<p><strong>Comments:</strong> ${epicData.comments.length} comment(s)</p>`;
    }
    
    if (epicData.attachments && epicData.attachments.length > 0) {
        const processedCount = epicData.attachments.filter(a => a.extracted_text).length;
        html += `<p><strong>Attachments:</strong> ${epicData.attachments.length} file(s)`;
        if (processedCount > 0) {
            html += ` (${processedCount} processed)`;
        }
        html += `</p>`;
    }
    
    if (epicData.confluence_pages && epicData.confluence_pages.length > 0) {
        html += `<p><strong>Confluence Pages:</strong> ${epicData.confluence_pages.length} page(s) loaded</p>`;
    }
    
    summaryContent.innerHTML = html;
}

async function generateStories() {
    const additionalContext = document.getElementById('additionalContext').value.trim();
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/generate-stories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                additional_context: additionalContext
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate stories');
        }
        
        currentStories = data.stories;
        displayStories(data.stories);
        document.getElementById('storiesSection').style.display = 'block';
        showAlert(`Successfully generated ${data.stories.length} user stories!`, 'success');
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function displayStories(stories) {
    const storiesList = document.getElementById('storiesList');
    
    if (!stories || stories.length === 0) {
        storiesList.innerHTML = '<p style="color: var(--text-muted);">No stories generated yet.</p>';
        return;
    }
    
    let html = '';
    
    stories.forEach((story, index) => {
        const priority = story.priority || 'medium';
        const priorityBadgeClass = `badge-priority-${priority}`;
        
        html += `
            <div class="story-card" id="story-${index}">
                <div class="story-header">
                    <div class="story-title">${escapeHtml(story.title || 'Untitled Story')}</div>
                    <div class="story-badges">
                        <span class="badge badge-points">
                            <i class="bi bi-speedometer2"></i> ${story.story_points || 'TBD'} pts
                        </span>
                        <span class="badge ${priorityBadgeClass}">
                            ${priority.toUpperCase()}
                        </span>
                    </div>
                </div>
                
                <div class="story-description">
                    ${escapeHtml(story.description || '')}
                </div>
                
                ${story.reasoning ? `
                <div style="background-color: rgba(124, 58, 237, 0.1); border-left: 3px solid var(--primary-purple); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
                    <strong style="color: var(--primary-purple);"><i class="bi bi-info-circle"></i> Reasoning:</strong><br>
                    <span style="color: var(--text-secondary); margin-top: 0.5rem; display: block;">${escapeHtml(story.reasoning)}</span>
                </div>
                ` : ''}
                
                <div class="criteria-section">
                    <h6><i class="bi bi-code-slash"></i> Developer Acceptance Criteria</h6>
                    <ul class="criteria-list">
                        ${(story.developer_criteria || []).map(c => `<li>${escapeHtml(c)}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="criteria-section">
                    <h6><i class="bi bi-clipboard-check"></i> QA Acceptance Criteria</h6>
                    <ul class="criteria-list">
                        ${(story.qa_criteria || []).map(c => `<li>${escapeHtml(c)}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    });
    
    storiesList.innerHTML = html;
}

function editStory(index) {
    showAlert('Story editing feature - would open a modal to edit story details', 'info');
}

async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        showAlert('Please enter a question', 'warning');
        return;
    }
    
    addMessageToConversation('user', question);
    questionInput.value = '';
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/ask-clarification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get answer');
        }
        
        addMessageToConversation('ai', data.answer);
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function addMessageToConversation(sender, message) {
    const conversationHistory = document.getElementById('conversationHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `conversation-message ${sender}`;
    messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'EpicMind'}:</strong> ${escapeHtml(message)}`;
    conversationHistory.appendChild(messageDiv);
    conversationHistory.scrollTop = conversationHistory.scrollHeight;
}

async function exportStories(format) {
    showLoading(true);
    
    try {
        const response = await fetch('/api/export-stories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: format
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to export stories');
        }
        
        if (format === 'json') {
            downloadFile('user-stories.json', JSON.stringify(data.data, null, 2), 'application/json');
        } else if (format === 'text') {
            downloadFile('user-stories.txt', data.data, 'text/plain');
        }
        
        showAlert('Stories exported successfully!', 'success');
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

document.getElementById('questionInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        askQuestion();
    }
});
