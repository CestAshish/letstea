import base64
import json
from flask import Flask, render_template, request
from groq import Groq

app = Flask(__name__)
client = Groq()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/record-audio', methods=['POST'])
def record_audio():
    audio_data = request.json['audioData']
    audio_binary = base64.b64decode(audio_data.split(',')[1])  # Decode the base64 audio data

    # Use Groq for audio transcription
    transcription = client.audio.transcriptions.create(
        file=("audio.wav", audio_binary),
        model="whisper-large-v3-turbo",
        response_format="verbose_json"
    )

    return json.dumps({'text': transcription.text}), 200, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
