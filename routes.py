#----------------------------------------------------------
# Module Imports
#----------------------------------------------------------

from __future__ import division, print_function
from datetime import datetime
from glob import glob
import numpy as np
import hashlib
from OpenSSL import SSL
import re

import os
import sys
import socket
import uuid as uuid_module
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_limiter import Limiter

# MongoEngine runs on pymongo so both should be fine
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required
import flask.ext.security as flask_security

from pymongo import MongoClient
from flask.ext.pymongo import PyMongo
from flask.ext.pymongo import ObjectId

from werkzeug import secure_filename
#from flask.ext.cors import CORS

import base64
import json
from bson.json_util import dumps
import cStringIO
from PIL import Image

#----------------------------------------------------------
# Flask Configuration
#----------------------------------------------------------

np.random.seed(9)

# change to match computer, somewhere not in static
UPLOAD_FOLDER = './files/img/'
UPLOAD_FOLDER2 = './files/thumb/'
ALLOWED_EXTENSIONS = set(['png','tiff','tif','jpg','jpeg','JPG','TIFF','TIF','PNG'])

app = Flask(__name__)

app.config['SECRET_KEY'] = "freakingsecretkey"
# secret key has some issues with weird characters since the url sends only unicode as args
# and for comparison sake, need to keep the secret key something w/o weird characters
# app.config['SECRET_KEY'] = '\x9ek\xdbS7\xc0k$\xac\x96 \x03W\x84\xb7\x1b\xec\xa0\xe0\xe32\\\x06\x9d'
app.config['MONGO_DBNAME'] = 'eye-learning-files'
app.config['MONGODB_SETTINGS'] = {
    'db': 'eye-learning-files'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2

limiter = Limiter(app, global_limits=["1 per 1 second"])

db = MongoEngine(app)
mongo = PyMongo(app)

HOST = 'localhost'    # The remote host
PORT = 50007              # The same port as used by the server
s = None

# image serving is somewhat broken at the moment ^.^ due to not recognizing paths
app.config['MEDIA_FOLDER'] = './files/thumb/'

@app.route('/files/thumb/')
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)

#----------------------------------------------------------
# Flask-Security and MongoEngine Setup
#----------------------------------------------------------
# User, Admin, etc. sort of roles
class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

# Generic User class
class User(db.Document, UserMixin):
    firstname = db.StringField(max_length=40)
    lastname = db.StringField(max_length=40)
    uid = db.StringField(max_length=40)
    password = db.StringField(max_length=20) # limit length
    active = db.BooleanField(default=True) # set False for user confirmation
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])

# Generic entry class, per image uploaded
# uid: uid of uploader; 0 if guest
# uuid: filename of image
# datetime: time of upload
# diag: diagnosis of image
class Entry(db.Document):
    uid = db.StringField(max_length=40)
    uuid = db.StringField(max_length=255)
    datetime = db.DateTimeField()
    diag = db.FloatField()

# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)


#----------------------------------------------------------
# API Key
#----------------------------------------------------------

from functools import wraps
from flask import request, abort

# The actual decorator function
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.args.get('key') and unicode(request.args.get('key')) == unicode(app.config['SECRET_KEY']):
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


def check_appkey():
    appkey = request.args.get('key')

#----------------------------------------------------------
# Image Manipulation Section
#----------------------------------------------------------

# separates file extension and checks if is an image file
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# b64: base64 encoded string
# return: decoded version of b64
def decodeB64(b64):
    str = b64.replace('data:image/png;base64,', '') #replace tag
    decoded = base64.b64decode(str)
    return decoded

# imgData: raw image data in string form
# return: PIL object containing the image
def encodePIL(imgData):
    str = cStringIO.StringIO()
    str.write(imgData)
    img = Image.open(str)
    return img

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

