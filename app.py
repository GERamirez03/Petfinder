"""Flask application for Pawprint."""

from flask import Flask, render_template, request, flash, redirect, session, get_flashed_messages, g 
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import requests

from models import db, connect_db, User, Organization, Pet, Bookmark, Follow
from forms import SignUpForm, LoginForm, EditUserForm, PetSearchForm, OrganizationSearchForm
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
PET_SEARCH_FORM_KEY = "pet_search_form"
ORGANIZATION_SEARCH_FORM_KEY = "organization_search_form"

# Goals with Bootstrap:
# 1: Make the forms pretty
# 2: Make the forms responsive - potentially implement my original stretch goal with drop-downs, buttons that alternace, etc.?
# 3: general beautification
# 4: incorporate animal and org pics into more of the website -- homepage, etc. ???
# 5: Make search results pages pretty... cards? responsive columns/grids?
# 6: incorporate alignment and justifying
# 7: FORMS & NAVBARS

# Known Bug: Query string persists in request after submitting new filter criteria in search while on pages beyond the first.

##### STRETCH GOALS #####
# 1: Implement a dynamic WTForms form on the homepage which lets the user toggle between searching for animals or organizations, and then
# populates a drop-down with a list of potential filters followed by a text input for that filter's value. Also has a "Add another filter" button which would 
# keep adding filters and text areas.
# 2: Find a way to ensure that user always has a valid token. If a request fails (401), attempt to resolve it by generating a new token and
# redirecting to the same page that the user was trying to access. timer, etc.? Could make this process a separate function that adds to flask session
# For Reference: {"type":"https://httpstatus.es/401", "status":401, "title":"Unauthorized", "detail":"Access token invalid or expired"}
# 3: Implement password reset functionality


