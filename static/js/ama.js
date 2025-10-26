let conversationHistory = [];
let currentQuestionId = 0;

document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    
    const textarea = document.getElementById('questionInput');
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
    
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

async function loadStats() {
    try {
        const response = await fetch('/api/ama/stats');
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.getElementById('projectDocsCount').textContent = data.stats.knowledge_base_size || 0;
            document.getElementById('conversationsCount').textContent = data.stats.conversations_stored || 0;
            document.getElementById('validatedCount').textContent = data.stats.validated_answers || 0;
            
            const statusIndicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            
            if (data.stats.status === 'active') {
                statusIndicator.className = 'status-indicator status-active';
                statusText.textContent = 'Active';
            } else {
                statusIndicator.className = 'status-indicator status-inactive';
                statusText.textContent = 'OAuth Not Configured';
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        return;
    }
    
    document.getElementById('chatWelcome')?.remove();
    
    addMessageToChat('user', question);
    
    questionInput.value = '';
    questionInput.style.height = 'auto';
    
    showLoading(true);
    
    const questionId = ++currentQuestionId;
    
    try {
        const response = await fetch('/api/ama/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                addMessageToChat('error', 'OAuth authentication not configured. Please set up OpenAI OAuth credentials.');
            } else {
                addMessageToChat('error', data.error || 'An error occurred');
            }
            return;
        }
        
        if (data.success) {
            addMessageToChat('assistant', data.answer, {
                questionId: questionId,
                question: question,
                confidence: data.confidence,
                validated: data.validated,
                sources: data.sources
            });
            
            conversationHistory.push({
                id: questionId,
                question: question,
                answer: data.answer,
                confidence: data.confidence,
                validated: data.validated
            });
            
            loadStats();
        } else {
            addMessageToChat('error', data.error || 'An error occurred');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('error', 'Failed to get response. Please check your connection and try again.');
    } finally {
        showLoading(false);
    }
}

function addMessageToChat(type, content, metadata = {}) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message chat-message-${type}`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-avatar message-avatar-user">
                <i class="bi bi-person-fill"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    } else if (type === 'assistant') {
        const confidenceBadge = metadata.confidence ? 
            `<span class="confidence-badge confidence-${metadata.confidence}">${metadata.confidence} confidence</span>` : '';
        
        const validatedBadge = metadata.validated ? 
            `<span class="validated-badge"><i class="bi bi-patch-check-fill"></i> Validated</span>` : '';
        
        let sourcesHtml = '';
        if (metadata.sources && metadata.sources.length > 0) {
            sourcesHtml = '<div class="message-sources"><div class="sources-header"><i class="bi bi-link-45deg"></i> Sources:</div>';
            metadata.sources.forEach(source => {
                const sourceType = source.type || 'unknown';
                const sourceTitle = source.metadata?.title || source.metadata?.source || 'Unknown';
                sourcesHtml += `<div class="source-item"><i class="bi bi-file-text"></i> ${sourceType}: ${escapeHtml(sourceTitle)}</div>`;
            });
            sourcesHtml += '</div>';
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar message-avatar-assistant">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    ${confidenceBadge}
                    ${validatedBadge}
                </div>
                <div class="message-text">${formatMessage(content)}</div>
                ${sourcesHtml}
                <div class="message-actions" data-question-id="${metadata.questionId}">
                    <button class="action-btn action-btn-accept" onclick="submitFeedback(${metadata.questionId}, 'accept')">
                        <i class="bi bi-check-circle"></i> Accept
                    </button>
                    <button class="action-btn action-btn-edit" onclick="editAnswer(${metadata.questionId})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="action-btn action-btn-reject" onclick="submitFeedback(${metadata.questionId}, 'reject')">
                        <i class="bi bi-x-circle"></i> Reject
                    </button>
                </div>
            </div>
        `;
    } else if (type === 'error') {
        messageDiv.innerHTML = `
            <div class="message-content message-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
    text = escapeHtml(text);
    text = text.replace(/\n/g, '<br>');
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function submitFeedback(questionId, feedbackType) {
    const conversation = conversationHistory.find(c => c.id === questionId);
    if (!conversation) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/ama/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: conversation.question,
                answer: conversation.answer,
                feedback_type: feedbackType
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const actionsDiv = document.querySelector(`[data-question-id="${questionId}"]`);
            if (actionsDiv) {
                actionsDiv.innerHTML = `<div class="feedback-submitted"><i class="bi bi-check-circle-fill"></i> Feedback submitted</div>`;
            }
            loadStats();
            showAlert('Feedback recorded successfully', 'success');
        } else {
            showAlert(data.error || 'Failed to record feedback', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to record feedback. Please check your connection and try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function editAnswer(questionId) {
    const conversation = conversationHistory.find(c => c.id === questionId);
    if (!conversation) {
        return;
    }
    
    const actionsDiv = document.querySelector(`[data-question-id="${questionId}"]`);
    if (!actionsDiv) {
        return;
    }
    
    const currentAnswer = conversation.answer;
    
    actionsDiv.innerHTML = `
        <div class="edit-answer-container">
            <textarea class="edit-answer-input" id="editInput${questionId}" rows="4">${escapeHtml(currentAnswer)}</textarea>
            <div class="edit-actions">
                <button class="action-btn action-btn-accept" onclick="saveEditedAnswer(${questionId})">
                    <i class="bi bi-check-circle"></i> Save
                </button>
                <button class="action-btn action-btn-reject" onclick="cancelEdit(${questionId})">
                    <i class="bi bi-x-circle"></i> Cancel
                </button>
            </div>
        </div>
    `;
}

async function saveEditedAnswer(questionId) {
    const conversation = conversationHistory.find(c => c.id === questionId);
    if (!conversation) {
        return;
    }
    
    const editInput = document.getElementById(`editInput${questionId}`);
    const correctedAnswer = editInput.value.trim();
    
    if (!correctedAnswer || correctedAnswer === conversation.answer) {
        cancelEdit(questionId);
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/ama/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: conversation.question,
                answer: conversation.answer,
                feedback_type: 'correct',
                corrected_answer: correctedAnswer
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const actionsDiv = document.querySelector(`[data-question-id="${questionId}"]`);
            if (actionsDiv) {
                actionsDiv.innerHTML = `<div class="feedback-submitted"><i class="bi bi-check-circle-fill"></i> Correction saved</div>`;
            }
            
            const messageText = actionsDiv.closest('.message-content').querySelector('.message-text');
            if (messageText) {
                messageText.innerHTML = formatMessage(correctedAnswer);
            }
            
            conversation.answer = correctedAnswer;
            
            loadStats();
            showAlert('Correction saved successfully', 'success');
        } else {
            showAlert(data.error || 'Failed to save correction', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to save correction. Please check your connection and try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function cancelEdit(questionId) {
    const conversation = conversationHistory.find(c => c.id === questionId);
    if (!conversation) {
        return;
    }
    
    const actionsDiv = document.querySelector(`[data-question-id="${questionId}"]`);
    if (actionsDiv) {
        actionsDiv.innerHTML = `
            <button class="action-btn action-btn-accept" onclick="submitFeedback(${questionId}, 'accept')">
                <i class="bi bi-check-circle"></i> Accept
            </button>
            <button class="action-btn action-btn-edit" onclick="editAnswer(${questionId})">
                <i class="bi bi-pencil"></i> Edit
            </button>
            <button class="action-btn action-btn-reject" onclick="submitFeedback(${questionId}, 'reject')">
                <i class="bi bi-x-circle"></i> Reject
            </button>
        `;
    }
}

async function indexCurrentEpic() {
    showLoading(true);
    
    try {
        const response = await fetch('/api/ama/index-epic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert(`Successfully indexed ${data.documents_added} documents from the current EPIC`, 'success');
            loadStats();
        } else {
            showAlert(data.error || 'Failed to index EPIC data', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to index EPIC data. Please check your connection and try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle-fill' : 'exclamation-triangle-fill'}"></i>
        <span>${message}</span>
    `;
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}
