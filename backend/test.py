import unittest
from app import app, db
from models import User

class FlaskAppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before all tests."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory DB for testing
        cls.client = app.test_client()

        with app.app_context():
            db.create_all()

    def setUp(self):
        """Runs before each test."""
        with app.app_context():
            db.session.query(User).delete()  # Clear database before each test
            db.session.commit()

    def test_user_creation(self):
        """Test creating a user and retrieving it from the database."""
        with app.app_context():
            new_user = User(username="testuser", password="hashedpassword", courses="CSC108,CSC148", hobbies="Reading,Swimming")
            db.session.add(new_user)
            db.session.commit()

            user = User.query.filter_by(username="testuser").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "testuser")
            self.assertEqual(user.courses, "CSC108,CSC148")

    def test_register_endpoint(self):
        """Test the /register API."""
        response = self.client.post("/register", json={
            "username": "testuser",
            "password": "securepassword",
            "courses": "CSC108,CSC148",
            "hobbies": "Reading,Swimming"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.json["message"])

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests."""
        with app.app_context():
            db.drop_all()

if __name__ == "__main__":
    unittest.main()
