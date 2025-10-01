let map;
let markers = [];
let poiMarkers = [];
let markerCluster;
let userLocation;
let currentPandalRoute = null;
let layerControl;
let heatmapLayer;

// Custom icons for markers
const icons = {
    user: L.icon({
        iconUrl: '/static/images/user-location.png',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    }),
    pandal: L.icon({
        iconUrl: '/static/images/pandal-marker.svg',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    }),
    hospital: L.icon({
        iconUrl: '/static/images/poi/hospital.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    }),
    police: L.icon({
        iconUrl: '/static/images/poi/police.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    }),
    restaurant: L.icon({
        iconUrl: '/static/images/poi/restaurant.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    }),
    parking: L.icon({
        iconUrl: '/static/images/poi/parking.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    }),
    bus_station: L.icon({
        iconUrl: '/static/images/poi/bus.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    }),
    default: L.icon({
        iconUrl: '/static/images/poi/default.svg',
        iconSize: [24, 24],
        iconAnchor: [12, 24],
        popupAnchor: [0, -24]
    })
};

// Initialize the map
function initMap() {
    console.log('Initializing map...');
    
    // Make sure the map container exists
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }

    // If map already exists, clean up and refresh
    if (window.map) {
        console.log('Map already initialized, cleaning up and refreshing...');
        
        // Clear existing markers
        if (window.markerCluster) {
            window.markerCluster.clearLayers();
        }
        if (markers && markers.length > 0) {
            markers.forEach(marker => {
                if (window.map.hasLayer(marker)) {
                    window.map.removeLayer(marker);
                }
            });
            markers = [];
        }
        
        // Refresh pandals and fit bounds
        fetchPandals();
        return;
    }

    // Default center (Mumbai)
    const defaultCenter = [19.0760, 72.8777];
    
    // Initialize the map
    window.map = L.map('map', {
        center: defaultCenter,
        zoom: 11,
        minZoom: 3,
        maxZoom: 18,
        zoomControl: false // We'll add it in a custom position
    });
    
    // Store reference for global access
    map = window.map;
    window.markers = markers; // Make markers globally accessible
    
    console.log('Map initialized successfully');
    
    // Add the tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add essential controls
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.control.scale().addTo(map);
    
    // Initialize marker clustering
    markerCluster = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });
    map.addLayer(markerCluster);
    
    // Store reference for global access
    window.markerCluster = markerCluster;

    // Add location control
    L.control.locate({
        position: 'bottomright',
        drawCircle: true,
        follow: false,
        setView: 'untilPanOrZoom',
        keepCurrentZoomLevel: true,
        markerStyle: {
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.8
        },
        circleStyle: {
            weight: 1,
            clickable: false
        },
        icon: 'fa fa-location-arrow',
        metric: true,
        strings: {
            title: 'Show me where I am'
        },
        locateOptions: {
            maxZoom: 16,
            enableHighAccuracy: true
        }
    }).addTo(map);

    // Get user's location (optional)
    getUserLocation();
    
    // Fetch pandals and add markers - THIS IS THE KEY FIX
    fetchPandals();
    
    // Add event listeners for POI toggles
    setupPOIToggles();

    // Fix map display when modal is shown
    const mapModal = document.getElementById('mapModal');
    if (mapModal) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'style' && 
                    mapModal.style.display === 'block') {
                    setTimeout(() => {
                        if (map && map.invalidateSize) {
                            map.invalidateSize();
                            console.log('Map invalidated and refreshed');
                            
                            // Force reload pandals when map modal opens
                            fetchPandals();
                            
                            // Ensure all pandals are visible after loading
                            setTimeout(() => {
                                if (markerCluster && markerCluster.getLayers().length > 0) {
                                    const bounds = markerCluster.getBounds();
                                    if (bounds.isValid()) {
                                        map.fitBounds(bounds, { padding: [20, 20] });
                                        console.log('Map bounds fitted to show all pandals');
                                    } else {
                                        console.log('Invalid bounds, using default view');
                                        map.setView([19.0760, 72.8777], 11);
                                    }
                                } else {
                                    console.log('No markers found, using default Mumbai view');
                                    map.setView([19.0760, 72.8777], 11);
                                }
                            }, 1000);
                        }
                    }, 300);
                }
            });
        });
        observer.observe(mapModal, { attributes: true });
    }
    
    console.log('Map initialization completed');
}

// Get user's location
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Add user marker
                L.marker([userLocation.lat, userLocation.lng], {
                    icon: icons.user,
                    title: 'Your Location'
                }).addTo(map);

                // Center map on user location
                map.setView([userLocation.lat, userLocation.lng], 13);
                
                // Update nearby pandals
                updateNearbyPandals();
            },
            () => {
                console.log('Error: The Geolocation service failed.');
            }
        );
    }
}

