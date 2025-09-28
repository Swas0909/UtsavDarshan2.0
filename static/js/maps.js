let map;
let markers = [];
let infoWindow;

// Initialize the map
function initMap() {
    // Default center (Mumbai)
    const defaultCenter = { lat: 19.0760, lng: 72.8777 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        center: defaultCenter,
        zoom: 12
    });

    infoWindow = new google.maps.InfoWindow();

    // Fetch pandals and add markers
    fetchPandals();
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
        title: pandal.name
    });

    markers.push(marker);

    marker.addListener("click", () => {
        const lat = pandal.lat;
        const lon = pandal.lon;

        // Show pandal info with a "nearby" section
        infoWindow.setContent(`
            <div class="info-window">
                <h3>${pandal.name}</h3>
                <p><strong>Theme:</strong> ${pandal.theme || 'Traditional'}</p>
                <p><strong>Idol Type:</strong> ${pandal.idol_type || 'N/A'}</p>
                <p><strong>Area:</strong> ${pandal.area || 'N/A'}</p>
                <div id="nearby">Loading nearby services...</div>
            </div>
        `);
        infoWindow.open(map, marker);

        // Fetch nearby POIs using Overpass API
        fetchNearbyPOIs(lat, lon);
    });
}

// Fetch nearby POIs using Overpass API
function fetchNearbyPOIs(lat, lon) {
    // Overpass query: find hospital, police, pharmacy, restaurant within 1 km
    const query = `
        [out:json];
        (
            node["amenity"="hospital"](around:1000,${lat},${lon});
            node["amenity"="police"](around:1000,${lat},${lon});
            node["amenity"="pharmacy"](around:1000,${lat},${lon});
            node["amenity"="restaurant"](around:1000,${lat},${lon});
        );
        out;
    `;

    const url = "https://overpass-api.de/api/interpreter?data=" + encodeURIComponent(query);

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.elements || data.elements.length === 0) {
                document.getElementById("nearby").innerHTML = "<p>No nearby services found.</p>";
                return;
            }

            // Group POIs by type
            const groupedPOIs = data.elements.reduce((acc, el) => {
                const type = el.tags?.amenity || "unknown";
                if (!acc[type]) acc[type] = [];
                acc[type].push(el);
                return acc;
            }, {});

            // Create HTML with grouped POIs
            let html = "<h4>Nearby Services</h4>";
            
            for (const [type, pois] of Object.entries(groupedPOIs)) {
                html += `<h5>${type.charAt(0).toUpperCase() + type.slice(1)}s</h5><ul>`;
                pois.forEach(poi => {
                    const name = poi.tags?.name || "Unnamed";
                    html += `<li>${name}</li>`;
                });
                html += "</ul>";
            }

            document.getElementById("nearby").innerHTML = html;
        })
        .catch(err => {
            console.error("Overpass API error:", err);
            document.getElementById("nearby").innerHTML = "<p>Error fetching nearby services.</p>";
        });
}

// Initialize map when the page loads
window.addEventListener('load', initMap);
