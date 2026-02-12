from flask import Flask, render_template, request, redirect, url_for
import json
import os
import random

app = Flask(__name__)
DATA_FILE = 'tickets.json'

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
        
        tickets = load_tickets()
        
        # specific logic to generate a new ID (simple max + 1)
        new_id = 1
        if tickets:
            new_id = max(t['id'] for t in tickets) + 1
            
        new_ticket_obj = {
            "id": new_id,
            "title": title,
            "description": description,
            "priority": priority, # This would come from the microservice
            "status": "Open"
        }
        
        tickets.append(new_ticket_obj)
        save_tickets(tickets)
        
        return redirect(url_for('index'))
    
    return render_template('new_ticket.html')

@app.route('/resolve/<int:ticket_id>')
def resolve_ticket(ticket_id):
    """Mark a ticket as Closed."""
    tickets = load_tickets()
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['status'] = 'Closed'
            break
    save_tickets(tickets)
    return redirect(url_for('index'))

app.run()
