from flask import Flask, request, jsonify, send_from_directory
import os
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
VALID_API_KEY = "A3F91C2B44F0E1D9B07C8E5A12F4B6D3"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Uploads a file associated with a ticket/task.
    Expects: multipart/form-data with 'file', 'id', and 'api_key'.
    """
    api_key = request.form.get('api_key')
    target_id = request.form.get('id')
    
    if api_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files or not target_id:
        return jsonify({"error": "Missing file or ID"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Create a subfolder for the ticket/task ID
    ticket_folder = os.path.join(UPLOAD_FOLDER, str(target_id))
    if not os.path.exists(ticket_folder):
        os.makedirs(ticket_folder)
    
    # Save file with a unique name to avoid collisions
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(ticket_folder, unique_filename)
    file.save(file_path)

    return jsonify({
        "status": "success",
        "filename": unique_filename,
        "path": file_path
    }), 200

@app.route('/files/<target_id>', methods=['GET'])
def list_files(target_id):
    """Returns a list of files for a specific ticket/task."""
    ticket_folder = os.path.join(UPLOAD_FOLDER, str(target_id))
    if not os.path.exists(ticket_folder):
        return jsonify({"files": []}), 200
    
    files = os.listdir(ticket_folder)
    return jsonify({"files": files}), 200

@app.route('/download/<target_id>/<filename>', methods=['GET'])
def download_file(target_id, filename):
    """Serves the actual file."""
    ticket_folder = os.path.join(UPLOAD_FOLDER, str(target_id))
    return send_from_directory(ticket_folder, filename)

if __name__ == '__main__':
    app.run(port=5002, debug=True)
