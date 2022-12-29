"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser_id = 7111
        self.testuser.id = self.testuser_id

        db.session.commit()


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_add_without_user(self):
        """Invalid response should be returned when user not logged in"""

        with self.client as client:
            res = client.post("/messages/new", data={"text":"warble one"}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))


    def test_add_with_fake_user(self):
        """Invalid user in session"""

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 74623732

            res = client.post("/messages/new", data={"text":"warbleeeeee"}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))


    def test_show_message(self):
        """Test message is shown for specific message route"""

        message = Message(id=6534, text="test warble!", user_id=self.testuser_id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY]= self.testuser.id

            mssg = Message.query.get(6534)

            res = client.get(f'/messages/{mssg.id}')

            self.assertEqual(res.status_code,200)
            self.assertIn(mssg.text, str(res.data))


    def test_show_invalid_message(self):
        """Test that 404 is returned for message that doesnt exist"""

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY]= self.testuser.id

            res = client.get('/messages/473847363')

            self.assertEqual(res.status_code, 404)


    def test_message_delete(self):
        """Test that user can delete their own message"""
        message = Message(id=11111, text="message to be deleted", user_id=self.testuser_id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            res = client.post("/messages/11111/delete", follow_redirects=True)
            self.assertEqual(res.status_code,200)

            message = Message.query.get(11111)

            self.assertIsNone(message)


    def test_message_delete_unauthorized(self):
        """Test that deleting a message when the user isn't authorized returns unauthorized message"""

        # create another user to delete a message from original user
        user2 = User.signup(username="testUser2", email="testuser2@lynx.com", password="impossdtoUnhash7524!", image_url=None)
        user2.id = 8552378

        # orginal user creates messages
        message = Message(id=432451, text="random warble!", user_id=self.testuser_id)
        db.session.add_all([user2, message])
        db.session.commit()

        # simulate logging user in, 
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 8552378

            res = client.post("/messages/432451/delete", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

            # checl that message is still in db
            message = Message.query.get(432451)
            self.assertEqual(message.text, "random warble!")


    def test_message_delete_unauthenticated(self):
        """Test that unauthorized is also returned when no one logged in and message dleete is attempted"""

        message = Message(id=7546342, text="test warble", user_id=self.testuser_id)
        db.session.add(message)
        db.session.commit()

        # try without logging in 
        with self.client as client:
            res = client.post("/messages/7546342/delete", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))