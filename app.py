"""Flask application for Pawprint."""

from flask import Flask, render_template, request, flash, redirect, session, get_flashed_messages, g 
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from models import db, connect_db, User, Organization, Pet, Bookmark, Follow
from forms import SignUpForm, LoginForm, EditUserForm, SearchForm
from secret import MY_API_KEY, MY_SECRET

from wtforms import StringField

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pawprint'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "geram03_pawprint"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

connect_db(app)

CURRENT_USER_KEY = "current_user"

# TODO: Implement Search Filters, search forms at the top of animals/organizations pages respectively to narrow down results.

# TODO: Clean-up: Bookmarking functionality, adding organization, pet, bookmark, follow into DB ...
# TODO: Clean-up: Error handling for attempted duplicate data entries for pets, organizations, follows, bookmarks

# TODO: STRETCH GOAL is to implement a dynamic WTForms form on the homepage which lets the user toggle between searching for animals or organizations, and then
# populates a drop-down with a list of potential filters followed by a text input for that filter's value. Also has a "Add another filter" button which would 
# keep adding filters and text areas.
# TODO: STRETCH GOAL find a way to ensure that user always has a valid token. If a request fails (401), attempt to resolve it by generating a new token and
# redirecting to the same page that the user was trying to access. timer, etc.? Could make this process a separate function that adds to flask session
# For Reference: {"type":"https://httpstatus.es/401", "status":401, "title":"Unauthorized", "detail":"Access token invalid or expired"}
# TODO: STRETCH GOAL implement password reset functionality

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

@app.route('/home')
def show_homepage():
    """Show Pawprint homepage with options to search, register, log in."""

    # STRETCH GOAL: Dynamic Search form in Homepage

        # class ModifiedSearchForm(SearchForm):
        #     pass

        # ModifiedSearchForm.username = StringField('username')

    form = SearchForm()

    return render_template('homepage.html', form=form)

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

@app.route('/profile', methods=["GET", "POST"])
def show_profile():
    """Show and edit profile for logged in user."""

    if not g.user:
        flash("Please log in to view and edit your profile!", "danger")
        return redirect("/")
    
    user = g.user
    
    form = EditUserForm(obj=user)

    if form.validate_on_submit():

        try:
            user.email = form.email.data 
            user.username = form.username.data 
            user.first_name = form.first_name.data 
            user.last_name = form.last_name.data 
            user.profile_picture_url = form.profile_picture_url.data 
            user.location = form.location.data 
            
            db.session.commit()

        except IntegrityError:
            flash("Username or email already taken", "danger")
            return render_template('/profile')

        flash("Profile changes saved successfully.")
        return redirect('/')
    
    else:    
        return render_template('users/profile.html', form=form)


@app.route('/bookmarks')
def show_bookmarks():
    """Show bookmarks for the logged in user."""

    if not g.user:
        flash("Please log in to view your bookmarks!", "danger")
        return redirect("/")
    
    pets = g.user.bookmarked_pets

    return render_template('users/bookmarks.html', pets=pets)

@app.route('/bookmarks/remove', methods=["POST"])
def remove_bookmark():
    """Remove target bookmark and redirect to bookmarks page."""

    if not g.user:
        flash("Unauthorized access", "danger")
        return redirect('/')
    
    user_id = g.user.id
    pet_id = request.form["pet_id"]

    bookmark = Bookmark.query.get((user_id, pet_id))
    if not bookmark:
        flash("Bookmark does not exist", "danger")
        return redirect('/bookmarks')
    
    db.session.delete(bookmark)
    db.session.commit()

    flash("Bookmark successfully removed.")
    return redirect('/bookmarks')

@app.route('/follows')
def show_follows():
    """Show follows for the logged in user."""

    if not g.user:
        flash("Please log in to view your followed organizations!", "danger")
        return redirect('/')
    
    organizations = g.user.followed_organizations

    return render_template('users/follows.html', organizations=organizations)

@app.route('/follows/remove', methods=["POST"])
def remove_follows():
    """Remove target follow and redirect to follows page."""

    if not g.user:
        flash("Unauthorized access", "danger")
        return redirect('/')
    
    user_id = g.user.id
    organization_id = request.form["organization_id"]

    follows = Follow.query.get((user_id, organization_id))
    if not follows:
        flash("Follow does not exist", "danger")
        return redirect('/follows')
    
    db.session.delete(follows)
    db.session.commit()

    flash("Follow successfully removed.")
    return redirect('/follows')
    


@app.route('/pets')
def show_pets():
    """Show list of pets from Petfinder API."""

    page = request.args["page"]

    url = f"https://api.petfinder.com/v2/animals?page={page}"

    headers = {"Authorization" : f"Bearer {session['access_token']}"}

    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()

    pets = json.get("animals")
    pagination = json.get("pagination")

    return render_template('pets.html', status_code=status_code, pets=pets, pagination=pagination)

@app.route('/organizations')
def show_organizations():
    """Show list of organizations from Petfinder API."""

    page = request.args["page"]

    url = f"https://api.petfinder.com/v2/organizations?page={page}"

    headers = {"Authorization" : f"Bearer {session['access_token']}"}

    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()

    organizations = json.get("organizations")
    pagination = json.get("pagination")

    return render_template('organizations.html', status_code=status_code, organizations=organizations, pagination=pagination)

@app.route('/organizations/<string:organization_id>')
def show_organization(organization_id):
    """Show details page for target organization."""

    url = f"https://api.petfinder.com/v2/organizations/{organization_id}"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()

    organization = json.get("organization")

    return render_template('organization.html', organization=organization)
    
@app.route('/pets/<int:pet_id>')
def show_pet(pet_id):
    """Show details page for target pet."""

    url = f"https://api.petfinder.com/v2/animals/{pet_id}"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()

    pet = json.get("animal")

    return render_template('pet.html', pet=pet)

# idea: replace path with pets/bookmark/new and just take out the pet_id in function params bc we use the form anyway...
@app.route('/pets/bookmark/<int:pet_id>', methods=["POST"])
def bookmark_pet(pet_id):
    """
    Bookmark target pet for logged-in user.
    Adds pet and its organization to Pawprint DB.
    """

    # TODO: If user is NOT logged in/registered, hold on to the animal/shelter they wanted to bookmark and THEN bookmark it for them once they log in/register!

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
            image_url = petfinder_organization.get("photos")[0].get("full") if petfinder_organization.get("photos") else "" #CARE
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


        color = petfinder_animal.get("colors").get("primary") if petfinder_animal.get("colors").get("primary") else "None listed"
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
        db.session.commit()

    bookmark = Bookmark(user_id=g.user.id, pet_id=pet.id)
    follow = Follow(user_id=g.user.id, organization_id=organization.id)
    db.session.add_all([bookmark, follow])
    # db.session.add(bookmark)
    db.session.commit()

    flash(f"Successfully bookmarked {pet.name} and followed {organization.name} for your profile, {g.user.first_name}!")

    return redirect('/pets?page=1')

    
    # get the Petfinder API Pet object for that pet REQURES PET ID
    # get the Petfinder API Organization object for that pet's organization REQUIRES ORG ID
    # convert and commit the organization to Pawprint DB format
    # convert and commit the pet the the Pawprint DB format
    # create and commit the Bookmark object in Pawprint DB