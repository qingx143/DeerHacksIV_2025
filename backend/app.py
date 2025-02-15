from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from models import db, User, QuizResponse, Friendship
import json

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
                hobbies=",".join(user["hobbies"])
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

if __name__ == "__main__":
    app.run(debug=True)
