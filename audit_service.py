from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
AUDIT_FILE = 'audit_log.json'
VALID_API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

def load_audit_log():
    """Reads the audit log from the JSON file."""
    if not os.path.exists(AUDIT_FILE):
        return {"logs": []}
    with open(AUDIT_FILE, 'r') as f:
        return json.load(f)

def save_audit_log(logs):
    """Writes the audit log back to the JSON file."""
    with open(AUDIT_FILE, 'w') as f:
        json.dump(logs, f, indent=4)

@app.route('/audit', methods=['POST'])
def add_audit_entry():
    """
    Records a change for a ticket/task.
    Expects a JSON body with 'api_key', 'item_id', 'action', and 'details'.
    """
    data = request.get_json()
    if not data or data.get('api_key') != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    item_id = data.get('item_id')
    action = data.get('action') # e.g., "created", "updated", "resolved"
    details = data.get('details') # e.g., "Changed priority from Low to High"

    if not item_id or not action:
        return jsonify({"error": "Missing required fields"}), 400

    logs = load_audit_log()
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "item_id": item_id,
        "action": action,
        "details": details
    }
    logs["logs"].append(new_entry)
    save_audit_log(logs)

    return jsonify({"status": "success"}), 200

@app.route('/history/<int:item_id>', methods=['GET'])
def get_history(item_id):
    """Returns the full history of a specific item."""
    logs = load_audit_log()
    item_history = [entry for entry in logs.get("logs", []) if entry["item_id"] == item_id]
    
    return jsonify({
        "item_id": item_id,
        "history": item_history
    }), 200

if __name__ == '__main__':
    app.run(port=5004, debug=True)
