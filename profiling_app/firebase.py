import firebase_admin
from firebase_admin import credentials, db
import bcrypt

# Initialize Firebase
cred = credentials.Certificate("letstea-f644f-firebase-adminsdk-7a144-02e97e3d87.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://letstea-f644f-default-rtdb.firebaseio.com'
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
        if ref.child(username).get() is not None:
            return {'status': 'error', 'message': 'Username already exists.'}, 400
        ref.child(username).set(user_data)
        return {'status': 'success', 'message': 'User created successfully.'}, 201
    except Exception as e:
        print(f"Error adding user {username}: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


def check_profile(username):
    ref = db.reference('users')
    user_data = ref.child(username).get()
    print("User Data Retrieved:", user_data)
    if user_data['user_profile'] is None:
        return False


def login_user(username, password):
    if not username or not password:
        return {'status': 'error', 'message': 'Username and password are required.'}, 400
    try:
        ref = db.reference('users')
        user_data = ref.child(username).get()
        print("User Data Retrieved:", user_data)
        if user_data is None:
            return {'status': 'error', 'message': 'User not found.'}, 404
        if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            flag = False
            if 'user_profile' in user_data:
                flag = True
            return {'status': 'success', 'message': 'Login successful!', 'email': user_data['email'], 'flag':flag}, 200
        else:
            print('Invalid password attempt for user:', username)
            return {'status': 'error', 'message': 'Invalid password.'}, 401
    except Exception as e:
        print("Exception occurred during login:", str(e))
        return {'status': 'error', 'message': 'An internal error occurred.'}, 500


def add_user_profile_to_firebase(username, combined_user_data):
    if not username or not combined_user_data:
        return {'status': 'error', 'message': 'Username and combined data are required.'}, 400
    try:
        ref = db.reference('users')
        user_profile_ref = ref.child(username).child('user_profile')
        user_profile_ref.set(combined_user_data)
    except Exception as e:
        print(f"Error updating user profile for {username}: {str(e)}")
