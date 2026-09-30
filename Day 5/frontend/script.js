// ==========================================================================
// CLIENT JAVASCRIPT - AEGIS SMART ASSISTANT
// ==========================================================================

// Global state
let currentSessionId = '';
const API_BASE = '/api';

// On document load
document.addEventListener('DOMContentLoaded', () => {
    initSession();
    setupEventListeners();
    checkAuthStatus();
    loadSessionList();
    checkBackendHealth();
});

// Initialize session ID
function initSession() {
    // Attempt to load existing session or create a new one
    const savedSession = localStorage.getItem('aegis_session_id');
    if (savedSession) {
        currentSessionId = savedSession;
    } else {
        startNewSession();
    }
}

// Generate new unique session ID
function startNewSession() {
    currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('aegis_session_id', currentSessionId);
    
    // Clear chat container and show welcome screen
    const container = document.getElementById('messages-container');
    container.innerHTML = '';
    
    const welcome = document.getElementById('welcome-screen');
    if (welcome) welcome.style.display = 'flex';
    
    // De-select active sidebar items
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    showToast('New conversation started.', 'info');
}

// Setup all click & enter event listeners
function setupEventListeners() {
    // Send message controls
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Sidebar controllers
    document.getElementById('new-chat-btn').addEventListener('click', startNewSession);
    document.getElementById('clear-chat-btn').addEventListener('click', clearCurrentChat);
    
    // Right panel weather search
    document.getElementById('weather-search-btn').addEventListener('click', searchWeather);
    document.getElementById('weather-search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchWeather();
        }
    });

    // Calendar refresh
    document.getElementById('calendar-refresh-btn').addEventListener('click', fetchCalendarEvents);

    // Responsive Mobile Drawers
    const sidebar = document.getElementById('sidebar');
    const widgets = document.getElementById('widgets-panel');

    document.getElementById('mobile-sidebar-toggle').addEventListener('click', () => {
        sidebar.classList.add('active');
    });
    document.getElementById('mobile-sidebar-close').addEventListener('click', () => {
        sidebar.classList.remove('active');
    });

    document.getElementById('mobile-widgets-toggle').addEventListener('click', () => {
        widgets.classList.add('active');
    });
    document.getElementById('mobile-widgets-close').addEventListener('click', () => {
        widgets.classList.remove('active');
    });
}

