"""User views tests."""

import os
from unittest import TestCase

from models import db, User, Organization, Pet, Bookmark, Follow
from sqlalchemy.exc import IntegrityError

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app, CURRENT_USER_KEY

# disable CSRF tokens to test signing up and logging in
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client and add sample data."""

        db.session.rollback()
        User.query.delete()
        Bookmark.query.delete()
        Follow.query.delete()

        self.client = app.test_client()
        app.testing=True

        self.app_context = app.app_context()
        self.app_context.push()

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

        self.user_id = user.id
        self.user = user
        self.pet = pet
        self.organization = organization

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()
        self.app_context.pop()

    def test_logged_out_restrictions(self):
        """
        When logged out, are users restricted from bookmarking pets,
        following organizations, and accessing the edit profile page?
        """

        # data for testing
        data = {
            "organization_id" : "TEST-0",
            "pet_id" : 11037
        }

        # logged out users should not be able to (un)bookmark pets
        response = self.client.post("/pets/bookmark/new", data=data, follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Please log in to bookmark a pet!", html)

        # logged out users should not be able to (un)follow organizations
        response = self.client.post("/follows/remove", data=data, follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Unauthorized access", html)

        # logged out users should not be able to access or submit the edit profile form
        response = self.client.get("/profile", follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Please log in to view and edit your profile!", html)
    
    def test_logged_in_functionality(self):
        """
        When logged in, are users able to bookmark pets, follow organizations, and
        access the edit profile page?
        """

        # "log in" by adding test user's ID to the session
        with self.client.session_transaction() as session:
            session[CURRENT_USER_KEY] = self.user_id

            # after login, can proceed with tests

            # data for testing
            data = {
                "organization_id" : "TEST-0",
                "pet_id" : 11037
            }

            # logged in users should be able to bookmark pets and follow organizations
            response = self.client.post("/pets/bookmark/new", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            # assert that the test organization is not in the test user's follows
            # AND the test pet is now in the test user's bookmarked pets
            self.assertEqual(response.status_code, 200)
            self.assertIn(self.organization, self.user.followed_organizations)
            self.assertIn(self.pet, self.user.bookmarked_pets)

            # logged in users should be able to access the edit profile page
            response = self.client.get("/profile")
            html = response.get_data(as_text=True)

            # assert that test user successfully accesses the Edit Profile form page
            self.assertEqual(response.status_code, 200)
            self.assertIn("Edit Profile", html)
