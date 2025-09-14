// Glassmorphism Infinity Loop Animations
document.addEventListener('DOMContentLoaded', function() {
    
    // Create infinity background
    createInfinityBackground();
    
    // Create floating particles
    createFloatingParticles();
    
    // Add glassmorphism effects to existing elements
    applyGlassmorphismEffects();
    
    // Initialize navbar functionality
    initializeNavbar();
});

// Navigation functionality using URL parameters
function setPage(pageName) {
    // Update active button
    const buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Find and activate the clicked button
    const clickedButton = event.target;
    clickedButton.classList.add('active');
    
    // Navigate using URL parameters
    const pageMap = {
        'Dashboard': 'dashboard',
        'Registration': 'registration', 
        'Attendance': 'attendance',
        'Classes': 'classes',
        'Reports': 'reports',
        'QR': 'qr'
    };
    
    const urlParam = pageMap[pageName];
    if (urlParam) {
        // Update URL with page parameter
        const url = new URL(window.location);
        url.searchParams.set('page', urlParam);
        window.history.pushState({}, '', url);
        
        // Trigger Streamlit rerun by finding hidden buttons
        setTimeout(() => {
            const streamlitButtonKey = `nav_${urlParam === 'qr' ? 'qr' : urlParam}`;
            
            // Look for buttons even if they're hidden
            const allButtons = document.querySelectorAll('button[key]');
            
            for (let btn of allButtons) {
                const key = btn.getAttribute('key');
                if (key === streamlitButtonKey) {
                    // Temporarily make button visible and clickable
                    const originalDisplay = btn.style.display;
                    const originalVisibility = btn.style.visibility;
                    
                    btn.style.display = 'block';
                    btn.style.visibility = 'visible';
                    btn.style.pointerEvents = 'auto';
                    
                    btn.click();
                    
                    // Hide it again
                    setTimeout(() => {
                        btn.style.display = originalDisplay || 'none';
                        btn.style.visibility = originalVisibility || 'hidden';
                        btn.style.pointerEvents = 'none';
                    }, 50);
                    break;
                }
            }
        }, 100);
    }
}

function initializeNavbar() {
    // Add click handlers to navbar buttons
    setTimeout(() => {
        const navButtons = document.querySelectorAll('.nav-button');
        navButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const pageName = this.textContent.split(' ')[1]; // Get page name after emoji
                setPage(pageName);
            });
        });
        
        // Hide the duplicate Streamlit navigation buttons
        hideStreamlitNavigation();
    }, 1000);
}

function hideStreamlitNavigation() {
    // Hide all navigation elements
    const streamlitColumns = document.querySelectorAll('.stColumn');
    streamlitColumns.forEach(col => {
        col.style.display = 'none';
    });
    
    // Hide horizontal rows containing navigation
    const horizontalRows = document.querySelectorAll('div.row-widget.stHorizontal');
    horizontalRows.forEach(row => {
        const buttons = row.querySelectorAll('button');
        if (buttons.length >= 6) { // Navigation row has 6 buttons
            row.style.display = 'none';
        }
    });
    
    // Hide any visible navigation buttons
    const navButtons = document.querySelectorAll('button[key^="nav_"]');
    navButtons.forEach(btn => {
        if (btn.closest('.stColumn')) {
            btn.closest('.stColumn').style.display = 'none';
        }
        btn.style.display = 'none';
        btn.style.visibility = 'hidden';
    });
}

function createInfinityBackground() {
    // Check if background already exists
    if (document.querySelector('.infinity-background')) return;
    
    const background = document.createElement('div');
    background.className = 'infinity-background';
    document.body.appendChild(background);
}

function createFloatingParticles() {
    // Check if particles container already exists
    if (document.querySelector('.floating-particles')) return;
    
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'floating-particles';
    
    // Create 15 floating particles
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random positioning and animation delay
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        // Random size variation
        const size = 2 + Math.random() * 4;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // Random opacity
        particle.style.opacity = 0.3 + Math.random() * 0.5;
        
        particlesContainer.appendChild(particle);
    }
    
    document.body.appendChild(particlesContainer);
}