// Check Backend Connectivity
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/auth/status`);
        if (response.ok) {
            document.getElementById('backend-status').textContent = 'Backend Connected';
            document.querySelector('.pulse-dot').style.backgroundColor = 'var(--accent-green)';
        } else {
            throw new Error();
        }
    } catch (e) {
        document.getElementById('backend-status').textContent = 'Backend Offline';
        document.querySelector('.pulse-dot').style.backgroundColor = 'var(--accent-red)';
        showToast('Cannot connect to FastAPI backend server.', 'error');
    }
}

// ==========================================================================
// CHAT LOGIC
// ==========================================================================

// Fill templates into chat input
window.fillPrompt = function(promptText) {
    const input = document.getElementById('chat-input');
    input.value = promptText;
    input.focus();
};

// Send message to agent
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    // Clear input
    input.value = '';
    
    // Hide welcome screen if showing
    const welcome = document.getElementById('welcome-screen');
    if (welcome) welcome.style.display = 'none';

    // Append user bubble to UI
    appendMessageBubble('user', message);
    
    // Show typing loader
    const indicator = document.getElementById('typing-indicator-wrapper');
    indicator.style.display = 'flex';
    scrollToBottom();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: currentSessionId })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to communicate with AI Agent');
        }

        const data = await response.json();
        
        // Hide loader
        indicator.style.display = 'none';
        
        // Append AI response
        appendMessageBubble('assistant', data.response, data.tool_called, data.tool_data);
        
        // Refresh sidebar lists & agenda panels if tools were triggered
        if (data.tool_called) {
            if (data.tool_called.includes('calendar')) {
                fetchCalendarEvents();
            }
            if (data.tool_called.includes('weather') && data.tool_data) {
                renderWeatherWidget(data.tool_data);
            }
        }
        
        loadSessionList();

    } catch (err) {
        indicator.style.display = 'none';
        appendMessageBubble('assistant', `Error: ${err.message}`);
        showToast(err.message, 'error');
    }
    scrollToBottom();
}

// Render message bubbles in panel
function appendMessageBubble(role, text, toolCalled = null, toolData = null) {
    const container = document.getElementById('messages-container');
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role}`;
    
    // Set avatars
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    if (role === 'user') {
        avatar.innerHTML = '<i class="fa-solid fa-user"></i>';
    } else {
        avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';
    }
    bubble.appendChild(avatar);

    // Set content details
    const wrapper = document.createElement('div');
    wrapper.className = 'message-content-wrapper';
    
    const textNode = document.createElement('div');
    textNode.className = 'message-text';
    
    // Standard markdown formatting highlights
    textNode.innerHTML = formatMarkdownText(text);
    wrapper.appendChild(textNode);

    // If a tool was executed, render a mini widget directly in the chat bubble
    if (toolCalled && toolData && !toolData.error) {
        const embeddedCard = document.createElement('div');
        embeddedCard.className = 'chat-embedded-widget';
        
        if (toolCalled === 'get_weather_data') {
            embeddedCard.innerHTML = getEmbeddedWeatherHTML(toolData);
        } else if (toolCalled === 'create_calendar_event') {
            embeddedCard.innerHTML = getEmbeddedCalendarHTML(toolData);
        } else if (toolCalled === 'list_calendar_events') {
            embeddedCard.innerHTML = getEmbeddedEventListHTML(toolData);
        }
        wrapper.appendChild(embeddedCard);
    }

    // Add Timestamp
    const timestamp = document.createElement('span');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    wrapper.appendChild(timestamp);

    bubble.appendChild(wrapper);
    container.appendChild(bubble);
}

// Auto scroll messages area
function scrollToBottom() {
    const container = document.getElementById('messages-container');
    container.scrollTop = container.scrollHeight;
}

