#----------------------------------------------------------
# Module Imports
#----------------------------------------------------------

from __future__ import division, print_function
from datetime import datetime
from datetime import date
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
app.config['SECURITY_PASSWORD_SALT'] = "eddb960e-269c-4458-8e08-c1027d8b290"

# we'll need this later for actual app
HOSTNAME = '0.0.0.0:6005'

db = MongoEngine(app)
mongo = PyMongo(app)

#----------------------------------------------------------
# Flask-Security and MongoEngine Setup
#----------------------------------------------------------


class Role(db.Document, RoleMixin):
    """ A class for user roles (e.g. User, Admin, ...) """
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    """ A class for users. Can have any/none of these attributes. """
    firstname = db.StringField(max_length=40)
    email = db.StringField(max_length=100, unique=True)
    lastname = db.StringField(max_length=40)
    uid = db.StringField(max_length=40, unique=True)
    password = db.StringField(max_length=255)  # because this is a hash
    active = db.BooleanField(default=True)  # set False for user confirmation
    confirmed_at = db.DateTimeField()

    # we want to remove long-inactive users
    last_active = db.DateTimeField(required=True)

    roles = db.ListField(db.ReferenceField(Role), default=[])


class CatalistKVP(db.EmbeddedDocument):
    """ A class for individual key-value pairs in our Catalist entries """
    # id is implicit in mongoengine, but we want to
    # share kvpid's across (CatalistEntry)s
    kvpid = db.StringField(max_length=40)
    key = db.StringField(max_length=40, default="")
    value = db.StringField(max_length=200, default="")


class CatalistEntry(db.EmbeddedDocument):
    """ A class for the entries in our Catalists """
    # entryid = db.StringField(max_length=40, unique=True)
    title = db.StringField(max_length=80, default="")
    contents = db.EmbeddedDocumentListField(CatalistKVP, default=[])
    score = db.IntField(default=0)
    upvoters = db.ListField(db.ReferenceField(User), default=[])
    downvoters = db.ListField(db.ReferenceField(User), default=[])


class Catalist(db.Document):
    """ A class for our lists (Catalists :P) """
    listid = db.StringField(max_length=40, unique=True)
    title = db.StringField(max_length=100, default="List Title")
    created = db.DateTimeField(required=True)  # when list was created

    # delete lists that haven't been visited for a long time
    last_visited = db.DateTimeField(required=True)

    # keys = db.ListField(db.StringField(max_length=20))
    contents = db.EmbeddedDocumentListField(CatalistEntry, default=[])

    creator = db.StringField(max_length=40)


# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)

#----------------------------------------------------
# User Interaction Section
#----------------------------------------------------


@app.route("/signup", methods=['POST'])
def signup():
    """
    Sign the user up, given valid credentials and a username the doesn't
    already exist in our database.
    """
    user_id = request.form['uid']
    pw = request.form['password']
    pw_hash = flask_security.utils.get_hmac(pw)
    email = request.form['email']
    time = datetime.utcnow()

    try:
        # if user exists, then can't sign up with same username
        user = User.objects.get(uid=unicode(user_id))
        return render_template('register.html',
                               message="Sorry, that username is taken!")
    except mongoengine.DoesNotExist:
        try:
            # if user exists, then can't sign up with same email
            user = User.objects.get(email=unicode(email))
            return render_template(
                'register.html',
                message="Sorry, that email is taken! " +
                "Did you forget your password?")
        except:
            user_datastore.create_user(uid=user_id, password=pw_hash,
                                       last_active=time, email=email)
    # if multiple objects, then something just screwed up
    except:
        return render_template('error.html')  # DNE yet

    return render_template('home.html')


@app.route("/signin", methods=['POST'])
def signin():
    """ Sign the user in, given valid credentials. """
    user_id = request.form['uid']
    pw = request.form['password']
    pw_hash = flask_security.utils.get_hmac(pw)
    whoops = "You have entered a wrong username or password. Please try again."
    try:
        # if user exists, then sign in
        user = User.objects.get(uid=unicode(user_id))
        if flask_security.utils.verify_and_update_password(pw_hash, user):
            time = datetime.utcnow()
            user.last_active = time
            print(user.last_active)
            flask_security.utils.login_user(user, remember=None)
            message = ""
        else:
            message = whoops
    except:  # user DNE
        message = whoops

    return render_template('./security/login_user.html', message=message)


@app.route("/logout", methods=['POST'])
def logout():
    """ Log out the current user, clearing the Remember Me cookie """
    flask_security.utils.logout_user()
    return render_template('logoutsuccess.html')


@app.route("/login", methods=['GET'])
def login():
    """ Page for user login """
    return render_template('./security/login_user.html')


@app.route("/register")
def register():
    """ Page for user registration """
    return render_template('register.html')


