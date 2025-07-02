// SMART FAQ BOT - MAIN SCRIPT

// Globalne zmienne
let conversationHistory = [];
let isTyping = false;

// ================================
// INICJALIZACJA
// ================================
document.addEventListener('DOMContentLoaded', function() {
    initializeBot();
    setupEventListeners();
    showWelcomeMessage();
});

function initializeBot() {
    updateAPIStatus();
    console.log('🤖 Smart FAQ Bot initialized');
    console.log('📡 API configured:', IS_API_CONFIGURED);
}

function updateAPIStatus() {
    const statusEl = document.getElementById('apiStatus');
    const statusText = document.getElementById('statusText');
    
    if (IS_API_CONFIGURED) {
        statusEl.className = 'api-status connected';
        statusText.textContent = 'AI CONNECTED';
    } else {
        statusEl.className = 'api-status demo';
        statusText.textContent = 'DEMO MODE';
    }
}

// ================================
// EVENT LISTENERS
// ================================
function setupEventListeners() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.querySelector('.send-button');
    
    // Enter key to send message
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize input (jeśli textarea)
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // Prevent double-clicking send button
    sendButton.addEventListener('click', function() {
        if (!isTyping) {
            sendMessage();
        }
    });
}

// ================================
// ZARZĄDZANIE WIADOMOŚCIAMI
// ================================
function addMessage(content, isUser = false, options = {}) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const currentTime = new Date().toLocaleTimeString('pl', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const messageContent = `
        <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
        <div class="message-content">
            <div class="message-bubble ${options.highlight ? 'highlight' : ''}">
                ${formatMessage(content)}
            </div>
            <div class="message-time">${currentTime}</div>
        </div>
    `;
    
    messageDiv.innerHTML = messageContent;
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Add to conversation history
    if (conversationHistory.length > BOT_CONFIG.maxConversationHistory) {
        conversationHistory.shift();
    }
    conversationHistory.push({
        role: isUser ? "user" : "assistant",
        content: content,
        timestamp: new Date().toISOString()
    });
}

function formatMessage(message) {
    return message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '• ')
        .replace(/📞/g, '<span style="color: #4CAF50;">📞</span>')
        .replace(/⚠️/g, '<span style="color: #ff9800;">⚠️</span>');
}

function showWelcomeMessage() {
    setTimeout(() => {
        const welcomeMsg = `Cześć! 👋 Jestem AI asystentem salonu "Kleopatra". 

Mogę pomóc Ci z:
✂️ Informacjami o usługach i cenach
📅 Sprawdzeniem wolnych terminów
💇‍♀️ Kontaktem z naszymi specjalistami
📍 Lokalizacją i godzinami otwarcia

Jak mogę Ci dzisiaj pomóc?`;
        
        addMessage(welcomeMsg);
    }, 1000);
}

// ================================
// WYSYŁANIE WIADOMOŚCI
// ================================
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (message === '' || isTyping) {
        return;
    }
    
    // Dodaj wiadomość użytkownika
    addMessage(message, true);
    input.value = '';
    
    // Sprawdź intencje
    const intent = detectIntent(message);
    const specialCase = handleSpecialCases(message, intent);
    
    if (specialCase) {
        showTyping();
        setTimeout(() => {
            hideTyping();
            addMessage(specialCase.response, false, { highlight: true });
            
            // Obsługa specjalnych akcji
            if (specialCase.action === 'TRANSFER_TO_HUMAN') {
                setTimeout(() => {
                    addMessage(`📞 Łączę z recepcją: ${specialCase.phone}`, false, { highlight: true });
                }, 1500);
            }
            
            if (specialCase.action === 'TRANSFER_TO_MANAGER') {
                setTimeout(() => {
                    addMessage(`📧 Kierownik odpowie na: ${specialCase.email}`, false, { highlight: true });
                }, 1500);
            }
        }, Math.random() * 1000 + 1000);
        return;
    }
    
    // Normalne przetwarzanie wiadomości
    try {
        showTyping();
        
        let response;
        if (IS_API_CONFIGURED) {
            response = await getAIResponse(message);
        } else {
            response = getFallbackResponse(message);
        }
        
        setTimeout(() => {
            hideTyping();
            addMessage(response);
        }, Math.random() * 1500 + 1000);
        
    } catch (error) {
        console.error('Error processing message:', error);
        hideTyping();
        addMessage('Przepraszam, wystąpił problem. Spróbuj ponownie lub zadzwoń: 123-456-789');
    }
}

