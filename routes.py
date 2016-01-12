#----------------------------------------------------------
# Module Imports
#----------------------------------------------------------

from __future__ import division, print_function
from datetime import datetime
# from glob import glob

import uuid as uuid_module
from flask import Flask, render_template, jsonify, request, redirect, url_for

from flask.ext.mongoengine import MongoEngine
from flask.ext.mongoengine import *
from flask.ext.pymongo import PyMongo
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

app.config['SECRET_KEY'] = "bc5e9bf3-3d4a-4860-b34a-248dbc0ebd5c"

HOSTNAME = '0.0.0.0:6005' # we'll need this later for actual app

db = MongoEngine(app)
mongo = PyMongo(app)

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
    email = db.StringField(max_length=100, unique=True)
    lastname = db.StringField(max_length=40)
    uid = db.StringField(max_length=40, unique=True)
    password = db.StringField(max_length=20) # limit length
    active = db.BooleanField(default=True) # set False for user confirmation
    confirmed_at = db.DateTimeField()

    # we want to remove long-inactive users
    last_active = db.DateTimeField(required=True)
    
    roles = db.ListField(db.ReferenceField(Role), default=[])

class CatalistKVP(db.EmbeddedDocument):
    # id is implicit in mongoengine, but we want to
    # share kvpid's across (CatalistEntry)s
    kvpid = db.StringField(max_length=40)
    key = db.StringField(max_length=40)
    value = db.StringField(max_length=200)

class CatalistEntry(db.EmbeddedDocument):
    # entryid = db.StringField(max_length=40, unique=True)
    title = db.StringField(max_length=80)
    contents = db.EmbeddedDocumentListField(CatalistKVP)
    score = db.IntField(default=0)
    upvoters = db.ListField(ReferenceField(User))
    downvoters = db.ListField(ReferenceField(User))

# a class for our lists (catalists :P)
class Catalist(db.Document):
    listid = db.StringField(max_length=40, unique=True)
    title = db.StringField(max_length=100)
    created = db.DateTimeField(required=True) # when list was created

    # delete lists that haven't been visited for a long time
    last_visited = db.DateTimeField(required=True)
    
    # keys = db.ListField(db.StringField(max_length=20))
    contents = db.EmbeddedDocumentListField(CatalistEntry, default=[])


# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)

#----------------------------------------------------
# User Interaction Section
#----------------------------------------------------

# signs user up, given valid credentials and no repeat
# of username
@app.route("/signup", methods=['POST'])
def signup():
    user_id = request.form['uid']
    pw = request.form['password']
    email = request.form['email']
    time = datetime.utcnow()

    try:
        # if user exists, then can't sign up with same username
        user = User.objects.get(uid = unicode(user_id))
        print("Sorry, that username is taken!")
    except mongoengine.DoesNotExist:
        try:
            # if user exists, then can't sign up with same username
            user = User.objects.get(email = unicode(email))
            print("Sorry, that email is taken! Did you forget your password?")
        except:
            user_datastore.create_user(uid=user_id, password=pw, last_active = time, email=email)
    # if multiple objects, then something just screwed up
    except:
        return render_template('error.html') # DNE yet

    return render_template('home.html')

# signs user in, given valid credentials
@app.route("/signin", methods=['POST'])
def signin():
    user_id = request.form['uid']
    pw = request.form['password']
    try:
        # if user exists, then sign in
        user = User.objects.get(uid = unicode(user_id))
        if flask_security.utils.verify_and_update_password(pw, user):
            time = datetime.utcnow()
            user.last_active = time
            print(user.last_active)
            flask_security.utils.login_user(user, remember=None)
            message = ""
        else:
            message = "You have entered a wrong username or password. Please try again."
    except: # user DNE
        message="You have entered a wrong username or password. Please try again."

    return render_template('./security/login_user.html', message=message)

# logs out current user and clears Remember Me cookie
@app.route("/logout", methods=['POST'])
def logout():
    flask_security.utils.logout_user()
    return render_template('logoutsuccess.html')

@app.route("/login")
def login():
    return render_template('./security/login_user.html')

# this route takes the user to the registration page
@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/list/<listid>", methods=['GET'])
def getlist(listid):
    the_list = Catalist.objects.get(listid=listid)
    return render_template('loadlist.html', entries=the_list.contents)

@app.route("/mylists", methods=['GET'])
@flask_security.login_required
def userlists():
    return render_template('userlists.html')

@app.route("/", methods=['GET','POST'])
def index():
    return render_template('home.html')

#----------------------------------------------------------
# Ajax Routes
#----------------------------------------------------------

@app.route("/ajax/makelist", methods=['GET'])
def make_list():
    """
    Upon making the first edit, an empty list will be
    created for the insertion of more data
    """
    list_id = str(uuid_module.uuid4())
    title = "";
    time = datetime.utcnow()
    new_list = Catalist(listid=list_id, created=time, last_visited=time)
    new_list.save()
    return jsonify(id = list_id)

