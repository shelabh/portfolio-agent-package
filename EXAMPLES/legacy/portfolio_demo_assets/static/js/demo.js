// Portfolio Agent Demo JavaScript

class PortfolioAgentDemo {
    constructor() {
        this.currentDemo = 'portfolio';
        this.initializeEventListeners();
        this.initializeAnimations();
    }
    
    initializeEventListeners() {
        // Demo navigation
        const demoButtons = document.querySelectorAll('[data-demo]');
        demoButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const demo = e.target.getAttribute('data-demo');
                this.switchDemo(demo);
            });
        });
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Form submissions
        const contactForm = document.getElementById('contactForm');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleContactForm(e);
            });
        }
        
        // Scroll animations
        window.addEventListener('scroll', () => {
            this.handleScrollAnimations();
        });
    }
    
    initializeAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);
        
        // Observe elements for animation
        document.querySelectorAll('.feature-card, .stat-item, .demo-preview').forEach(el => {
            observer.observe(el);
        });
    }
    
    switchDemo(demo) {
        // Update active button
        document.querySelectorAll('[data-demo]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-demo="${demo}"]`).classList.add('active');
        
        // Update demo content
        this.currentDemo = demo;
        this.updateDemoContent(demo);
    }
    
    updateDemoContent(demo) {
        const demoContent = document.getElementById('demoContent');
        if (!demoContent) return;
        
        const demos = {
            portfolio: {
                title: 'Portfolio Agent',
                description: 'AI-powered portfolio assistant that can answer questions about your skills, experience, and projects.',
                features: [
                    'Natural language queries about your background',
                    'Project-specific information retrieval',
                    'Skills and experience analysis',
                    'Contact and availability information'
                ],
                example: 'Ask me about my Python experience or specific projects I\'ve worked on!'
            },
            recruiter: {
                title: 'Recruiter Assistant',
                description: 'Specialized AI for recruiters to evaluate candidates, match skills to job requirements, and streamline the hiring process.',
                features: [
                    'Candidate skill assessment',
                    'Job requirement matching',
                    'Interview question generation',
                    'Cultural fit analysis'
                ],
                example: 'Perfect for recruiters to quickly evaluate candidate fit for specific roles.'
            },
            knowledge: {
                title: 'Internal Knowledge Base',
                description: 'Enterprise knowledge management system for teams to share information, document processes, and collaborate effectively.',
                features: [
                    'Team knowledge sharing',
                    'Process documentation',
                    'Collaborative Q&A',
                    'Search across all team resources'
                ],
                example: 'Great for teams to build and maintain their internal knowledge base.'
            }
        };
        
        const demoData = demos[demo];
        if (demoData) {
            demoContent.innerHTML = `
                <div class="row">
                    <div class="col-lg-6">
                        <h3 class="text-gradient">${demoData.title}</h3>
                        <p class="lead">${demoData.description}</p>
                        <ul class="list-unstyled">
                            ${demoData.features.map(feature => 
                                `<li class="mb-2"><i class="fas fa-check text-success me-2"></i>${feature}</li>`
                            ).join('')}
                        </ul>
                        <div class="alert alert-info">
                            <i class="fas fa-lightbulb me-2"></i>
                            ${demoData.example}
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="demo-preview p-4 text-center">
                            <i class="fas fa-robot display-1 text-primary mb-3"></i>
                            <h4>Interactive Demo</h4>
                            <p>Try the ${demoData.title.toLowerCase()} in action!</p>
                            <button class="btn btn-primary btn-lg" onclick="scrollToDemo()">
                                <i class="fas fa-play me-2"></i>Start Demo
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    handleContactForm(e) {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        // Simulate form submission
        const submitButton = e.target.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        
        submitButton.innerHTML = '<span class="loading"></span> Sending...';
        submitButton.disabled = true;
        
        setTimeout(() => {
            // Show success message
            this.showNotification('Message sent successfully! I\'ll get back to you soon.', 'success');
            
            // Reset form
            e.target.reset();
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 2000);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    handleScrollAnimations() {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelector('.hero-section');
        
        if (parallax) {
            const speed = scrolled * 0.5;
            parallax.style.transform = `translateY(${speed}px)`;
        }
    }
}

// Utility functions
function scrollToDemo() {
    const demoSection = document.getElementById('demo');
    if (demoSection) {
        demoSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function scrollToFeatures() {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
        featuresSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function scrollToContact() {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
        contactSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Initialize demo when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PortfolioAgentDemo();
    
    // Add smooth scrolling to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(button => {
        if (button.type === 'submit') {
            button.addEventListener('click', function() {
                if (!this.disabled) {
                    const originalText = this.innerHTML;
                    this.innerHTML = '<span class="loading"></span> Loading...';
                    this.disabled = true;
                    
                    setTimeout(() => {
                        this.innerHTML = originalText;
                        this.disabled = false;
                    }, 2000);
                }
            });
        }
    });
});

// Add CSS for additional animations
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    .fade-in {
        animation: fadeInUp 0.6s ease forwards;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .hero-section {
        transition: transform 0.1s ease-out;
    }
    
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .btn::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(255,255,255,0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .btn:active::before {
        width: 300px;
        height: 300px;
    }
`;
document.head.appendChild(additionalStyles);
