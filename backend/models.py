from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    courses = db.Column(db.Text, nullable=True)  # Store as comma-separated values
    hobbies = db.Column(db.Text, nullable=True)

class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    responses = db.Column(db.Text, nullable=False)  # Store quiz answers as JSON
