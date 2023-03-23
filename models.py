"""SQLAlchemy models for Pawprint."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """Pawprint user."""

    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   autoincrement=True,
                   primary_key=True)
    
    email = db.Column(db.String,
                      unique=True,
                      nullable=False)
    
    username = db.Column(db.String,
                      unique=True,
                      nullable=False)
    
    password = db.Column(db.String,
                      nullable=False)
    
    first_name = db.Column(db.String,
                           nullable=False)
    
    last_name = db.Column(db.String)

    profile_picture_url = db.Column(db.String,
                                  default="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQNMw2X0QrpOWXaB-XTgu_fwKnrnLhJhSsh3GVZm0A&s")
    
    location = db.Column(db.String)

    bookmarked_pets = db.relationship('Pet',
                                      secondary='bookmarks',
                                      backref='bookmarked_by')
    
    followed_organizations = db.relationship('Organization',
                                             secondary='follows',
                                             backref='followed_by')

    @classmethod
    def signup(cls, email, username, password, first_name, last_name, profile_picture_url, location):
        """
        Sign up user.
        
        Hashes password to securely add user to Pawprint DB.
        """

        hashed_password = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            email=email,
            username=username,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            profile_picture_url=profile_picture_url,
            location=location,
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """
        Searches for a user with 'username' and checks if the provided password
        matches that user's password after hashing.
        
        Returns the matching User object if successful.
        
        If no such user can be found, or the password is incorrect, returns False.
        """

        user = cls.query.filter_by(username=username).one_or_none()

        if user:
            is_authenticated = bcrypt.check_password_hash(user.password, password)

            if is_authenticated:
                return user
            
        return False


class Organization(db.Model):
    """Animal welfare organization in Petfinder API database."""

    __tablename__ = 'organizations'

    id = db.Column(db.String,
                   primary_key=True)
    
    name = db.Column(db.String,
                      nullable=False)
    
    email = db.Column(db.String,
                      nullable=False)
    
    phone = db.Column(db.String)
    
    address = db.Column(db.String)
    
    city = db.Column(db.String,
                      nullable=False)
    
    state = db.Column(db.String,
                      nullable=False)
    
    postcode = db.Column(db.String,
                      nullable=False)
    
    country = db.Column(db.String,
                      nullable=False)
    
    url = db.Column(db.String,
                      nullable=False)
    
    image_url = db.Column(db.String)

    pets = db.relationship('Pet',
                           backref='organization')

    # add methods to help create organization?
    @classmethod
    def create(cls, petfinder_organization):
        """
        Creates a Pawprint DB organization object from
        a given Petfinder API organization object.
        """

        organization = Organization(
            id = petfinder_organization.get("id"),
            name = petfinder_organization.get("name"),
            email = petfinder_organization.get("email"),
            phone = petfinder_organization.get("phone"), 
            address = petfinder_organization.get("address").get("address1"), #CARE
            city = petfinder_organization.get("address").get("city"), #CARE
            state = petfinder_organization.get("address").get("state"), #CARE
            postcode = petfinder_organization.get("address").get("postcode"), #CARE
            country = petfinder_organization.get("address").get("country"), #CARE
            url = petfinder_organization.get("url"),
            image_url = petfinder_organization.get("photos")[0].get("full") if petfinder_organization.get("photos") else "" #CARE
        )

        db.session.add(organization)
        return organization


class Pet(db.Model):
    """Pet in Petfinder API database."""

    __tablename__ = 'pets'

    id = db.Column(db.Integer,
                   autoincrement=False,
                   primary_key=True)
    
    name = db.Column(db.String,
                      nullable=False)
    
    type = db.Column(db.String,
                      nullable=False)
    
    species = db.Column(db.String,
                      nullable=False)
    
    breed = db.Column(db.String,
                      nullable=False)
    
    color = db.Column(db.String)
    
    age = db.Column(db.String,
                      nullable=False)
    
    gender = db.Column(db.String,
                      nullable=False)
    
    size = db.Column(db.String,
                      nullable=False)
    
    status = db.Column(db.String,
                      nullable=False)
    
    description = db.Column(db.String)

    image_url = db.Column(db.String)

    organization_id = db.Column(db.String,
                                db.ForeignKey('organizations.id', ondelete="cascade"))
    
    @classmethod
    def create(cls, petfinder_animal):
        """
        Creates a Pawprint DB Pet object from the
        given Petfinder API Animal object.
        """

        color = petfinder_animal.get("colors").get("primary") if petfinder_animal.get("colors").get("primary") else "No Color Listed"
        image_url = petfinder_animal.get("photos")[0].get("full") if petfinder_animal.get("photos") else None

        pet = Pet(
            id = petfinder_animal.get("id"),
            name = petfinder_animal.get("name"),
            type = petfinder_animal.get("type"),
            species = petfinder_animal.get("species"),
            breed = petfinder_animal.get("breeds").get("primary"),
            color = color,
            age = petfinder_animal.get("age"),
            gender = petfinder_animal.get("gender"),
            size = petfinder_animal.get("size"),
            status = petfinder_animal.get("status"),
            description = petfinder_animal.get("description"),
            image_url = image_url,
            organization_id = petfinder_animal.get("organization_id"),
        )

        db.session.add(pet)
        return pet
    
    # organization = db.relationship('Organization')

    # # bookmarked_by = db.relationship('User',
    #                                 secondary='bookmarks')


class Bookmark(db.Model):
    """Pawprint user 'bookmarking' a pet for future reference."""

    __tablename__ = 'bookmarks'

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='cascade'),
                        primary_key=True)
    
    pet_id = db.Column(db.Integer,
                       db.ForeignKey('pets.id', ondelete='cascade'),
                       primary_key=True)
    
class Follow(db.Model):
    """Pawprint user 'following' an animal welfare organization."""

    __tablename__ = 'follows'

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='cascade'),
                        primary_key=True)
    
    organization_id = db.Column(db.String,
                       db.ForeignKey('organizations.id', ondelete='cascade'),
                       primary_key=True)
    

def connect_db(app):
    """Connect database to Flask app."""

    db.app = app
    db.init_app(app)