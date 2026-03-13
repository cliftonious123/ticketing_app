from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
METRICS_FILE = 'metrics.json'
VALID_API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

def load_metrics():
    """Reads metrics from the JSON file."""
    if not os.path.exists(METRICS_FILE):
        return {"events": []}
    with open(METRICS_FILE, 'r') as f:
        return json.load(f)

def save_metrics(metrics):
    """Writes metrics back to the JSON file."""
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=4)

@app.route('/log', methods=['POST'])
def log_event():
    """
    Logs an event (e.g., ticket creation).
    Expects a JSON body with 'api_key', 'event_type', and 'item_id'.
    """
    data = request.get_json()
    if not data or data.get('api_key') != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    event_type = data.get('event_type')
    item_id = data.get('item_id')
    
    if not event_type:
        return jsonify({"error": "Missing event type"}), 400

    metrics = load_metrics()
    new_event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "item_id": item_id
    }
    metrics["events"].append(new_event)
    save_metrics(metrics)

    return jsonify({"status": "success"}), 200

@app.route('/report', methods=['GET'])
def generate_report():
    """Returns a simple report of logged events."""
    metrics = load_metrics()
    events = metrics.get("events", [])
    
    # Calculate some basic statistics
    report = {
        "total_events": len(events),
        "breakdown": {}
    }
    
    for event in events:
        etype = event["event_type"]
        report["breakdown"][etype] = report["breakdown"].get(etype, 0) + 1
        
    return jsonify(report), 200

if __name__ == '__main__':
    app.run(port=5003, debug=True)
