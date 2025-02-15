from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    courses = db.Column(db.Text, nullable=True)  # Store as comma-separated values
    hobbies = db.Column(db.Text, nullable=True)
    
    # Relationship to get a user's friends
    friends = db.relationship(
        "User",
        secondary="friendship",
        primaryjoin="User.id == Friendship.user_id",
        secondaryjoin="User.id == Friendship.friend_id",
        backref="friend_list"
    )

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    #  that the same friendship isn't added twice
    __table_args__ = (db.UniqueConstraint("user_id", "friend_id", name="unique_friendship"),)
class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    responses = db.Column(db.Text, nullable=False)  # Store quiz answers as JSON
