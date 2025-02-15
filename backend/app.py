from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from models import db, User, QuizResponse
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
    """Parses a JSON file and loads it into the database"""
    try:
        with open("data/users.json", "r") as file:
            users_data = json.load(file)

        for user in users_data:
            hashed_password = bcrypt.generate_password_hash(user["password"]).decode("utf-8")
            new_user = User(
                username=user["username"],
                password=hashed_password,
                courses=",".join(user["courses"]),  # Convert list to comma-separated string
                hobbies=",".join(user["hobbies"])  # Convert list to comma-separated string
            )
            db.session.add(new_user)

        db.session.commit()
        return jsonify({"message": "Users loaded successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