# file: FileStorage object or PIL Image that as a save() function
# postcondition: img saved in UPLOAD_FOLDER as uuid.png
# return: fullpath to image file, and uuid (unique) filename for file
thumb_size = 128, 128
def saveImg(file):
    uuid = str(uuid_module.uuid4())
    filename = uuid + ".png"
    filename_thumb = uuid + "_thumb.png"
    fullpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(fullpath)
    img = Image.open(fullpath)
    img.thumbnail(thumb_size)
    img.save(os.path.join(app.config['UPLOAD_FOLDER2'], filename_thumb))
    return (fullpath,filename[:-4])

# filepath: full path string to image file machine learning algorithm will analyze
# s: socket connection to machine learning algorithm
# data: string of estimate 0-4 for image grade
# return: response from machine learning algorithm over socket connection
def getDiagRequest(filepath):
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            s = None
            continue
        try:
            s.connect(sa)
        except socket.error as msg:
            s.close()
            s = None
            continue
        break
    if s is None:
        print('could not open socket')
        return "' Err!'"
    s.sendall(filepath)
    data = s.recv(1024)
    s.close()
    return repr(data)

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

# sends swagger ui rendered page from dist/swagger.json documentation
@app.route("/docs")
def docs():
    return app.send_static_file('dist/index.html')

# gets image data from client and processes it
@app.route("/api/v1/uploadImage", methods=['POST'])
def uploadImage():
    file = request.files['file'] # in the .js element is referred to as 'file'
    #filename = request.form['filename'] # separated since b64
    if (flask_security.core.current_user.is_authenticated):
        uid = flask_security.core.current_user.get_id()
    else:
        uid = '0' # placeholder for anonymous
    # place holders for no/bad file upload
    diag = '-Err1'
    entryID = '-Err1'
    if file and allowed_file(file.filename):
        diag,entryID = processImage(file, uid)
    return jsonify(grade=diag[1:-1],uid=uid,database_id=entryID)

# gets b64 image data from client and processes it
@app.route("/api/v1/uploadImageB64", methods=['POST'])
def uploadImageB64():
    file = request.form['file'] # in the .js element is referred to as 'file'
    filename = request.form['filename'] # separated since b64
    if (flask_security.core.current_user.is_authenticated):
        uid = flask_security.core.current_user.get_id()
    else:
        uid = 0 # placeholder for anonymous
    print(uid)
    # place holders for no/bad file upload
    diag = '-Err1'
    entryID = '-Err1'
    if file and allowed_file(filename):
        filename = secure_filename(filename) #werkzeug thing
        file = decodeB64(file)
        img = encodePIL(file)
        diag,entryID = processImage(img, uid)
    return jsonify(grade=diag[1:-1],uid=uid,database_id=entryID)

# signs user up, given valid credentials and no repeat
# of username
@app.route("/api/v1/signup", methods=['POST'])
def signup():
    id = request.form['uid']
    pw = request.form['password']
    users = mongo.db.users
    user = users.find_one({'uid': unicode(id)})
    if user == None: # does not currently exist
        user_datastore.create_user(uid=id, password=pw)
    return render_template('home.html')

# signs user in, given valid credentials
@app.route("/api/v1/signin", methods=['POST'])
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
@app.route("/api/v1/logout", methods=['POST'])
def logout():
    flask_security.utils.logout_user()
    return render_template('logoutsuccess.html')

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

@app.route("/api/v1/login")
def login():
    return render_template('./security/login_user.html')

# this route takes the user to the registration page
@app.route("/api/v1/register")
def register():
    return render_template('register.html')

@app.route("/api/v1/images", methods=['GET'])
@flask_security.login_required
def images():
    #login-required so current_user MUST exist
    datetime, diag, imgs = findUserImgs(flask_security.core.current_user.get_id())
    n = len(imgs)
    return render_template('images.html', imgs=imgs, datetime=datetime, diag=diag, n=n)

@app.route("/", methods=['GET','POST'])
@require_appkey
def index():
    return render_template('home.html')

#----------------------------------------------------------
# Start Application with SSL
#----------------------------------------------------------
if __name__ == "__main__":
    context = ('./SSL/theia.crt','./SSL/theia.key')
    app.run(host='0.0.0.0', port=5001, debug=True, ssl_context=context)
