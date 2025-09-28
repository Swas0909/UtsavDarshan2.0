from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import config

app = Flask(__name__)
app.config.from_object(config)

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
    return render_template('all_pandals.html', pandals=pandal_list)

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
        # Create a new pandal document
        new_pandal = {
            "name": request.form.get('name'),
            "theme": request.form.get('theme', 'Traditional'),
            "idol_type": request.form.get('idol_type', 'Eco-friendly'),
            "area": request.form.get('location'),
            "address": request.form.get('details', ''),
            "location": {
                "type": "Point",
                "coordinates": [
                    float(request.form.get('longitude', 0)),
                    float(request.form.get('latitude', 0))
                ]
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

    nearby = pandals.find({
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": radius
            }
        }
    })
    results = [{"id": str(p["_id"]), "name": p["name"]} for p in nearby]
    return jsonify(results)

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
