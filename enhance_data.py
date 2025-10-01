# Enhanced data import script for testing the new features

import sys
import os
import json
from datetime import datetime
import random

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, pandals, ratings
    from bson.objectid import ObjectId
    
    def add_sample_ratings():
        """Add sample ratings to existing pandals for testing"""
        
        with app.app_context():
            # Get all pandals
            all_pandals = list(pandals.find())
            
            if not all_pandals:
                print("No pandals found. Please import pandals first.")
                return
            
            print(f"Found {len(all_pandals)} pandals. Adding sample ratings...")
            
            # Sample user IDs (you can replace with real user IDs)
            sample_users = [
                "user_123", "user_456", "user_789", 
                "user_abc", "user_def", "user_ghi"
            ]
            
            # Sample comments
            sample_comments = [
                "Amazing decoration and peaceful atmosphere!",
                "Beautiful theme this year. Must visit!",
                "Crowded but worth the visit. Great darshan experience.",
                "Traditional setup with modern touches. Loved it!",
                "One of the best pandals in the area.",
                "Good organization and crowd management.",
                "Spectacular idol and creative theme.",
                "Perfect for family visit. Clean and well-maintained.",
                "Outstanding cultural programs and activities.",
                "Divine experience. Highly recommended!"
            ]
            
            ratings_added = 0
            
            for pandal in all_pandals:
                pandal_id = str(pandal['_id'])
                
                # Check if ratings already exist for this pandal
                existing_ratings = ratings.find_one({'pandal_id': pandal_id})
                if existing_ratings:
                    print(f"Ratings already exist for {pandal.get('name', 'Unknown')}. Skipping...")
                    continue
                
                # Add 2-5 random ratings for each pandal
                num_ratings = random.randint(2, 5)
                
                for i in range(num_ratings):
                    rating_data = {
                        'user_id': random.choice(sample_users),
                        'pandal_id': pandal_id,
                        'rating': random.randint(3, 5),  # Ratings between 3-5 stars
                        'comment': random.choice(sample_comments),
                        'created_at': datetime.utcnow()
                    }
                    
                    ratings.insert_one(rating_data)
                    ratings_added += 1
                
                print(f"Added {num_ratings} ratings for {pandal.get('name', 'Unknown')}")
            
            print(f"\\nTotal ratings added: {ratings_added}")
    
    def update_pandal_themes():
        """Update pandals with proper theme information"""
        
        themes = [
            "Traditional", "Modern", "Eco-friendly", "Cultural", 
            "Historical", "Innovative", "Religious", "Artistic"
        ]
        
        with app.app_context():
            all_pandals = list(pandals.find())
            
            for pandal in all_pandals:
                if not pandal.get('theme'):
                    theme = random.choice(themes)
                    pandals.update_one(
                        {'_id': pandal['_id']},
                        {'$set': {'theme': theme}}
                    )
                    print(f"Updated theme for {pandal.get('name', 'Unknown')} to {theme}")
    
    def ensure_proper_structure():
        """Ensure all pandals have proper structure with required fields"""
        
        with app.app_context():
            all_pandals = list(pandals.find())
            
            for pandal in all_pandals:
                updates = {}
                
                # Ensure opening and closing times
                if not pandal.get('opening_time'):
                    updates['opening_time'] = '08:00'
                
                if not pandal.get('closing_time'):
                    updates['closing_time'] = '22:00'
                
                # Ensure idol type
                if not pandal.get('idol_type'):
                    idol_types = ['Traditional', 'Eco-friendly', 'Artistic', 'Modern']
                    updates['idol_type'] = random.choice(idol_types)
                
                # Update if there are changes
                if updates:
                    pandals.update_one(
                        {'_id': pandal['_id']},
                        {'$set': updates}
                    )
                    print(f"Updated fields for {pandal.get('name', 'Unknown')}: {updates}")
    
    if __name__ == "__main__":
        print("Starting data enhancement for pandal search features...")
        
        # Update pandal structure
        ensure_proper_structure()
        
        # Update themes
        update_pandal_themes()
        
        # Add sample ratings
        add_sample_ratings()
        
        print("\\nData enhancement completed!")
        print("\\nYou can now test the enhanced search and filter features with:")
        print("- Area-based filtering")
        print("- Theme-based filtering") 
        print("- Rating-based filtering")
        print("- Location-based sorting")
        print("- Search functionality")

except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project directory and have all dependencies installed.")
except Exception as e:
    print(f"Error: {e}")