// ================================
// FUNKCJE POMOCNICZE
// ================================
function quickReply(message) {
    const input = document.getElementById('userInput');
    input.value = message;
    sendMessage();
}

function showTyping() {
    isTyping = true;
    const typingEl = document.getElementById('typing');
    typingEl.style.display = 'flex';
    
    // Scroll to show typing indicator
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTyping() {
    isTyping = false;
    const typingEl = document.getElementById('typing');
    typingEl.style.display = 'none';
}

// ================================
// ROZPOZNAWANIE INTENCJI
// ================================
function detectIntent(message) {
    const lowerMessage = message.toLowerCase();
    
    for (const [intent, keywords] of Object.entries(INTENTS)) {
        if (keywords.some(keyword => lowerMessage.includes(keyword.toLowerCase()))) {
            return intent;
        }
    }
    return 'GENERAL';
}

function handleSpecialCases(message, intent) {
    if (intent === 'EMERGENCY') {
        return {
            response: "Rozumiem, że sprawa jest pilna! 🚨 Łączę Cię z recepcją...",
            action: "TRANSFER_TO_HUMAN",
            phone: "123-456-789"
        };
    }
    
    if (intent === 'COMPLAINT') {
        return {
            response: "Przepraszam za niedogodności. Przekierowuję sprawę do kierownika...",
            action: "TRANSFER_TO_MANAGER", 
            email: "manager@salon-kleopatra.pl"
        };
    }
    
    return null;
}

// ================================
// ODPOWIEDZI AI
// ================================
async function getAIResponse(message) {
    try {
        return await callTogetherAI(message, conversationHistory.slice(-6));
    } catch (error) {
        console.error('Together AI error:', error);
        return getFallbackResponse(message);
    }
}

function getFallbackResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    // Sprawdź każdą kategorię w bazie wiedzy
    for (const [category, data] of Object.entries(KNOWLEDGE_BASE)) {
        if (data.keywords.some(keyword => lowerMessage.includes(keyword.toLowerCase()))) {
            return data.response;
        }
    }
    
    // Domyślna odpowiedź
    return KNOWLEDGE_BASE.default.response;
}

// ================================
// KOMUNIKACJA Z BACKEND
// ================================
async function callTogetherAI(userMessage, conversationHistory = []) {
    try {
        console.log('🔄 Wysyłam zapytanie do backend...');
        
        const messages = [
            {role: "system", content: SYSTEM_PROMPT},
            ...conversationHistory,
            {role: "user", content: userMessage}
        ];

        const response = await fetch(BACKEND_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Odpowiedź z backend:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        return data.response;
        
    } catch (error) {
        console.error('❌ Backend Error:', error);
        return getFallbackResponse(userMessage);
    }
}

// ================================
// DODATKOWE FUNKCJE
// ================================
function clearChat() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    conversationHistory = [];
    showWelcomeMessage();
}

function exportChat() {
    const chatData = {
        timestamp: new Date().toISOString(),
        conversation: conversationHistory
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
}

// ================================
// FUNKCJE GLOBALNE (dostępne z HTML)
// ================================
window.sendMessage = sendMessage;
window.quickReply = quickReply;
window.clearChat = clearChat;
window.exportChat = exportChat;

// ================================
// DEBUG FUNCTIONS
// ================================
if (typeof window !== 'undefined') {
    window.debugBot = {
        getHistory: () => conversationHistory,
        getConfig: () => BOT_CONFIG,
        testIntent: (message) => detectIntent(message),
        clearHistory: () => conversationHistory = []
    };
}