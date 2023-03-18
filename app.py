"""Flask application for Pawprint."""

from flask import Flask, render_template, request, flash, redirect, session, get_flashed_messages, g 
from flask_debugtoolbar import DebugToolbarExtension
import requests

from models import db, connect_db, User, Organization, Pet, Bookmark
from secret import MY_API_KEY, MY_SECRET

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pawprint'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "geram03_pawprint"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True

debug = DebugToolbarExtension(app)

connect_db(app)


# TODO: If a request is made and then we get a 401 in response, ATTEMPT to generate a new access token AND redirect to the same page/make the same request again with that new access token
# TODO: Make this process of getting a new access token its own separate function, which also adds the token to the flask session
# Idea: Only add pets/organizations to Pawprint DB if user bookmarks them?

# Reference: {"type":"https://httpstatus.es/401", "status":401, "title":"Unauthorized", "detail":"Access token invalid or expired"}

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

    return render_template('pets.html', status_code=status_code, pets=pets)