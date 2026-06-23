import os
import csv
from flask import Flask, request, jsonify, render_template
import uuid
import warnings
import torch

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

FEEDBACK_FILE = 'feedback.csv'

if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'transcript', 'rating', 'timestamp'])

transcriber_cache = {
    "model_path": None,
    "pipeline": None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_model', methods=['GET'])
def select_model():
    import tkinter as tk
    from tkinter import filedialog
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory(title="Select Model Directory")
        root.destroy()
        return jsonify({"path": folder_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    model_path = request.form.get('model_path', 'Aadarshttech/nepali-english-codeswitched-whisper')
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{file.filename}")
    file.save(filepath)
    
    if transcriber_cache["model_path"] != model_path or transcriber_cache["pipeline"] is None:
        try:
            from transformers import pipeline
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            print(f"Loading model {model_path} on {device}...")
            transcriber_cache["pipeline"] = pipeline(
                "automatic-speech-recognition", 
                model=model_path,
                device=device,
                generate_kwargs={"no_repeat_ngram_size": 5}
            )
            transcriber_cache["model_path"] = model_path
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f"Model failed to load. Error: {str(e)}"}), 500
        
    try:
        result = transcriber_cache["pipeline"](filepath)
        text = result.get('text', '')
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'text': text})
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    transcript = data.get('transcript', '')
    rating = data.get('rating', 0)
    
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    
    with open(FEEDBACK_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([str(uuid.uuid4()), transcript, rating, timestamp])
        
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