// Fetch pandals from the backend
function fetchPandals() {
    console.log('Fetching pandals for map display...');
    
    // Use the enhanced API endpoint that works correctly
    fetch('/api/pandals/enhanced')
        .then(response => {
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received pandals data:', data);
            const pandals = data.pandals || data; // Handle both response formats
            
            // Clear existing markers
            markers.forEach(marker => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
            markers = [];
            
            // Clear marker cluster
            if (markerCluster) {
                markerCluster.clearLayers();
            }
            
            console.log(`Processing ${pandals.length} pandals for map display`);
            
            pandals.forEach((pandal, index) => {
                if (pandal.lat && pandal.lon) {
                    try {
                        const marker = addPandalMarker(pandal);
                        if (marker && markerCluster) {
                            markerCluster.addLayer(marker);
                        }
                    } catch (error) {
                        console.error(`Error adding marker for pandal ${pandal.name}:`, error);
                    }
                } else {
                    console.warn(`Pandal ${pandal.name} has no coordinates:`, pandal);
                }
            });
            
            console.log(`Added ${markers.length} markers to the map`);
            
            // Create heatmap layer if we have the plugin
            if (typeof L.heatLayer === 'function') {
                createHeatmap(pandals);
            }
            
            // Fit map to show all markers after a short delay
            setTimeout(() => {
                if (markerCluster && markerCluster.getLayers().length > 0) {
                    console.log('Fitting map bounds to show all pandals');
                    map.fitBounds(markerCluster.getBounds(), { padding: [20, 20] });
                } else {
                    console.log('No markers to fit bounds, using default Mumbai view');
                    map.setView([19.0760, 72.8777], 11);
                }
            }, 500);
        })
        .catch(error => {
            console.error('Error fetching pandals:', error);
            // Fallback to default view
            map.setView([19.0760, 72.8777], 11);
        });
}

// Add a marker for a pandal
function addPandalMarker(pandal) {
    console.log('Adding marker for pandal:', pandal.name);
    
    const marker = L.marker([pandal.lat, pandal.lon], {
        icon: icons.pandal,
        title: pandal.name
    });

    markers.push(marker);

    const contentString = `
        <div class="info-window">
            <h3>${pandal.name}</h3>
            <p><strong>Theme:</strong> ${pandal.theme || 'Traditional'}</p>
            <p><strong>Area:</strong> ${pandal.area || 'N/A'}</p>
            <p><strong>Timings:</strong> ${pandal.opening_time || '08:00'} - ${pandal.closing_time || '22:00'}</p>
            ${pandal.average_rating ? `<p><strong>Rating:</strong> ${pandal.average_rating} ⭐ (${pandal.rating_count || 0} reviews)</p>` : ''}
            ${pandal.distance ? `<p><strong>Distance:</strong> ${pandal.distance} km away</p>` : ''}
            <div class="info-window-buttons">
                <button onclick="getDirections(${pandal.lat}, ${pandal.lon})">Get Directions</button>
                <button onclick="showPandalDetails('${pandal._id || pandal.id}')">View Details</button>
            </div>
        </div>
    `;

    marker.bindPopup(contentString);
    
    marker.on('click', () => {
        if (currentPandalRoute) {
            map.removeLayer(currentPandalRoute);
        }
        // Optional: fetch nearby POIs
        // fetchNearbyPOIs(pandal.lat, pandal.lon, pandal._id || pandal.id);
        highlightRoute([pandal.lat, pandal.lon]);
    });

    return marker;
}

// Get directions to a pandal using OSRM
function getDirections(lat, lon) {
    if (!userLocation) {
        alert('Please enable location services to get directions.');
        return;
    }

    const destination = [lon, lat]; // OSRM expects coordinates in [longitude, latitude] format
    const origin = [userLocation.lng, userLocation.lat];
    
    // Clear previous route
    if (currentPandalRoute) {
        map.removeLayer(currentPandalRoute);
    }

    // Using OSRM public instance
    fetch(`https://router.project-osrm.org/route/v1/driving/${origin};${destination}?overview=full&geometries=geojson`)
        .then(response => response.json())
        .then(data => {
            if (data.routes && data.routes.length > 0) {
                const route = data.routes[0];
                const coordinates = route.geometry.coordinates;
                
                // Convert coordinates to Leaflet format [lat, lng]
                const latLngs = coordinates.map(coord => [coord[1], coord[0]]);
                
                // Create route polyline
                currentPandalRoute = L.polyline(latLngs, {
                    color: '#0066CC',
                    weight: 5,
                    opacity: 0.7
                }).addTo(map);
                
                // Fit map to show the entire route
                map.fitBounds(currentPandalRoute.getBounds());
                
                // Show directions in panel
                const directionsPanel = document.getElementById('directions-panel');
                directionsPanel.style.display = 'block';
                directionsPanel.innerHTML = `
                    <div class="directions-info">
                        <h3>Route Information</h3>
                        <p>Distance: ${(route.distance / 1000).toFixed(2)} km</p>
                        <p>Duration: ${Math.round(route.duration / 60)} minutes</p>
                    </div>
                `;
            } else {
                alert('Could not calculate directions. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error getting directions:', error);
            alert('Error calculating directions. Please try again later.');
        });
}

// Fetch nearby POIs using Overpass API
function fetchNearbyPOIs(lat, lon, pandalId) {
    poiMarkers.forEach(m => map.removeLayer(m));
    poiMarkers = [];

    const types = [
        { type: 'hospital', query: 'amenity=hospital' },
        { type: 'police', query: 'amenity=police' },
        { type: 'restaurant', query: 'amenity=restaurant' },
        { type: 'parking', query: 'amenity=parking' },
        { type: 'bus_station', query: 'highway=bus_stop' }
    ];

    const radius = 1000; // 1km radius
    const promises = types.map(({ type, query }) => {
        const overpassQuery = `
            [out:json][timeout:25];
            (
                node["${query}"](around:${radius},${lat},${lon});
                way["${query}"](around:${radius},${lat},${lon});
                relation["${query}"](around:${radius},${lat},${lon});
            );
            out body;
            >;
            out skel qt;
        `;

        return fetch(`https://overpass-api.de/api/interpreter`, {
            method: 'POST',
            body: overpassQuery
        })
        .then(response => response.json())
        .then(data => ({ type, places: data.elements }));
    });

    Promise.all(promises)
        .then(results => {
            let html = '<h4>Nearby Services</h4><div class="poi-list">';
            
            results.forEach(({ type, places }) => {
                if (places.length > 0) {
                    html += `<div class="poi-category"><h5>${type.replace('_', ' ').toUpperCase()}</h5><ul>`;
                    
                    places.forEach(place => {
                        if (place.lat && place.lon) { // Only add markers for nodes with coordinates
                            const marker = L.marker([place.lat, place.lon], {
                                icon: icons[type] || icons.default,
                                title: place.tags.name || type
                            });
                            
                            poiMarkers.push(marker);
                            
                            const popupContent = `
                                <div class="poi-info">
                                    <h4>${place.tags.name || type}</h4>
                                    <p>${place.tags.address || ''}</p>
                                    <button onclick="getDirections(${place.lat}, ${place.lon})">
                                        Directions
                                    </button>
                                </div>
                            `;
                            
                            marker.bindPopup(popupContent);
                            marker.addTo(map);

                            html += `
                                <li>
                                    <strong>${place.tags.name || type}</strong>
                                    <br>${place.tags.address || ''}
                                </li>
                            `;
                        }
                    });
                    
                    html += '</ul></div>';
                }
            });
            
            html += '</div>';
            document.getElementById(`nearby-${pandalId}`).innerHTML = html;
        })
        .catch(error => {
            console.error('Error fetching POIs:', error);
            document.getElementById(`nearby-${pandalId}`).innerHTML = 
                '<p>Error loading nearby services. Please try again later.</p>';
        });
}

// Show interactive map in new window
function showInteractiveMap(pandalId) {
    const mapUrl = `/map/pandal/${pandalId}`;
    window.open(mapUrl, '_blank', 'width=800,height=600');
}

// Create heatmap layer
function createHeatmap(pandals) {
    if (typeof L.heatLayer !== 'function') {
        console.warn('Leaflet.heat plugin not loaded');
        return;
    }

    if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
    }

    const points = pandals
        .filter(pandal => pandal.lat && pandal.lon)
        .map(pandal => [pandal.lat, pandal.lon, 1]);

    heatmapLayer = L.heatLayer(points, {
        radius: 25,
        blur: 15,
        maxZoom: 10
    });
}

// Add custom controls to map
function addCustomControls() {
    // Add heatmap toggle
    const heatmapControl = L.Control.extend({
        options: {
            position: 'topright'
        },
        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'custom-map-control leaflet-bar');
            container.innerHTML = '<a href="#" title="Toggle Heatmap">🔥</a>';
            
            L.DomEvent.on(container, 'click', function(e) {
                L.DomEvent.stopPropagation(e);
                L.DomEvent.preventDefault(e);
                if (map.hasLayer(heatmapLayer)) {
                    map.removeLayer(heatmapLayer);
                } else if (heatmapLayer) {
                    heatmapLayer.addTo(map);
                }
            });
            
            return container;
        }
    });

    map.addControl(new heatmapControl());

    // Add cluster toggle
    const clusterControl = L.Control.extend({
        options: {
            position: 'topright'
        },
        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'custom-map-control leaflet-bar');
            container.innerHTML = '<a href="#" title="Toggle Clustering">👥</a>';
            
            L.DomEvent.on(container, 'click', function(e) {
                L.DomEvent.stopPropagation(e);
                L.DomEvent.preventDefault(e);
                if (map.hasLayer(markerCluster)) {
                    map.removeLayer(markerCluster);
                    markers.forEach(marker => marker.addTo(map));
                } else {
                    markers.forEach(marker => map.removeLayer(marker));
                    markerCluster.addTo(map);
                }
            });
            
            return container;
        }
    });

    map.addControl(new clusterControl());
}

