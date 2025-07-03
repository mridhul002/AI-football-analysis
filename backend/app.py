from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import sys
import subprocess
from werkzeug.utils import secure_filename

# Define Flask App
app = Flask(__name__, static_folder="../website/static", template_folder="../website/templates")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This gets the correct backend folder

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static")
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "video" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename.replace(" ","_"))
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        print(f"✅ File uploaded: {filepath}")  # Debugging log

        # Process the video using main.py
        output_filename = f"processed_{filename}"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        # Run the processing script using the correct Python interpreter
        try:
            subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "main.py"), filepath, output_path], 
                check=True
            )
            print(f"✅ Processing complete: {output_path}")  # Debugging log
        except subprocess.CalledProcessError as e:
            print(f"❌ Error processing video: {e}")  # Print error details
            return jsonify({"error": "Failed to process video"}), 500

        return jsonify({"message": "File processed successfully", "video_url": f"/static/{output_filename}"})
    
    return jsonify({"error": "Invalid file format"}), 400

# Serve processed videos from the correct folder
@app.route(r"/static/<path:filename>")
def serve_video(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
