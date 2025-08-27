# --- utils/gemini_chat.py ---
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure with API key, not application default credentials
genai.configure(api_key=GEMINI_API_KEY)

# Use the correct model name for Gemini
model = genai.GenerativeModel("gemini-2.0-flash")

def get_gemini_response(message, location=None):
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not found in environment variables"
    
    prompt = f"You are a travel assistant for India. Location: {location or 'unspecified'}.\nUser: {message}\nGive detailed and friendly travel suggestions."
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return f"Error: {str(e)}"

def get_place_suggestions(destination):
    """Get AI-generated place suggestions for a destination"""
    if not GEMINI_API_KEY:
        return None
    
    prompt = f"""
    You are a travel expert. Generate exactly 8-10 tourist attractions for {destination}, India.
    Return ONLY a valid JSON array with this exact format:
    [
        {{"name": "Place Name", "description": "Brief description", "category": "attraction"}},
        {{"name": "Place Name", "description": "Brief description", "category": "food"}},
        ...
    ]
    
    Categories should be: attraction, food, accommodation, activity, shopping, transport
    Keep descriptions under 100 characters.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error for suggestions: {str(e)}")
        return None