// Setup POI toggle buttons
function setupPOIToggles() {
    const poiButtons = document.querySelectorAll('.poi-btn');
    poiButtons.forEach(button => {
        button.addEventListener('click', () => {
            const type = button.dataset.type;
            button.classList.toggle('active');
            togglePOIType(type, button.classList.contains('active'));
        });
    });
}

// Toggle POI visibility by type
function togglePOIType(type, visible) {
    poiMarkers.forEach(marker => {
        if (marker.options.poiType === type) {
            if (visible) {
                marker.addTo(map);
            } else {
                map.removeLayer(marker);
            }
        }
    });
}

// Get POI icon based on type
function getPOIIcon(type) {
    return icons[type] || icons.default;
}

// Highlight route to pandal
function highlightRoute(destination) {
    if (!userLocation) return;
    
    if (currentPandalRoute) {
        map.removeLayer(currentPandalRoute);
    }

    currentPandalRoute = L.polyline([
        [userLocation.lat, userLocation.lng],
        destination
    ], {
        color: '#FF0000',
        weight: 2,
        opacity: 0.5
    }).addTo(map);
}

// Update nearby pandals list
function updateNearbyPandals() {
    if (!userLocation) return;
    
    const url = `/api/pandals/nearby?lat=${userLocation.lat}&lon=${userLocation.lng}&radius=5000`;
    fetch(url)
        .then(response => response.json())
        .then(pandals => {
            const nearbyList = document.getElementById('nearby-pandals-list');
            if (nearbyList) {
                nearbyList.innerHTML = pandals.map(pandal => `
                    <div class="nearby-pandal-item">
                        <h4>${pandal.name}</h4>
                        <p>Distance: ${pandal.distance} km</p>
                        <p>ETA: ${pandal.duration || 'N/A'}</p>
                        <button onclick="getDirections(${pandal.lat}, ${pandal.lon})">
                            Get Directions
                        </button>
                    </div>
                `).join('');
            }
        });
}

// Initialize map when the page loads
window.addEventListener('load', initMap);

// Make key functions globally accessible
window.initMap = initMap;
window.fetchPandals = fetchPandals;
window.addPandalMarker = addPandalMarker;
window.getDirections = getDirections;
