import json
import os
from flask import Flask, request, jsonify, redirect, url_for, session, render_template
from groq import Groq
from firebase import add_user, login_user, add_user_profile_to_firebase, add_progress_to_firebase, \
    get_Data, get_progress, get_code
from worker import essay_topic, chat_bot, proficiency_cal, teach_bot, question_generator, evaluation_generator

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the 'uploads' directory exists
client = Groq()
app.config['SECRET_KEY'] = os.urandom(24)

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/')
def index():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    print(f'log : {e}')
    return render_template('404.html'), 404


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/progress')
def progress():
    user = request.cookies.get('username')
    data = get_progress(user)
    return jsonify(data)


@app.route('/getdata', methods=['POST'])
def getdata():
    data = request.get_json()
    topic = data.get('topic')
    user = request.cookies.get('username')
    data = get_Data(user, topic)
    return jsonify(data)


@app.route('/learn')
def learn():
    return render_template("learn.html")


@app.route('/learn_next')
def learn_next():
    return render_template("learn.html")


@app.route('/profiler')
def profiler():
    return render_template("PROF.html")


@app.route('/quiz', methods=['POST'])
def quiz():
    user = request.cookies.get('username')
    try:
        data = request.form.get('questiondata')
        if data is None:
            raise ValueError("No data found")
        data = json.loads(data)
        topic = data.get('topicname')
        history = data.get('chathistory')
        if not topic or not history:
            raise ValueError("Missing topic or history data")
        prog = get_progress(user)
        cefr = prog['cefr']
        questions = question_generator(topic, history, cefr)
        return render_template('quiz.html', ques=questions, history = history)

    except Exception as e:
        print(f"Error in proficiency_test: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        answers = request.form.get('answers')
        if not answers:
            raise ValueError("No answers data found.")
        answers = json.loads(answers)
        user = request.cookies.get('username')
        prog = get_progress(user)
        cefr = prog['cefr']
        evaluation = evaluation_generator(answers, cefr)
        code = get_code(evaluation, user)
        print("Answers received:", evaluation)
        return render_template('evaluation.html', eval=evaluation, code=code)
    except Exception as e:
        print(f"Error in submitting quiz: {e}")
        return jsonify({"error": "An error occurred while submitting the quiz."}), 500


@app.route('/proficiency_test', methods=['POST'])
def proficiency_test():
    try:
        user_data = request.form.get('userData')
        user_data = json.loads(user_data)
        topic_response = essay_topic(user_data)
        session['topic'] = topic_response
        return jsonify({"redirect_url": url_for('proficiency_test_page')})
    except Exception as e:
        print(f"Error in proficiency_test: {e}")
        return jsonify({"error": "error occurred"}), 500


@app.route('/proficiency_test_page')
def proficiency_test_page():
    try:
        topic = session.get('topic')
        if not topic:
            return jsonify({"error": "Topic not found"}), 404
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
            add_user_profile_to_firebase(username, user_data)
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
