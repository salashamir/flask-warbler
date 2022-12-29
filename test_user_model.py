"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup("testuser1", "testuser1@email.com", "SUPERSECRETPASSWORD746", None)
        uid1 = 45454
        user1.id = uid1

        user2 = User.signup("testuser2", "testuser2@email.com", "turtleLettuce7462", None)
        uid2 = 77733
        user2.id = uid2

        db.session.commit()

        self.user1 = User.query.get(uid1)
        self.user2 = User.query.get(uid2)
        self.uid1 = uid1
        self.uid2 = uid2

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages, followers, following, and likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)
        self.assertEqual(len(u.likes), 0)


    def test_user_follows(self):
        """Test that following functionality works"""

        self.user2.following.append(self.user1)
        db.session.commit()

        self.assertEqual(len(self.user2.followers), 0)
        self.assertEqual(len(self.user2.following), 1)
        self.assertEqual(len(self.user1.following), 0)
        self.assertEqual(len(self.user1.followers), 1)

        self.assertEqual(self.user1.followers[0].id, self.user2.id)
        self.assertEqual(self.user2.following[0].id, self.user1.id)


    def test_user_is_following(self):
        """Test the is following instance method"""

        self.user2.following.append(self.user1)
        db.session.commit()

        self.assertFalse(self.user1.is_following(self.user2))
        self.assertTrue(self.user2.is_following(self.user1))


    def test_user_is_followed_by(self):
        """Test the is_followed_by instance method"""

        self.user2.following.append(self.user1)
        db.session.commit()

        self.assertTrue(self.user1.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))

    
    def test_repr(self):
        self.assertEqual(repr(self.user1), f"<User #{self.user1.id}: {self.user1.username}, {self.user1.email}>" )
        self.assertEqual(repr(self.user2), f"<User #{self.user2.id}: {self.user2.username}, {self.user2.email}>" )


    def test_user_signup(self):
        """Test a valid user signup process"""

        user = User.signup("testvalid", "validsignup@email.com", "herald28234", None)
        user_id = 83627
        user.id = user_id
        db.session.commit()

        user_test = User.query.get(user_id)

        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username, user.username)
        self.assertEqual(user_test.email, user.email)
        self.assertEqual(user_test.password, user.password)
        self.assertNotEqual(user_test.password, "herald28234")
        self.assertTrue(user_test.password.startswith("$2b$"))


    def test_user_invalid_username_signup(self):
        """Test that error is raised when username not valid"""

        user = User.signup(None, "usertest@email.com", "kdniuerive232", None)
        uid = 475382637
        user.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_user_invalid_email_signup(self):
        """Test that error is raised when email is invalid"""

        user = User.signup("userrrr23", None, "kdniuerive232", None)
        uid = 475382637
        user.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_user_invalid_password_signup(self):
        """Test that error is raised when password empty and None"""

        with self.assertRaises(ValueError) as context:
            User.signup("testuser", "eidneun@email.com", "", None)
            
        with self.assertRaises(ValueError) as context:
            User.signup("testuser", "eidneun@email.com", None, None)

    
    def test_authentication(self):
        """Test user is authenticated"""

        user = User.authenticate(self.user1.username, "SUPERSECRETPASSWORD746")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.uid1)


    def test_user_invalid_username(self):
        """Test that false is returned from authenticate method"""

        self.assertFalse(User.authenticate("wrongusername", "SUPERSECRETPASSWORD746"))


    def test_user_invalid_password(self):
        """Test that false is reutrned from authenticate"""

        self.assertFalse(User.authenticate(self.user1.username, "wiurnfierfrfe4"))