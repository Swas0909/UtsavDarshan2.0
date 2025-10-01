// Enhanced Pandal Search and Filter System
class PandalSearchSystem {
    constructor() {
        this.userLocation = null;
        this.allPandals = [];
        this.filteredPandals = [];
        this.isLocationMode = false;
        this.searchTimeout = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Check for geolocation permission
            if ('permissions' in navigator) {
                const permission = await navigator.permissions.query({name: 'geolocation'});
                if (permission.state === 'granted') {
                    this.getUserLocation();
                }
            }
        } catch (error) {
            console.log('Geolocation permission check not supported');
        }
        
        this.setupEventListeners();
        this.loadPandals();
    }
    
    setupEventListeners() {
        // Search input with debouncing
        const searchInput = document.getElementById('pandal-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.handleSearch(e.target.value);
                }, 300);
            });
            
            searchInput.addEventListener('focus', () => {
                this.showSearchSuggestions();
            });
            
            searchInput.addEventListener('blur', () => {
                // Hide suggestions after a small delay to allow clicking
                setTimeout(() => {
                    this.hideSearchSuggestions();
                }, 200);
            });
        }
        
        // Filter controls
        const filters = ['area-filter', 'theme-filter', 'rating-filter', 'sort-filter'];
        filters.forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        });
        
        // Clear filters button
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAllFilters());
        }
        
        // Location button
        const locationBtn = document.getElementById('location-btn');
        if (locationBtn) {
            locationBtn.addEventListener('click', () => this.toggleLocationMode());
        }
    }
    
    async loadPandals() {
        try {
            this.showLoadingState();
            
            const url = this.userLocation ? 
                `/api/pandals/enhanced?lat=${this.userLocation.lat}&lng=${this.userLocation.lng}` :
                '/api/pandals/enhanced';
                
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.allPandals = data.pandals || [];
            this.filteredPandals = [...this.allPandals];
            
            // Populate area filter
            this.populateAreaFilter(data.areas || []);
            
            // Render pandals
            this.renderPandals();
            this.updateResultsCount();
            
            this.hideLoadingState();
        } catch (error) {
            console.error('Error loading pandals:', error);
            this.showErrorState(error.message);
        }
    }
    
    async handleSearch(query) {
        // If query is empty, just apply current filters
        if (!query.trim()) {
            this.applyFilters();
            return;
        }
        
        // Apply search filter
        this.applyFilters();
        
        // Show suggestions if query length > 2
        if (query.length > 2) {
            try {
                const response = await fetch(`/api/pandals/search?q=${encodeURIComponent(query)}&limit=5`);
                const data = await response.json();
                this.showSearchSuggestions(data.suggestions || []);
            } catch (error) {
                console.error('Error fetching search suggestions:', error);
            }
        }
    }
    
    showSearchSuggestions(suggestions = []) {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;
        
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        suggestionsContainer.innerHTML = suggestions.map(suggestion => `
            <div class="suggestion-item" onclick="pandalSearch.selectSuggestion('${suggestion.type}', '${suggestion.text}')">
                <i class="fas ${this.getSuggestionIcon(suggestion.type)}"></i>
                <span>${suggestion.text}</span>
                <small class="suggestion-type">${suggestion.type}</small>
            </div>
        `).join('');
        
        suggestionsContainer.style.display = 'block';
    }
    
    hideSearchSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }
    
    selectSuggestion(type, text) {
        const searchInput = document.getElementById('pandal-search');
        
        switch(type) {
            case 'pandal':
                if (searchInput) searchInput.value = text;
                break;
            case 'area':
                document.getElementById('area-filter').value = text;
                if (searchInput) searchInput.value = '';
                break;
            case 'theme':
                document.getElementById('theme-filter').value = text;
                if (searchInput) searchInput.value = '';
                break;
        }
        
        this.hideSearchSuggestions();
        this.applyFilters();
    }
    
    getSuggestionIcon(type) {
        const icons = {
            'pandal': 'fa-om',
            'area': 'fa-map-marker-alt',
            'theme': 'fa-palette'
        };
        return icons[type] || 'fa-search';
    }
    
    async toggleLocationMode() {
        const locationBtn = document.getElementById('location-btn');
        const locationText = document.getElementById('location-text');
        const locationStatus = document.getElementById('location-status');
        
        if (!this.isLocationMode) {
            try {
                locationBtn.classList.add('loading');
                locationText.textContent = 'Getting location...';
                
                await this.getUserLocation();
                
                if (this.userLocation) {
                    this.isLocationMode = true;
                    locationBtn.classList.add('active');
                    locationBtn.classList.remove('loading');
                    locationText.textContent = 'Near Me';
                    locationStatus.textContent = 'Showing pandals near you';
                    
                    // Automatically set sorting to distance when location mode is enabled
                    const sortFilter = document.getElementById('sort-filter');
                    if (sortFilter) {
                        sortFilter.value = 'distance';
                    }
                    
                    // Reload pandals with location data
                    await this.loadPandals();
                } else {
                    throw new Error('Location not available');
                }
            } catch (error) {
                locationBtn.classList.remove('loading');
                locationText.textContent = 'Location Failed';
                locationStatus.textContent = '';
                alert('Unable to get your location. Please enable location services and try again.');
            }
        } else {
            // Disable location mode
            this.isLocationMode = false;
            locationBtn.classList.remove('active');
            locationText.textContent = 'Near Me';
            locationStatus.textContent = '';
            
            // Reload without location data
            await this.loadPandals();
        }
    }
    
    getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    resolve(this.userLocation);
                },
                (error) => {
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000
                }
            );
        });
    }
    
    applyFilters() {
        const searchQuery = document.getElementById('pandal-search').value.toLowerCase().trim();
        const areaFilter = document.getElementById('area-filter').value;
        const themeFilter = document.getElementById('theme-filter').value;
        const ratingFilter = document.getElementById('rating-filter').value;
        const sortFilter = document.getElementById('sort-filter').value;
        
        // Filter pandals
        this.filteredPandals = this.allPandals.filter(pandal => {
            // Search filter
            const matchesSearch = !searchQuery || 
                pandal.name.toLowerCase().includes(searchQuery) ||
                (pandal.area && pandal.area.toLowerCase().includes(searchQuery)) ||
                (pandal.theme && pandal.theme.toLowerCase().includes(searchQuery)) ||
                (pandal.address && pandal.address.toLowerCase().includes(searchQuery));
            
            // Area filter
            const matchesArea = !areaFilter || pandal.area === areaFilter;
            
            // Theme filter
            const matchesTheme = !themeFilter || pandal.theme === themeFilter;
            
            // Rating filter
            const matchesRating = !ratingFilter || 
                (pandal.average_rating && pandal.average_rating >= parseFloat(ratingFilter));
            
            return matchesSearch && matchesArea && matchesTheme && matchesRating;
        });
        
        // Apply sorting
        this.applySorting(sortFilter);
        
        // Render results
        this.renderPandals();
        this.updateResultsCount();
        this.updateActiveFilters();
    }
    
    applySorting(sortBy) {
        switch(sortBy) {
            case 'distance':
                if (this.isLocationMode && this.userLocation) {
                    // Sort by distance in ASCENDING order (closest first)
                    this.filteredPandals.sort((a, b) => {
                        const distA = a.distance !== null && a.distance !== undefined ? a.distance : Infinity;
                        const distB = b.distance !== null && b.distance !== undefined ? b.distance : Infinity;
                        return distA - distB;
                    });
                }
                break;
            case 'rating':
                this.filteredPandals.sort((a, b) => (b.average_rating || 0) - (a.average_rating || 0));
                break;
            case 'popularity':
                this.filteredPandals.sort((a, b) => (b.visit_count || 0) - (a.visit_count || 0));
                break;
            case 'name':
            default:
                this.filteredPandals.sort((a, b) => a.name.localeCompare(b.name));
                break;
        }
    }
    
    renderPandals() {
        const container = document.getElementById('pandal-cards-container');
        const noResults = document.getElementById('no-results');
        
        if (!container) return;
        
        if (this.filteredPandals.length === 0) {
            container.style.display = 'none';
            if (noResults) noResults.style.display = 'block';
            return;
        }
        
        container.style.display = 'grid';
        if (noResults) noResults.style.display = 'none';
        
        container.innerHTML = this.filteredPandals.map(pandal => this.createPandalCard(pandal)).join('');
    }
    
    createPandalCard(pandal) {
        const distanceInfo = this.isLocationMode && pandal.distance !== undefined && pandal.distance !== null
            ? `<div class="distance-info"><i class="fas fa-map-marker-alt"></i> ${pandal.distance} km away</div>`
            : '';
        
        const ratingInfo = pandal.average_rating
            ? `<div class="rating-info"><i class="fas fa-star"></i> ${pandal.average_rating} (${pandal.rating_count || 0} reviews)</div>`
            : '<div class="rating-info"><i class="far fa-star"></i> No ratings yet</div>';
        
        const themeBadge = pandal.theme
            ? `<div class="theme-badge">${pandal.theme}</div>`
            : '';
        
        return `
            <div class="pandal-card enhanced-card" onclick="showPandalDetails('${pandal._id || pandal.id}')">
                <div class="card-image">
                    <img src="${pandal.image || '/static/images/default-pandal.svg'}" alt="${pandal.name}" loading="lazy">
                    ${themeBadge}
                    ${distanceInfo}
                </div>
                <div class="card-content">
                    <h3 class="card-title">${pandal.name}</h3>
                    <div class="card-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${pandal.area || 'Location not specified'}</span>
                    </div>
                    ${ratingInfo}
                    <div class="card-actions">
                        <button class="card-btn primary" onclick="event.stopPropagation(); showPandalDetails('${pandal._id || pandal.id}')">
                            <i class="fas fa-info-circle"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    populateAreaFilter(areas) {
        const areaFilter = document.getElementById('area-filter');
        if (!areaFilter) return;
        
        const currentValue = areaFilter.value;
        
        // Clear existing options except the first one
        areaFilter.innerHTML = '<option value="">All Areas</option>';
        
        areas.forEach(area => {
            const option = document.createElement('option');
            option.value = area;
            option.textContent = area;
            areaFilter.appendChild(option);
        });
        
        // Restore previous selection if it exists
        if (currentValue && areas.includes(currentValue)) {
            areaFilter.value = currentValue;
        }
    }
    
    updateResultsCount() {
        const countElement = document.getElementById('results-count');
        if (!countElement) return;
        
        const count = this.filteredPandals.length;
        const total = this.allPandals.length;
        
        if (count === total) {
            countElement.textContent = `Showing all ${total} pandals`;
        } else {
            countElement.textContent = `Showing ${count} of ${total} pandals`;
        }
    }
    
    updateActiveFilters() {
        const activeFiltersContainer = document.getElementById('active-filters');
        if (!activeFiltersContainer) return;
        
        const activeFilters = [];
        
        // Check each filter
        const searchQuery = document.getElementById('pandal-search').value.trim();
        const areaFilter = document.getElementById('area-filter').value;
        const themeFilter = document.getElementById('theme-filter').value;
        const ratingFilter = document.getElementById('rating-filter').value;
        
        if (searchQuery) activeFilters.push({ type: 'search', value: searchQuery, label: `Search: "${searchQuery}"` });
        if (areaFilter) activeFilters.push({ type: 'area', value: areaFilter, label: `Area: ${areaFilter}` });
        if (themeFilter) activeFilters.push({ type: 'theme', value: themeFilter, label: `Theme: ${themeFilter}` });
        if (ratingFilter) activeFilters.push({ type: 'rating', value: ratingFilter, label: `${ratingFilter}+ Stars` });
        if (this.isLocationMode) activeFilters.push({ type: 'location', value: 'location', label: 'Near Me' });
        
        if (activeFilters.length === 0) {
            activeFiltersContainer.style.display = 'none';
            return;
        }
        
        activeFiltersContainer.style.display = 'flex';
        activeFiltersContainer.innerHTML = activeFilters.map(filter => `
            <div class="active-filter-tag">
                <span>${filter.label}</span>
                <button onclick="pandalSearch.removeFilter('${filter.type}', '${filter.value}')" class="remove-filter">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }
    
    removeFilter(type, value) {
        switch(type) {
            case 'search':
                document.getElementById('pandal-search').value = '';
                break;
            case 'area':
                document.getElementById('area-filter').value = '';
                break;
            case 'theme':
                document.getElementById('theme-filter').value = '';
                break;
            case 'rating':
                document.getElementById('rating-filter').value = '';
                break;
            case 'location':
                this.toggleLocationMode();
                return;
        }
        this.applyFilters();
    }
    
    clearAllFilters() {
        document.getElementById('pandal-search').value = '';
        document.getElementById('area-filter').value = '';
        document.getElementById('theme-filter').value = '';
        document.getElementById('rating-filter').value = '';
        document.getElementById('sort-filter').value = 'name';
        
        if (this.isLocationMode) {
            this.toggleLocationMode();
        } else {
            this.applyFilters();
        }
    }
    
    showLoadingState() {
        const loadingState = document.getElementById('loading-state');
        const cardsContainer = document.getElementById('pandal-cards-container');
        const noResults = document.getElementById('no-results');
        
        if (loadingState) loadingState.style.display = 'block';
        if (cardsContainer) cardsContainer.style.display = 'none';
        if (noResults) noResults.style.display = 'none';
    }
    
    hideLoadingState() {
        const loadingState = document.getElementById('loading-state');
        if (loadingState) loadingState.style.display = 'none';
    }
    
    showErrorState(message) {
        this.hideLoadingState();
        const countElement = document.getElementById('results-count');
        if (countElement) {
            countElement.textContent = `Error loading pandals: ${message}`;
        }
    }
}

