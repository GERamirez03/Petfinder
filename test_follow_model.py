"""User model tests."""

import os
from unittest import TestCase

from models import db, User, Organization, Bookmark, Follow

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app

db.drop_all()
db.create_all()

class FollowModelTestCase(TestCase):
    """Test model for bookmarks."""

    def setUp(self):
        """Create test client."""

        db.session.rollback()
        User.query.delete()
        Bookmark.query.delete()
        Follow.query.delete()

        self.client = app.test_client()
        app.testing=True

        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()
        self.app_context.pop()

    def test_follow_model(self):
        """Does the basic Follow model work?"""

        # create and commit a test user

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            first_name="Test"
        )

        db.session.add(user)
        db.session.commit()

        # need a test organization to for user to follow

        organization = Organization(
            id="TEST-0",
            name="Test Organization",
            email="test@organization.org",
            city="Test City",
            state="Test State",
            postcode="TEST-CODE",
            country="Test Country",
            url="https://google.com"
        )

        db.session.add(organization)
        db.session.commit()

        # create and commit a follow for user following organization

        follow = Follow(user_id=user.id, organization_id=organization.id)
        db.session.add(follow)
        db.session.commit()

        # the follow should be an instance of Follow and be in Follow.query.all()
        self.assertIsInstance(follow, Follow)
        self.assertIn(follow, Follow.query.all())

        # the follow should have the correct IDs
        self.assertEqual(follow.user_id, user.id)
        self.assertEqual(follow.organization_id, organization.id)
