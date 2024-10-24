import os
from flask import Flask, request, jsonify, render_template
from groq import Groq

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the 'uploads' directory exists

# Initialize Groq client
client = Groq()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    audio_file = request.files['audio']
    filename = os.path.join(UPLOAD_FOLDER, 'audio.wav')  # Change extension to .wav for compatibility

    try:
        audio_file.save(filename)

        # Use Groq for audio transcription
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(filename), open(filename, 'rb').read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json"
        )

        return jsonify({'transcription': transcription.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
