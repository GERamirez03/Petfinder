"""User model tests."""

import os
from unittest import TestCase

from models import db, User, Organization, Pet, Bookmark, Follow

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app

db.drop_all()
db.create_all()

class BookmarkModelTestCase(TestCase):
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

    def test_bookmark_model(self):
        """Does the basic Bookmark model work?"""

        # create and commit a test user

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            first_name="Test"
        )

        db.session.add(user)
        db.session.commit()

        # need a test organization to reference in Pet organization_id Foreign Key column

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

        # create and commit a test pet

        pet = Pet(
            id=11037,
            name="Test Pet",
            type="Test",
            species="Test",
            breed="Beta",
            age="Newborn",
            gender="Unknown",
            size="Small",
            status="Unavailable",
            organization_id="TEST-0"
        )

        db.session.add(pet)
        db.session.commit()

        # create and commit a bookmark for user bookmarking pet

        bookmark = Bookmark(user_id=user.id, pet_id=pet.id)
        db.session.add(bookmark)
        db.session.commit()

        # the bookmark should be an instance of Bookmark and be in Bookmark.query.all()
        self.assertIsInstance(bookmark, Bookmark)
        self.assertIn(bookmark, Bookmark.query.all())

        # the bookmark should have the correct IDs
        self.assertEqual(bookmark.user_id, user.id)
        self.assertEqual(bookmark.pet_id, pet.id)
