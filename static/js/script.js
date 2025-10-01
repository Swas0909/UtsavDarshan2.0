// Main JavaScript for UtsavDarshan
document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    initMapButtons();
    initSearchFilter();
    initFormHandlers();
    initAnimations();
    initModal();
});

// Map functionality
function initMapButtons() {
    const mapButtons = document.querySelectorAll('.map-btn');
    const mapModal = document.getElementById('map-modal');
    const mapContainer = document.getElementById('map-container');
    const closeModal = document.querySelector('.close-modal');
    
    mapButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.getAttribute('data-lat'));
            const lng = parseFloat(btn.getAttribute('data-lng'));
            
            // Show modal with map
            mapModal.style.display = 'block';
            
            // Initialize Leaflet map
            mapContainer.innerHTML = '<div id="leaflet-map" style="height: 400px;"></div>';
            const map = L.map('leaflet-map').setView([lat, lng], 15);
            
            // Add OpenStreetMap tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            // Add marker
            L.marker([lat, lng])
                .addTo(map)
                .bindPopup('Pandal Location');
            }
        });
    });
    
    // Close modal
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            mapModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === mapModal) {
            mapModal.style.display = 'none';
        }
    });
}

// Search and filter functionality
function initSearchFilter() {
    const searchInput = document.getElementById('pandal-search');
    const filterTaluka = document.getElementById('filter-taluka');
    const cards = document.querySelectorAll('.card');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterCards);
    }
    
    if (filterTaluka) {
        filterTaluka.addEventListener('change', filterCards);
    }
    
    function filterCards() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const selectedTaluka = filterTaluka ? filterTaluka.value.toLowerCase() : '';
        
        cards.forEach(card => {
            const title = card.querySelector('h3').textContent.toLowerCase();
            const description = card.querySelector('.card-description').textContent.toLowerCase();
            const taluka = card.getAttribute('data-taluka').toLowerCase();
            
            const matchesSearch = title.includes(searchTerm) || description.includes(searchTerm);
            const matchesTaluka = selectedTaluka === '' || taluka === selectedTaluka;
            
            if (matchesSearch && matchesTaluka) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
}

// Form submission handlers
function initFormHandlers() {
    const feedbackForm = document.getElementById('feedback-form');
    const registerForm = document.getElementById('quick-register-form');
    const feedbackMessage = document.getElementById('feedback-message');
    const registerMessage = document.getElementById('register-message');
    
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const feedbackText = this.querySelector('textarea').value;
            
            if (feedbackText.trim() !== '') {
                // Submit form via AJAX (simplified for demo)
                fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                })
                .then(() => {
                    // Show success message
                    this.reset();
                    feedbackMessage.classList.remove('hidden');
                    setTimeout(() => {
                        feedbackMessage.classList.add('hidden');
                    }, 3000);
                })
                .catch(error => console.error('Error:', error));
            }
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Submit form via AJAX (simplified for demo)
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this)
            })
            .then(() => {
                // Show success message
                this.reset();
                registerMessage.classList.remove('hidden');
                setTimeout(() => {
                    registerMessage.classList.add('hidden');
                }, 3000);
            })
            .catch(error => console.error('Error:', error));
        });
    }
}

// Animation effects
function initAnimations() {
    // Reveal animations on scroll
    const revealElements = document.querySelectorAll('.card');
    
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        revealElements.forEach((element, index) => {
            const elementTop = element.getBoundingClientRect().top;
            
            if (elementTop < windowHeight - 100) {
                // Add staggered animation delay
                setTimeout(() => {
                    element.classList.add('fade-in');
                }, index * 100);
            }
        });
    };
    
    // Initial check
    revealOnScroll();
    
    // Check on scroll
    window.addEventListener('scroll', revealOnScroll);
}

// Modal functionality
function initModal() {
    // Add any additional modal functionality here
    document.addEventListener('keydown', (e) => {
        const mapModal = document.getElementById('map-modal');
        if (e.key === 'Escape' && mapModal.style.display === 'block') {
            mapModal.style.display = 'none';
        }
    });
}