// Initialize the search system when DOM is loaded
let pandalSearch;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing pandal search...');
    pandalSearch = new PandalSearchSystem();
    
    // Make functions globally accessible
    window.pandalSearch = pandalSearch;
    
    // Global showPandalDetails function
    window.showPandalDetails = function(pandalId) {
        console.log('showPandalDetails called with ID:', pandalId);
        
        fetch(`/api/pandals/${pandalId}`)
            .then(response => {
                console.log('API response status:', response.status);
                return response.json();
            })
            .then(pandal => {
                console.log('Pandal data received:', pandal);
                const modal = document.getElementById('pandal-modal');
                const detailsContainer = document.getElementById('pandal-details');
                
                if (!modal || !detailsContainer) {
                    console.error('Modal elements not found');
                    return;
                }
                
                const ratingStars = pandal.average_rating ? 
                    generateStarRating(pandal.average_rating) : 
                    '<span class="no-rating">No ratings yet</span>';
                
                // Get location mode status and user location from pandalSearch instance
                const isLocationMode = window.pandalSearch ? window.pandalSearch.isLocationMode : false;
                const userLocation = window.pandalSearch ? window.pandalSearch.userLocation : null;
                
                console.log('Location mode:', isLocationMode, 'User location:', userLocation);
                
                const distanceInfo = isLocationMode && userLocation && pandal.lat && pandal.lon ?
                    `<div class="distance-badge">
                        <i class="fas fa-map-marker-alt"></i>
                        ${calculateDistance(userLocation.lat, userLocation.lng, pandal.lat, pandal.lon).toFixed(1)} km away
                    </div>` : '';
                
                // Create a simple modal content for now
                detailsContainer.innerHTML = `
                    <div class="pandal-full-details bookmyshow-style">
                        <div class="details-header">
                            <div class="header-image">
                                <img src="${pandal.image || '/static/images/default-pandal.svg'}" alt="${pandal.name}" class="details-image">
                                ${distanceInfo}
                            </div>
                            <div class="header-info">
                                <h1 class="pandal-title">${pandal.name}</h1>
                                <div class="rating-section">
                                    ${ratingStars}
                                    <span class="rating-count">(${pandal.rating_count || 0} reviews)</span>
                                </div>
                                <div class="location-info">
                                    <i class="fas fa-map-marker-alt"></i>
                                    <span>${pandal.area || 'Location not specified'}</span>
                                </div>
                            </div>
                        </div>
                        <div class="details-content">
                            <div class="content-section">
                                <h3>About This Pandal</h3>
                                <p>${pandal.history || 'History and details about this pandal are not available at the moment.'}</p>
                            </div>
                            <div class="info-card">
                                <h4>Visit Information</h4>
                                <div class="info-item">
                                    <strong>Timings:</strong>
                                    <span>${pandal.opening_time || '08:00'} - ${pandal.closing_time || '22:00'}</span>
                                </div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="btn btn-primary btn-large" onclick="openDirectionsInMap(${pandal.lat}, ${pandal.lon}, '${pandal.name}')">
                                <i class="fas fa-directions"></i> Get Directions
                            </button>
                        </div>
                    </div>
                `;
                
                modal.style.display = "block";
                document.body.style.overflow = 'hidden';
                console.log('Modal opened successfully');
            })
            .catch(error => {
                console.error('Error loading pandal details:', error);
                alert('Error loading pandal details. Please try again.');
            });
    };
    
    // Global functions for compatibility
    window.toggleLocationMode = function() {
        if (window.pandalSearch) {
            window.pandalSearch.toggleLocationMode();
        }
    };
    
    window.clearAllFilters = function() {
        if (window.pandalSearch) {
            window.pandalSearch.clearAllFilters();
        }
    };
});

