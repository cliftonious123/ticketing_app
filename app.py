from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super-secret-key-replace-in-production' # For session management

DATA_FILE = 'tickets.json'
RNG_SERVICE_URL = "https://rng-microservice-4b0c29beb99a.herokuapp.com/generate-id"
FILE_SERVICE_URL = "https://attachment-microservice-fd7891de4df9.herokuapp.com/upload"
FILE_LIST_URL = "https://attachment-microservice-fd7891de4df9.herokuapp.com/files"
FILE_DOWNLOAD_URL = "https://attachment-microservice-fd7891de4df9.herokuapp.com/download"
METRICS_REPORT_URL = "https://metrics-microservice-6c7a57f3cbb8.herokuapp.com/report"
METRICS_LOG_URL = "https://metrics-microservice-6c7a57f3cbb8.herokuapp.com/log"
AUDIT_LOG_URL = "https://audit-microservice-4c490370dceb.herokuapp.com/audit"
AUDIT_HISTORY_URL = "https://audit-microservice-4c490370dceb.herokuapp.com/history"
API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return "Unauthorized", 401
        return f(*args, **kwargs)
    return decorated_function

def upload_to_file_service(item_id, file):
    """Helper to send attachment to the File Attachment microservice."""
    try:
        files = {'file': (file.filename, file.stream, file.mimetype)}
        data = {'api_key': API_KEY, 'id': item_id}
        requests.post(FILE_SERVICE_URL, data=data, files=files, timeout=5)
    except Exception:
        pass 

def log_to_metrics(event_type, item_id):
    """Helper to send event data to the Metrics microservice."""
    try:
        requests.post(METRICS_LOG_URL, json={
            "api_key": API_KEY,
            "event_type": event_type,
            "item_id": item_id
        }, timeout=2)
    except Exception:
        pass 

def log_to_audit(item_id, action, details):
    """Helper to send change data to the Audit microservice."""
    try:
        requests.post(AUDIT_LOG_URL, json={
            "api_key": API_KEY,
            "item_id": item_id,
            "action": action,
            "details": details
        }, timeout=2)
    except Exception:
        pass 

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple logic: admin/admin for admin, anything else for user
        if username == 'admin' and password == 'admin':
            session['username'] = username
            session['role'] = 'admin'
            return redirect(url_for('index'))
        elif username and password:
            session['username'] = username
            session['role'] = 'user'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """The Homepage: Displays the dashboard of all tickets."""
    tickets = load_tickets()
    return render_template('index.html', tickets=tickets, role=session.get('role'), username=session.get('username'))

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = random.choice(["Low", "Medium", "High"]) 
        
        try:
            response = requests.post(RNG_SERVICE_URL, json={"api_key": API_KEY}, timeout=5)
            if response.status_code == 200:
                new_id = response.json().get('ticket_id')
            else:
                raise Exception("Microservice error")
        except Exception:
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

        attachment = request.files.get('attachment')
        if attachment and attachment.filename:
            upload_to_file_service(new_id, attachment)

        log_to_metrics("ticket_created", new_id)
        log_to_audit(new_id, "created", f"Ticket created with title: {title}")
        return redirect(url_for('index'))
    
    return render_template('new_ticket.html')

@app.route('/resolve/<int:ticket_id>')
@login_required
def resolve_ticket(ticket_id):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['status'] = 'Closed'
            log_to_metrics("ticket_resolved", ticket_id)
            log_to_audit(ticket_id, "resolved", "Ticket marked as Closed")
            break
    save_tickets(tickets)
    return redirect(url_for('index'))

# Admin-only routes for microservice data
@app.route('/admin/metrics')
@login_required
@admin_required
def view_metrics():
    try:
        response = requests.get(METRICS_REPORT_URL, timeout=5)
        data = response.json()
    except Exception:
        data = {"error": "Metrics service unavailable"}
    return render_template('metrics.html', data=data)

@app.route('/admin/audit')
@login_required
@admin_required
def view_audit_log():
    # For simplicity, we just show a general message or try to fetch all if service supports it
    # Currently audit service has /history/<item_id>. Let's assume we want to see it for specific items or a general view
    return render_template('audit.html')

@app.route('/admin/audit/<int:item_id>')
@login_required
@admin_required
def view_item_audit(item_id):
    try:
        response = requests.get(f"{AUDIT_HISTORY_URL}/{item_id}", timeout=5)
        data = response.json()
    except Exception:
        data = {"error": "Audit service unavailable"}
    return render_template('audit_detail.html', data=data, item_id=item_id)

@app.route('/admin/attachments/<int:item_id>')
@login_required
@admin_required
def view_attachments(item_id):
    try:
        response = requests.get(f"{FILE_LIST_URL}/{item_id}", timeout=5)
        data = response.json()
    except Exception:
        data = {"error": "Attachment service unavailable"}
    return render_template('attachments.html', data=data, item_id=item_id, download_url=FILE_DOWNLOAD_URL)

if __name__ == '__main__':
    app.run()
