import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from groq import Groq
import json
import subprocess
import time
from firebase import add_user, login_user, add_user_profile_to_firebase, check_profile
from worker import essay_topic, chat_bot, proficiency_cal

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the 'uploads' directory exists
client = Groq()


@app.route('/')
def index():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/learn')
def learn():
    return render_template("teach.html")


@app.route('/profiler')
def profiler():
    return render_template("profiler.html")


@app.route('/proficiency_test', methods=['POST'])
def proficiency_test():
    try:
        user_data = request.form.get('userData')
        user_data = json.loads(user_data)
        topic_response = essay_topic(user_data)
        return render_template('proficiency_test.html', topic=topic_response)
    except Exception as e:
        print(f"Error in proficiency_test: {e}")
        return jsonify({"error": "error occurred"}), 500


@app.route('/proficiency_test_cal', methods=['POST'])
def proficiency_test_cal():
    try:
        user_data = request.form.get('user_data')
        essay = request.form.get('essay')
        username = request.form.get('username')
        user_data = json.loads(user_data)
        ce_fr_level_data = proficiency_cal(essay)
        combined_user_data = {**user_data, **ce_fr_level_data}
        add_user_profile_to_firebase(username, combined_user_data)
        return redirect(url_for('learn'))
    except Exception as e:
        print(f"Error in proficiency_test_cal: {e}")
        return jsonify({"status": "error", "message": "There was an error in proficiency_test_cal"}), 500


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message_history = data.get('history', [])
    response = chat_bot(0, message_history)
    if response.startswith('{'):
        response = response.strip()
        try:
            if not response.endswith('}'):
                continuation = chat_bot(0,
                                        f"Please continue from where you left off.{message_history + [response]}"
                                        )
                response += continuation.strip()
            user_data = json.loads(response)
            return jsonify({
                "status": "success",
                "message": "resulthasbeenobtained",
                "data": user_data,
            })
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return jsonify({"status": "error", "message": "restartisrequired"})
    return jsonify({
        "status": "message",
        "message": response,
    })


@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400
    audio_file = request.files['audio']
    filename = os.path.join(UPLOAD_FOLDER, 'audio.wav')  # Change extension to .wav for compatibility
    try:
        audio_file.save(filename)
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(filename), open(filename, 'rb').read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json"
        )
        return jsonify({'transcription': transcription.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create_user', methods=['POST'])
def create_user_route():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    result, status = add_user(username, email, password)
    return jsonify(result), status


@app.route('/login', methods=['POST'])
def login_route():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    result, status = login_user(username, password)
    return jsonify(result), status


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