# DEV NOTE: maybe make this a regular route, not AJAX
@app.route("/ajax/savelist", methods=['POST'])
def list_save():
    """
    For saving an entire list.

    syntax:
    {
        title: <thetitle>,
        contents: [
            *[title, [*[attrname, attrval]]]
        ]
    }
    """
    req_json = request.form
    print(req_json)
    list_title = req_json["title"]
    list_contents = req_json["contents[]"]
    formatted_list_contents = []
    for entry in list_contents:
        temp = CatalistEntry(title=entry[0])
        keys = [], kvps = []
        for index, (k, v) in enumerate(entry[1]):
            keys.append(key)
            kvps.append(CatalistKVP(kvpid=hash(list_title+str(index)),
                                    key=k,value=v))
        temp.contents = kvps
        formatted_list_contents.append(temp)
    newlist = Catalist(title=list_title, contents=formatted_list_contents)
    newlist.save()
    return redirect("/list/"+str(newlist.id),code=302)

# let's start small, since the receiving end is so picky
# this one successfully receives the listItemTitle inputs
# and does nothing with them at the moment
@app.route("/ajax/saveitems", methods=['POST'])
def items_save():
    req_json = request.form
    list_items = req_json["items[title][]"]
    print(list_items)
    return "List Saved"

@app.route("/ajax/savekey", methods=['POST'])
def key_save():
    """
    mini-API for this view function
    POST a JS associative array (basically a dict) like so:
    {
        listid:  <the list id>,
        entryid: <entryid of entry>,
        kvpid: <kvpid of key-val pair>,
        newvalue: <new value of key>
    }
    """
    req_json = request.form
    # eid = req_json["entryid"] # necessary only for option ONLY (see later)
    kid = req_json["kvpid"]
    val = req_json["newvalue"]
    the_list = Catalist.get(listid=req_json["listid"])

    # two options for updating key name: either we update it
    # for this entry ONLY or update it for ALL entries

    # option ONLY
    # the_list.contents.get(entryid=eid).getattr(kvpid)[0] = val

    # option ALL
    for x in the_list.contents:
        x.contents.get(kvpid=kid).key = val
        # the following should be taken care of my the_list.save()
        # I'll leave just in case [txz]
        x.save()

    the_list.save()
    return jsonify({}) # return a blank 200

# maybe merge this with /ajax/savekey and have client pass an extra
# key-val pair; this would be repeat significantly less code [txz]
@app.route("/ajax/savevalue", methods=['POST'])
def value_save():
    req_json = request.form
    eid = req_json["entryid"]
    val = req_json["newvalue"]
    the_list = Catalist.objects(listid=req_json["listid"])
    the_list.contents.get(entryid=eid).contents.get(kvpid=kid).value = val
    the_list.save()
    return jsonify({}) # return a 200

@app.route("/ajax/vote", methods=['POST'])
def vote():
    """
    Two options:
    1) Update the database to incorporate a user's vote on an entry.
    2) Find the user's current vote and the current score of the entry.

    usage: POST the following
    {
        listid: <listid>,
        entryid: <entryid>,
        userid: <userid>,
        vote: {1 (upvote) | 0 (no vote) |
               -1 (downvote) | 100 (get the current vote)}
    }
    """
    req_json = request.form
    listid = req_json["listid"]
    uid = req_json["userid"]
    vote_val = req_json["vote"]
    the_user = User.objects(uid=uid)
    the_entry = Catalist(listid=listid).contents(id=req_json["entryid"])
    curscore = the_entry.score

    # find the current vote, possibly removing user from up/downvoters lists
    cur_vote = 0
    if the_user in the_entry.upvoters:
        cur_vote = 1
        if vote_val in (-1,0,1):
            the_entry.update_one(pull__upvoters=the_user)
    elif the_user in the_entry.downvoters:
        cur_vote = -1
        if vote_val in (-1,0,1):
            the_entry.update_one(pull__downvoters=the_user)

    # do we only want to look up some values?
    # TODO maybe change this to NaN instead of 100?
    if vote_val == 100:
        return jsonify({"current_vote": cur_vote, "score": curscore})

    # stick the user in the correct list
    if vote_val == 1:
        the_entry.update_one(push__upvoters=the_user)
    elif vote_val == -1:
        the_entry.update_one(push__downvoters=the_user)

    # update the score in the database
    the_entry.score += (vote_val - cur_vote)
    the_entry.save()

    return jsonify({"current_vote": vote_val, "score": the_entry.score})


autocomplete_dict = ["contacts", "groceries", "movie", "shopping"]
autocomplete_dict.sort()

# completes a word fragment with a possible list type
# usage: POST to this route with
# {"fragment": myfragment}, response is the list of possible
# completions of *myfragment* drawn from *autocomplete_dict*
@app.route("/ajax/autocomplete", methods=['POST'])
def autocomplete():
    req_json = request.form
    fragment = req_json["fragment"]
    completions = []
    for item in autocomplete_dict:
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
