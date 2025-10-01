#!/usr/bin/env python3
"""
UtsavDarshan Demo App with Google Maps Integration
Runs without MongoDB dependency for testing the Google Maps functionality
"""

import json
from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

# Sample pandal data
SAMPLE_PANDALS = [
    {
        "id": "1",
        "name": "Lalbaugcha Raja",
        "theme": "Traditional",
        "idol_type": "Clay", 
        "area": "Lalbaug",
        "address": "Lalbaug, Mumbai, Maharashtra",
        "opening_time": "06:00",
        "closing_time": "22:00",
        "lat": 18.9777,
        "lon": 72.8333
    },
    {
        "id": "2",
        "name": "GSB Ganpati Matunga", 
        "theme": "Traditional",
        "idol_type": "Eco-friendly",
        "area": "Matunga",
        "address": "Matunga, Mumbai, Maharashtra", 
        "opening_time": "05:00",
        "closing_time": "23:00",
        "lat": 19.0291,
        "lon": 72.8583
    },
    {
        "id": "3",
        "name": "Kamathipura Cha Ganraj",
        "theme": "Cultural",
        "idol_type": "Traditional",
        "area": "Kamathipura", 
        "address": "Kamathipura, Mumbai, Maharashtra",
        "opening_time": "06:00",
        "closing_time": "22:00",
        "lat": 18.9653,
        "lon": 72.8276
    },
    {
        "id": "4",
        "name": "Mumbai Cha Raja",
        "theme": "Modern",
        "idol_type": "Clay",
        "area": "Fort",
        "address": "Fort, Mumbai, Maharashtra",
        "opening_time": "07:00", 
        "closing_time": "21:00",
        "lat": 18.9390,
        "lon": 72.8347
    },
    {
        "id": "5",
        "name": "Andhericha Raja",
        "theme": "Traditional",
        "idol_type": "Eco-friendly",
        "area": "Andheri",
        "address": "Andheri, Mumbai, Maharashtra",
        "opening_time": "06:00",
        "closing_time": "22:00", 
        "lat": 19.1136,
        "lon": 72.8697
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/locations')
def locations():
    areas = list(set(p['area'] for p in SAMPLE_PANDALS))
    talukas = [{'name': area} for area in sorted(areas)]
    return render_template('locations.html', talukas=talukas)

@app.route('/register_pandal', methods=['GET', 'POST'])
def register_pandal():
    if request.method == 'POST':
        return jsonify({'success': True, 'message': 'Pandal registered successfully'})
    return render_template('register_pandal.html')

@app.route('/pandal/<pandal_id>')
def pandal_detail(pandal_id):
    pandal = next((p for p in SAMPLE_PANDALS if p['id'] == pandal_id), None)
    if not pandal:
        return render_template('index.html')
    return render_template('pandal.html', pandal=pandal)

@app.route('/feedback', methods=['POST'])
def feedback():
    return jsonify({'success': True, 'message': 'Feedback submitted successfully'})

@app.route('/api/pandals', methods=['GET'])
def api_get_pandals():
    return jsonify(SAMPLE_PANDALS)

@app.route('/api/pandals/filtered', methods=['GET'])
def get_filtered_pandals():
    """Get pandals with filtering options"""
    theme = request.args.get('theme')
    idol_type = request.args.get('idol_type')
    area = request.args.get('area')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    distance = request.args.get('distance', type=int, default=5000)
    
    filtered = SAMPLE_PANDALS.copy()
    
    if theme:
        filtered = [p for p in filtered if theme.lower() in p['theme'].lower()]
    if idol_type:
        filtered = [p for p in filtered if idol_type.lower() in p['idol_type'].lower()]
    if area:
        filtered = [p for p in filtered if area.lower() in p['area'].lower()]
    
    if lat and lon:
        def distance_calc(lat1, lon1, lat2, lon2):
            return abs(lat1 - lat2) + abs(lon1 - lon2)
        
        max_dist = distance / 111000
        filtered = [
            p for p in filtered 
            if distance_calc(lat, lon, p['lat'], p['lon']) <= max_dist
        ]
    
    return jsonify(filtered)

@app.route('/api/nearby-pois', methods=['GET'])
def get_nearby_pois():
    """Get nearby POIs using Google Places API"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float) 
    radius = request.args.get('radius', type=int, default=2000)
    poi_types = request.args.get('types', 'hospital,police,pharmacy,restaurant').split(',')
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    api_key = 'AIzaSyACmm4cbgqxOWmSBa-qAQU69oXMJAR1Hw8'
    all_pois = []
    
    for poi_type in poi_types:
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'location': f'{lat},{lon}',
            'radius': radius,
            'type': poi_type.strip(),
            'key': api_key
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for place in data.get('results', [])[:3]:
                    poi = {
                        'id': place.get('place_id'),
                        'name': place.get('name'),
                        'type': poi_type.strip(),
                        'rating': place.get('rating'),
                        'lat': place['geometry']['location']['lat'],
                        'lon': place['geometry']['location']['lng'],
                        'vicinity': place.get('vicinity'),
                        'open_now': place.get('opening_hours', {}).get('open_now')
                    }
                    all_pois.append(poi)
        except Exception as e:
            print(f'Error fetching {poi_type}: {str(e)}')
    
    return jsonify(all_pois)

@app.route('/api/filter-options', methods=['GET'])
def get_filter_options():
    """Get available filter options"""
    themes = list(set(p['theme'] for p in SAMPLE_PANDALS))
    idol_types = list(set(p['idol_type'] for p in SAMPLE_PANDALS))
    areas = list(set(p['area'] for p in SAMPLE_PANDALS))
    
    return jsonify({
        'themes': sorted(themes),
        'idol_types': sorted(idol_types), 
        'areas': sorted(areas)
    })

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    print("Starting UtsavDarshan Demo with Google Maps...")
    print("Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)