@app.route("/list/<listid>", methods=['GET'])
def getlist(listid):
    """
    Fetch the list with given listid from our database,
    display with template
    """
    the_list = Catalist.objects.get(listid=listid)
    # print(the_list.contents)  # for debug
    print(the_list.title)  # for debug
    return render_template('loadlist.html', listtitle=the_list.title,
                           entries=the_list.contents)


@app.route("/mylists", methods=['GET'])
@flask_security.login_required
def userlists():
    current_user = flask_security.core.current_user
    lists = Catalist.objects(creator=current_user.uid).only(
        'listid', 'title', 'created', 'last_visited').all()
    if lists.first() is None:
        return render_template(
            'home.html',
            message="Oops! You have no lists saved! " +
                    "Would you like to create one?")

    lists = lists.order_by('last_visited').all()

    n = 0
    urls = []
    urls_actual = []
    titles = []
    last_visited = []

    for list in lists:
        # urls.append("/list/" + list.listid)
        urls.append("/preview/" + list.listid)
        urls_actual.append("/list/" + list.listid)
        titles.append(list.title)

        c = list.created
        lv = list.last_visited

        # formatting last visited
        if(lv.date() == date.today()):
            lv = lv.strftime("%I:%M %p")
        else:
            lv = lv.strftime("%I:%M %p, %x")
        if lv[0:1] == "0":
            lv = lv[1:]

        last_visited.append(lv)
        n += 1

    return render_template('mylists.html', n=n, titles=titles,
                           last_visited=last_visited, urls=urls, urls_actual=urls_actual)

@app.route("/preview/<listid>", methods=['GET'])
def preview_list(listid):
    return render_template('preview.html')


def get_id():
    """ Return name of current user """
    current_user = flask_security.core.current_user
    uid = current_user.uid
    return uid

