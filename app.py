from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, session
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
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient
import json
from models.user import User

app = Flask(__name__)
app.config.from_object(config)

# Allow OAuth over HTTP for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Set session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# OAuth 2.0 client setup
client = WebApplicationClient(config.GOOGLE_CLIENT_ID)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize Nominatim geocoder with a custom user agent
geolocator = Nominatim(user_agent="UtsavDarshan_" + datetime.now().strftime("%Y%m%d"))

@login_manager.user_loader
def load_user(user_id):
    user_data = users.find_one({"_id": user_id})
    if not user_data:
        return None
    return User(user_data)

# MongoDB connection
app.config["MONGO_URI"] = config.MONGO_URI
mongo = PyMongo(app)

# Collections
pandals = mongo.db.pandals
users = mongo.db.users
visits = mongo.db.visits
ratings = mongo.db.ratings
badges = mongo.db.badges

def get_google_provider_cfg():
    try:
        return requests.get(config.GOOGLE_DISCOVERY_URL).json()
    except:
        return None

@app.route("/login")
def login():
    try:
        # Generate and store a new state parameter
        state = os.urandom(16).hex()
        session.clear()
        session["oauth_state"] = state
        
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        if not google_provider_cfg:
            return "Error loading Google configuration", 500
            
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri="http://localhost:5000/login/callback",
            scope=["openid", "email", "profile"],
            state=state
        )
        return redirect(request_uri)
    except Exception as e:
        return f"Failed to initiate login: {str(e)}", 500

@app.route("/login/callback")
def callback():
    try:
        # Get authorization code and state from Google
        code = request.args.get("code")
        received_state = request.args.get("state")
        stored_state = session.get("oauth_state")

        # Debug logging
        print(f"Received state: {received_state}")
        print(f"Stored state: {stored_state}")

        # Verify state matches
        if not received_state or not stored_state or received_state != stored_state:
            session.clear()
            return "State verification failed. Please try logging in again.", 400

        if not code:
            session.clear()
            return "Authorization code not received", 400
        
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        if not google_provider_cfg:
            return "Error loading Google configuration", 500
            
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send request to get tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url="http://localhost:5000/login/callback",
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET),
        )
        
        if not token_response.ok:
            return f"Failed to get token: {token_response.json()}", 400

    except Exception as e:
        return f"Failed to process authentication: {str(e)}", 400

    # Parse the tokens
    try:
        client.parse_request_body_response(json.dumps(token_response.json()))
    except Exception as e:
        session.clear()
        return f"Failed to parse token response: {str(e)}", 400

    # Get user info from Google
    try:
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        if not userinfo_response.ok:
            session.clear()
            return f"Failed to get user info: {userinfo_response.json()}", 400
    except Exception as e:
        session.clear()
        return f"Failed to get user info: {str(e)}", 400

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json().get("given_name", "")
        
        # Create a user in our db with the information provided
        user_data = {
            "_id": unique_id,
            "name": users_name,
            "email": users_email,
            "profile_pic": userinfo_response.json().get("picture")
        }

        # Save user if they don't exist
        users.update_one(
            {"_id": unique_id},
            {"$set": user_data},
            upsert=True
        )

        # Create user object for Flask-Login
        user = User(user_data)

        # Begin user session by logging the user in
        login_user(user)

        # Send user back to homepage
        return redirect(url_for("index"))
    else:
        return "User email not verified by Google.", 400

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/')
def index():
    # Get only 4 pandals for the homepage
    pandal_list = list(pandals.find().limit(4))
    return render_template('index.html', pandals=pandal_list)

@app.route('/all-pandals')
def all_pandals():
    # Fetch all pandals and compute auxiliary data for filters and UI
    pandal_list = list(pandals.find())

    # Build unique filter options
    unique_areas = sorted({p.get('area') for p in pandal_list if p.get('area')})
    unique_themes = sorted({p.get('theme') for p in pandal_list if p.get('theme')})

    # Attach rating summary if ratings collection present
    pandal_summaries = []
    for p in pandal_list:
        pid = str(p.get('_id'))
        rating_docs = list(ratings.find({"pandal_id": pid}))
        avg_rating = None
        review_count = 0
        if rating_docs:
            review_count = len(rating_docs)
            avg_rating = round(sum([float(r.get('rating', 0)) for r in rating_docs]) / review_count, 1)
        p_copy = dict(p)
        p_copy['avg_rating'] = avg_rating
        p_copy['review_count'] = review_count
        pandal_summaries.append(p_copy)

    return render_template(
        'all_pandals.html',
        pandals=pandal_summaries,
        areas=unique_areas,
        themes=unique_themes
    )

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
@login_required
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
@login_required
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
@login_required
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
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required"}), 401
            
        data = request.json
        rating_value = data.get('rating')
        comment = data.get('comment')
        
        if not rating_value:
            return jsonify({"error": "Missing required fields"}), 400
        
        rating_data = {
            "user_id": current_user.get_id(),
            "pandal_id": pandal_id,
            "rating": rating_value,
            "comment": comment,
            "created_at": mongo.db.command('serverStatus')['localTime']
        }
        result = ratings.insert_one(rating_data)
        return jsonify({"success": True, "id": str(result.inserted_id)})
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
