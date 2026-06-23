import os
import csv
from flask import Flask, request, jsonify, render_template
import uuid
import warnings
warnings.filterwarnings("ignore")

try:
    from transformers import pipeline
    MODEL_NAME = "Aadarshttech/nepali-english-codeswitched-whisper"
    print(f"Loading model {MODEL_NAME}...")
    transcriber = pipeline("automatic-speech-recognition", model=MODEL_NAME)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Failed to load model: {e}")
    transcriber = None

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

FEEDBACK_FILE = 'feedback.csv'

if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'transcript', 'rating', 'timestamp'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{file.filename}")
    file.save(filepath)
    
    if transcriber is None:
        # Mock transcriber response for testing if model failed to load
        text = "This is a mocked transcription. The model failed to load or is taking too long."
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'text': text})
        
    try:
        result = transcriber(filepath)
        text = result.get('text', '')
        # Clean up file after transcription
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'text': text})
    except Exception as e:
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
    app.run(debug=True, port=5000)
