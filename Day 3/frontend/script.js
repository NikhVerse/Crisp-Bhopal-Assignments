// Configuration
const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8000';

// State Management
let chatHistory = [];
let isUploading = false;
let isProcessingChat = false;
let isConnected = false;
let checkStatusInterval = null;

// DOM Elements
const apiStatusDot = document.getElementById('api-status-dot');
const apiStatusText = document.getElementById('api-status-text');
const btnClearChat = document.getElementById('btn-clear-chat');
const btnResetAll = document.getElementById('btn-reset-all');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadProgressContainer = document.getElementById('upload-progress-container');
const progressFilename = document.getElementById('progress-filename');
const progressPercentage = document.getElementById('progress-percentage');
const progressBarFill = document.getElementById('progress-bar-fill');
const uploadStatusSubtext = document.getElementById('upload-status-subtext');
const activeFileContainer = document.getElementById('active-file-container');
const activeFilename = document.getElementById('active-filename');
const activeFileMeta = document.getElementById('active-file-meta');
const btnRemoveFile = document.getElementById('btn-remove-file');
const chatMessagesContainer = document.getElementById('chat-messages-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const toastContainer = document.getElementById('toast-container');

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkAPIStatus();
    // Periodically monitor backend status
    checkStatusInterval = setInterval(checkAPIStatus, 5000);
});

// Setup Event Listeners
function setupEventListeners() {
    // Textarea auto-grow
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight - 4) + 'px';
    });

    // Handle shift+enter to add newline, enter to send
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Chat submit
    chatForm.addEventListener('submit', handleChatSubmit);

    // File Drag and Drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });

    // Action buttons
    btnClearChat.addEventListener('click', clearChatUI);
    btnResetAll.addEventListener('click', resetApplication);
    btnRemoveFile.addEventListener('click', resetApplication);
}

// Check Backend API Health Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) throw new Error('API unstable');
        const data = await response.json();
        
        setConnectionStatus(true);
        
        // Update UI state based on database content
        if (data.pdf_uploaded) {
            if (!activeFileContainer.classList.contains('hidden') === false) {
                // If backend has a PDF loaded, but frontend is not showing it
                showActiveFileState('Loaded PDF Reference Document', 'Vector store active');
                enableChat(true);
            }
        } else {
            if (activeFileContainer.classList.contains('hidden') === false) {
                // If backend cleared PDF, but frontend is showing active file
                showUploadState();
                enableChat(false);
            }
        }
    } catch (error) {
        console.error('Connection health check failed:', error);
        setConnectionStatus(false);
    }
}

// Set Network Status State
function setConnectionStatus(connected) {
    isConnected = connected;
    if (connected) {
        apiStatusDot.className = 'status-dot connected';
        apiStatusText.textContent = 'API Connected';
        // Enable file input if not actively uploading
        if (!isUploading) {
            fileInput.disabled = false;
            dropZone.style.pointerEvents = 'auto';
            dropZone.style.opacity = '1';
        }
    } else {
        apiStatusDot.className = 'status-dot disconnected';
        apiStatusText.textContent = 'Offline';
        // Disable file upload and chat if offline
        fileInput.disabled = true;
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.5';
        enableChat(false);
    }
}

// File Selection Handler
function handleFileSelection(file) {
    if (!isConnected) {
        showToast('Error', 'API server is offline. Cannot upload file.', 'error');
        return;
    }
    if (isUploading) {
        showToast('Info', 'Another upload is in progress.', 'info');
        return;
    }

    // Validate PDF
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Invalid File', 'Please upload a PDF document.', 'error');
        return;
    }

    uploadFile(file);
}

