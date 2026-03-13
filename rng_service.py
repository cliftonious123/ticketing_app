from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# The specific test API key from the user story
VALID_API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

@app.route('/generate-id', methods=['POST'])
def generate_id():
    """
    Generates a random ticket ID.
    Expects a JSON body with the 'api_key'.
    """
    data = request.get_json()
    
    # Check if API key is present and valid
    if not data or data.get('api_key') != VALID_API_KEY:
        return jsonify({"error": "Unauthorized: Invalid or missing API key"}), 401

    # Generate a random positive integer
    # Using a range common for IDs
    ticket_id = random.randint(1000, 999999)

    return jsonify({
        "status": "success",
        "ticket_id": ticket_id
    }), 200

if __name__ == '__main__':
    # Running on port 5001 to avoid conflict with the main app (port 5000)
    app.run(port=5001, debug=True)
