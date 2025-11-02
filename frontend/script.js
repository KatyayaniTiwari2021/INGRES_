// API Configuration
// Use 127.0.0.1 instead of localhost to avoid CORS/DNS issues on some browsers
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const connectionStatus = document.getElementById('connectionStatus');

// State
let isTyping = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    messageInput.focus();
    // Ensure we start at the bottom if welcome message is long
    scrollToBottom(true);
});

// Check API connection
async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            setConnectionStatus(true);
        } else {
            setConnectionStatus(false);
        }
    } catch (error) {
        setConnectionStatus(false);
    }
}

// Set connection status indicator
function setConnectionStatus(connected) {
    const statusDot = connectionStatus.querySelector('.status-dot');
    const statusText = connectionStatus.querySelector('span:last-child');
    
    if (connected) {
        statusDot.style.background = '#4ade80';
        statusText.textContent = 'Connected';
    } else {
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Disconnected';
    }
}

// Handle Enter key press
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send to API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        addMessage(data.response, 'bot', data);
        
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage('⚠️ Sorry, I encountered an error. Please check if the backend server is running.', 'bot');
        setConnectionStatus(false);
    }
}

// Send quick query
function sendQuickQuery(query) {
    messageInput.value = query;
    sendMessage();
}

// Add message to chat
function addMessage(message, sender, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Process and format the message
    bubble.innerHTML = formatMessage(message);
    
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = formatTime(new Date());
    
    content.appendChild(bubble);
    content.appendChild(time);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    // Ensure latest message is visible
    scrollToBottom(true);
}

// Format message with markdown-like syntax
function formatMessage(message) {
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    message = message.replace(/\*(.*?)\*/g, '<em>$1</em>');
    message = message.replace(/\n/g, '<br>');
    message = message.replace(/• /g, '&nbsp;&nbsp;• ');
    message = message.replace(/🟢/g, '<span style="color: #10b981;">●</span>');
    message = message.replace(/🟡/g, '<span style="color: #f59e0b;">●</span>');
    message = message.replace(/🟠/g, '<span style="color: #fb923c;">●</span>');
    message = message.replace(/🔴/g, '<span style="color: #ef4444;">●</span>');
    return message;
}

// Show typing indicator
function showTypingIndicator() {
    isTyping = true;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typingIndicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator message-bubble';
    indicator.innerHTML = `
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
    `;
    
    content.appendChild(indicator);
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(content);
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom(true);
}

// Remove typing indicator
function removeTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
    scrollToBottom(true); // Keep scroll at bottom after removal
}

// Format time
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// Clear chat history
async function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        try {
            await fetch(`${API_BASE_URL}/clear`, {
                method: 'POST',
            });
            
            const messages = chatMessages.querySelectorAll('.message');
            messages.forEach((msg, index) => {
                if (index > 0) msg.remove();
            });
            
            scrollToBottom(true); // Reset scroll after clearing
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }
}

// Auto scroll helper (robust + smooth)
function scrollToBottom(smooth = false) {
    if (!chatMessages) return;
    const behavior = smooth ? 'smooth' : 'auto';
    // Use rAF to ensure DOM/layout is flushed before scrolling
    requestAnimationFrame(() => {
        chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior });
        // A second pass helps after images/fonts render
        requestAnimationFrame(() => {
            chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'auto' });
        });
    });
}

// Periodic connection check
setInterval(checkConnection, 30000);
