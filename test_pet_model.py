"""Pet model tests."""

import os
from unittest import TestCase

from models import db, Pet, Organization
from sqlalchemy.exc import IntegrityError

#set environmental variable to be a test db
os.environ['DATABASE_URL'] = "postgresql:///pawprint-test"

from app import app

db.drop_all()
db.create_all()

class PetModelTestCase(TestCase):
    """Test model for pets."""

    def setUp(self):
        """Create test client."""

        db.session.rollback()
        Pet.query.delete()

        self.client = app.test_client()
        app.testing=True

        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()
        self.app_context.pop()

    def test_pet_model(self):
        """Does the basic Pet model work?"""

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

        # Pet should have no bookmarked_by
        self.assertEqual(len(pet.bookmarked_by), 0)

        # Pet should have organization_id of the test organization AND organization of test organization
        self.assertEqual(pet.organization_id, "TEST-0")
        self.assertEqual(pet.organization, organization)
    
    def test_pet_create(self):
        """
        Does Pet.create successfully create a new Pet given
        valid information and fail to create one if any validations fail?
        """

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

        pet_data = {
            "id":11037,
            "name":"Test Pet",
            "type":"Test",
            "species":"Test",
            "breeds": {
                "primary":"Beta",
                },
            "age":"Newborn",
            "gender":"Unknown",
            "size":"Small",
            "status":"Unavailable",
            "organization_id":"TEST-0"
        }

        # create and commit a pet with necessary information
        good_pet = Pet.create(pet_data)

        db.session.add(good_pet)
        db.session.commit()

        # good_pet should be an instance of Pet and be in Pet.query.all()

        self.assertIsInstance(good_pet, Pet)
        self.assertIn(good_pet, Pet.query.all())

        # create and commit a pet WITHOUT the necessary information: no name
        pet_data = {
            "id":11037,
            # no name
            "type":"Test",
            "species":"Test",
            "breeds": {
                "primary":"Beta",
                },
            "age":"Newborn",
            "gender":"Unknown",
            "size":"Small",
            "status":"Unavailable",
            "organization_id":"TEST-0"
        }
        bad_pet = Pet.create(pet_data)

        # attempting to commit bad_pet should raise an IntegrityError exception
        db.session.add(bad_pet)
        self.assertRaises(IntegrityError, db.session.commit)