// Upload File via XMLHttpRequest (to support progress bar)
function uploadFile(file) {
    isUploading = true;
    showUploadProgress(file.name);
    enableChat(false);
    
    // Disable inputs
    fileInput.disabled = true;
    dropZone.classList.add('disabled');

    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            updateProgressBar(percentComplete);
            if (percentComplete === 100) {
                uploadStatusSubtext.textContent = 'Processing PDF & generating embeddings...';
            }
        }
    });

    // Handle upload completion
    xhr.addEventListener('load', () => {
        isUploading = false;
        fileInput.disabled = false;
        dropZone.classList.remove('disabled');

        if (xhr.status === 200) {
            try {
                const response = JSON.parse(xhr.responseText);
                showToast('Success', 'PDF vectorized successfully!', 'success');
                showActiveFileState(response.filename, `${response.chunks_count} chunks generated`);
                enableChat(true);
                clearChatUI(); // Clear UI for the new PDF
            } catch (err) {
                showToast('Error', 'Failed to parse upload response.', 'error');
                showUploadState();
            }
        } else {
            let errorMsg = 'Failed to upload PDF.';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMsg = response.detail || errorMsg;
            } catch (err) {}
            showToast('Upload Error', errorMsg, 'error');
            showUploadState();
        }
    });

    // Handle connection failures
    xhr.addEventListener('error', () => {
        isUploading = false;
        fileInput.disabled = false;
        dropZone.classList.remove('disabled');
        showToast('Connection Error', 'Network error during upload.', 'error');
        showUploadState();
    });

    xhr.open('POST', `${API_BASE}/upload`, true);
    xhr.send(formData);
}

// UI States
function showUploadProgress(filename) {
    dropZone.classList.add('hidden');
    activeFileContainer.classList.add('hidden');
    uploadProgressContainer.classList.remove('hidden');
    progressFilename.textContent = filename;
    updateProgressBar(0);
    uploadStatusSubtext.textContent = 'Uploading file...';
}

function updateProgressBar(percentage) {
    progressPercentage.textContent = `${percentage}%`;
    progressBarFill.style.width = `${percentage}%`;
}

function showActiveFileState(filename, subtext) {
    uploadProgressContainer.classList.add('hidden');
    dropZone.classList.add('hidden');
    activeFileContainer.classList.remove('hidden');
    activeFilename.textContent = filename;
    activeFileMeta.textContent = subtext;
}

function showUploadState() {
    uploadProgressContainer.classList.add('hidden');
    activeFileContainer.classList.add('hidden');
    dropZone.classList.remove('hidden');
    fileInput.value = '';
}

function enableChat(enable) {
    if (enable && isConnected) {
        chatInput.disabled = false;
        btnSend.disabled = false;
        chatInput.placeholder = 'Ask a question about the uploaded document...';
    } else {
        chatInput.disabled = true;
        btnSend.disabled = true;
        chatInput.placeholder = isConnected ? 'Upload a PDF to start chatting...' : 'Connecting to API server...';
        chatInput.value = '';
        chatInput.style.height = 'auto';
    }
}

// Chat Submission Handler
async function handleChatSubmit(e) {
    e.preventDefault();
    if (!isConnected || isProcessingChat) return;

    const question = chatInput.value.trim();
    if (!question) return;

    // Clear input box
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Add user message to UI
    appendMessage('user', question);
    
    isProcessingChat = true;
    enableChatInputArea(false);

    // Append Typing Animation Indicator
    const typingIndicator = appendTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                history: chatHistory
            })
        });

        // Remove typing animation
        typingIndicator.remove();

        if (response.ok) {
            const data = await response.json();
            appendMessage('assistant', data.answer);
            
            // Add to chat history memory
            chatHistory.push({ role: 'user', content: question });
            chatHistory.push({ role: 'assistant', content: data.answer });
        } else {
            let errorMsg = 'Could not generate a response.';
            try {
                const data = await response.json();
                errorMsg = data.detail || errorMsg;
            } catch (err) {}
            appendMessage('assistant', `Error: ${errorMsg}`);
            showToast('Chat Error', errorMsg, 'error');
        }
    } catch (error) {
        console.error('Chat error:', error);
        typingIndicator.remove();
        appendMessage('assistant', 'Sorry, a connection error occurred while communicating with the server.');
        showToast('Connection Error', 'Could not reach the server.', 'error');
    } finally {
        isProcessingChat = false;
        enableChatInputArea(true);
        chatInput.focus();
    }
}

function enableChatInputArea(enable) {
    if (enable) {
        chatInput.disabled = false;
        btnSend.disabled = false;
    } else {
        chatInput.disabled = true;
        btnSend.disabled = true;
    }
}

// Append a Message to the Chat Window
function appendMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    let avatarSvg = '';
    if (role === 'user') {
        avatarSvg = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        `;
    } else {
        avatarSvg = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M12 2v2M8 5a4 4 0 0 1 8 0M16 11V7a4 4 0 0 0-8 0v4"/>
            </svg>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar flex-center">${avatarSvg}</div>
        <div class="message-content">${formatMarkdown(text)}</div>
    `;

    chatMessagesContainer.appendChild(messageDiv);
    autoScrollChat();
}