// Helper to format text markdown tags (bolding and code snippets)
function formatMarkdownText(text) {
    if (!text) return '';
    // Format bolding **text** to <strong>text</strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Format bullet lines starting with - or *
    formatted = formatted.replace(/^\s*[-*]\s+(.*)$/gm, '<li>$1</li>');
    // Wrap consecutive list items in ul
    formatted = formatted.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
    // Format newlines
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

// ==========================================================================
// SESSION MANAGEMENT (SIDEBAR COLUMN 1)
// ==========================================================================

// Load session list in sidebar history
async function loadSessionList() {
    try {
        const response = await fetch(`${API_BASE}/chat/history/sessions`);
        if (!response.ok) throw new Error();
        
        const sessions = await response.json();
        const container = document.getElementById('history-list');
        container.innerHTML = '';
        
        if (sessions.length === 0) {
            container.innerHTML = '<div class="history-empty">No conversations yet</div>';
            return;
        }

        sessions.forEach(sid => {
            const item = document.createElement('button');
            item.className = `history-item ${sid === currentSessionId ? 'active' : ''}`;
            item.setAttribute('data-id', sid);
            
            // Generate title based on ID
            let title = sid.replace('session_', '');
            if (title.length > 15) title = 'Chat ' + title.substr(0, 8);
            
            item.innerHTML = `
                <div class="history-item-content" onclick="switchSession('${sid}')">
                    <i class="fa-solid fa-message"></i>
                    <span>${title}</span>
                </div>
                <button class="history-item-delete" onclick="deleteSession(event, '${sid}')" title="Delete Chat">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;
            container.appendChild(item);
        });

    } catch (e) {
        console.error('Failed to load session list');
    }
}

// Switch active conversation session
window.switchSession = async function(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('aegis_session_id', sessionId);
    
    // Hide welcome panel
    const welcome = document.getElementById('welcome-screen');
    if (welcome) welcome.style.display = 'none';

    // Highlight item
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-id') === sessionId);
    });

    // Fetch and render chat histories
    const container = document.getElementById('messages-container');
    container.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE}/chat/history?session_id=${sessionId}`);
        if (!response.ok) throw new Error('Failed to retrieve chat history');
        
        const logs = await response.json();
        if (logs.length === 0) {
            if (welcome) welcome.style.display = 'flex';
            return;
        }

        logs.forEach(log => {
            appendMessageBubble(log.role, log.content);
        });
        scrollToBottom();
        showToast('Loaded conversation history.', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
};

// Delete single session from history list
window.deleteSession = async function(event, sessionId) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this chat history?')) return;

    try {
        const response = await fetch(`${API_BASE}/chat/clear?session_id=${sessionId}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to delete session');
        
        showToast('Chat history deleted.', 'success');
        
        // If deleted current session, start fresh
        if (sessionId === currentSessionId) {
            startNewSession();
        }
        
        loadSessionList();
    } catch (err) {
        showToast(err.message, 'error');
    }
};

// Clear current chat
async function clearCurrentChat() {
    if (!confirm('Are you sure you want to clear the current conversation history?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/chat/clear?session_id=${currentSessionId}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to clear conversation history');
        
        startNewSession();
        loadSessionList();
        showToast('Conversation cleared.', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================================================
// WEATHER EXPLORER (COLUMN 3 / SEARCH)
// ==========================================================================

// Weather lookup search
async function searchWeather() {
    const input = document.getElementById('weather-search-input');
    const city = input.value.trim();
    if (!city) return;

    const body = document.getElementById('weather-widget-body');
    body.innerHTML = `
        <div class="weather-placeholder">
            <div class="spinner"></div>
            <p>Retrieving weather details for ${city}...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(city)}`);
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'City not found');
        }
        
        const data = await response.json();
        renderWeatherWidget(data);
        showToast(`Retrieved weather details for ${data.city}.`, 'success');
    } catch (err) {
        body.innerHTML = `
            <div class="weather-placeholder">
                <i class="fa-solid fa-cloud-bolt text-pink"></i>
                <p class="text-pink">${err.message}</p>
            </div>
        `;
        showToast(err.message, 'error');
    }
}

// Render Weather Widget card details
function renderWeatherWidget(data) {
    const body = document.getElementById('weather-widget-body');
    
    body.innerHTML = `
        <div class="weather-report-card">
            <div class="weather-main-row">
                <div class="weather-city-details">
                    <h4>${data.city}</h4>
                    <span>Condition: ${data.condition}</span>
                </div>
                <div class="weather-temp-icon">
                    <img class="weather-icon-img" src="https://openweathermap.org/img/wn/${data.icon}@2x.png" alt="${data.condition}">
                    <span class="weather-temperature">${Math.round(data.temperature)}°C</span>
                </div>
            </div>
            
            <div class="weather-desc-row">
                ${data.description}
            </div>

            <div class="weather-stats-grid">
                <div class="weather-stat-item">
                    <i class="fa-solid fa-temperature-half"></i>
                    <div class="stat-info">
                        <label>Feels Like</label>
                        <span>${Math.round(data.feels_like)}°C</span>
                    </div>
                </div>
                <div class="weather-stat-item">
                    <i class="fa-solid fa-droplet"></i>
                    <div class="stat-info">
                        <label>Humidity</label>
                        <span>${data.humidity}%</span>
                    </div>
                </div>
                <div class="weather-stat-item">
                    <i class="fa-solid fa-wind"></i>
                    <div class="stat-info">
                        <label>Wind</label>
                        <span>${data.wind_speed} m/s</span>
                    </div>
                </div>
                <div class="weather-stat-item">
                    <i class="fa-solid fa-eye"></i>
                    <div class="stat-info">
                        <label>Visibility</label>
                        <span>${(data.visibility / 1000).toFixed(1)} km</span>
                    </div>
                </div>
                <div class="weather-stat-item">
                    <i class="fa-solid fa-sun"></i>
                    <div class="stat-info">
                        <label>Sunrise</label>
                        <span>${data.sunrise}</span>
                    </div>
                </div>
                <div class="weather-stat-item">
                    <i class="fa-solid fa-moon"></i>
                    <div class="stat-info">
                        <label>Sunset</label>
                        <span>${data.sunset}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate embedded weather HTML for chat
function getEmbeddedWeatherHTML(data) {
    return `
        <div class="widget-card embedded-weather-bubble">
            <div class="weather-report-card">
                <div class="weather-main-row" style="margin-bottom: 0;">
                    <div class="weather-city-details">
                        <h4 style="font-size: 14px;"><i class="fa-solid fa-cloud-sun text-cyan" style="margin-right: 6px;"></i>${data.city}</h4>
                        <span style="font-size: 10px;">${data.description}</span>
                    </div>
                    <div class="weather-temp-icon">
                        <img style="width: 36px; height: 36px;" src="https://openweathermap.org/img/wn/${data.icon}.png" alt="${data.condition}">
                        <span style="font-size: 20px; font-weight: 700;">${Math.round(data.temperature)}°C</span>
                    </div>
                </div>
                <div class="weather-stats-grid" style="grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-top: 6px;">
                    <div class="weather-stat-item" style="padding: 4px; font-size: 10px; gap: 4px;">
                        <i class="fa-solid fa-temperature-half" style="font-size: 10px;"></i>
                        <span style="font-size: 10px;">Feels ${Math.round(data.feels_like)}°</span>
                    </div>
                    <div class="weather-stat-item" style="padding: 4px; font-size: 10px; gap: 4px;">
                        <i class="fa-solid fa-droplet" style="font-size: 10px;"></i>
                        <span style="font-size: 10px;">Hum ${data.humidity}%</span>
                    </div>
                    <div class="weather-stat-item" style="padding: 4px; font-size: 10px; gap: 4px;">
                        <i class="fa-solid fa-wind" style="font-size: 10px;"></i>
                        <span style="font-size: 10px;">Wind ${data.wind_speed}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ==========================================================================
// GOOGLE CALENDAR (COLUMN 3 & OAUTH INTEGRATION)
// ==========================================================================

// Check Google OAuth connectivity status
async function checkAuthStatus() {
    const container = document.getElementById('auth-status-container');
    try {
        const response = await fetch(`${API_BASE}/auth/status`);
        if (!response.ok) throw new Error();
        
        const data = await response.json();
        
        if (data.is_connected) {
            container.innerHTML = `
                <div class="status-linked">
                    <div class="status-badge">
                        <i class="fa-solid fa-circle-check"></i> Linked Account
                    </div>
                    <button class="btn btn-secondary btn-full" id="unlink-btn">
                        <i class="fa-solid fa-link-slash"></i> Unlink Google Account
                    </button>
                </div>
            `;
            // Add unlink listener
            document.getElementById('unlink-btn').addEventListener('click', unlinkCalendar);
            // Fetch calendar events agenda
            fetchCalendarEvents();
        } else {
            container.innerHTML = `
                <div class="status-unlinked">
                    <p class="status-text text-muted" style="margin-bottom: 12px;">Link your account to create, search, and manage Google Calendar events via AI Agent prompts.</p>
                    <a href="${data.auth_url}" target="_blank" class="btn btn-gradient btn-full" id="auth-link-btn">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i> Connect Calendar
                    </a>
                </div>
            `;
            
            // Add a callback handler trigger when authorization tab closes
            const authBtn = document.getElementById('auth-link-btn');
            authBtn.addEventListener('click', () => {
                showToast("Opening Google Sign-in...", "info");
                // Poll check status every 3 seconds to auto-detect login callback completion
                let checks = 0;
                const interval = setInterval(async () => {
                    checks++;
                    const checkRes = await fetch(`${API_BASE}/auth/status`);
                    const checkData = await checkRes.json();
                    if (checkData.is_connected) {
                        clearInterval(interval);
                        checkAuthStatus();
                        showToast("Google Calendar integrated successfully!", "success");
                    }
                    if (checks > 40) clearInterval(interval); // Timeout after 2 minutes
                }, 3000);
            });

            // Set placeholder for events
            document.getElementById('calendar-events-container').innerHTML = `
                <div class="calendar-placeholder">
                    <i class="fa-solid fa-calendar-xmark text-muted"></i>
                    <p>Connect Google Calendar in the sidebar to visualize your schedule here.</p>
                </div>
            `;
        }
    } catch (e) {
        container.innerHTML = `<p class="status-text text-pink">Authorization status check failed.</p>`;
    }
}

// Disconnect OAuth Credentials
async function unlinkCalendar() {
    if (!confirm('Are you sure you want to unlink your Google Calendar account?')) return;
    try {
        const response = await fetch(`${API_BASE}/auth/disconnect`, { method: 'POST' });
        if (!response.ok) throw new Error('Unlinking failed.');
        
        showToast('Google Account unlinked successfully.', 'success');
        checkAuthStatus();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Fetch events list and populate agenda widget
async function fetchCalendarEvents() {
    const container = document.getElementById('calendar-events-container');
    const refreshBtn = document.getElementById('calendar-refresh-btn');
    const icon = refreshBtn.querySelector('i');
    
    icon.classList.add('fa-spin');
    
    try {
        // Query next 15 upcoming events
        const response = await fetch(`${API_BASE}/calendar/events?max_results=15`);
        
        if (response.status === 401) {
            // Unconnected or expired token
            checkAuthStatus();
            icon.classList.remove('fa-spin');
            return;
        }
        
        if (!response.ok) throw new Error('Failed to retrieve calendar events');
        
        const events = await response.json();
        icon.classList.remove('fa-spin');
        
        if (events.length === 0) {
            container.innerHTML = '<div class="calendar-empty">No upcoming events found.</div>';
            return;
        }

        // Categorize events into Today vs Upcoming
        const todayStr = new Date().toDateString();
        const todayEvents = [];
        const upcomingEvents = [];

        events.forEach(e => {
            const evDate = new Date(e.start_time).toDateString();
            if (evDate === todayStr) {
                todayEvents.push(e);
            } else {
                upcomingEvents.push(e);
            }
        });

        let html = '';

        if (todayEvents.length > 0) {
            html += `<div class="events-list-section">
                <h4>Today</h4>`;
            todayEvents.forEach(e => {
                html += getEventItemHTML(e);
            });
            html += `</div>`;
        }

        if (upcomingEvents.length > 0) {
            html += `<div class="events-list-section" style="margin-top: 14px;">
                <h4>Upcoming Agenda</h4>`;
            upcomingEvents.forEach(e => {
                html += getEventItemHTML(e);
            });
            html += `</div>`;
        }

        container.innerHTML = html;

    } catch (err) {
        icon.classList.remove('fa-spin');
        container.innerHTML = `
            <div class="calendar-placeholder">
                <i class="fa-solid fa-triangle-exclamation text-pink"></i>
                <p class="text-pink">${err.message}</p>
            </div>
        `;
    }
}

// Single Event HTML formatting
function getEventItemHTML(e) {
    const start = new Date(e.start_time);
    // Parse time
    const timeStr = e.start_time.includes('T') 
        ? start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : 'All Day';
        
    const dateStr = start.toLocaleDateString([], { month: 'short', day: 'numeric' });
    const fullTimeStr = e.start_time.includes('T') ? `${dateStr}, ${timeStr}` : dateStr;

    return `
        <div class="calendar-event-item" id="event-${e.id}">
            <div class="event-details">
                <span class="event-summary">${e.summary}</span>
                <span class="event-time">
                    <i class="fa-regular fa-clock"></i> ${fullTimeStr}
                </span>
            </div>
            <div class="event-actions">
                ${e.html_link ? `<a class="event-action-btn" href="${e.html_link}" target="_blank" title="Open in Google Calendar"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : ''}
                <button class="event-action-btn delete" onclick="deleteCalendarEvent('${e.id}')" title="Delete event">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        </div>
    `;
}

// Delete Event directly from Widget list
window.deleteCalendarEvent = async function(eventId) {
    if (!confirm('Are you sure you want to cancel and delete this event?')) return;
    
    const eventItem = document.getElementById(`event-${eventId}`);
    if (eventItem) eventItem.style.opacity = '0.5';

    try {
        const response = await fetch(`${API_BASE}/calendar/delete?event_id=${eventId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Deletion failed');
        
        showToast('Calendar event deleted.', 'success');
        fetchCalendarEvents();
    } catch (err) {
        if (eventItem) eventItem.style.opacity = '1';
        showToast(err.message, 'error');
    }
};

// HTML builders for embedded bubbles
function getEmbeddedCalendarHTML(e) {
    const start = new Date(e.start_time);
    const timeStr = start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = start.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });

    return `
        <div class="widget-card embedded-weather-bubble" style="border-left: 4px solid var(--accent-green) !important;">
            <div style="display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 11px; text-transform: uppercase; color: var(--accent-green); font-weight:700;"><i class="fa-solid fa-circle-check"></i> Event Scheduled Successfully</span>
                <h4 style="font-size: 14px; margin: 4px 0 2px 0;">${e.summary}</h4>
                <span style="font-size: 12px; color: var(--text-secondary);"><i class="fa-regular fa-calendar"></i> ${dateStr} at ${timeStr}</span>
                ${e.html_link ? `<a href="${e.html_link}" target="_blank" class="btn btn-secondary btn-full" style="padding: 6px 12px; font-size: 11px; margin-top: 8px;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open in Google Calendar</a>` : ''}
            </div>
        </div>
    `;
}

function getEmbeddedEventListHTML(data) {
    const events = data.events || [];
    if (events.length === 0) {
        return `
            <div class="widget-card embedded-weather-bubble" style="border-left: 4px solid var(--accent-cyan) !important;">
                <span style="font-size: 12px; color: var(--text-secondary);">No upcoming events found on your Google Calendar schedule.</span>
            </div>
        `;
    }

    let listHtml = `<div class="widget-card embedded-weather-bubble" style="border-left: 4px solid var(--accent-cyan) !important; display: flex; flex-direction: column; gap: 8px;">
        <span style="font-size: 11px; text-transform: uppercase; color: var(--accent-cyan); font-weight:700;"><i class="fa-solid fa-calendar-days"></i> Retreived Agenda events</span>
        <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 4px;">`;
    
    events.slice(0, 5).forEach(e => {
        const start = new Date(e.start_time);
        const time = e.start_time.includes('T') ? start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'All Day';
        const date = start.toLocaleDateString([], { month: 'short', day: 'numeric' });
        listHtml += `
            <div style="display: flex; justify-content: space-between; font-size: 12px; background: rgba(0,0,0,0.1); padding: 6px; border-radius: 6px; border: 1px solid var(--glass-border);">
                <span style="font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 180px;">${e.summary}</span>
                <span style="color: var(--text-secondary); font-size: 11px;">${date}, ${time}</span>
            </div>
        `;
    });
    
    if (events.length > 5) {
        listHtml += `<span style="font-size:10px; color: var(--text-muted); text-align: center; display: block;">+ ${events.length - 5} more events (check dashboard panel)</span>`;
    }
    
    listHtml += `</div></div>`;
    return listHtml;
}

// ==========================================================================
// TOAST MESSAGES UTILITY
// ==========================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Pick icons
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    if (type === 'error') iconClass = 'fa-times-circle';
    if (type === 'warning') iconClass = 'fa-exclamation-triangle';

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <div class="toast-content">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove toast after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in forwards';
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 4000);
}

// CSS injection for slideOut animation
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes slideOut {
    to { transform: translateX(120%); opacity: 0; }
}
`;
document.head.appendChild(styleSheet);
