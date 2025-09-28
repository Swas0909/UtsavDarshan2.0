let map;
let markers = [];
let poiMarkers = [];

// Initialize the map
function initMap() {
    // Default center (Mumbai)
    const defaultCenter = [19.0760, 72.8777];
    
    map = L.map('map').setView(defaultCenter, 12);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Fetch pandals and add markers
    fetchPandals();

    // Add click handlers for POI toggle buttons
    document.querySelectorAll('.poi-btn').forEach(button => {
        button.addEventListener('click', () => {
            button.classList.toggle('active');
            if (button.classList.contains('active')) {
                const poiType = button.dataset.type;
                const activeMarker = markers.find(m => m.isPopupOpen());
                if (activeMarker) {
                    fetchNearbyPOIs(activeMarker.getLatLng(), poiType);
                }
            } else {
                clearPOIMarkers(button.dataset.type);
            }
        });
    });
}

// Fetch pandals from the backend
function fetchPandals() {
    fetch('/api/pandals')
        .then(response => response.json())
        .then(pandals => {
            pandals.forEach(pandal => {
                if (pandal.lat && pandal.lon) {
                    addPandalMarker(pandal);
                }
            });
        });
}

// Add a marker for a pandal
function addPandalMarker(pandal) {
    const position = [pandal.lat, pandal.lon];
    const marker = L.marker(position)
        .addTo(map)
        .bindPopup(createPandalPopupContent(pandal));

    markers.push(marker);

    marker.on('click', () => {
        // Clear existing POI markers
        clearAllPOIMarkers();
        // Fetch new POIs for active categories
        document.querySelectorAll('.poi-btn.active').forEach(button => {
            fetchNearbyPOIs(marker.getLatLng(), button.dataset.type);
        });
    });
}

// Create pandal popup content
function createPandalPopupContent(pandal) {
    return L.popup().setContent(`
        <div class="info-window">
            <h3>${pandal.name}</h3>
            <p><strong>Theme:</strong> ${pandal.theme || 'N/A'}</p>
            <p><strong>Idol Type:</strong> ${pandal.idol_type || 'N/A'}</p>
            <p><strong>Area:</strong> ${pandal.area || 'N/A'}</p>
            <p><strong>Timings:</strong> ${pandal.opening_time || '08:00'} - ${pandal.closing_time || '22:00'}</p>
            <div class="poi-list">
                <h4>Nearby Places</h4>
                <div id="poi-results">
                    <p>Click POI buttons above to see nearby places</p>
                </div>
            </div>
        </div>
    `);
}

// Fetch nearby POIs using Overpass API
function fetchNearbyPOIs(position, poiType) {
    const radius = 1000; // 1km radius
    const query = buildOverpassQuery(position.lat, position.lng, radius, poiType);
    
    fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: `data=${encodeURIComponent(query)}`
    })
        .then(response => response.json())
        .then(data => {
            displayPOIs(data.elements, poiType);
        })
        .catch(error => console.error('Error fetching POIs:', error));
}

// Build Overpass API query
function buildOverpassQuery(lat, lon, radius, type) {
    let amenity;
    switch (type) {
        case 'hospital':
            amenity = 'hospital';
            break;
        case 'police':
            amenity = 'police';
            break;
        case 'pharmacy':
            amenity = 'pharmacy';
            break;
        case 'restaurant':
            amenity = 'restaurant';
            break;
    }

    return `[out:json][timeout:25];
    (
      node["amenity"="${amenity}"](around:${radius},${lat},${lon});
      way["amenity"="${amenity}"](around:${radius},${lat},${lon});
      relation["amenity"="${amenity}"](around:${radius},${lat},${lon});
    );
    out body;
    >;
    out skel qt;`;
}

// Display POIs on map and in info window
function displayPOIs(pois, type) {
    clearPOIMarkers(type);
    
    const poiResults = document.getElementById('poi-results');
    let poiHTML = '';
    
    pois.forEach(poi => {
        if (poi.type === 'node' && poi.lat && poi.lon) {
            // Add marker
            const marker = L.marker([poi.lat, poi.lon], {
                icon: L.divIcon({
                    className: 'poi-marker',
                    html: getPOIIcon(type)
                })
            }).addTo(map);

            marker.poiType = type;
            poiMarkers.push(marker);
            
            // Add to info window list
            poiHTML += `
                <div class="poi-item">
                    ${getPOIIcon(type)}
                    <span>${poi.tags.name || getPoiTypeLabel(type)}</span>
                </div>
            `;
        }
    });
    
    if (poiHTML) {
        const typeSection = document.createElement('div');
        typeSection.innerHTML = `
            <h4>${getPoiTypeLabel(type)}s Nearby</h4>
            ${poiHTML}
        `;
        poiResults.appendChild(typeSection);
    }
}

// Get POI icon based on type
function getPOIIcon(type) {
    // Using Font Awesome icons instead of Google Maps icons
    switch (type) {
        case 'hospital':
            return '<i class="fas fa-hospital text-blue"></i>';
        case 'police':
            return '<i class="fas fa-shield-alt text-purple"></i>';
        case 'pharmacy':
            return '<i class="fas fa-prescription-bottle-alt text-green"></i>';
        case 'restaurant':
            return '<i class="fas fa-utensils text-yellow"></i>';
        default:
            return '<i class="fas fa-map-marker-alt text-blue"></i>';
    }
}

// Get POI type label
function getPoiTypeLabel(type) {
    switch (type) {
        case 'hospital':
            return 'Hospital';
        case 'police':
            return 'Police Station';
        case 'pharmacy':
            return 'Pharmacy';
        case 'restaurant':
            return 'Restaurant';
        default:
            return type.charAt(0).toUpperCase() + type.slice(1);
    }
}

// Clear POI markers of a specific type
function clearPOIMarkers(type) {
    poiMarkers = poiMarkers.filter(marker => {
        if (marker.poiType === type) {
            map.removeLayer(marker);
            return false;
        }
        return true;
    });
}

// Clear all POI markers
function clearAllPOIMarkers() {
    poiMarkers.forEach(marker => map.removeLayer(marker));
    poiMarkers = [];
    if (document.getElementById('poi-results')) {
        document.getElementById('poi-results').innerHTML = '<p>Click POI buttons above to see nearby places</p>';
    }
}

// Initialize map when it becomes visible
function initMapWhenVisible() {
    // Check if map div exists
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;

    // Initialize map if not already initialized
    if (!window.map) {
        initMap();
    } else {
        // Update map size when displayed in modal
        map.invalidateSize();
        
        // Fit bounds to show all markers if they exist
        if (markers.length > 0) {
            const group = L.featureGroup(markers);
            map.fitBounds(group.getBounds());
        }
    }
}
