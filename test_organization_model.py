"""Organization model tests."""

import os
from unittest import TestCase

from models import db, Organization
from sqlalchemy.exc import IntegrityError

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app

db.drop_all()
db.create_all()

class OrganizationModelTestCase(TestCase):
    """Test model for organizations."""

    def setUp(self):
        """Create test client."""

        db.session.rollback()
        Organization.query.delete()

        self.client = app.test_client()
        app.testing=True

        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()
        self.app_context.pop()

    def test_organization_model(self):
        """Does the basic Organization model work?"""

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

        # Organization should have no pets or followed_by
        self.assertEqual(len(organization.pets), 0)
        self.assertEqual(len(organization.followed_by), 0)
    
    def test_organization_create(self):
        """
        Does Organization.create successfully create a new Organization given
        valid information and fail to create one if any validations fail?
        """

        organization_data = {
            "id":"TEST-0",
            "name":"Test Organization",
            "email":"test@organization.org",
            "address":{
                "city":"Test City",
                "state":"Test State",
                "postcode":"TEST-CODE",
                "country":"Test Country"
            },
            "url":"https://google.com",
        }

        # create and commit an organization with necessary information
        good_organization = Organization.create(organization_data)

        db.session.add(good_organization)
        db.session.commit()

        # good_organization should be an instance of Organization and be in Organization.query.all()

        self.assertIsInstance(good_organization, Organization)
        self.assertIn(good_organization, Organization.query.all())

        # create and commit an organization WITHOUT the necessary information: no city
        organization_data = {
            "id":"TEST-0",
            "name":"Test Organization",
            "email":"test@organization.org",
            "address":{
                # No city
                "state":"Test State",
                "postcode":"TEST-CODE",
                "country":"Test Country"
            },
            "url":"https://google.com",
        }
        bad_organization = Organization.create(organization_data)

        # attempting to commit bad_organization should raise an IntegrityError exception
        db.session.add(bad_organization)
        self.assertRaises(IntegrityError, db.session.commit)
