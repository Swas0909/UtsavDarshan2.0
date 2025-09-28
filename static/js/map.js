let map;
let markers = [];
let infoWindow;
let poiMarkers = [];

// Initialize the map
function initMap() {
    // Default center (Mumbai)
    const defaultCenter = { lat: 19.0760, lng: 72.8777 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        center: defaultCenter,
        zoom: 12,
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });

    infoWindow = new google.maps.InfoWindow();

    // Fetch pandals and add markers
    fetchPandals();

    // Add click handlers for POI toggle buttons
    document.querySelectorAll('.poi-btn').forEach(button => {
        button.addEventListener('click', () => {
            button.classList.toggle('active');
            if (button.classList.contains('active')) {
                const poiType = button.dataset.type;
                const activeMarker = markers.find(m => m.infoWindow.getMap());
                if (activeMarker) {
                    fetchNearbyPOIs(activeMarker.position, poiType);
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
    const position = { lat: pandal.lat, lng: pandal.lon };
    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: pandal.name,
        icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
        }
    });

    marker.position = position;
    markers.push(marker);

    marker.addListener('click', () => {
        showPandalInfo(marker, pandal);
        // Clear existing POI markers
        clearAllPOIMarkers();
        // Fetch new POIs for active categories
        document.querySelectorAll('.poi-btn.active').forEach(button => {
            fetchNearbyPOIs(position, button.dataset.type);
        });
    });
}

// Show pandal information in info window
function showPandalInfo(marker, pandal) {
    const content = `
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
    `;

    infoWindow.setContent(content);
    infoWindow.open(map, marker);
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
            const marker = new google.maps.Marker({
                position: { lat: poi.lat, lng: poi.lon },
                map: map,
                icon: getPOIIcon(type),
                title: poi.tags.name || getPoiTypeLabel(type)
            });
            
            marker.poiType = type;
            poiMarkers.push(marker);
            
            // Add to info window list
            poiHTML += `
                <div class="poi-item">
                    <i class="${getPOIIcon(type)}"></i>
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
    switch (type) {
        case 'hospital':
            return 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png';
        case 'police':
            return 'https://maps.google.com/mapfiles/ms/icons/purple-dot.png';
        case 'pharmacy':
            return 'https://maps.google.com/mapfiles/ms/icons/green-dot.png';
        case 'restaurant':
            return 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
        default:
            return 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png';
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
            marker.setMap(null);
            return false;
        }
        return true;
    });
}

// Clear all POI markers
function clearAllPOIMarkers() {
    poiMarkers.forEach(marker => marker.setMap(null));
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
        // Trigger a resize event to fix the map display in modal
        google.maps.event.trigger(window.map, 'resize');
        
        // Fit bounds to show all markers if they exist
        if (markers.length > 0) {
            const bounds = new google.maps.LatLngBounds();
            markers.forEach(marker => bounds.extend(marker.position));
            window.map.fitBounds(bounds);
        }
    }
}
