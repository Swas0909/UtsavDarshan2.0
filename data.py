# Sample data for Ganapati Pandals
pandals = [
    {
        'id': 1,
        'name': 'Lalbaugcha Raja',
        'taluka': 'Mumbai Suburban',
        'location': {'lat': 18.9777, 'lng': 72.8333},
        'history': 'One of the most famous Ganesh idols in Mumbai, known for its grandeur.',
        'timings': 'Open 24 hours during festival',
        'image': 'https://via.placeholder.com/300x200?text=Lalbaugcha+Raja'
    },
    {
        'id': 2,
        'name': 'Siddhivinayak Temple',
        'taluka': 'Mumbai Suburban',
        'location': {'lat': 19.0178, 'lng': 72.8308},
        'history': 'A historic temple dedicated to Lord Ganesha.',
        'timings': '5:30 AM to 9:30 PM',
        'image': 'https://via.placeholder.com/300x200?text=Siddhivinayak'
    },
    {
        'id': 3,
        'name': 'Ganesh Galli Pandals',
        'taluka': 'Thane',
        'location': {'lat': 19.2183, 'lng': 72.9781},
        'history': 'Famous for unique themes and decorations.',
        'timings': '6:00 AM to 11:00 PM',
        'image': 'https://via.placeholder.com/300x200?text=Ganesh+Galli'
    },
    {
        'id': 4,
        'name': 'Powai Ganpati',
        'taluka': 'Mumbai Suburban',
        'location': {'lat': 19.1197, 'lng': 72.9051},
        'history': 'Known for eco-friendly decorations.',
        'timings': '7:00 AM to 10:00 PM',
        'image': 'https://via.placeholder.com/300x200?text=Powai+Ganpati'
    }
]

talukas = [
    {'name': 'Mumbai Suburban', 'pandals': [p for p in pandals if p['taluka'] == 'Mumbai Suburban']},
    {'name': 'Thane', 'pandals': [p for p in pandals if p['taluka'] == 'Thane']},
    {'name': 'Raigad', 'pandals': []},  # Add more as needed
    {'name': 'Palghar', 'pandals': []}
]
