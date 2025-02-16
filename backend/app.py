from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from models import db, User, QuizResponse, Friendship
import json
import openai
import os

app = Flask(__name__)

# Configure Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "supersecret"

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Create tables in the database
with app.app_context():
    db.create_all()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(username=data["username"], password=hashed_password, courses=data["courses"], hobbies=data["hobbies"])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        token = create_access_token(identity=user.id)
        return jsonify({"token": token})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/load_json", methods=["GET", "POST"])
def load_json():
    """Parses a JSON file and loads it into the database, avoiding duplicate usernames."""
    try:
        with open("data/users.json", "r") as file:
            users_data = json.load(file)

        for user in users_data:
            existing_user = User.query.filter_by(username=user["username"]).first()
            if existing_user:
                continue  # Skip this user if they already exist

            hashed_password = bcrypt.generate_password_hash(user["password"]).decode("utf-8")
            new_user = User(
                username=user["username"],
                password=hashed_password,
                courses=",".join(user["courses"]),
                hobbies=",".join(user["hobbies"]),
                community=",".join(user["community"])
            )
            db.session.add(new_user)

        db.session.commit()
        return jsonify({"message": "Users loaded successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_friend", methods=["POST"])
def add_friend():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()
    friend = User.query.filter_by(username=data["friend_username"]).first()

    if not user or not friend:
        return jsonify({"error": "User or friend not found"}), 404

    # Check if friendship already exists
    existing_friendship = Friendship.query.filter_by(user_id=user.id, friend_id=friend.id).first()
    if existing_friendship:
        return jsonify({"message": "Friendship already exists"}), 400

    # Add both sides of the friendship
    new_friendship = Friendship(user_id=user.id, friend_id=friend.id)
    reverse_friendship = Friendship(user_id=friend.id, friend_id=user.id)

    db.session.add(new_friendship)
    db.session.add(reverse_friendship)
    db.session.commit()

    return jsonify({"message": f"{user.username} and {friend.username} are now friends!"}), 201

@app.route("/friends/<username>", methods=["GET"])
def get_friends(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    friends = [
        {"id": friend.id, "username": friend.username}
        for friend in user.friends
    ]
    
    return jsonify({"username": user.username, "friends": friends})


# pair compatibility using openAI

openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

@app.route("/")
def home():
    return jsonify({"message": "OpenAI API is running!"})

@app.route("/find_study_buddies", methods=["POST"])
def find_study_buddies():
    """Fetches user data and finds the best study buddies using OpenAI."""
    data = request.json
    username = data.get("username")

    # Retrieve the requesting user from the database
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch all other users from the database
    other_users = User.query.filter(User.username != username).all()
    if not other_users:
        return jsonify({"message": "No other users found to match."}), 200

    # Convert data to structured format
    user_data = {
        "username": user.username,
        "courses": user.courses.split(",") if user.courses else [],
        "hobbies": user.hobbies.split(",") if user.hobbies else [],
        "community": user.community.split(",") if user.community else []

    }

    other_users_data = [
        {
            "username": u.username,
            "courses": u.courses.split(",") if u.courses else [],
            "hobbies": u.hobbies.split(",") if u.hobbies else [],
            "community": u.community.split(",") if u.community else []

        }
        for u in other_users
    ]

    # AI Prompt for Finding Compatible Users
    prompt = f"""
    You are an intelligent system that finds the best study buddies at university.
    Match the following user with the top 3 most compatible students based on shared courses, hobbies and communities.

    **User:**
    - Name: {user_data["username"]}
    - Courses: {", ".join(user_data["courses"])}
    - Hobbies: {", ".join(user_data["hobbies"])}
    - Community: {", ".join(user_data["community"])}

    **Other Users:**
    {other_users_data}

    **Instructions:**
    - Find the top 3 most compatible users based on shared courses, hobbies, and communities.
    - Return the result in **valid JSON format** like this:

    ```json
    {{
        "matches": [
            {{"username": "best_match_1"}},
            {{"username": "best_match_2"}},
            {{"username": "best_match_3"}}
        ]
    }}
    ```

    **Only return the JSON, nothing else.**
    """

    # Send request to OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",  # You can use "gpt-3.5-turbo" if needed
        messages=[{"role": "system", "content": "You are an expert in matching students based on courses and hobbies."},
                  {"role": "user", "content": prompt}]
    )

    # Parse AI Response (Ensure it is JSON)
    ai_response = response["choices"][0]["message"]["content"]

    return jsonify({"matches": ai_response})

if __name__ == "__main__":
    app.run(debug=True)
