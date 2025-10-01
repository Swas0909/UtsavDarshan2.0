# Quick script to add sample data for testing the enhanced modal

from app import app, pandals

def add_sample_data():
    with app.app_context():
        # Update a few specific pandals with rich data for testing
        sample_updates = {
            'history': 'This pandal has been serving the community for several decades, bringing people together during Ganesh Chaturthi with traditional celebrations and devotional atmosphere. Known for its beautiful decorations and peaceful environment.',
            'established_year': '1975',
            'special_features': ['Traditional Setup', 'Community Gathering', 'Devotional Atmosphere', 'Beautiful Decorations'],
            'famous_for': 'Community celebrations and traditional values',
            'facilities': ['Parking Available', 'Prasad Counter', 'First Aid', 'Drinking Water'],
            'expected_crowd': 'Medium',
            'best_time_to_visit': 'Early Morning (6-9 AM)',
            'contact_number': '+91 98765 43210'
        }
        
        # Update all pandals with sample data
        result = pandals.update_many({}, {'$set': sample_updates})
        print(f"Updated {result.modified_count} pandals with sample data for testing")

if __name__ == "__main__":
    add_sample_data()