app.jinja_env.globals.update(get_id=get_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    """ Our homepage! """
    return render_template('home.html')

#----------------------------------------------------------
# Error Handlers
#----------------------------------------------------------


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#----------------------------------------------------------
# THE API!!!
#----------------------------------------------------------


@app.route("/api/makelist", methods=['GET'])
def make_list():
    """
    Upon making the first edit, an empty list will be
    created for the insertion of more data
    """
    list_id = str(uuid_module.uuid4())
    title = ""
    time = datetime.utcnow()

    current_user = flask_security.core.current_user
    if not current_user.is_authenticated:
        uid = "Guest"
    else:
        uid = current_user.uid
    new_list = Catalist(listid=list_id, created=time,
                        last_visited=time, creator=uid)
    new_list.save()
    return jsonify(id=list_id)


# DEV NOTE: maybe make this a regular route, not AJAX
@app.route("/api/savelist", methods=['POST'])
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
    list_title = request.form["title"]
    list_contents = request.form["contents[]"]
    formatted_list_contents = []
    for entry in list_contents:
        temp = CatalistEntry(title=entry[0])
        keys = [], kvps = []
        for index, (k, v) in enumerate(entry[1]):
            keys.append(key)
            kvps.append(CatalistKVP(kvpid=hash(list_title + str(index)),
                                    key=k, value=v))
        temp.contents = kvps
        formatted_list_contents.append(temp)
    newlist = Catalist(title=list_title, contents=formatted_list_contents)
    newlist.save()
    return redirect("/list/" + str(newlist.id), code=302)

# seems like vestigial stuff: remove from API?
# 
# let's start small, since the receiving end is so picky
# this one successfully receives the listItemTitle inputs
# and does nothing with them at the moment
# @app.route("/api/saveitems", methods=['POST'])
# def items_save():
#     list_items = request.form["items[title][]"]
#     print(list_items)
#     return "List Saved"


@app.route("/api/savekey", methods=['POST'])
def key_save():
    """
    mini-API for this view function
    POST a JS associative array (basically a dict) like so:
    {
        listid:  <the list id>,
        entryind: <index of entry w.r.t. list (0-indexing)>,
        index: <index of key-val pair w.r.t. entry>,
        newvalue: <new value of key>
    }
    """
    # necessary only for option ONLY (see later)
    eind = int(request.form["entryind"])
    val = request.form["newvalue"]
    ind = int(request.form["index"])
    lid = request.form["listid"]
    # print("The list id is {} and the newvalue is {}".format(lid, val))
    the_list = Catalist.objects.get(listid=lid)

    # pad the_list.contents if index eind out of bounds
    pad_len = eind - len(the_list.contents) + 1
    if pad_len > 0:
        the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[eind]

    # do the same for the_entry.contents and ind
    pad_len = ind - len(the_entry.contents) + 1
    if pad_len > 0:
        the_entry.contents += [CatalistKVP() for i in xrange(pad_len)]

    # two options for updating key name: either we update it
    # for this entry ONLY or update it for ALL entries

    # option ONLY
    the_entry.contents[ind].key = val

    # option ALL
    # for entry in the_list.contents:
    #     entry.contents[ind].key = val

    the_list.save()
    return jsonify()  # return a blank 200


# maybe merge this with /api/savekey and have client pass an extra
# key-val pair; this would be repeat significantly less code [txz]
@app.route("/api/savevalue", methods=['POST'])
def value_save():
    """
    Save the value in a particular key-value pair.

    The API is virtually identical the that of key_save()
    """
    eind = int(request.form["entryind"])
    val = request.form["newvalue"]
    ind = int(request.form["index"])
    lid = request.form["listid"]
    the_list = Catalist.objects.get(listid=lid)

    # pad the_list.contents if index eind out of bounds
    pad_len = eind - len(the_list.contents) + 1
    if pad_len > 0:
        the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[eind]

    pad_len = ind - len(the_entry.contents) + 1
    if pad_len > 0:
        the_entry.contents += [CatalistKVP() for i in xrange(pad_len)]
    the_entry.contents[ind].value = val

    the_list.save()
    return jsonify()  # return a 200


@app.route("/api/saveentrytitle", methods=['POST'])
def entry_title_save():
    """
    AJAXily save the title of an entry.

    usage: POST a JS associative array (basically a dict) like so:
    {
        listid:  <the list id>,
        entryind: <index of entry w.r.t. list (0-indexing)>,
        newvalue: <new entry title>
    }
    """
    req_json = request.form
    lid, eind = [req_json[s] for s in ["listid", "entryind"]]
    eind = int(eind)
    val = req_json["newvalue"]
    the_list = Catalist.objects.get(listid=lid)

    pad_len = eind - len(the_list.contents) + 1
    if pad_len > 0:
        the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[eind]
    the_entry.title = val
    the_list.save()
    return jsonify()  # 200 OK ^_^


@app.route("/api/savelisttitle", methods=['POST'])
def list_title_save():
    """
    AJAXily save the title of a Catalist ^_^

    usage: POST a JS assoc array like so:
    {
        listid: <the list id>,
        newvalue: <our new title>
    }
    """
    req_json = request.form
    the_list = Catalist.objects.get(listid=req_json["listid"])
    the_list.title = req_json["newvalue"]
    the_list.save()
    return jsonify()  # 200 OK ^_^


@app.route("/api/deletelist", methods=['POST'])
def list_delete():
    """
    Delete a Catalist.

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the list to be deleted>
    }
    """
    listid = request.form["listid"]
    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        return "The list doesn't exist", 400
    the_list.delete()
    return 'OK'  # this should return a 200


@app.route("/api/deleteentry", methods=['POST'])
def entry_delete():
    """
    Delete an entry from a Catalist.

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the Catalist>,
        entryind: <the index of the entry to remove>
    }
    """
    listid = request.form["listid"]
    entryind = int(request.form["entryind"])
    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        return "The list doesn't exist", 400
    try:
        removed = the_list.contents.pop(entryind)
    except IndexError:
        return "Entry index out of bounds", 400
    the_list.save()
    return 'OK'  # 200 OK


@app.route("/api/deletekvp", methods=['POST'])
def kvp_delete():
    """
    Delete a key-value pair from a Catalist entry.

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the Catalist>,
        entryind: <the index of the entry to remove>,
        index: <the index of the kvp within the entry>
    }
    """
    listid = request.form["listid"]
    entryind = int(request.form["entryind"])
    ind = int(request.form["index"])
    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        return "The list doesn't exist", 400
    try:
        the_entry = the_list.contents[entryind]
    except IndexError:
        return "Entry index out of bounds"
    try:
        removed = the_entry.contents.pop(ind)
    except IndexError:
        return "KVP index out of bounds"
    the_list.save()
    return 'OK'  # 200 OK


@app.route("/api/vote", methods=['POST'])
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
    listid = request.form["listid"]
    uid = request.form["userid"]
    vote_val = request.form["vote"]
    the_user = User.objects(uid=uid)
    the_entry = Catalist(listid=listid).contents(
        id=request.form["entryid"])
    curscore = the_entry.score

    # find the current vote, possibly removing user from up/downvoters lists
    cur_vote = 0
    if the_user in the_entry.upvoters:
        cur_vote = 1
        if vote_val in (-1, 0, 1):
            the_entry.update_one(pull__upvoters=the_user)
    elif the_user in the_entry.downvoters:
        cur_vote = -1
        if vote_val in (-1, 0, 1):
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

    return jsonify(current_vote=vote_val, score=the_entry.score)


autocomplete_dict = ["contacts", "groceries", "movie", "shopping"]
autocomplete_dict.sort()

@app.route("/api/autocomplete", methods=['POST'])
def autocomplete():
    """
    completes a word fragment with a possible list type
    usage: POST to this route with {"fragment": myfragment},
    response is the list of possible completions of *myfragment*
    drawn from *autocomplete_dict*
    """
    fragment = request.form["fragment"]
    completions = []
    for item in autocomplete_dict:
        l = len(fragment)
        if item[:l] == fragment:
            completions.append(item)
    response = jsonify(completions=completions)
    return response

#----------------------------------------------------------
# Start Application
#----------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005, debug=True)
