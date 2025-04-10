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
CORS(app, resources={r"/*": {"origins": "*"}})

generation_status = {}
generation_flags = {}
generation_lock = Lock()

UPLOAD_FOLDER = "static/uploads"
DOC_FOLDER = "static/generated_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOC_FOLDER, exist_ok=True)

def get_extension(filename):
    return os.path.splitext(filename)[1].lower()

@app.route("/upload", methods=["POST"])
def upload():
    try:
        print("🚀 Upload endpoint hit.")

        files = request.files.getlist("files")
        print(f"📂 Received {len(files)} file(s)")

        parsed_data = []

        # 🌟 Unique ID for tracking this generation
        generation_id = str(uuid.uuid4())
        print(f"🆔 Generated unique generation_id: {generation_id}")

        generation_status[generation_id] = "processing"
        generation_flags[generation_id] = "active"

        for file in files:
            filename = secure_filename(file.filename)
            print(f"📝 Processing file: {filename}")

            file_ext = get_extension(filename)
            print(f"📄 File extension: {file_ext}")

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            print(f"📥 File saved to: {file_path}")

            parsed = parse_file_by_type(
                file_path,
                generation_id=generation_id,
                status=generation_status,
                flags=generation_flags
            )

            if parsed:
                print(f"✅ Successfully parsed {filename}")
                parsed_data.append((filename, parsed, file_ext))
            else:
                print(f"⚠️ Failed to parse {filename} or returned None")

        if generation_flags[generation_id] == "cancelled":
            print("🛑 Generation was flagged for cancellation.")
            raise Exception("Generation cancelled by user")

        html_filename = f"documentation_{generation_id}.html"
        html_path = os.path.join(DOC_FOLDER, html_filename)

        print(f"📄 Generating HTML at: {html_path}")
        generate_html(parsed_data, html_path, hide_buttons=False)

        if os.path.exists(html_path):
            print(f"🎉 HTML file successfully created: {html_path}")
        else:
            print(f"💥 HTML file NOT created: {html_path}")

        generation_status[generation_id] = "done"

        return jsonify({
            "success": True,
            "htmlPath": f"/docs/{html_filename}",  # Use correct route
            "generation_id": generation_id
        })

    except Exception as e:
        print("🐍 Backend Error:", traceback.format_exc())
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

        print(f"❌ Generation {generation_id} flagged for cancellation")

        # 💣 Optionally delete any partial docs
        try:
            os.remove(os.path.join(DOC_FOLDER, "documentation.html"))
        except FileNotFoundError:
            pass

        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Generation ID not found"}), 404
    
@app.route("/<filename>", methods=["GET"])
def docs(filename):
    html_path = os.path.join(DOC_FOLDER, filename)
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
        formatted_data = convert_to_pdf_format([parsed])  # 🎯 Just the current one

        output_path = os.path.join(DOC_FOLDER, "documentation.pdf")
        generate_pdf(formatted_data, output_path, filename)

        return send_file(output_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        print("🐍 PDF Generation Error:", traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 4000)), debug=True)
