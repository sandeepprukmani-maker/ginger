let currentStories = [];

function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cursor = 'pointer';
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    messageSpan.style.flex = '1';
    
    alert.appendChild(messageSpan);
    alertContainer.appendChild(alert);
    
    alert.addEventListener('click', () => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    });
    
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

async function analyzeEpic() {
    const epicKey = document.getElementById('epicKey').value.trim();
    const confluencePageIdsInput = document.getElementById('confluencePageIds').value.trim();
    
    if (!epicKey) {
        showAlert('Please provide a Jira EPIC key', 'warning');
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
    
    console.log('Displaying EPIC summary:', epicData);
    
    if (epicData.title) {
        html += `
            <div class="mb-3">
                <h6 style="color: var(--primary-purple); margin-bottom: 0.5rem;">
                    <i class="bi bi-bookmark-fill"></i> Title
                </h6>
                <p style="margin: 0; font-size: 1.1rem;">${escapeHtml(epicData.title)}</p>
            </div>`;
    }
    
    if (epicData.description) {
        const desc = escapeHtml(epicData.description);
        const truncated = desc.length > 500 ? desc.substring(0, 500) + '...' : desc;
        html += `
            <div class="mb-3">
                <h6 style="color: var(--primary-purple); margin-bottom: 0.5rem;">
                    <i class="bi bi-file-text-fill"></i> Description
                </h6>
                <p style="margin: 0; white-space: pre-wrap;">${truncated}</p>
            </div>`;
    }
    
    const metadata = [];
    
    if (epicData.comments && epicData.comments.length > 0) {
        metadata.push(`<i class="bi bi-chat-dots-fill"></i> ${epicData.comments.length} comment(s)`);
    }
    
    if (epicData.attachments && epicData.attachments.length > 0) {
        const processedCount = epicData.attachments.filter(a => a.extracted_text).length;
        let attText = `<i class="bi bi-paperclip"></i> ${epicData.attachments.length} attachment(s)`;
        if (processedCount > 0) {
            attText += ` (${processedCount} processed)`;
        }
        metadata.push(attText);
    }
    
    if (epicData.confluence_pages && epicData.confluence_pages.length > 0) {
        metadata.push(`<i class="bi bi-journal-text"></i> ${epicData.confluence_pages.length} Confluence page(s)`);
    }
    
    if (metadata.length > 0) {
        html += `
            <div class="mb-3">
                <h6 style="color: var(--primary-purple); margin-bottom: 0.5rem;">
                    <i class="bi bi-info-circle-fill"></i> Additional Data
                </h6>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    ${metadata.map(m => `<span class="badge-pill">${m}</span>`).join('')}
                </div>
            </div>`;
    }
    
    if (!html) {
        html = '<p style="color: var(--text-muted);">No EPIC data available</p>';
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

let currentCoverageAnalysis = null;

async function analyzeCoverage() {
    const epicKey = document.getElementById('epicKey').value.trim();
    
    if (!epicKey) {
        showAlert('Please enter an EPIC key first', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/analyze-coverage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                epic_key: epicKey
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze coverage');
        }
        
        currentCoverageAnalysis = data.coverage_analysis;
        displayCoverageAnalysis(data.coverage_analysis, data.existing_issues_count);
        document.getElementById('coverageSection').style.display = 'block';
        showAlert('Coverage analysis completed successfully!', 'success');
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function displayCoverageAnalysis(analysis, existingCount) {
    const coverageSummary = document.getElementById('coverageSummary');
    let html = '';
    
    html += `<div class="mb-4">
        <p style="color: var(--text-secondary);">
            <i class="bi bi-info-circle-fill"></i> 
            Found <strong>${existingCount}</strong> existing stories/bugs linked to this EPIC
        </p>
    </div>`;
    
    const coverageData = analysis.coverage_analysis || {};
    
    if (coverageData.fully_covered && coverageData.fully_covered.length > 0) {
        html += `<div class="coverage-card coverage-full">
            <h5><i class="bi bi-check-circle-fill"></i> Fully Covered (${coverageData.fully_covered.length})</h5>`;
        coverageData.fully_covered.forEach(item => {
            html += `<div class="coverage-item">
                <strong>${escapeHtml(item.requirement)}</strong>
                <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0;">
                    Covered by: ${item.covered_by.join(', ')}
                </p>
                <p style="color: var(--text-muted); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    ${escapeHtml(item.coverage_details || '')}
                </p>
            </div>`;
        });
        html += `</div>`;
    }
    
    if (coverageData.partially_covered && coverageData.partially_covered.length > 0) {
        html += `<div class="coverage-card coverage-partial">
            <h5><i class="bi bi-exclamation-triangle-fill"></i> Partially Covered (${coverageData.partially_covered.length})</h5>`;
        coverageData.partially_covered.forEach(item => {
            html += `<div class="coverage-item">
                <strong>${escapeHtml(item.requirement)}</strong>
                <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0;">
                    Covered by: ${item.covered_by.join(', ')}
                </p>
                <p style="color: #f59e0b; margin: 0.5rem 0 0 0; font-weight: 600;">
                    Missing: ${item.missing_aspects.map(a => escapeHtml(a)).join(', ')}
                </p>
                <p style="color: var(--text-muted); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    ${escapeHtml(item.recommendation || '')}
                </p>
            </div>`;
        });
        html += `</div>`;
    }
    
    if (coverageData.not_covered && coverageData.not_covered.length > 0) {
        html += `<div class="coverage-card coverage-missing">
            <h5><i class="bi bi-x-circle-fill"></i> Not Covered (${coverageData.not_covered.length})</h5>`;
        coverageData.not_covered.forEach(item => {
            const priorityClass = `badge-priority-${item.priority || 'medium'}`;
            html += `<div class="coverage-item">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <strong style="flex: 1;">${escapeHtml(item.requirement)}</strong>
                    <span class="badge ${priorityClass}">${(item.priority || 'medium').toUpperCase()}</span>
                </div>
                <p style="color: var(--text-muted); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    ${escapeHtml(item.reason || '')}
                </p>
            </div>`;
        });
        html += `</div>`;
    }
    
    coverageSummary.innerHTML = html;
    
    if (analysis.suggested_stories && analysis.suggested_stories.length > 0) {
        displaySuggestedStories(analysis.suggested_stories);
        document.getElementById('suggestedStoriesSection').style.display = 'block';
    }
    
    if (analysis.recommendations_for_existing && analysis.recommendations_for_existing.length > 0) {
        displayExistingRecommendations(analysis.recommendations_for_existing);
        document.getElementById('existingRecommendationsSection').style.display = 'block';
    }
}

function displaySuggestedStories(stories) {
    const storiesList = document.getElementById('suggestedStoriesList');
    let html = '';
    
    stories.forEach((story, index) => {
        const priority = story.priority || 'medium';
        const priorityBadgeClass = `badge-priority-${priority}`;
        const storyType = story.story_type === 'enhancement_to_existing' ? 'Enhancement' : 'New Story';
        
        html += `
            <div class="story-card">
                <div class="story-header">
                    <input type="checkbox" class="story-checkbox" data-index="${index}" checked>
                    <div class="story-title">${escapeHtml(story.title || 'Untitled Story')}</div>
                    <div class="story-badges">
                        <span class="badge badge-info">${storyType}</span>
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
                
                ${story.addresses_requirement ? `
                <div style="background-color: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 1rem; border-radius: 6px; margin: 1rem 0;">
                    <strong style="color: #3b82f6;"><i class="bi bi-bullseye"></i> Addresses:</strong><br>
                    <span style="color: var(--text-secondary); margin-top: 0.5rem; display: block;">${escapeHtml(story.addresses_requirement)}</span>
                </div>
                ` : ''}
                
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

function displayExistingRecommendations(recommendations) {
    const recommendationsList = document.getElementById('existingRecommendationsList');
    let html = '';
    
    recommendations.forEach((rec, index) => {
        const priorityBadgeClass = `badge-priority-${rec.priority || 'medium'}`;
        
        html += `
            <div class="recommendation-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                    <h6 style="margin: 0; color: var(--primary-purple);">
                        <i class="bi bi-ticket-detailed-fill"></i> ${escapeHtml(rec.story_key)}
                    </h6>
                    <span class="badge ${priorityBadgeClass}">${(rec.priority || 'medium').toUpperCase()}</span>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <strong style="color: #ef4444;"><i class="bi bi-exclamation-circle"></i> Issue:</strong>
                    <p style="margin: 0.5rem 0 0 1.5rem; color: var(--text-secondary);">${escapeHtml(rec.current_issue)}</p>
                </div>
                
                <div>
                    <strong style="color: #10b981;"><i class="bi bi-plus-circle"></i> Recommended Additions:</strong>
                    <ul style="margin: 0.5rem 0 0 1.5rem; color: var(--text-secondary);">
                        ${rec.recommended_additions.map(add => `<li>${escapeHtml(add)}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    });
    
    recommendationsList.innerHTML = html;
}

async function approveSelectedStories() {
    const checkboxes = document.querySelectorAll('.story-checkbox:checked');
    const approvedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
    
    if (approvedIndices.length === 0) {
        showAlert('Please select at least one story to approve', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/approve-coverage-stories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                approved_indices: approvedIndices
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to approve stories');
        }
        
        currentStories = data.stories;
        displayStories(data.stories);
        document.getElementById('storiesSection').style.display = 'block';
        showAlert(`${data.approved_count} stories approved and ready for export!`, 'success');
        
        document.getElementById('storiesSection').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}
