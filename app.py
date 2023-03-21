"""Flask application for Pawprint."""

from flask import Flask, render_template, request, flash, redirect, session, get_flashed_messages, g 
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from models import db, connect_db, User, Organization, Pet, Bookmark
from forms import SignUpForm, LoginForm
from secret import MY_API_KEY, MY_SECRET

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pawprint'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "geram03_pawprint"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True

debug = DebugToolbarExtension(app)

connect_db(app)

CURRENT_USER_KEY = "current_user"

# TODO: Implement functionality that adds organizations and pets to the local DB WHEN the user bookmarks a pet/organization. 


# TODO: If a request is made and then we get a 401 in response, ATTEMPT to generate a new access token AND redirect to the same page/make the same request again with that new access token
# TODO: Make this process of getting a new access token its own separate function, which also adds the token to the flask session
# Idea: Only add pets/organizations to Pawprint DB if user bookmarks them?
# TODO: Navbar which displays logged in user with options to view account/bookmarks/edit account/logout OR login/register if logged out

# Reference: {"type":"https://httpstatus.es/401", "status":401, "title":"Unauthorized", "detail":"Access token invalid or expired"}

# def create_pets(pets):
#     """Helper function that accepts a list of pets from Petfinder API and returns a list of Pawprint DB Pet objects."""

#     converted_pets = []

#     for pet in pets:
#         if Pet.query.get(pet.id):
#             converted_pet = Pet.query.get(pet.id)
#         else:
#             converted_pet = Pet(
#                 id = pet.id,
#                 name = pet.name,
#                 type = pet.type,
#                 species = pet.species,
#                 breed = pet.breed,
#                 color = pet.color,
#                 age = pet.age,
#                 gender = pet.gender,
#                 size = pet.size,
#                 status = pet.status,
#                 description = pet.description,
#                 image_url = pet.image_url,

#             )

# def create_organizations(organizations):
#     """Helper function that accepts a list of organizations from Petfinder API and returns a list of Pawprint DB Organization objects."""

#     converted_organizations = []

#     for organization in organizations:
#         if Organization.query.get(organization.id):
#             converted_organization = Organization.query.get(organization.id)
#         else:
#             converted_pet = Pet(
#                 id = pet.id,
#                 name = pet.name,
#                 type = pet.type,
#                 species = pet.species,
#                 breed = pet.breed,
#                 color = pet.color,
#                 age = pet.age,
#                 gender = pet.gender,
#                 size = pet.size,
#                 status = pet.status,
#                 description = pet.description,
#                 image_url = pet.image_url,

#             )


