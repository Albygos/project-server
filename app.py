from flask import Flask, request, jsonify
import os
import pytesseract
from PIL import Image
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
TEXT_FILE = "output.txt"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Use environment variable for security
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def clean_upload_folder():
    """Deletes old images in the upload folder."""
    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

def correct_grammar(text):
    """Sends text to Groq API for grammar correction."""
    if not GROQ_API_KEY:
        return "Error: API Key not set"
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Correct this text:\n\n{text}"}]
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return "Error in API response"

@app.route("/upload", methods=["POST"])
def upload_image():
    """Handles image upload and OCR text extraction."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    clean_upload_folder()
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Extract text using OCR
    text = pytesseract.image_to_string(Image.open(file_path)).strip()
    if not text:
        return jsonify({"error": "No text extracted from image"}), 400

    # Correct the extracted text
    corrected_text = correct_grammar(text)

    # Save corrected text to file
    with open(TEXT_FILE, "w") as f:
        f.write(corrected_text)

    return jsonify({"message": "Processing complete", "corrected_text": corrected_text})

@app.route("/get_text", methods=["GET"])
def get_text():
    """Fetches the latest corrected text."""
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r") as f:
            return jsonify({"corrected_text": f.read()})
    return jsonify({"message": "No processed text available"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
