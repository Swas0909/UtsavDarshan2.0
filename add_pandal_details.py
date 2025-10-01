# Add history and additional details to pandals for enhanced modal

import sys
import os
import random
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, pandals
    from bson.objectid import ObjectId
    
    def add_pandal_history():
        """Add sample history and additional details to existing pandals"""
        
        # Sample histories for famous pandals
        pandal_histories = {
            "Lalbaugcha Raja": {
                "history": "Established in 1934, Lalbaugcha Raja is one of Mumbai's most famous Ganesh pandals. Known for its massive crowds and the belief that this Ganesha fulfills wishes, it attracts millions of devotees during Ganesh Chaturthi. The pandal was started by the residents of Lalbaug to bring the community together.",
                "established_year": "1934",
                "special_features": ["Sarvajanik Darshan", "24/7 Open", "Famous for Wish Fulfillment", "Massive Crowds", "Traditional Setup"],
                "famous_for": "Most visited Ganesh pandal in Mumbai"
            },
            "Mumbaicha Raja": {
                "history": "One of the oldest and most revered Ganesh pandals in Mumbai, known for its traditional celebrations and community participation. The pandal has been serving devotees for over 8 decades with unwavering devotion.",
                "established_year": "1928",
                "special_features": ["Traditional Celebrations", "Community Participation", "Cultural Programs", "Eco-friendly Initiatives"],
                "famous_for": "Traditional celebrations and community bonding"
            },
            "Khetwadi Cha Raja": {
                "history": "Established in the heart of Khetwadi, this pandal is famous for its innovative themes and artistic decorations. Each year, the pandal showcases different themes ranging from social messages to mythological stories.",
                "established_year": "1965",
                "special_features": ["Innovative Themes", "Artistic Decorations", "Social Messages", "Photography Spot"],
                "famous_for": "Creative themes and artistic presentations"
            },
            "Andhericha Raja": {
                "history": "Located in Andheri East, this pandal has gained immense popularity in recent years. Known for its grand setup and elaborate decorations, it attracts devotees from all over Mumbai.",
                "established_year": "1966",
                "special_features": ["Grand Setup", "Elaborate Decorations", "Modern Facilities", "VIP Darshan"],
                "famous_for": "Grand celebrations and modern amenities"
            }
        }
        
        # Generic histories for other pandals
        generic_histories = [
            {
                "history": "This pandal has been serving the community for several decades, bringing people together during the auspicious festival of Ganesh Chaturthi. Known for its traditional celebrations and devotional atmosphere.",
                "established_year": str(random.randint(1950, 1990)),
                "special_features": ["Traditional Setup", "Community Gathering", "Devotional Atmosphere", "Cultural Programs"],
                "famous_for": "Community celebrations and traditional values"
            },
            {
                "history": "A prominent Ganesh pandal in the locality, this mandal has been organizing celebrations with great enthusiasm and devotion. The pandal is known for its beautiful decorations and peaceful environment.",
                "established_year": str(random.randint(1960, 1995)),
                "special_features": ["Beautiful Decorations", "Peaceful Environment", "Family Friendly", "Prasad Distribution"],
                "famous_for": "Peaceful darshan and beautiful ambiance"
            },
            {
                "history": "Established by local residents to celebrate Ganesh Chaturthi with traditional fervor, this pandal has become an integral part of the community. It focuses on eco-friendly celebrations and social awareness.",
                "established_year": str(random.randint(1970, 2000)),
                "special_features": ["Eco-friendly Celebrations", "Social Awareness", "Community Participation", "Educational Programs"],
                "famous_for": "Environmental consciousness and social initiatives"
            }
        ]
        
        with app.app_context():
            all_pandals = list(pandals.find())
            
            print(f"Adding history and details to {len(all_pandals)} pandals...")
            
            for pandal in all_pandals:
                pandal_name = pandal.get('name', '')
                updates = {}
                
                # Check if pandal already has extended details
                if pandal.get('history'):
                    print(f"History already exists for {pandal_name}. Skipping...")
                    continue
                
                # Use specific history if available, otherwise use generic
                if pandal_name in pandal_histories:
                    pandal_data = pandal_histories[pandal_name]
                    updates['history'] = pandal_data['history']
                    updates['established_year'] = pandal_data['established_year']
                    updates['special_features'] = pandal_data['special_features']
                    updates['famous_for'] = pandal_data['famous_for']
                else:
                    # Use random generic history
                    generic_data = random.choice(generic_histories)
                    updates['history'] = generic_data['history']
                    updates['established_year'] = generic_data['established_year']
                    updates['special_features'] = generic_data['special_features']
                    updates['famous_for'] = generic_data['famous_for']
                
                # Add additional details
                if not pandal.get('contact_number'):
                    updates['contact_number'] = f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"
                
                if not pandal.get('website'):
                    updates['website'] = f"www.{pandal_name.lower().replace(' ', '').replace('cha', '').replace('raj', 'raja')}.com"
                
                # Add facilities
                facilities = [
                    "Wheelchair Accessible",
                    "Parking Available", 
                    "Prasad Counter",
                    "Photography Allowed",
                    "Queue Management",
                    "First Aid",
                    "Lost & Found",
                    "Drinking Water"
                ]
                updates['facilities'] = random.sample(facilities, random.randint(3, 6))
                
                # Add crowd information
                crowd_levels = ["Low", "Medium", "High", "Very High"]
                updates['expected_crowd'] = random.choice(crowd_levels)
                
                # Add best time to visit
                visit_times = [
                    "Early Morning (6-9 AM)",
                    "Late Evening (8-11 PM)", 
                    "Afternoon (2-5 PM)",
                    "Night (11 PM - 2 AM)"
                ]
                updates['best_time_to_visit'] = random.choice(visit_times)
                
                # Update the pandal
                pandals.update_one(
                    {'_id': pandal['_id']},
                    {'$set': updates}
                )
                
                print(f"Updated details for {pandal_name}")
            
            print("\\nPandal history and details update completed!")
    
    if __name__ == "__main__":
        print("Adding history and additional details to pandals...")
        add_pandal_history()
        print("\\nYou can now test the enhanced modal with complete pandal information!")

except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project directory and have all dependencies installed.")
except Exception as e:
    print(f"Error: {e}")