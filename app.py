from flask import Flask, render_template, request, redirect, url_for
import json
import os
import random
import requests

app = Flask(__name__)
DATA_FILE = 'tickets.json'
RNG_SERVICE_URL = "https://rng-microservice-4b0c29beb99a.herokuapp.com/generate-id"
FILE_SERVICE_URL = "http://127.0.0.1:5002/upload"
METRICS_SERVICE_URL = "http://127.0.0.1:5003/log"
AUDIT_SERVICE_URL = "http://127.0.0.1:5004/audit"
API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

def upload_to_file_service(item_id, file):
    """Helper to send attachment to the File Attachment microservice."""
    try:
        files = {'file': (file.filename, file.stream, file.mimetype)}
        data = {'api_key': API_KEY, 'id': item_id}
        requests.post(FILE_SERVICE_URL, data=data, files=files, timeout=5)
    except Exception:
        pass # Silently fail if microservice is down

def log_to_metrics(event_type, item_id):
    """Helper to send event data to the Metrics microservice."""
    try:
        requests.post(METRICS_SERVICE_URL, json={
            "api_key": API_KEY,
            "event_type": event_type,
            "item_id": item_id
        }, timeout=2)
    except Exception:
        pass # Silently fail if microservice is down

def log_to_audit(item_id, action, details):
    """Helper to send change data to the Audit microservice."""
    try:
        requests.post(AUDIT_SERVICE_URL, json={
            "api_key": API_KEY,
            "item_id": item_id,
            "action": action,
            "details": details
        }, timeout=2)
    except Exception:
        pass # Silently fail if microservice is down

def load_tickets():
    """Reads the list of tickets from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_tickets(tickets):
    """Writes the list of tickets back to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(tickets, f, indent=4)

@app.route('/')
def index():
    """The Homepage: Displays the dashboard of all tickets."""
    tickets = load_tickets()
    return render_template('index.html', tickets=tickets)

@app.route('/new', methods=['GET', 'POST'])
def new_ticket():
    """
    GET: Displays the form to create a new ticket.
    POST: Processes the form data and saves the new ticket.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        priority = random.choice(["Low", "Medium", "High"]) 
        
        # Call the RNG microservice for a new ID
        try:
            response = requests.post(RNG_SERVICE_URL, json={"api_key": API_KEY}, timeout=5)
            if response.status_code == 200:
                new_id = response.json().get('ticket_id')
            else:
                raise Exception("Microservice error")
        except Exception as e:
            # Fallback logic if microservice is down
            tickets = load_tickets()
            new_id = 1
            if tickets:
                new_id = max(t['id'] for t in tickets) + 1
            
        tickets = load_tickets()
        
        new_ticket_obj = {
            "id": new_id,
            "title": title,
            "description": description,
            "priority": priority, 
            "status": "Open"
        }
        
        tickets.append(new_ticket_obj)
        save_tickets(tickets)

        # Handle attachment if present
        attachment = request.files.get('attachment')
        if attachment and attachment.filename:
            upload_to_file_service(new_id, attachment)

        # Notify Metrics and Audit microservices
        log_to_metrics("ticket_created", new_id)
        log_to_audit(new_id, "created", f"Ticket created with title: {title}")
        
        return redirect(url_for('index'))
    
    return render_template('new_ticket.html')

@app.route('/resolve/<int:ticket_id>')
def resolve_ticket(ticket_id):
    """Mark a ticket as Closed."""
    tickets = load_tickets()
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['status'] = 'Closed'
            
            # Notify Metrics and Audit microservices
            log_to_metrics("ticket_resolved", ticket_id)
            log_to_audit(ticket_id, "resolved", "Ticket marked as Closed")
            break
    save_tickets(tickets)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
