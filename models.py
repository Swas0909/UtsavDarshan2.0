from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import datetime

# MongoDB collections schema definitions:
# 
# users: {
#   "_id": "google_uid_123",  # Using external auth ID as primary key
#   "name": "Sam",
#   "email": "sam@example.com",
#   "preferred_lang": "en",
#   "created_at": ISODate("2025-09-20T12:00:00Z")
# }
#
# pandals: {
#   "_id": ObjectId("..."),
#   "name": "Lalbaugcha Raja",
#   "theme": "Traditional",
#   "idol_type": "Eco-friendly",
#   "area": "Dadar",
#   "address": "Lalbaug, Mumbai",
#   "location": { "type": "Point", "coordinates": [72.844, 19.977] },
#   "opening_time": "08:00",
#   "closing_time": "22:00",
#   "created_at": ISODate("2025-09-01T10:00:00Z")
# }
#
# visits: {
#   "_id": ObjectId("..."),
#   "user_id": "google_uid_123",
#   "pandal_id": ObjectId("..."),
#   "visited_at": ISODate("2025-09-20T12:30:00Z")
# }
#
# ratings: {
#   "_id": ObjectId("..."),
#   "user_id": "google_uid_123",
#   "pandal_id": ObjectId("..."),
#   "rating": 5,
#   "comment": "Amazing theme this year!",
#   "created_at": ISODate("2025-09-20T13:00:00Z")
# }
#
# badges: {
#   "_id": "badge_10_visits",
#   "title": "Explorer",
#   "description": "Visited 10 pandals",
#   "icon": "explorer.png"
# }

class Database:
    def __init__(self, app):
        self.mongo = PyMongo(app)
        self.db = self.mongo.db
        # Ensure the database connection is established
        if not self.db:
            raise ConnectionError("Failed to connect to MongoDB database")
    
    # Pandal operations
    def get_all_pandals(self):
        return list(self.db.pandals.find())
    
    def get_pandal_by_id(self, pandal_id):
        return self.db.pandals.find_one({"_id": ObjectId(pandal_id)})
    
    def get_pandals_by_taluka(self, taluka):
        return list(self.db.pandals.find({"properties.area": taluka}))
    
    def insert_pandal(self, pandal_data):
        return self.db.pandals.insert_one(pandal_data)
    
    def update_pandal(self, pandal_id, update_data):
        return self.db.pandals.update_one(
            {"_id": ObjectId(pandal_id)},
            {"$set": update_data}
        )
    
    def delete_pandal(self, pandal_id):
        return self.db.pandals.delete_one({"_id": ObjectId(pandal_id)})
    
    # User operations
    def get_user_by_id(self, user_id):
        return self.db.users.find_one({"_id": ObjectId(user_id)})
    
    def create_user(self, user_data):
        user_data["created_at"] = datetime.datetime.utcnow()
        return self.db.users.insert_one(user_data)
    
    # Visit operations
    def record_visit(self, user_id, pandal_id):
        visit_data = {
            "user_id": user_id,
            "pandal_id": ObjectId(pandal_id),
            "visited_at": datetime.datetime.utcnow()
        }
        return self.db.visits.insert_one(visit_data)
    
    def get_user_visits(self, user_id):
        return list(self.db.visits.find({"user_id": user_id}))
    
    # Rating operations
    def add_rating(self, user_id, pandal_id, rating, comment=None):
        rating_data = {
            "user_id": user_id,
            "pandal_id": ObjectId(pandal_id),
            "rating": rating,
            "comment": comment,
            "created_at": datetime.datetime.utcnow()
        }
        return self.db.ratings.insert_one(rating_data)
    
    def get_pandal_ratings(self, pandal_id):
        return list(self.db.ratings.find({"pandal_id": ObjectId(pandal_id)}))
    
    # Badge operations
    def get_all_badges(self):
        return list(self.db.badges.find())
    
    def assign_badge_to_user(self, user_id, badge_id):
        user_badge = {
            "user_id": user_id,
            "badge_id": badge_id,
            "awarded_at": datetime.datetime.utcnow()
        }
        return self.db.user_badges.insert_one(user_badge)
    
    # Geospatial operations
    def find_nearby_pandals(self, lon, lat, max_distance=2000):
        """
        Find pandals near a specific location
        
        Args:
            lon: Longitude coordinate
            lat: Latitude coordinate
            max_distance: Maximum distance in meters (default 2000m/2km)
            
        Returns:
            List of pandals within the specified distance
        """
        return list(self.db.pandals.find({
            "location": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "$maxDistance": max_distance
                }
            }
        }))
    
    def get_user_visits(self, user_id):
        return list(self.db.visits.find({"user_id": user_id}))
    
    # Rating operations
    def add_rating(self, user_id, pandal_id, rating, comment=None):
        rating_data = {
            "user_id": user_id,
            "pandal_id": pandal_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.datetime.utcnow()
        }
        return self.db.ratings.insert_one(rating_data)
    
    def get_pandal_ratings(self, pandal_id):
        return list(self.db.ratings.find({"pandal_id": pandal_id}))
    
    # Import GeoJSON data
    def import_geojson_features(self, features):
        """Import GeoJSON features into the pandals collection"""
        if not features:
            return {"inserted": 0}
        
        # Clear existing data if needed
        # self.db.pandals.delete_many({})
        
        result = self.db.pandals.insert_many(features)
        return {"inserted": len(result.inserted_ids)}