from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from parser.file_parser import parse_file_by_type, generate_html
import os
from werkzeug.utils import secure_filename
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
import traceback
import asyncio
import json
from parser.pdf_generator import convert_to_pdf_format, generate_pdf
from threading import Lock
import uuid
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://codescroll-document-generator-tech-dragoness-projects.vercel.app"
]}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "https://codescroll-document-generator-tech-dragoness-projects.vercel.app"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response    

generation_status = {}
generation_flags = {}
generation_lock = Lock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_FOLDER = os.path.join(BASE_DIR, "server/static/generated_docs")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "server/static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOC_FOLDER, exist_ok=True)

def get_extension(filename):
    return os.path.splitext(filename)[1].lower()

@app.route("/upload", methods=["POST"])
def upload():
    try:
        files = request.files.getlist("files")
        parsed_data = []

        # 🌟 Unique ID for tracking this generation
        generation_id = request.form.get("generation_id") or str(uuid.uuid4())
        generation_status[generation_id] = "processing"
        generation_flags[generation_id] = "active"
        
        batch_size = request.form.get("batch_size", type=int) or 5  # Default to 5 if not sent

        for file in files:
            # 🛑 Check before starting this file
            if generation_flags.get(generation_id) == "cancelled":
                raise Exception("Generation cancelled by user before parsing")

            filename = secure_filename(file.filename)
            file_ext = get_extension(filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            parsed = parse_file_by_type(
                file_path,
                generation_id=generation_id,
                status=generation_status,
                flags=generation_flags,
                batch_size=batch_size
            )
            
            # 🛑 Check again after parsing (if user cancelled mid-descriptions)
            if generation_flags.get(generation_id) == "cancelled":
                raise Exception("Generation cancelled by user during parsing")

            if parsed:
                parsed_data.append((filename, parsed, file_ext))

        # 🛑 Final pre-check before generating doc
        if generation_flags[generation_id] == "cancelled":
            raise Exception("Generation cancelled before HTML creation")

        html_filename = f"documentation_{generation_id}.html"
        html_path = os.path.join(DOC_FOLDER, html_filename)

        generate_html(parsed_data, html_path, hide_buttons=False)

        generation_status[generation_id] = "done"

        return jsonify({
            "success": True,
            "htmlPath": f"/docs/{html_filename}",  # Use correct route
            "generation_id": generation_id
        })

    except Exception as e:
        print("🐍 Backend Error:", traceback.format_exc(), flush=True)
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/generate-id")
def generate_id():
    generation_id = str(uuid.uuid4())
    generation_status[generation_id] = "starting"
    generation_flags[generation_id] = "active"
    return jsonify({"generation_id": generation_id})
    
@app.route("/generation-progress/<generation_id>")
def generation_progress(generation_id):
    return jsonify({
        "status": generation_status.get(generation_id, "unknown")
    })
    
@app.route("/cancel-generation", methods=["POST"])
def cancel_generation():
    generation_id = request.json.get("generation_id")

    if generation_id in generation_flags:
        generation_flags[generation_id] = "cancelled"
        generation_status[generation_id] = "cancelled"  # Also update status

        # 💣 Optionally delete any partial docs
        try:
            os.remove(os.path.join(DOC_FOLDER, "documentation.html"))
        except FileNotFoundError:
            pass

        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Generation ID not found"}), 404
    
@app.route("/docs/<filename>", methods=["GET"])
def docs(filename):
    html_path = os.path.join(DOC_FOLDER, filename)
    print(f"📦 Fetching HTML from: {html_path}")

    if os.path.exists(html_path):
        return send_file(html_path)
    return "No documentation generated yet.", 404

@app.route("/download-html")
def download_html():
    filename = request.args.get("filename")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    file_ext = os.path.splitext(filename)[1]
    cache_path = file_path + ".docjson"

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
    else:
        parsed = parse_file_by_type(file_path)
        if not parsed:
            return "Could not parse the file", 400

    parsed_data = [(filename, parsed, file_ext)]
    temp_output_path = os.path.join(DOC_FOLDER, "temp_download.html")
    generate_html(parsed_data, temp_output_path, hide_buttons=True)

    if os.path.exists(temp_output_path):
        return send_file(temp_output_path, as_attachment=True, download_name="documentation.html")
    return "HTML file not found", 404

@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    try:
        filename = request.args.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400
        
        ext = request.args.get("ext", None)

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.isfile(file_path):
            return jsonify({"success": False, "error": "File not found"}), 404

        cache_path = file_path + ".docjson"

        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                parsed = json.load(f)
        else:
            parsed = parse_file_by_type(file_path)
            if not parsed:
                return jsonify({"success": False, "error": "Unsupported or empty file"}), 400

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)

        parsed_data = [(filename, parsed)]  # ✅ Only this file
        formatted_data = convert_to_pdf_format([parsed], ext=ext)  # 🎯 Just the current one

        output_path = os.path.join(DOC_FOLDER, "documentation.pdf")
        generate_pdf(formatted_data, output_path, filename)

        return send_file(output_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        print("🐍 PDF Generation Error:", traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 4000)), debug=True)
