import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from groq import Groq
import json

from firebase import add_user, login_user, add_user_profile_to_firebase, get_Data, add_progress_to_firebase
from worker import essay_topic, chat_bot, proficiency_cal, teach_bot


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the 'uploads' directory exists
client = Groq()

app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/progress')
def progress_and_teach_info():
     user = request.cookies.get('username')
     Data = get_Data(user)
     print(Data)
     return jsonify(Data)


@app.route('/learn')
def learn():
     return render_template("learn.html")


@app.route('/selected_topic', methods=['POST'])
def selected_topic():
    data = request.get_json()  # Get the JSON data from the request

    # Extract the index, domain, and level from the data
    index = data.get('index')
    domain = data.get('domain')
    level = data.get('level')

    # You can process the data here (e.g., save it to a database, log it, etc.)
    print(f"Selected Topic - Index: {index}, Domain: {domain}, Level: {level}")

    # Return a response
    return jsonify({'status': 'success', 'message': 'Topic data received successfully'})


@app.route('/profiler')
def profiler():
    return render_template("PROF.html")


from flask import session

@app.route('/proficiency_test', methods=['POST'])
def proficiency_test():
    try:
        user_data = request.form.get('userData')
        user_data = json.loads(user_data)
        topic_response = essay_topic(user_data)

        # Store the topic response in the session
        session['topic'] = topic_response

        # Return a redirection URL without exposing the topic in the URL
        return jsonify({"redirect_url": url_for('proficiency_test_page')})
    except Exception as e:
        print(f"Error in proficiency_test: {e}")
        return jsonify({"error": "error occurred"}), 500


from flask import session, render_template


@app.route('/proficiency_test_page')
def proficiency_test_page():
    try:
        topic = session.get('topic')

        # If the topic is not available, handle the case (redirect or show an error)
        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        # Render the template with the topic
        return render_template('proficiency_test.html', topic=topic)

    except Exception as e:
        print(f"Error in proficiency_test_page: {e}")
        return jsonify({"error": "An error occurred while loading the page"}), 500


@app.route('/proficiency_test_cal', methods=['POST'])
def proficiency_test_cal():
    try:
        essay = request.form.get('essay')
        username = request.form.get('username')
        ce_fr_level_data = proficiency_cal(essay)
        cefr = ce_fr_level_data['cefr']
        add_progress_to_firebase(username, cefr)
        return redirect(url_for('learn'))
    except Exception as e:
        print(f"Error in proficiency_test_cal: {e}")
        return jsonify({"status": "error", "message": "There was an error in proficiency test"}), 500


@app.route('/teach', methods=['POST'])
def teach():
    data = request.get_json()
    info = data['userData']
    message_history = data['history']
    print(info)
    print(message_history)
    response = teach_bot(info, message_history)
    return jsonify({
        "status": "message",
        "message": response,
    })


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message_history = data.get('history', [])
    username = data.get("username")
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
            add_user_profile_to_firebase(username,user_data)
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


@app.route('/dologin', methods=['POST'])
def login_route():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    result, status = login_user(username, password)
    return jsonify(result), status


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
