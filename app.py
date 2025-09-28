from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import config
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import folium
from folium import plugins
import tempfile
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config)

# Initialize Nominatim geocoder with a custom user agent
geolocator = Nominatim(user_agent="UtsavDarshan_" + datetime.now().strftime("%Y%m%d"))

# MongoDB connection
app.config["MONGO_URI"] = config.MONGO_URI
mongo = PyMongo(app)

# Collections
pandals = mongo.db.pandals
users = mongo.db.users
visits = mongo.db.visits
ratings = mongo.db.ratings
badges = mongo.db.badges

@app.route('/')
def index():
    # Get only 4 pandals for the homepage
    pandal_list = list(pandals.find().limit(4))
    return render_template('index.html', 
                         pandals=pandal_list,
                         GOOGLE_MAPS_API_KEY='AIzaSyACmm4cbgqxOWmSBa-qAQU69oXMJAR1Hw8')

@app.route('/all-pandals')
def all_pandals():
    pandal_list = list(pandals.find())
    return render_template('all_pandals.html', 
                         pandals=pandal_list,
                         GOOGLE_MAPS_API_KEY=config.GOOGLE_MAPS_API_KEY)

@app.route('/locations')
def locations():
    # Get unique areas (talukas) from pandals collection
    pipeline = [
        {"$group": {"_id": "$area"}},
        {"$sort": {"_id": 1}}
    ]
    areas = list(pandals.aggregate(pipeline))
    talukas = [{"name": area["_id"]} for area in areas if area["_id"]]
    return render_template('locations.html', talukas=talukas)

@app.route('/taluka/<taluka_name>')
def taluka_pandals(taluka_name):
    # Get pandals for the specified taluka
    pandal_list = list(pandals.find({"area": taluka_name}))
    if not pandal_list:
        return redirect(url_for('locations'))
    taluka = {"name": taluka_name, "pandals": pandal_list}
    return render_template('taluka.html', taluka=taluka)

@app.route('/pandal/<pandal_id>')
def pandal_detail(pandal_id):
    try:
        pandal = pandals.find_one({"_id": ObjectId(pandal_id)})
        if not pandal:
            return redirect(url_for('index'))
        return render_template('pandal.html', pandal=pandal)
    except:
        return redirect(url_for('index'))

@app.route('/feedback', methods=['POST'])
def feedback():
    if request.method == 'POST':
        user_feedback = request.form.get('feedback')
        # Store feedback in MongoDB
        feedback_data = {
            "feedback": user_feedback,
            "timestamp": mongo.db.command('serverStatus')['localTime']
        }
        mongo.db.feedback.insert_one(feedback_data)
        return redirect(url_for('index'))

@app.route('/register_pandal', methods=['GET', 'POST'])
def register_pandal():
    if request.method == 'POST':
        address = f"{request.form.get('details', '')}, {request.form.get('location', '')}"
        
        # Try to geocode the address using Nominatim
        try:
            location = geolocator.geocode(address)
            if location:
                lat = location.latitude
                lon = location.longitude
                formatted_address = location.address
            else:
                lat = float(request.form.get('latitude', 0))
                lon = float(request.form.get('longitude', 0))
                formatted_address = address
        except Exception:
            lat = float(request.form.get('latitude', 0))
            lon = float(request.form.get('longitude', 0))
            formatted_address = address

        # Create a new pandal document
        new_pandal = {
            "name": request.form.get('name'),
            "theme": request.form.get('theme', 'Traditional'),
            "idol_type": request.form.get('idol_type', 'Eco-friendly'),
            "area": request.form.get('location'),
            "address": formatted_address,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "opening_time": request.form.get('opening_time', '08:00'),
            "closing_time": request.form.get('closing_time', '22:00'),
            "created_at": mongo.db.command('serverStatus')['localTime']
        }
        pandals.insert_one(new_pandal)
        return redirect(url_for('index'))
    return render_template('register_pandal.html')

# API Endpoints
@app.route('/api/pandals', methods=['GET'])
def api_get_pandals():
    results = []
    for p in pandals.find():
        results.append({
            "id": str(p["_id"]),
            "name": p.get("name"),
            "theme": p.get("theme"),
            "idol_type": p.get("idol_type"),
            "area": p.get("area"),
            "lat": p["location"]["coordinates"][1] if "location" in p else None,
            "lon": p["location"]["coordinates"][0] if "location" in p else None
        })
    return jsonify(results)

