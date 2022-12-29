"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

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


class UserViewTestCase(TestCase):
    """Test views for users."""

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

        self.user1 = User.signup(username="carl",
                                    email="test1@test.com",
                                    password="carlpassword",
                                    image_url=None)
        
        self.user1_id = 88332 
        self.user1.id = self.user1_id

        self.user2 = User.signup(username="owen",
                                    email="owen1@test.com",
                                    password="owenpassword",
                                    image_url=None)
        self.user2_id = 23388
        self.user2.id = self.user2_id

        self.user3 = User.signup(username="emily",
                                    email="emily1@test.com",
                                    password="emilypassword",
                                    image_url=None)
        self.user4 = User.signup(username="patricia",
                                    email="patty1@test.com",
                                    password="patriciasecret483984",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_users_list(self):
        """Test that users added in setup show up on list index page"""

        with self.client as client:
            res = client.get("/users")

            self.assertIn("@testuser", str(res.data))
            self.assertIn("@carl", str(res.data))
            self.assertIn("@owen", str(res.data))
            self.assertIn("@emily", str(res.data))
            self.assertIn("@patricia", str(res.data))

    def test_users_search(self):
        """test that search functionality returns releveant users displayed on page"""
        
        with self.client as client:
            res = client.get("/users?q=l")

            self.assertIn("@emily", str(res.data))
            self.assertIn("@carl", str(res.data))
            self.assertNotIn("@testuser", str(res.data))
            self.assertNotIn("@owen", str(res.data))
            self.assertNotIn("@patricia", str(res.data))

            res2 = client.get("/users?q=testuser")
            self.assertIn("@testuser", str(res2.data))
            self.assertNotIn("@carl", str(res2.data))
            self.assertNotIn("@owen", str(res2.data))
            self.assertNotIn("@emily", str(res2.data))
            self.assertNotIn("@patricia", str(res2.data))

    def test_user_show(self):
        """Test that user details are displayed"""

        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}")

            self.assertEqual(res.status_code, 200)
            self.assertIn("@testuser", str(res.data))

    def likes_setup(self):
        """Code that will be reused in other methods"""

        message1 = Message(text="cool new warble", user_id=self.testuser_id)
        message2 = Message(text="Bought a new laptop!", user_id=self.testuser_id)
        message3 = Message(id=77731, text="drinking fizzy pop", user_id=self.user1_id)
        message4 = Message(id=738271, text="i'm new here!", user_id=self.user1_id)
        message5 = Message(id=555555, text="CORE.", user_id=self.user1_id)

        db.session.add_all([message1,message2,message3,message4,message5])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id=555555)

        db.session.add(like)
        db.session.commit()

    def test_user_details_likes(self):
        """Test that the user details are updated with a like added"""

        self.likes_setup()

        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}")

            self.assertEqual(res.status_code, 200)

            self.assertIn("@testuser", str(res.data))
            bs = BeautifulSoup(str(res.data), 'html.parser')

            messages_li = bs.find(id="messages-stat")
            following_li = bs.find(id="following-stat")
            followers_li = bs.find(id="followers-stat")
            likes_li = bs.find(id="likes-stat")

            self.assertIsNotNone(messages_li)
            self.assertIsNotNone(following_li)
            self.assertIsNotNone(followers_li)
            self.assertIsNotNone(likes_li)

            self.assertIn("2", messages_li.text)
            self.assertIn("0", following_li.text)
            self.assertIn("0", followers_li.text)
            self.assertIn("1", likes_li.text)

    def test_user_new_like(self):
        """Test adding of a like"""

        message = Message(id=372836, text="I'm hailing a taxi on the street", user_id=self.user1_id)
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            res = client.post("/users/add_like/372836", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==372836).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_user_remove_like(self):
        """Test that like is removed from user likes"""

        self.likes_setup()

        message = Message.query.filter(Message.text=="CORE.").one()
        self.assertIsNotNone(message)
        self.assertNotEqual(message.user_id, self.testuser_id)
        self.assertEqual(message.user_id, self.user1_id)

        like = Likes.query.filter(Likes.user_id==self.testuser_id and Likes.message_id==message.id).one()

        self.assertIsNotNone(like)

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            res = client.post(f"/users/add_like/{message.id}", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==message.id).all()

            self.assertEqual(len(likes), 0)

    def followers_setup(self):
        """Setup follows for tests below pertaining to folloing and follower methods"""

        follower_one = Follows(user_being_followed_id=self.user1.id, user_following_id=self.testuser_id)
        follower_two = Follows(user_being_followed_id=self.user2.id, user_following_id=self.testuser_id)
        follower_three = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.user2_id)

        db.session.add(follower_one)
        db.session.add(follower_two)
        db.session.add(follower_three)

        db.session.commit()

    def test_user_show_follows(self):
        """Test that following users appear as stat on details page"""

        self.followers_setup()

        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}")
            self.assertEqual(res.status_code, 200)

            self.assertIn("@testuser", str(res.data))
            bs = BeautifulSoup(str(res.data), 'html.parser')

            messages_li = bs.find(id="messages-stat")
            following_li = bs.find(id="following-stat")
            followers_li = bs.find(id="followers-stat")
            likes_li = bs.find(id="likes-stat")

            self.assertIsNotNone(messages_li)
            self.assertIsNotNone(following_li)
            self.assertIsNotNone(followers_li)
            self.assertIsNotNone(likes_li)

            self.assertIn("0", messages_li.text)
            self.assertIn("2", following_li.text)
            self.assertIn("1", followers_li.text)
            self.assertIn("0", likes_li.text)

    def test_user_following(self):
        """Test that following users show up on following page"""

        self.followers_setup()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            res = client.get(f"/users/{self.testuser_id}/following")

            self.assertEqual(res.status_code, 200)
            self.assertIn("@carl", str(res.data))
            self.assertIn("@owen", str(res.data))
            self.assertNotIn("@emily", str(res.data))
            self.assertNotIn("@patricia", str(res.data))

    def test_user_followers(self):
        """Test that followers page shows users who follow testuser"""

        self.followers_setup()
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            res = client.get(f"/users/{self.testuser_id}/followers")
            self.assertEqual(res.status_code,200)
            self.assertIn("@owen", str(res.data))
            self.assertNotIn("@carl", str(res.data))
            self.assertNotIn("@emily", str(res.data))
            self.assertNotIn("@patricia", str(res.data))

    def test_user_unathorized_follows(self):
        """Test that an unauthorized person gets unauthorized message response"""

        self.followers_setup()
        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn("@carl", str(res.data))
            self.assertNotIn("@owen", str(res.data))
            self.assertNotIn("@emily", str(res.data))
            self.assertNotIn("@patricia", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))

    def test_user_unathorized_followers(self):
        """Test that an unauthorized person gets unauthorized message response"""

        self.followers_setup()
        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn("@carl", str(res.data))
            self.assertNotIn("@owen", str(res.data))
            self.assertNotIn("@emily", str(res.data))
            self.assertNotIn("@patricia", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))














            