@app.before_request
def add_user_to_g():
    """If user is logged in, add the current user to Flask globally."""

    if CURRENT_USER_KEY in session:
        g.user = User.query.get(session[CURRENT_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""

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

    access_token = json.get("access_token")

    session["access_token"] = access_token

    flash("Access token generated!", "info")

    return redirect('/home')

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

        flash(f"Welcome to Pawprint, {user.first_name}!", "success")

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
            flash(f"Welcome back, {user.first_name}!", "primary")
            return redirect("/")
        
        flash("Invalid credentials.", 'warning')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout."""

    do_logout()
    flash("Logout successful.", "info")
    return redirect('login')

@app.route('/profile', methods=["GET", "POST"])
def show_profile():
    """Show and edit profile for logged in user."""

    if not g.user:
        flash("Please log in to view and edit your profile!", "warning")
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
            flash("Username or email already taken.", "danger")
            return render_template('/profile')

        flash("Profile changes saved successfully.", "success")
        return redirect('/')
    
    else:    
        return render_template('users/profile.html', form=form)


@app.route('/bookmarks')
def show_bookmarks():
    """Show bookmarks for the logged in user."""

    if not g.user:
        flash("Please log in to view your bookmarks!", "warning")
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
        flash("Bookmark does not exist", "warning")
        return redirect('/bookmarks')
    
    db.session.delete(bookmark)
    db.session.commit()

    flash("Bookmark successfully removed.", "success")
    return redirect('/bookmarks')

@app.route('/follows')
def show_follows():
    """Show follows for the logged in user."""

    if not g.user:
        flash("Please log in to view your followed organizations!", "warning")
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
        flash("Follow does not exist", "warning")
        return redirect('/follows')
    
    db.session.delete(follows)
    db.session.commit()

    flash("Follow successfully removed.", "success")
    return redirect('/follows')
    
@app.route('/pets', methods=["GET", "POST"]) 
def show_pets():
    """Show list of pets from Petfinder API."""

    url = f"https://api.petfinder.com/v2/animals"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    parameters = {}

    if PET_SEARCH_FORM_KEY in session:

        search_form_dict = session[PET_SEARCH_FORM_KEY]
        form = PetSearchForm(data=search_form_dict) # use "data" parameter to pre-populate search form all active filters
        parameters = { key : value for key, value in search_form_dict.items() if value }
        parameters["page"] = request.args["page"] if "page" in request.args else 1

    else:
        form = PetSearchForm()

    if form.validate_on_submit():
        session[PET_SEARCH_FORM_KEY] = { field.name : field.data for field in form }

        parameters = { field.name : field.data for field in form if field.data }
        parameters["page"] = 1

    response = requests.get(url, params=parameters, headers=headers)
    status_code = response.status_code
    json = response.json()
        
    pets = json.get("animals")
    pagination = json.get("pagination")

    return render_template('pets.html', form=form, status_code=status_code, pets=pets, pagination=pagination)
    # parameters = request.args

@app.route('/organizations', methods=["GET", "POST"])
def show_organizations():
    """Show list of organizations from Petfinder API."""

    url = f"https://api.petfinder.com/v2/organizations"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    parameters = {}

    if ORGANIZATION_SEARCH_FORM_KEY in session:

        search_form_dict = session[ORGANIZATION_SEARCH_FORM_KEY]
        form = OrganizationSearchForm(data=search_form_dict) # use "data" parameter to pre-populate search form all active filters
        parameters = { key : value for key, value in search_form_dict.items() if value }
        parameters["page"] = request.args["page"] if "page" in request.args else 1

    else:
        form = OrganizationSearchForm()

    if form.validate_on_submit():
        session[ORGANIZATION_SEARCH_FORM_KEY] = { field.name : field.data for field in form }

        parameters = { field.name : field.data for field in form if field.data }
        parameters["page"] = 1

    response = requests.get(url, params=parameters, headers=headers)
    status_code = response.status_code
    json = response.json()

    organizations = json.get("organizations")
    pagination = json.get("pagination")

    return render_template('organizations.html', form=form, status_code=status_code, organizations=organizations, pagination=pagination)

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

def create_organization(organization_id):
    """
    Helper function that accepts an organization ID and makes a request to Petfinder API
    for all of the organization information to add it to Pawprint DB.
    """

    url = f"https://api.petfinder.com/v2/organizations/{organization_id}"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    response = requests.get(url, headers=headers)

    status_code = response.status_code
    json = response.json()
    petfinder_organization = json.get("organization")

    organization = Organization.create(petfinder_organization)

    db.session.commit()

    return organization

def create_pet(pet_id):
    """
    Helper function that accepts a pet ID and makes a request to Petfinder API
    for all of the pet details to add it to Pawprint DB.
    """

    url = f"https://api.petfinder.com/v2/animals/{pet_id}"
    headers = {"Authorization" : f"Bearer {session['access_token']}"}
    response = requests.get(url, headers=headers)


    status_code = response.status_code
    json = response.json()
    petfinder_animal = json.get("animal")

    pet = Pet.create(petfinder_animal)
    db.session.commit()
    return pet

@app.route('/pets/bookmark/new', methods=["POST"])
def bookmark_pet():
    """
    Bookmark target pet for logged-in user.
    Adds pet and its organization to Pawprint DB.
    """

    if not g.user:
        flash("Please log in to bookmark a pet!", "warning")
        return redirect("/")
    
    organization_id = request.form["organization_id"]
    organization = Organization.query.get(organization_id)

    if not organization:
        organization = create_organization(organization_id)

    pet_id = request.form["pet_id"]
    pet = Pet.query.get(pet_id)

    if not pet:
        pet = create_pet(pet_id)

    bookmark = Bookmark.query.get((g.user.id, pet.id))
    if not bookmark:
        bookmark = Bookmark(user_id=g.user.id, pet_id=pet.id)
        db.session.add(bookmark)

    follow = Follow.query.get((g.user.id, organization.id))
    if not follow:
        follow = Follow(user_id=g.user.id, organization_id=organization.id)
        db.session.add(follow)

    db.session.commit()

    flash(f"Successfully saved {pet.name} from {organization.name} to your profile, {g.user.first_name}!", "success")

    return redirect('/pets')