@app.route('/api/pandals/<pandal_id>', methods=['GET'])
def api_get_pandal(pandal_id):
    try:
        pandal = pandals.find_one({"_id": ObjectId(pandal_id)})
        if not pandal:
            return jsonify({"error": "Pandal not found"}), 404
        
        result = {
            "id": str(pandal["_id"]),
            "name": pandal.get("name"),
            "theme": pandal.get("theme"),
            "idol_type": pandal.get("idol_type"),
            "area": pandal.get("area"),
            "address": pandal.get("address"),
            "opening_time": pandal.get("opening_time"),
            "closing_time": pandal.get("closing_time"),
            "lat": pandal["location"]["coordinates"][1] if "location" in pandal else None,
            "lon": pandal["location"]["coordinates"][0] if "location" in pandal else None
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pandals', methods=['POST'])
def add_pandal():
    data = request.json
    pandal_id = pandals.insert_one({
        "name": data["name"],
        "theme": data["theme"],
        "idol_type": data["idol_type"],
        "area": data["area"],
        "address": data["address"],
        "location": {
            "type": "Point",
            "coordinates": [data["lon"], data["lat"]]
        },
        "created_at": mongo.db.command('serverStatus')['localTime']
    }).inserted_id
    return jsonify({"id": str(pandal_id)})

@app.route('/api/pandals/nearby', methods=['GET'])
def get_nearby_pandals():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    radius = int(request.args.get("radius", 2000))  # meters
    user_location = (lat, lon)

    nearby = pandals.find({
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius
            }
        }
    })

    results = []
    for p in nearby:
        pandal_location = (p["location"]["coordinates"][1], p["location"]["coordinates"][0])
        distance = geodesic(user_location, pandal_location).kilometers
        
        # Get estimated duration using OSRM
        try:
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{p['location']['coordinates'][0]},{p['location']['coordinates'][1]}?overview=false"
            response = requests.get(osrm_url)
            if response.status_code == 200:
                route_data = response.json()
                if route_data['routes']:
                    duration = f"{int(route_data['routes'][0]['duration'] / 60)} mins"
                else:
                    duration = None
            else:
                duration = None
        except:
            duration = None

        results.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "distance": round(distance, 2),
            "duration": duration,
            "lat": pandal_location[0],
            "lon": pandal_location[1]
        })

    return jsonify(results)

@app.route('/map/pandal/<pandal_id>')
def get_pandal_map(pandal_id):
    try:
        pandal = pandals.find_one({"_id": ObjectId(pandal_id)})
        if not pandal:
            return "Pandal not found", 404

        # Create a folium map centered on the pandal
        lat = pandal["location"]["coordinates"][1]
        lon = pandal["location"]["coordinates"][0]
        pandal_map = folium.Map(location=[lat, lon], zoom_start=15,
                               tiles='OpenStreetMap')

        # Add the pandal marker
        folium.Marker(
            [lat, lon],
            popup=f"<b>{pandal['name']}</b><br>{pandal.get('address', '')}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(pandal_map)

        # Add nearby amenities using Overpass API
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:1000,{lat},{lon});
          node["amenity"="police"](around:1000,{lat},{lon});
          node["amenity"="restaurant"](around:1000,{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """
        
        response = requests.post(overpass_url, data={"data": overpass_query})
        if response.status_code == 200:
            data = response.json()
            for element in data.get('elements', []):
                if 'lat' in element and 'lon' in element:
                    place_type = element.get('tags', {}).get('amenity')
                    name = element.get('tags', {}).get('name', 'Unnamed')
                    
                    # Choose icon color based on place type
                    icon_color = {
                        'hospital': 'green',
                        'police': 'blue',
                        'restaurant': 'orange'
                    }.get(place_type, 'gray')

                    folium.Marker(
                        [element['lat'], element['lon']],
                        popup=f"<b>{name}</b><br>Type: {place_type}",
                        icon=folium.Icon(color=icon_color, icon='info-sign')
                    ).add_to(pandal_map)

        # Add fullscreen option
        plugins.Fullscreen().add_to(pandal_map)
        
        # Add location finder
        plugins.LocateControl().add_to(pandal_map)
        
        # Add measurement control
        plugins.MeasureControl().add_to(pandal_map)
        
        # Add minimap
        plugins.MiniMap().add_to(pandal_map)
        
        # Save map to a temporary file
        _, temp_path = tempfile.mkstemp(suffix='.html')
        pandal_map.save(temp_path)
        
        return send_file(temp_path)
    except Exception as e:
        return str(e), 500

@app.route('/api/geocode', methods=['POST'])
def geocode_address():
    try:
        address = request.json.get('address')
        if not address:
            return jsonify({"error": "Address is required"}), 400

        # Use Nominatim for geocoding
        location = geolocator.geocode(address)
        if location:
            return jsonify({
                "lat": location.latitude,
                "lon": location.longitude,
                "formatted_address": location.address
            })
        else:
            return jsonify({"error": "Location not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pandals/<pandal_id>/ratings', methods=['GET', 'POST'])
def api_pandal_ratings(pandal_id):
    if request.method == 'GET':
        rating_list = list(ratings.find({"pandal_id": pandal_id}))
        for rating in rating_list:
            rating['_id'] = str(rating['_id'])
        return jsonify(rating_list)
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        rating_value = data.get('rating')
        comment = data.get('comment')
        
        if not user_id or not rating_value:
            return jsonify({"error": "Missing required fields"}), 400
        
        rating_data = {
            "user_id": user_id,
            "pandal_id": pandal_id,
            "rating": rating_value,
            "comment": comment,
            "created_at": mongo.db.command('serverStatus')['localTime']
        }
        result = ratings.insert_one(rating_data)
        return jsonify({"success": True, "id": str(result.inserted_id)})

if __name__ == '__main__':
    app.run(debug=True)
