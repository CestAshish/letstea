import firebase_admin
from firebase_admin import credentials, db
import bcrypt
from worker import chat_bot, topic_desc

# Initialize Firebase
cred = credentials.Certificate("letstea.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://letstea-340ff-default-rtdb.firebaseio.com'
})


def add_user(username, email, password):
    if not username or not email or not password:
        return {'status': 'error', 'message': 'All fields are required.'}, 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_data = {
        'email': email,
        'password': hashed_password
    }

    try:
        ref = db.reference('users')

        # Check if username already exists
        if ref.child(username).get() is not None:
            return {'status': 'error', 'message': 'Username already exists.'}, 400

        # Check if email already exists
        users = ref.get()  # Get all users
        if users:
            for user in users.values():
                if user.get('email') == email:
                    return {'status': 'error', 'message': 'Email already exists.'}, 400

        # Add the new user
        ref.child(username).set(user_data)
        return {'status': 'success', 'message': 'User created successfully.'}, 201

    except Exception as e:
        print(f"Error adding user {username}: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


def get_progress(username):
    ref = db.reference('users')
    user_data = ref.child(username).get()
    progress = user_data["progress"]
    return progress

# hi
def get_Data(username, topic, progtopic):
    code = 0
    if topic == progtopic:
        code = 1
    ref = db.reference('users')
    user_data = ref.child(username).get()
    history = user_data['message_history']
    if code == 0:
        history = []
    persona = user_data["ai_persona"]
    profile = user_data["user_profile"]
    cefr = user_data["progress"]["cefr"]
    topic_detail = topic_desc(topic, user_data)
    data = {"user profile": profile,
            "cefr": cefr,
            "ai persona": persona,
            "topic description": topic_detail,
            "previous session history": history,
            "code": code
            }
    print(topic,progtopic)
    return data


def get_code(evaluation, username):
    print("entered code")
    print(evaluation)
    total_score = 0
    total_questions = len(evaluation)
    for item in evaluation:
        total_score += item[2]
    score_percentage = total_score / total_questions
    ref = db.reference('users')
    user_progress_ref = ref.child(username).child('progress')
    user_data = user_progress_ref.get()
    domain = user_data["domain"]
    cefr = user_data["cefr"]
    index = user_data["index"]
    if score_percentage >= 0.7:
        index += 1
    if index > 100:
        index = 1
        if cefr == "A1":
            cefr = "A2"
        elif cefr == "A2":
            cefr = "B1"
        elif cefr == "B1":
            cefr = "B2"
        elif cefr == "B2":
            cefr = "C1"
        elif cefr == "C1":
            cefr = "C2"
        elif cefr == "C2":
            pass
    user_progress_ref.update({
        'domain': domain,
        'cefr': cefr,
        'index': index
    })
    return 1 if score_percentage >= 0.7 else 0


def login_user(username, password):
    if not username or not password:
        return {'status': 'error', 'message': 'Username and password are required.'}, 400
    try:
        ref = db.reference('users')
        user_data = ref.child(username).get()
        if user_data is None:
            return {'status': 'error', 'message': 'User not found.'}, 404
        if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            flag = False
            if 'user_profile' in user_data:
                flag = True
            return {'status': 'success', 'message': 'Login successful!', 'email': user_data['email'], 'flag': flag}, 200
        else:
            print('Invalid password attempt for user:', username)
            return {'status': 'error', 'message': 'Invalid password.'}, 401
    except Exception as e:
        print("Exception occurred during login:", str(e))
        return {'status': 'error', 'message': 'An internal error occurred.'}, 500


def add_user_profile_to_firebase(username, user_data):
    if not username or not user_data:
        return {'status': 'error', 'message': 'Username and combined data are required.'}, 400
    try:
        ref = db.reference('users')
        user_data_persona = [{'role': 'user', 'content': f'user profile input : {user_data}'}]
        persona = chat_bot(3, user_data_persona)
        user_profile_ref = ref.child(username).child('user_profile')
        ai_persona = ref.child(username).child('ai_persona')
        user_profile_ref.set(user_data)
        ai_persona.set(persona)
        print("done")
    except Exception as e:
        print(f"Error updating user profile for {username}: {str(e)}")


def add_progress_to_firebase(username, cefr):
    if not username or not cefr:
        return {'status': 'error', 'message': 'Username and combined data are required.'}, 400
    try:
        ref = db.reference('users')
        user_data = ref.child(username).get()
        domain = user_data["user_profile"]["Domain"]
        progress = {
            "domain": domain,
            "cefr": cefr,
            "index": 1,
        }
        # message_history = {'history':'temp'}
        # user_history_ref = ref.child(username).child('message_history')
        user_progress_ref = ref.child(username).child('progress')
        user_progress_ref.set(progress)
        # user_history_ref.set(message_history)

    except Exception as e:
        print(f"Error updating cefr for {username}: {str(e)}")


def update_history(username, history):
    ref = db.reference('users')
    user_progress_ref = ref.child(username).child('message_history')
    user_progress_ref.update({'history':history})