// Utility functions
function generateStarRating(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let starsHtml = '';
    
    for (let i = 0; i < fullStars; i++) {
        starsHtml += '<i class="fas fa-star"></i>';
    }
    
    if (hasHalfStar) {
        starsHtml += '<i class="fas fa-star-half-alt"></i>';
    }
    
    for (let i = 0; i < emptyStars; i++) {
        starsHtml += '<i class="far fa-star"></i>';
    }
    
    return `<div class="star-rating">${starsHtml} <span class="rating-value">${rating.toFixed(1)}</span></div>`;
}

function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Additional global functions for map integration
function openDirectionsInMap(lat, lon, name) {
    // Close the pandal details modal first
    document.getElementById('pandal-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Open map modal and get directions
    const mapModal = document.getElementById('mapModal');
    mapModal.style.display = 'block';
    
    if (!window.map && typeof initMap === 'function') {
        initMap();
    }
    
    // Get directions after a small delay to ensure map is loaded
    setTimeout(() => {
        if (typeof getDirections === 'function') {
            getDirections(lat, lon);
        }
    }, 500);
}

function viewOnMap(lat, lon, name) {
    const mapModal = document.getElementById('mapModal');
    mapModal.style.display = 'block';
    
    if (!window.map && typeof initMap === 'function') {
        initMap();
    }
    
    // Center map on pandal
    if (window.map && window.map.setView) {
        window.map.setView([lat, lon], 16);
    }
    
    // Close pandal details modal
    document.getElementById('pandal-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function shareLocation(name, lat, lon) {
    if (navigator.share) {
        navigator.share({
            title: name,
            text: `Check out ${name} on UtsavDarshan`,
            url: `${window.location.origin}/pandal/${lat},${lon}`
        });
    } else {
        // Fallback to copying to clipboard
        const url = `${window.location.origin}/pandal/${lat},${lon}`;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(() => {
                alert('Location link copied to clipboard!');
            });
        } else {
            // Fallback for older browsers
            alert(`Share this location: ${url}`);
        }
    }
}