// Append Typing Animation Dot Loading Node
function appendTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message assistant-message typing-indicator-wrapper';
    indicatorDiv.innerHTML = `
        <div class="message-avatar flex-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M12 2v2M8 5a4 4 0 0 1 8 0M16 11V7a4 4 0 0 0-8 0v4"/>
            </svg>
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessagesContainer.appendChild(indicatorDiv);
    autoScrollChat();
    return indicatorDiv;
}

// Auto Scroll to Bottom of Chat
function autoScrollChat() {
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

// Clear Chat Action (UI ONLY)
function clearChatUI() {
    // Keep first greeting message
    const greetingMsg = chatMessagesContainer.firstElementChild;
    chatMessagesContainer.innerHTML = '';
    if (greetingMsg) {
        chatMessagesContainer.appendChild(greetingMsg);
    }
    chatHistory = [];
    showToast('Success', 'Conversation cleared.', 'success');
}

// Reset Entire Application State (Backend API and Vector DB)
async function resetApplication() {
    if (!isConnected) {
        showToast('Error', 'API server is offline. Cannot reset application.', 'error');
        return;
    }
    
    const confirmReset = confirm('Are you sure you want to delete the vector database and clear all uploads? This action cannot be undone.');
    if (!confirmReset) return;

    try {
        const response = await fetch(`${API_BASE}/clear`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Success', 'Application database reset complete.', 'success');
            clearChatUI();
            showUploadState();
            enableChat(false);
        } else {
            showToast('Error', 'Failed to clear backend database.', 'error');
        }
    } catch (error) {
        console.error('Failed to reset app:', error);
        showToast('Connection Error', 'Failed to reach API server to reset DB.', 'error');
    }
}

// Simple Custom Markdown Renderer
function formatMarkdown(text) {
    if (!text) return '';

    // Escape basic html tags to prevent layout injections
    let escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks: ```code```
    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code: `code`
    escaped = escaped.replace(/`(.*?)`/g, '<code>$1</code>');

    // Bold formatting: **text**
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Split paragraphs and handle bullet lists
    const lines = escaped.split('\n');
    let output = [];
    let inList = false;

    for (let line of lines) {
        const trimmed = line.trim();
        
        // Bullet list detection: starts with * or - followed by space
        if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            if (!inList) {
                output.push('<ul>');
                inList = true;
            }
            output.push(`<li>${trimmed.substring(2)}</li>`);
        } else {
            if (inList) {
                output.push('</ul>');
                inList = false;
            }
            // Check for empty lines to separate paragraphs
            if (trimmed === '') {
                // Ignore multiple empty lines
            } else {
                output.push(`<p>${line}</p>`);
            }
        }
    }

    if (inList) {
        output.push('</ul>');
    }

    return output.join('\n');
}

// Toast Notifications System
function showToast(title, message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Auto color code border icon
    let statusIcon = '';
    if (type === 'success') {
        statusIcon = `
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="var(--success-color)" stroke-width="2.5" fill="none">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
        `;
    } else if (type === 'error') {
        statusIcon = `
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="var(--danger-color)" stroke-width="2.5" fill="none">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
        `;
    } else {
        statusIcon = `
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="var(--primary-color)" stroke-width="2.5" fill="none">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
        `;
    }

    toast.innerHTML = `
        <div class="toast-icon">${statusIcon}</div>
        <div class="toast-body">
            <strong style="display: block; margin-bottom: 2px;">${title}</strong>
            <span style="color: var(--text-sub); font-size: 0.8rem;">${message}</span>
        </div>
        <button class="toast-close-btn flex-center">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
    `;

    // Toast event close listener
    const closeBtn = toast.querySelector('.toast-close-btn');
    closeBtn.addEventListener('click', () => {
        toast.style.animation = 'slideOutRight 0.3s forwards';
        toast.addEventListener('animationend', () => toast.remove());
    });

    toastContainer.appendChild(toast);

    // Auto-remove toast after 4.5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s forwards';
            toast.addEventListener('animationend', () => toast.remove());
        }
    }, 4500);
}

// Add slideOut Animation to style stylesheet programmatically to keep CSS modular
const styleSheet = document.createElement("style");
styleSheet.innerText = `
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(styleSheet);