function createInfinitySymbol() {
    // Check if infinity symbol already exists
    if (document.querySelector('.infinity-symbol')) return;
    
    const infinitySymbol = document.createElement('div');
    infinitySymbol.className = 'infinity-symbol';
    document.body.appendChild(infinitySymbol);
}

function applyGlassmorphismEffects() {
    // Apply glassmorphism to Streamlit elements
    setTimeout(() => {
        // Ensure background persists
        ensureBackgroundPersists();
        
        // Main container
        const mainContainer = document.querySelector('.main');
        if (mainContainer) {
            mainContainer.style.background = 'transparent';
        }
        
        // Sidebar
        const sidebar = document.querySelector('.css-1d391kg');
        if (sidebar) {
            sidebar.classList.add('glass-sidebar');
        }
        
        // Cards and containers
        const containers = document.querySelectorAll('.stContainer, .element-container');
        containers.forEach(container => {
            if (!container.classList.contains('glass-card')) {
                container.classList.add('glass-card');
            }
        });
        
        // Buttons
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            if (!button.classList.contains('glass-button')) {
                button.classList.add('glass-button');
            }
        });
        
        // Add hover effects to interactive elements
        addHoverEffects();
        
    }, 1000);
}

function ensureBackgroundPersists() {
    // Force background to stay after Streamlit updates
    const stApp = document.querySelector('.stApp');
    if (stApp) {
        stApp.style.background = 'transparent';
        stApp.style.setProperty('background', 'transparent', 'important');
    }
    
    // Ensure galaxy background exists and is visible
    let galaxyBg = document.querySelector('.infinity-background');
    if (!galaxyBg) {
        createInfinityBackground();
        galaxyBg = document.querySelector('.infinity-background');
    }
    
    if (galaxyBg) {
        galaxyBg.style.display = 'block';
        galaxyBg.style.visibility = 'visible';
        galaxyBg.style.opacity = '1';
        galaxyBg.style.zIndex = '-1';
        galaxyBg.style.position = 'fixed';
        galaxyBg.style.top = '0';
        galaxyBg.style.left = '0';
        galaxyBg.style.width = '100%';
        galaxyBg.style.height = '100%';
    }
    
    // Re-apply background styles after Streamlit reruns
    document.body.style.background = 'transparent';
    document.body.style.setProperty('background', 'transparent', 'important');
    document.documentElement.style.background = '#000000';
    document.documentElement.style.setProperty('background', '#000000', 'important');
    
    // Force all Streamlit containers to be transparent
    const containers = document.querySelectorAll('.stApp, .stApp > div, .main, .block-container');
    containers.forEach(container => {
        container.style.background = 'transparent';
        container.style.setProperty('background', 'transparent', 'important');
    });
}

function addHoverEffects() {
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.glass-button');
    buttons.forEach(button => {
        button.addEventListener('click', createRippleEffect);
    });
}

function createRippleEffect(e) {
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Dynamic particle generation
function generateNewParticles() {
    const particlesContainer = document.querySelector('.floating-particles');
    if (!particlesContainer) return;
    
    setInterval(() => {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (10 + Math.random() * 15) + 's';
        
        const size = 1 + Math.random() * 3;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.opacity = 0.2 + Math.random() * 0.4;
        
        particlesContainer.appendChild(particle);
        
        // Remove particle after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.remove();
            }
        }, 15000);
        
    }, 2000);
}

// Initialize continuous particle generation
setTimeout(generateNewParticles, 3000);

// Monitor for Streamlit reruns and maintain background - More frequent checking
setInterval(() => {
    ensureBackgroundPersists();
}, 500);

// Apply effects less frequently to avoid performance issues
setInterval(() => {
    applyGlassmorphismEffects();
}, 3000);

// Immediate background fix on page interactions
document.addEventListener('click', () => {
    setTimeout(ensureBackgroundPersists, 100);
    setTimeout(ensureBackgroundPersists, 500);
    setTimeout(ensureBackgroundPersists, 1000);
});

// Fix background on Streamlit state changes
const observer = new MutationObserver(() => {
    ensureBackgroundPersists();
});

observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['style', 'class']
});

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

// Add CSS for ripple effect
const rippleCSS = `
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: scale(0);
    animation: ripple-animation 0.6s linear;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}
`;

const style = document.createElement('style');
style.textContent = rippleCSS;
document.head.appendChild(style);
