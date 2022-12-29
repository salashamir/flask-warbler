"""Message Model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()


class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample users."""
        db.drop_all()
        db.create_all()

        # Deletee all records in tables, extra check
        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        # create sample user to test
        self.uid = 85855
        u = User.signup("testUser", "testUser@warbler.com", "password123", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)
        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_model_attributes(self):
        """Does our message contain correct attributes"""
        sample_msg = Message(text="This is a message from u!", user_id=self.uid)
        db.session.add(sample_msg)
        db.session.commit()

        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "This is a message from u!")

        msg = Message.query.filter_by(user_id=self.uid).first()
        self.assertEqual(msg.user_id, self.uid)
        self.assertEqual(msg.text, "This is a message from u!")

      
    def test_msg_user_relationship(self):
        """Does the relationship between user and message models hold true"""
        m = Message(text="a new warble.", user_id=self.uid)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.user, self.u)
      

    def test_message_liking(self):
        """Test whether likes are recorded on models"""
        msg_1 = Message(text="warble one", user_id=self.uid)
        msg_2 = Message(text="warble two", user_id=self.uid)

        u = User.signup("testuser2", "user2@proton.com", "icecavern_hasedh123", None)
        uid = 555
        u.id = uid
        db.session.add_all([msg_1,msg_2,u])
        db.session.commit()

        like = Likes(user_id=u.id, message_id=msg_2.id)
        db.session.add(like)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, msg_2.id)



    
