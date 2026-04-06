// Portfolio Agent Chat Interface

class PortfolioAgentChat {
    constructor() {
        this.chatContainer = document.getElementById('chatContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.exampleQuestions = document.querySelectorAll('.example-question');
        this.isLoading = false;
        
        this.initializeEventListeners();
        this.addWelcomeMessage();
    }
    
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Example question clicks
        this.exampleQuestions.forEach(question => {
            question.addEventListener('click', () => {
                const questionText = question.textContent.trim();
                this.messageInput.value = questionText;
                this.sendMessage();
            });
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }
    
    addWelcomeMessage() {
        const welcomeMessage = {
            type: 'bot',
            content: `👋 Welcome to the Portfolio Agent Demo! I'm your AI assistant, trained on your portfolio data. I can help you with:

• **Skills & Experience**: Ask about my technical skills, projects, and experience
• **Project Details**: Get information about specific projects I've worked on
• **Career Journey**: Learn about my professional background and achievements
• **Contact & Availability**: Find out how to get in touch or schedule a meeting

Try asking one of the example questions below, or type your own question!`,
            timestamp: new Date().toLocaleTimeString()
        };
        
        this.addMessage(welcomeMessage);
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message
        const userMessage = {
            type: 'user',
            content: message,
            timestamp: new Date().toLocaleTimeString()
        };
        this.addMessage(userMessage);
        
        // Clear input and show loading
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.setLoading(true);
        
        try {
            // Send to API
            const response = await fetch('/api/v1/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    user_id: 'demo_user',
                    session_id: 'demo_session'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response
            const botMessage = {
                type: 'bot',
                content: data.response,
                citations: data.citations || [],
                metadata: data.metadata || {},
                timestamp: new Date().toLocaleTimeString()
            };
            this.addMessage(botMessage);
            
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = {
                type: 'bot',
                content: `❌ Sorry, I encountered an error: ${error.message}. Please try again or check if the server is running.`,
                timestamp: new Date().toLocaleTimeString()
            };
            this.addMessage(errorMessage);
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.type}-message mb-3`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content p-3 rounded';
        
        if (message.type === 'user') {
            messageContent.className += ' bg-primary text-white ms-auto';
            messageContent.style.maxWidth = '80%';
        } else {
            messageContent.className += ' bg-white border';
            messageContent.style.maxWidth = '90%';
        }
        
        // Add content
        const contentDiv = document.createElement('div');
        contentDiv.innerHTML = this.formatMessage(message.content);
        messageContent.appendChild(contentDiv);
        
        // Add citations if present
        if (message.citations && message.citations.length > 0) {
            const citationsDiv = document.createElement('div');
            citationsDiv.className = 'sources mt-2 p-2 rounded';
            citationsDiv.innerHTML = '<strong>📚 Sources:</strong><br>' + 
                message.citations.map(citation => 
                    `<div class="source-item">• ${citation}</div>`
                ).join('');
            messageContent.appendChild(citationsDiv);
        }
        
        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'text-muted small mt-1';
        timestampDiv.style.fontSize = '0.75rem';
        timestampDiv.textContent = message.timestamp;
        messageContent.appendChild(timestampDiv);
        
        messageElement.appendChild(messageContent);
        this.chatContainer.appendChild(messageElement);
        
        // Scroll to bottom
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        
        // Add animation
        messageElement.classList.add('fade-in');
    }
    
    formatMessage(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.sendButton.disabled = loading;
        
        if (loading) {
            this.sendButton.innerHTML = '<span class="loading"></span>';
            this.addTypingIndicator();
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.removeTypingIndicator();
        }
    }
    
    addTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot-message mb-3 typing-indicator';
        typingElement.id = 'typingIndicator';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'message-content p-3 rounded bg-white border';
        typingContent.style.maxWidth = '90%';
        
        typingContent.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="ms-2 text-muted">AI is thinking...</span>
            </div>
        `;
        
        typingElement.appendChild(typingContent);
        this.chatContainer.appendChild(typingElement);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
    
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PortfolioAgentChat();
});

// Add typing animation CSS
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: inline-flex;
        align-items: center;
    }
    
    .typing-dots span {
        height: 8px;
        width: 8px;
        background-color: #6c757d;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) {
        animation-delay: -0.32s;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: -0.16s;
    }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
