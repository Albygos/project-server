from flask import Flask, request, jsonify
import os
import pytesseract
from PIL import Image
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
TEXT_FILE = "output.txt"
GROQ_API_KEY = "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"  # Replace with your API key
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def clean_upload_folder():
    """Clean the uploads folder by deleting old files."""
    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

def correct_grammar(text):
    """Correct grammar using Groq API."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": f"Correct this text:\\n\\n{text}"}]}
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except requests.exceptions.RequestException as e:
        return f"Error correcting grammar: {e}"

@app.route("/upload", methods=["POST"])
def upload_image():
    """Handle image upload and process the text using OCR and grammar correction."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    clean_upload_folder()  # Clean old files
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Perform OCR to extract text
    text = pytesseract.image_to_string(Image.open(file_path))

    # Correct grammar using Groq API
    corrected_text = correct_grammar(text)

    # Save the corrected text to a file
    with open(TEXT_FILE, "w") as f:
        f.write(corrected_text)

    return jsonify({"message": "Processing complete", "corrected_text": corrected_text})

@app.route("/get_text", methods=["GET"])
def get_text():
    """Return the corrected text from the output file."""
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r") as f:
            return jsonify({"corrected_text": f.read()})
    return jsonify({"message": "No processed text available"}), 404

# Run the app with the correct port for deployment on Render
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))  # Use Render's provided port or default to 5000
    app.run(host="0.0.0.0", port=PORT)
