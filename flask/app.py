from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# Firebase configuration
cred = credentials.Certificate("letstea-f644f-firebase-adminsdk-7a144-02e97e3d87.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://letstea-f644f-default-rtdb.firebaseio.com'
})

# Define reference to the root path in the database
ref = db.reference("/")

@app.route("/add_data")
def add_data():
    # Define the data structure to add
    data = {
        "Name": "Sam",
        "Age": 28,
        "Interests": ["Photography", "Traveling", "Cooking", "Writing", "Art", "Music", "Hiking"],
        "Domain": "Creative Writing",
        "Location": "New York, USA",
        "Gender": "Female",
        "Tone": "Friendly and adventurous",
        "Persona": "A creative soul who loves to express herself through writing and photography. "
                   "Sam enjoys exploring new places and cultures."
    }

    # Use the ref to add data at the path 'user/userprofile'
    ref.child("user").child("userprofile").set(data)  # Use `.set()` to overwrite or create

    return jsonify({"success": True, "message": "User profile data added!"}), 201


# Retrieve data from Firebase
@app.route("/get_data", methods=["GET"])
def get_data():
    data = ref.get()
    return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)