@app.before_request
def add_user_to_g():
    """If user is logged in, add the current user to Flask globally."""

    if CURRENT_USER_KEY in session:
        g.user = User.query.get(session[CURRENT_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""

    # to track logged in user, add their id to the flask session
    session[CURRENT_USER_KEY] = user.id

def do_logout():
    """Log user out."""

    if CURRENT_USER_KEY in session:
        del session[CURRENT_USER_KEY]

@app.route('/')
def generate_token():
    """Generate an access token and redirect to homepage."""

    url = "https://api.petfinder.com/v2/oauth2/token"

    data = {
        "grant_type" : "client_credentials",
        "client_id" : MY_API_KEY,
        "client_secret" : MY_SECRET
    }

    response = requests.post(url, data=data)

    status_code = response.status_code
    text = response.text
    json = response.json()

    access_token = json.get("access_token") # need a new access token every 60min... for now, just have every new session make a new token.

    session["access_token"] = access_token

    flash("Access token generated!")

    return redirect('/home')

    # return render_template('home.html', status_code=status_code, text=text, json=json)

@app.route('/home')
def show_homepage():
    """Show Pawprint homepage with options to search, register, log in."""

    return render_template('homepage.html')

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """
    Handle user signup.
    
    Create user and add to DB.
    
    Redirect to homepage.
    """

    form = SignUpForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                email = form.email.data,
                username = form.username.data,
                password = form.password.data,
                first_name = form.first_name.data,
                last_name = form.last_name.data,
                profile_picture_url = form.profile_picture_url.data or User.profile_picture_url.default.arg,
                location = form.location.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username or email already taken", "danger")
            return render_template('users/signup.html', form=form)

        do_login(user)

        flash(f"Welcome to Pawprint, {user.first_name}!")

        return redirect('/')
    
    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user:
            do_login(user)
            flash(f"Welcome back, {user.first_name}!", "success")
            return redirect("/")
        
        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout."""

    do_logout()
    flash("Logout successful.")
    return redirect('login')

@app.route('/bookmarks')
def show_bookmarks():
    """Show bookmarks for the logged in user."""

    if not g.user:
        flash("Please log in to view your bookmarks!", "danger")
        return redirect("/")
    
    pets = g.user.bookmarked_pets

    return render_template('users/bookmarks.html', pets=pets)
    


@app.route('/pets')
def show_pets():
    """Show list of pets from Petfinder API."""

    url = "https://api.petfinder.com/v2/animals"

    headers = {"Authorization" : f"Bearer {session['access_token']}"}

    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()

    pets = json.get("animals")
    pagination = json.get("pagination")

    # converted_pets = create_pets(pets)

    # for pet in pets:
    #     pawprint_pet = create_pet(pet)
    #     pawprint_pets.append(pawprint_pet)
    # for pet in pets
    # if Pet.query.one_or_none(pet.id) is None:
    # (construct and commit that pet to the Pawprint DB) TRY Pet.query.get(PK) first and i think that returns None?

    return render_template('pets.html', status_code=status_code, pets=pets)

# idea: replace path with pets/bookmark/new and just take out the pet_id in function params bc we use the form anyway...
@app.route('/pets/bookmark/<int:pet_id>', methods=["POST"])
def bookmark_pet(pet_id):
    """
    Bookmark target pet for logged-in user.
    Adds pet and its organization to Pawprint DB.
    """

    # if the user is logged in
    if not g.user:
        flash("Please log in to bookmark a pet!", "danger")
        return redirect("/")
    

    # handle adding the organization first
    # do we already have the organization locally?
    organization_id = request.form["organization_id"]
    organization = Organization.query.get(organization_id)

    if not organization:
        # if the organization is not registered locally, add it to our local DB before proceeding

        # need all of the organization's info before commiting it to DB
        url = f"https://api.petfinder.com/v2/organizations/{organization_id}"
        headers = {"Authorization" : f"Bearer {session['access_token']}"}
        response = requests.get(url, headers=headers)

        status_code = response.status_code
        json = response.json()

        petfinder_organization = json.get("organization")

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
            image_url = petfinder_organization.get("photos")[0].get("full") #CARE
        )

        db.session.add(organization)
        db.session.commit()

    #at this point we have the org in the DB but not the pet
    pet_id = request.form["pet_id"]
    pet = Pet.query.get(pet_id)

    # TODO: Idea for a helper function for creating Pawprint DB Organization AND/OR Pet objects:
    # they accept the pet/org DICT from Petfinder and create the object, return the object if successful, return false if integrity error

    if not pet:
        # if the pet is not registered on local DB, add it to local DB before creating bookmark

        # need all of the pet's info before commiting it to DB
        url = f"https://api.petfinder.com/v2/animals/{pet_id}"
        headers = {"Authorization" : f"Bearer {session['access_token']}"}
        response = requests.get(url, headers=headers)

        #IDEA for pet creation specifically: have ALL of pet's relevant info as hidden inputs to read off

        status_code = response.status_code
        json = response.json()

        petfinder_animal = json.get("animal")

        pet = Pet(
            id = petfinder_animal.get("id"),
            name = petfinder_animal.get("name"),
            type = petfinder_animal.get("type"),
            species = petfinder_animal.get("species"),
            breed = petfinder_animal.get("breeds").get("primary"),
            color = petfinder_animal.get("colors").get("primary"),
            age = petfinder_animal.get("age"),
            gender = petfinder_animal.get("gender"),
            size = petfinder_animal.get("size"),
            status = petfinder_animal.get("status"),
            description = petfinder_animal.get("description"),
            image_url = petfinder_animal.get("photos")[0].get("full"),
            organization_id = petfinder_animal.get("organization_id"),
        )

        db.session.add(pet)
        db.session.commit()

    bookmark = Bookmark(user_id=g.user.id, pet_id=pet.id)
    db.session.add(bookmark)
    db.session.commit()

    flash(f"Successfully bookmarked {pet.name} to your profile, {g.user.first_name}!")

    return redirect('/pets')

    
    # get the Petfinder API Pet object for that pet REQURES PET ID
    # get the Petfinder API Organization object for that pet's organization REQUIRES ORG ID
    # convert and commit the organization to Pawprint DB format
    # convert and commit the pet the the Pawprint DB format
    # create and commit the Bookmark object in Pawprint DB