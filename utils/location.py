# --- utils/location.py ---
import json
import re
import requests
from .gemini_chat import get_gemini_response

def get_coordinates(place):
    """Get coordinates using OpenStreetMap Nominatim API (free)"""
    try:
        # Using Nominatim API (OpenStreetMap's free geocoding service)
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{place}, India",
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'TravelApp/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            print(f"Got coordinates for {place}: [{lat}, {lon}]")
            return [lat, lon]
        else:
            print(f"No coordinates found for {place}")
            return None
            
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None

def get_suggestions_from_gemini(place, coordinates):
    """Get tourist attractions from Gemini with descriptions"""
    try:
        prompt = f"""
        For the location "{place}" in India (coordinates: {coordinates}), provide 8 popular tourist attractions/places to visit nearby.
        
        Return the response in this exact JSON format:
        [
            {{"name": "Attraction Name 1", "coords": [lat1, lon1], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 2", "coords": [lat2, lon2], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 3", "coords": [lat3, lon3], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 4", "coords": [lat4, lon4], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 5", "coords": [lat5, lon5], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 6", "coords": [lat6, lon6], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 7", "coords": [lat7, lon7], "description": "Brief attractive description"}},
            {{"name": "Attraction Name 8", "coords": [lat8, lon8], "description": "Brief attractive description"}}
        ]
        
        Make descriptions appealing, 1-2 sentences, under 80 characters each.
        Only return the JSON array, no additional text.
        """
        
        response = get_gemini_response(prompt, place)
        print(f"Raw Gemini suggestions response: {response}")
        
        # Try to extract JSON array from the response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            suggestions = json.loads(json_str)
            print(f"Parsed suggestions successfully: {suggestions}")
            return suggestions
        else:
            print("No JSON array found in Gemini response")
            return None
            
    except Exception as e:
        print(f"Error getting suggestions from Gemini: {e}")
        return None

def get_place_details(place):
    # Get coordinates from free geocoding API
    coordinates = get_coordinates(place)
    
    if not coordinates:
        # Fallback to Delhi coordinates
        coordinates = [28.6139, 77.2090]
        print(f"Using fallback coordinates for Delhi")
    
    # Get suggestions from Gemini
    suggestions = get_suggestions_from_gemini(place, coordinates)
    
    if not suggestions:
        # Generate fallback suggestions with descriptions
        lat, lon = coordinates
        suggestions = [
            {"name": f"Red Fort, {place}", "coords": [lat + 0.01, lon + 0.01], "description": "Historic Mughal fortress with stunning red walls"},
            {"name": f"Local Market, {place}", "coords": [lat - 0.01, lon + 0.01], "description": "Vibrant local market with authentic crafts"},
            {"name": f"Temple, {place}", "coords": [lat + 0.01, lon - 0.01], "description": "Sacred temple with beautiful architecture"},
            {"name": f"Cultural Center, {place}", "coords": [lat - 0.01, lon - 0.01], "description": "Rich cultural heritage and local arts"},
            {"name": f"Gardens, {place}", "coords": [lat, lon + 0.02], "description": "Peaceful gardens perfect for relaxation"},
            {"name": f"Museum, {place}", "coords": [lat + 0.02, lon], "description": "Local history and artifacts museum"},
            {"name": f"Viewpoint, {place}", "coords": [lat - 0.02, lon], "description": "Scenic viewpoint with panoramic views"},
            {"name": f"Food Street, {place}", "coords": [lat, lon - 0.02], "description": "Famous street food and local delicacies"}
        ]
        print(f"Using fallback suggestions with descriptions for {place}")
    
    return {
        "coordinates": coordinates,
        "suggestions": suggestions
    }