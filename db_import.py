import json
import pymongo
import config

def import_geojson_data(file_path):
    """Import GeoJSON data from file into MongoDB"""
    # Connect directly to MongoDB using pymongo
    client = pymongo.MongoClient(config.MONGO_URI)
    
    # Select database - use config.MONGO_DBNAME or default to "utsavdarshan"
    db = client.utsavdarshan
    
    print(f"Connected to MongoDB: {client.server_info()['version']}")
    
    # Load GeoJSON data
    with open(file_path, 'r') as f:
        geojson_data = json.load(f)
    
    # Extract features
    features = geojson_data.get('features', [])
    print(f"Found {len(features)} features in GeoJSON file")
    
    # Clear existing data if needed
    # db.pandals.delete_many({})
    
    # Import features into MongoDB
    if features:
        result = db.pandals.insert_many(features)
        print(f"Imported {len(result.inserted_ids)} pandal records into MongoDB")
        
        # Create geospatial index for location field
        print("Creating geospatial index on location field...")
        db.pandals.create_index([("location", pymongo.GEOSPHERE)])
        print("Geospatial index created successfully")
        
        return {"inserted": len(result.inserted_ids)}
    return {"inserted": 0}

def setup_collections():
    """Set up all collections with proper indexes"""
    client = pymongo.MongoClient(config.MONGO_URI)
    db = client.utsavdarshan
    
    print(f"Connected to MongoDB: {client.server_info()['version']}")
    
    # Create geospatial index for pandals collection
    print("Creating geospatial index on pandals collection...")
    db.pandals.create_index([("location", pymongo.GEOSPHERE)])
    
    # Create indexes for other collections
    print("Creating indexes for other collections...")
    db.visits.create_index([("user_id", pymongo.ASCENDING)])
    db.visits.create_index([("pandal_id", pymongo.ASCENDING)])
    db.ratings.create_index([("pandal_id", pymongo.ASCENDING)])
    db.ratings.create_index([("user_id", pymongo.ASCENDING)])
    
    print("All indexes created successfully")
    return {"status": "success"}

if __name__ == "__main__":
    # Import data from the GeoJSON file
    result = import_geojson_data('ganesh_mandals_with_details.geojson')
    print(f"Imported {result['inserted']} pandal records into MongoDB")
    
    # Set up all collections with proper indexes
    setup_collections()