#----------------------------------------------------------
# Module Imports
#----------------------------------------------------------

from __future__ import division, print_function
from datetime import datetime
from glob import glob
import numpy as np

import uuid as uuid_module
from flask import Flask, render_template, jsonify, request, redirect, url_for

from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required
import flask.ext.security as flask_security

import json

#----------------------------------------------------------
# Flask Configuration
#----------------------------------------------------------

app = Flask(__name__)

# host mongo locally
app.config['MONGODB_SETTINGS'] = {
    'db': 'zutara-forever'
}

app.config['SECRET_KEY'] = "secretkey"

db = MongoEngine(app)

#----------------------------------------------------------
# Flask-Security and MongoEngine Setup
#----------------------------------------------------------
# User, Admin, etc. sort of roles
class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

# Generic User class
# can have any or none of these attributes
class User(db.Document, UserMixin):
    firstname = db.StringField(max_length=40)
    lastname = db.StringField(max_length=40)
    uid = db.StringField(max_length=40)
    password = db.StringField(max_length=20) # limit length
    active = db.BooleanField(default=True) # set False for user confirmation
    confirmed_at = db.DateTimeField()
    last_active = db.DateTimeField(required=True) # we want to remove long-inactive users
    roles = db.ListField(db.ReferenceField(Role), default=[])

# a class for our lists (catalists :P)
class Catalist(db.Document):

    class CatalistEntry(db.DynamicEmbeddedDocument):
        pass # we'll change this schema as we go along... at least that's how I think this works [txz]

    listid = db.StringField(max_length=40)
    title = db.StringField(max_length=100)
    created = db.DateTimeField(required=True) # when list was created
    last_visited = db.DateTimeField(required=True) # delete lists that haven't been visited for a long time
    # keys = db.ListField(db.StringField(max_length=20))
    contents = db.ListField(db.EmbeddedDocumentField(CatalistEntry), default=[])


# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# MIGHT WANT TO JUST EDIT THIS ONE

# uid: uid of uploader
# uuid: filename of image
# diag: diagnosis of image
# postcondition: an Entry containing the datetime, UID, and diagnosis
# of a given image is saved to collection 'entry'
# return: entryID, which is randomly assigned, will help connect file and data
def dbwrite(uid, uuid, diag):
    time = str(datetime.utcnow())
    #entry = Entry(uid = uid, uuid = uuid, diag = diag, datetime = time)
    entry = Entry(uid = uid, uuid = uuid, diag = 2, datetime = time)
    entry.save()
    # entryID = .inserted_id
    # entryId must be a string ObjectId("")
    # entryId = str(entryId)
    # MongoEngine doesn't seem to support inserted IDs
    return uuid

# file: image file sent by client
# uid: user ID of the current user
# postcondition: data regarding the image has been saved to mongoDB,
# and image file has been saved to an upload folder locally
# return: diagnosis of the given image file, and entryID in db
def processImage(file, uid):
    # file is either filestorage (verified as valid image) or img
    fullpath,uuid = saveImg(file)
    # blocking socket connection to NN interface [PORT?
    diag = getDiagRequest(fullpath)
    entryID = dbwrite(uid, uuid, diag) #save image, uid, diagnosis, date to a database
    return (diag,entryID)

#----------------------------------------------------
# User Interaction Section
#----------------------------------------------------

# signs user up, given valid credentials and no repeat
# of username
@app.route("/signup", methods=['POST'])
def signup():
    id = request.form['uid']
    pw = request.form['password']
    users = mongo.db.users
    user = users.find_one({'uid': unicode(id)})
    if user == None: # does not currently exist
        user_datastore.create_user(uid=id, password=pw)
    return render_template('home.html')

# signs user in, given valid credentials
@app.route("/signin", methods=['POST'])
def signin():
    id = request.form['uid']
    pw = request.form['password']
    user = User.objects.get(uid = unicode(id))
    if not(user == None): # user exists
        if flask_security.utils.verify_and_update_password(pw, user):
            flask_security.utils.login_user(user, remember=None)
            message=""
        else:
            message="You have entered a wrong username or password. Please try again."
    else:
        message="You have entered a wrong username or password. Please try again."
    return render_template('./security/login_user.html', message=message)

# logs out current user and clears Remember Me cookie
@app.route("/logout", methods=['POST'])
def logout():
    flask_security.utils.logout_user()
    return render_template('logoutsuccess.html')

# COULD ADAPT FOR USR LISTS

# locate all the thumbnails uploaded by the user
# since images is a login-required page, won't worry
# about guest users
def findUserImgs(uid):
    entries = Entry.objects(uid = unicode(uid)).as_pymongo()
    uuids = []
    datetime = []
    diag = []
    
    for entry in entries:
        uuid = str(entry['uuid'])
        uuids.append(str(uuid))
        datetime.append(entry['datetime'])
        diag.append(entry['diag'])
    
    filenames = []
    for uuid in uuids:
        # for some reason it can't find this directory out of static
        # command works when I link an external image url
        filename = "/Users/Rachel/Documents/UROP/CC/eye-learning-api/files/thumb/" + uuid + "_thumb.png"
        print(filename)
        filenames.append(filename)
    return datetime, diag, filenames

@app.route("/login")
def login():
    return render_template('./security/login_user.html')

# this route takes the user to the registration page
@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/images", methods=['GET'])
@flask_security.login_required
def images():
    #login-required so current_user MUST exist
    datetime, diag, imgs = findUserImgs(flask_security.core.current_user.get_id())
    n = len(imgs)
    return render_template('images.html', imgs=imgs, datetime=datetime, diag=diag, n=n)

@app.route("/", methods=['GET','POST'])
def index():
    return render_template('home.html')

#----------------------------------------------------------
# Ajax Routes
#----------------------------------------------------------

listtypes = ["contacts", "groceries", "movie", "shopping"]
listtypes.sort()

# completes a word fragment with a possible list type
# usage: POST to this route with
# {"fragment": myfragment}, response is the list of possible
# completions of *myfragment* drawn from *listtypes*
@app.route("/ajax/autocomplete", methods=['POST'])
def autocomplete():
    req_json = request.form
    fragment = req_json["fragment"]
    completions = []
    for item in listtypes:
        l = len(fragment)
        if item[:l] == fragment:
            completions.append(item)
    response = jsonify({'completions': completions})
    return response

#----------------------------------------------------------
# Start Application
#----------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005, debug=True)
