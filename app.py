import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from utils.gemini_chat import get_gemini_response
from utils.itinerary import create_itinerary_pdf
from utils.location import get_place_details

app = Flask(__name__)

# Environment-based configuration
NODE_SERVER_URL = os.getenv('NODE_SERVER_URL', 'http://localhost:3001')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# CORS configuration - allow multiple origins for deployment
CORS(app, origins=[
    FRONTEND_URL,
    "http://localhost:3000",  # Development
    "https://your-app-name.netlify.app",  # Production (replace with your actual domain)
    "https://your-app-name.vercel.app"   # Alternative deployment
], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.route('/api/destination/<place>', methods=['GET'])
def destination(place):
    data = get_place_details(place)
    return jsonify(data)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    location = request.json.get("location")
    user_location = request.json.get("userLocation")
    if user_location:
        location_info = f"{location} (User is at {user_location})"
    else:
        location_info = location
    reply = get_gemini_response(user_input, location_info)
    return jsonify({"reply": reply})

@app.route('/api/itinerary', methods=['POST'])
def itinerary():
    selected_places = request.json.get("places")
    user_location = request.json.get("userLocation")
    days = request.json.get("days")
    budget = request.json.get("budget")
    people = request.json.get("people")
    template_id = request.json.get("template", "modern")
    format_type = request.json.get("format", "pdf")
    return_text = request.json.get("returnText", False)
    
    if format_type != "pdf":
        format_type = "pdf"
    
    personalization = ""
    if days:
        personalization += f"For {days} days. "
    if budget:
        personalization += f"Budget: ₹{budget}. "
    if people:
        personalization += f"For {people} people. "
    if user_location:
        start_point = f"Start from user's current location: {user_location}. "
    else:
        start_point = ""
    
    itinerary_text = get_gemini_response(
        f"{start_point}{personalization}Create a detailed travel itinerary for: {', '.join(selected_places)}. Suggest the best order, time to spend at each, and what to do at each place. Include tips and local insights.", ""
    )
    
    from utils.location import get_coordinates
    places_with_coords = []
    for name in selected_places:
        coords = get_coordinates(name)
        if coords:
            places_with_coords.append({"name": name, "coords": coords})
    
    options = {"days": days, "budget": budget, "people": people}
    
    # Save adventure to Node.js server
    auth_header = request.headers.get('Authorization')
    if auth_header and selected_places and itinerary_text:
        try:
            # Prepare data for Node.js server
            adventure_data = {
                "destination": selected_places[0] if selected_places else "Unknown",
                "places": places_with_coords,
                "itinerary": {"text": itinerary_text},
                "options": options
            }
            
            # Forward to Node.js server
            node_response = requests.post(
                f"{NODE_SERVER_URL}/api/adventures",
                json=adventure_data,
                headers={'Authorization': auth_header},
                timeout=10
            )
            
            if node_response.status_code == 201:
                print("Adventure saved successfully")
            else:
                print(f"Failed to save adventure: {node_response.status_code}")
                
        except Exception as e:
            print(f"Error saving adventure: {e}")
    
    # Handle preview request or return text request
    if request.args.get("preview") == "1" or return_text:
        return jsonify({"reply": itinerary_text})
    
    from utils.itinerary import create_itinerary_pdf
    pdf_buffer = create_itinerary_pdf(itinerary_text, places=places_with_coords, options=options, template_id=template_id)
    return send_file(
        pdf_buffer, 
        as_attachment=True, 
        download_name=f"itinerary_{template_id}.pdf",
        mimetype="application/pdf"
    )

# New endpoint for downloading existing itinerary
@app.route('/api/itinerary/download', methods=['POST'])
def download_itinerary():
    itinerary_text = request.json.get("itineraryText")
    places = request.json.get("places", [])
    template_id = request.json.get("template", "modern")
    format_type = request.json.get("format", "pdf")
    destination = request.json.get("destination", "destination")
    days = request.json.get("days", 3)
    budget = request.json.get("budget", 10000)
    people = request.json.get("people", 2)
    
    if not itinerary_text:
        return jsonify({"error": "Itinerary text is required"}), 400
    
    options = {"days": days, "budget": budget, "people": people}
    
    from utils.itinerary import create_itinerary_pdf
    pdf_buffer = create_itinerary_pdf(itinerary_text, places=places, options=options, template_id=template_id)
    return send_file(
        pdf_buffer, 
        as_attachment=True, 
        download_name=f"{destination}_itinerary_{template_id}.pdf",
        mimetype="application/pdf"
    )

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "node_server": NODE_SERVER_URL,
        "environment": os.getenv('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))  # Use FLASK_PORT instead of PORT
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("🚀 Starting Flask server...")
    print(f"📊 Node.js server URL: {NODE_SERVER_URL}")
    print(f"🌐 Frontend URL: {FRONTEND_URL}")
    print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)