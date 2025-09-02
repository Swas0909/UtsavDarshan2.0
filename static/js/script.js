// For index.html map buttons
document.addEventListener('DOMContentLoaded', () => {
    const mapButtons = document.querySelectorAll('.map-btn');
    mapButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = btn.getAttribute('data-lat');
            const lng = btn.getAttribute('data-lng');
            // Open Google Maps with directions (assuming user's location, but for demo, just show location)
            const url = `https://www.google.com/maps?q=${lat},${lng}`;
            window.open(url, '_blank');
        });
    });
});
