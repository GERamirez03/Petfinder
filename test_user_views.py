"""User model tests."""

import os
from unittest import TestCase

from models import db, User
from sqlalchemy.exc import IntegrityError

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app

db.drop_all()
db.create_all()

class UserModelTestCase(TestCase):
    """Test model for users."""

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does the basic User model work?"""

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            first_name="Test"
        )

        db.session.add(user)
        db.session.commit()

        # User should have no Favorites or Follows
        self.assertEqual(len(user.bookmarked_pets), 0)
        self.assertEqual(len(user.followed_organizations), 0)
    
    def test_user_signup(self):
        """
        Does User.signup successfully create a new User given valid credentials
        and fail to create a new User if any validations fail?
        """

        # create and commit a user with proper credentials
        good_user = User.signup(
            email="good@email.com",
            username="gooduser",
            password="goodpasswordhash",
            first_name="Good"
        )

        db.session.add(good_user)
        db.session.commit()

        # good_user should be an instance of User and be in User.query.all()

        self.assertIsInstance(good_user, User)
        self.assertIn(good_user, User.query.all())

        # create and commit a user with INVALID credentials: no password
        bad_user = User.signup(
            email="bad@email.com",
            username="baduser",
            # no password
            first_name="Bad"
        )

        # attempting to commit bad_user should raise an IntegrityError exception
        db.session.add(bad_user)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_authenticate(self):
        """
        Does User.authenticate successfully return a user when given a valid username and
        password? Also, does it return False if the username OR password are invalid?
        """

        # create and commit a valid user
        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            first_name="Test"
        )

        db.session.add(user)
        db.session.commit()

        # User.authenticate should return the user if given correct credentials
        self.assertIs(user, User.authenticate(username="testuser", password="HASHED_PASSWORD"))

        # User.authenticate should return False if given incorrect username or password
        self.assertFalse(User.authenticate(username="testuse", password="HASHED_PASSWORD"))
        self.assertFalse(User.authenticate(username="testuser", password="HASHED_PASWORD"))