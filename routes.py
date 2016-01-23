# Good luck brought to you by Safety Pig
# http://qr.ae/RgLMU8
#
#                          _
#  _._ _..._ .-',     _.._(`))
# '-. `     '  /-._.-'    ',/
#    )         \            '.
#   / _    _    |             \
#  |  a    a    /              |
#  \   .-.                     ;
#   '-('' ).-'       ,'       ;
#      '-;           |      .'
#         \           \    /
#         | 7  .__  _.-\   \
#         | |  |  ``/  /`  /
#        /,_|  |   /,_/   /
#           /,_/      '`-'
#           http://www.asciiworld.com/-Mangas,48-.html
#                   and T O T O R O <3
#                           ~ t o t o r o ~
#
#                              !         !
#                             ! !       ! !          
#                            ! . !     ! . !          
#                               ^^^^^^^^^ ^            
#                             ^             ^          
#                           ^  (0)       (0)  ^       
#                          ^        ""         ^       
#                         ^   ***************    ^     
#                       ^   *                 *   ^    
#                      ^   *   /\   /\   /\    *    ^   
#                     ^   *                     *    ^
#                    ^   *   /\   /\   /\   /\   *    ^
#                   ^   *                         *    ^
#                   ^  *                           *   ^
#                   ^  *                           *   ^
#                    ^ *                           *  ^  
#                     ^*                           * ^ 
#                      ^ *                        * ^
#                      ^  *                      *  ^
#                        ^  *       ) (         * ^
#                            ^^^^^^^^ ^^^^^^^^^

# **********************************************************
# Module Imports
# **********************************************************

from __future__ import division, print_function
from datetime import datetime, date, timedelta
# from glob import glob

import uuid as uuid_module
from flask import Flask, render_template, jsonify, \
    request, redirect, url_for, make_response

from flask.ext.mongoengine import MongoEngine
from flask.ext.mongoengine import *
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required
import flask.ext.security as flask_security

import json

# **********************************************************
# Flask Configuration
# **********************************************************

app = Flask(__name__)

# host mongo locally
app.config['MONGODB_SETTINGS'] = {
    'db': 'zutara-forever'
}

app.config['SECRET_KEY'] = "bc5e9bf3-3d4a-4860-b34a-248dbc0ebd5c"
app.config['SECURITY_PASSWORD_SALT'] = "eddb960e-269c-4458-8e08-c1027d8b290"

# we'll need this later for actual app
HOSTNAME = 'catalist.eastus2.cloudapp.azure.com'

db = MongoEngine(app)

# **********************************************************
# Flask-Security and MongoEngine Setup
# **********************************************************


class Role(db.Document, RoleMixin):
    """ A class for user roles (e.g. user, admin, ...) """
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    """ A class for users. Can have any/none of these attributes. """
    firstname = db.StringField(max_length=40)
    lastname = db.StringField(max_length=40)
    email = db.StringField(max_length=100, unique=True)
    uid = db.StringField(max_length=40, unique=True)
    password = db.StringField(max_length=255)  # because this is a hash
    active = db.BooleanField(default=True)  # set False for user confirmation
    confirmed_at = db.DateTimeField()
    preferred_theme = db.IntField(maximum=10, required=True, default=0)

    # we want to remove long-inactive users
    last_active = db.DateTimeField(required=True)

    # users the current user has somehow interacted with
    acquaintances = db.ListField(db.ReferenceField('self'), default=[])

    # my lists
    my_custom_lists = db.ListField(db.ReferenceField('Catalist'), default=[])
    anti_my_lists = db.ListField(db.ReferenceField('Catalist'), default=[])

    roles = db.ListField(db.ReferenceField(Role), default=[])


# maximum lengths
key_max_len = 32
val_max_len = 1024
entry_title_max_len = 128
list_title_max_len = 128


class CatalistKVP(db.EmbeddedDocument):
    """ A class for individual key-value pairs in our Catalist entries """
    # id is implicit in mongoengine, but we want to
    # share kvpid's across (CatalistEntry)s
    kvpid = db.StringField(max_length=40)
    key = db.StringField(max_length=key_max_len, default="")
    value = db.StringField(max_length=val_max_len, default="")


class CatalistEntry(db.EmbeddedDocument):
    """ A class for the entries in our Catalists """
    title = db.StringField(max_length=entry_title_max_len, default="")
    contents = db.EmbeddedDocumentListField(CatalistKVP, default=[])
    score = db.IntField(default=0)
    upvoters = db.ListField(db.ReferenceField(User), default=[])
    downvoters = db.ListField(db.ReferenceField(User), default=[])


class Catalist(db.Document):
    """ A class for our lists (Catalists :P) """

    # METADATA

    listid = db.StringField(max_length=40, unique=True)
    created = db.DateTimeField(required=True)  # when list was created

    # should be implemented as RefField(User)
    creator = db.StringField(max_length=40)

    # this is actually "last modified", but name persists for backwards-compat
    last_visited = db.DateTimeField(required=True)

    # CONTENTS

    title = db.StringField(max_length=list_title_max_len,
                           default="untitled list")
    contents = db.EmbeddedDocumentListField(CatalistEntry, default=[])

    # PERMISSIONS

    # the permission the public has with the list
    public_level = db.StringField(choices=["edit", "view", "none"],
                                  default="edit")

    # people with own/edit/view permission
    owners = db.ListField(db.ReferenceField(User))
    editors = db.ListField(db.ReferenceField(User))
    viewers = db.ListField(db.ReferenceField(User))

    # people who manually add the list to "my lists"
    # pls don't judge my name choice
    mylisters = db.ListField(db.ReferenceField(User))


# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# **********************************************************
# Permissions
# **********************************************************

#: A list of all permission levels, from lowest to highest.
#: The levels:
#:
#: #. none  -- no permission
#: #. view  -- permission to view a list
#: #. edit  -- permission to edit a list
#: #. own   -- permission to change permission for a list
#: #. admin -- can do anything
perm_list = ["none", "view", "edit", "own", "admin"]

#: Currently admins are determined by residency on this list.
#: Hacky, I know. .__.
admin_unames = ['rmwu', 'txz']


def cmp_permission(perm1, perm2):
    """ Return a positive/0/negative integer when perm1 >/=/< perm2 """
    return perm_list.index(perm1) - perm_list.index(perm2)


def query_permission(user, catalist):
    """
    Gives the permission level a user has for a list.
    "None" represents an anonymous user.
    """
    # handle anonymous users
    if user.is_anonymous:
        return catalist.public_level

    if user.uid in admin_unames:
        return "admin"
    elif user in catalist.owners:
        return "own"
    elif cmp_permission(catalist.public_level, "edit") >= 0 or \
            user in catalist.editors:
        return "edit"
    elif cmp_permission(catalist.public_level, "view") >= 0 or \
            user in catalist.viewers:
        return "view"
    return "none"


def query_cur_perm(catalist):
    """ Finds the permission the current user has for list *catalist* """
    return query_permission(flask_security.core.current_user, catalist)


# **********************************************************
# User Interaction Section
# **********************************************************


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
                message="Sorry, that email is taken!")
        except:
            user_datastore.create_user(uid=user_id, password=pw_hash,
                                       last_active=time, email=email)
    # if multiple objects, then something just screwed up
    except:
        return render_template('error.html')  # DNE yet
    
    # we just made the user so they better exist
    user = User.objects.get(uid=unicode(user_id))
    flask_security.utils.login_user(user, remember=None)
    
    return render_template('home.html',
                           message="Welcome to Catalist, " + user_id)


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
            flask_security.utils.login_user(user, remember=None)
            message = ""
        else:
            message = whoops
    except:  # user DNE
        message = whoops
    return render_template('./security/login_user.html', success=message)


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
    """ Display a list with given listid from our database. """
    url = request.base_url
    the_list = Catalist.objects.get(listid=listid)
    if cmp_permission(query_cur_perm(the_list), "view") < 0:
        abort(403)
    msg = ('Access or share this list at:<br>'
           '<input type="url" id="listurl" value={0}>').format(url)

    return render_template('loadlist.html', listtitle=the_list.title,
                           entries=the_list.contents, message=msg)


def human_readable_time_since(tiem):
    """
    Give a human-readable representation of time elapsed since a given time

    :param tiem: a :attr:`datetime` object representing the given time.
    """
    today = datetime.utcnow().timetuple()
    lv = tiem.timetuple()
    # formatting last visited
    if(lv[7] == today[7]):  # same day
        timeSince = today[3] - lv[3]
        if(timeSince == 0):  # same hour
            timeSince = today[4] - lv[4]
            if timeSince == 1:
                since = "1 minute ago"
            else:
                since = str(timeSince) + " minutes ago"
        elif (timeSince == 1):
            since = "1 hour ago"
        else:
            since = str(timeSince) + " hours ago"
    else:
        # days since January 1
        timeSince = today[7] - lv[7]
        if timeSince == 1:
            since = "1 day ago"
        else:
            since = str(timeSince) + " days ago"
    return since


app.jinja_env.globals.update(
    human_readable_time_since=human_readable_time_since)


@app.route("/mylists", methods=['GET'])
@flask_security.login_required
def userlists():
    """ A page displaying all lists belonging to the user. """

    current_user = flask_security.core.current_user
    cur_user_nat_id = current_user.id  # the natively used id for the user,
    # since we're querying reference fields
    lists = Catalist.objects(
            db.Q(creator=current_user.uid) |
            db.Q(owners=current_user.id) |
            db.Q(editors=current_user.id) |
            db.Q(viewers=current_user.id) |
            db.Q(mylisters=current_user.id)
        ).only(
            'listid', 'title', 'last_visited').all()
    if lists.first() is None:
        return render_template(
            'home.html',
            message="Oops! You have no lists saved! " +
                    "Would you like to create one?")

    lists = lists.order_by('-last_visited').all()
    return render_template('mylists.html', lists=lists, host=HOSTNAME)


@app.route("/preview/<listid>", methods=['GET'])
def preview_list(listid):
    """
    Fetch the list with given listid from our database,
    display with template
    """
    the_list = Catalist.objects.get(listid=listid)
    if cmp_permission(query_cur_perm(the_list), "view") < 0:
        abort(403)
    return render_template('preview.html', listtitle=the_list.title,
                           entries=the_list.contents)


@app.route("/api/loggedin", methods=['POST'])
def logged_in():
    print("hi")
    """ Used for .js to call """
    if flask_security.core.current_user.is_authenticated:
        return jsonify(loggedin=1)
    return jsonify(loggedin=0)

def get_id():
    """ Return name of current user """
    try:
        return flask_security.core.current_user.uid
    except AttributeError:
        return None

app.jinja_env.globals.update(get_id=get_id)


@app.route("/about", methods=['GET', 'POST'])
def about():
    """ About us. """
    return render_template('about.html')


@app.route("/", methods=['GET', 'POST'])
def index():
    """ Our homepage! """
    return render_template('home.html')

# **********************************************************
# Error Handlers
# **********************************************************


@app.errorhandler(403)
def forbidden(e):
    return render_template('error/403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@app.errorhandler(405)
def method_not_found(e):
    return render_template('404.html'), 405


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('error/405.html'), 405

@app.errorhandler(410)
def page_gone(e):
    return render_template('error/410.html'), 410


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500


class InvalidAPIUsage(Exception):
    """
    A class for exceptions to raise in invalid API usage.
    Shamelessly pillaged from `Flask's documentation
    <http://flask.pocoo.org/docs/0.10/patterns/apierrors/>`_
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    print("\033[93m{} -- {}\033[0m".format(error.status_code, error.message))
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# **********************************************************
# THE API!!!
# **********************************************************


# # # # # # # # # # # # # #
# LIST-WIDE FUNCTIONS
# # # # # # # # # # # # # #


def create_list():
    """ Create a new list and return the assigned listid

    Returns: the assigned listid
    """
    list_id = str(uuid_module.uuid4())
    title = ""
    time = datetime.utcnow()

    current_user = flask_security.core.current_user
    if not current_user.is_authenticated:
        new_list = Catalist(listid=list_id, created=time,
                            last_visited=time)
    else:
        uid = current_user.uid
        new_list = Catalist(listid=list_id, created=time,
                            last_visited=time, creator=uid)
        user = User.objects.get(uid=uid)
        new_list.owners.append(user)

    new_list.last_visited = datetime.utcnow()
    new_list.save()
    return list_id


@app.route("/api/makelist", methods=['GET'])
def make_list():
    """
    Upon making the first edit, an empty list will be
    created for the insertion of more data
    """
    list_id = create_list()
    return jsonify(listid=list_id)


@app.route("/api/savelist", methods=['POST'])
def list_save():
    """
    Save an entire list. If listid is provided, the list is
    written onto the referenced list. Otherwise, a new list is
    created. In both cases the listid to which we saved the list
    is returned.

    usage:
    {
        title: <thetitle>,
        contents: [
            [title, [
                [attrname, attrval],
                ...
                ]
            ],
            ...
        ]
        (optionally) , listid: <the listid to save to>
    }

    Returns: the given or assigned listid
    """
    the_listid = request.form.get("listid", create_list())
    the_list = Catalist.objects.get(listid=the_listid)

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    the_list.title = request.form["title"]
    the_list.last_visited = datetime.utcnow()

    the_list.contents = [
        CatalistEntry(title=entry[0], contents=[
                CatalistKVP(key=k, value=v)
                for k, v in entry[1]
            ])
        for entry in request.form.getlist("contents")
    ]

    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return jsonify(listid=the_listid)


# # # # # # # # # # # # # #
# SAVE AND DELETE METHODS
# # # # # # # # # # # # # #


def key_val_save(req_form, key_or_val):
    """ Save a key or value in a KVP. Auxillary method for `/api/savekey`
    and `/api/savevalue` -- captures repetitive code. """
    if key_or_val not in ("key", "value"):
        raise InvalidAPIUsage("Invalid argument {}".format(key_or_val))
    max_len = key_max_len if key_or_val == "key" else val_max_len

    try:
        eind = int(req_form["entryind"])
        newval = req_form["newvalue"][:max_len]
        ind = int(req_form["index"])
        lid = req_form["listid"]
        the_list = Catalist.objects.get(listid=lid)
    except KeyError, ValueError:
        raise InvalidAPIUsage("Invalid argument")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".format(lid))

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    # pad the_list.contents if index eind out of bounds
    pad_len = eind - len(the_list.contents) + 1
    the_list.contents.extend([CatalistEntry() for i in xrange(pad_len)])
    the_entry = the_list.contents[eind]

    # do the same for the_entry.contents and ind
    pad_len = ind - len(the_entry.contents) + 1
    the_entry.contents.extend([CatalistKVP() for i in xrange(pad_len)])

    setattr(the_entry.contents[ind], key_or_val, newval)
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return jsonify()  # return a blank 200


@app.route("/api/savekey", methods=['POST'])
def key_save():
    """
    Save a key. Requires at least edit permission.

    POST a JS associative array (basically a dict) like so:
    {
        listid:  <the list id>,
        entryind: <index of entry w.r.t. list (0-indexing)>,
        index: <index of key-val pair w.r.t. entry>,
        newvalue: <new value of key>
    }
    """
    return key_val_save(request.form, "key")


@app.route("/api/savevalue", methods=['POST'])
def value_save():
    """
    Save the value in a particular key-value pair. Requires
    at least edit permission.

    The API is virtually identical the that of key_save()
    """
    return key_val_save(request.form, "value")


@app.route("/api/saveentrytitle", methods=['POST'])
def entry_title_save():
    """
    AJAXily save the title of an entry. Requires at least edit permission

    usage: POST a JS associative array (basically a dict) like so:
    {
        listid:  <the list id>,
        entryind: <index of entry w.r.t. list (0-indexing)>,
        newvalue: <new entry title>
    }
    """
    try:
        req_json = request.form
        lid, eind = [req_json[s] for s in ["listid", "entryind"]]
        eind = int(eind)
        val = req_json["newvalue"][:entry_title_max_len]
        the_list = Catalist.objects.get(listid=lid)
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".foramt(lid))

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    pad_len = eind - len(the_list.contents) + 1
    the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[eind]
    the_entry.title = val
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return "OK"  # 200 OK ^_^


@app.route("/api/savelisttitle", methods=['POST'])
def list_title_save():
    """
    AJAXily save the title of a Catalist ^_^
    Requires at least edit permission.

    usage: POST a JS assoc array like so:
    {
        listid: <the list id>,
        newvalue: <our new title>
    }
    """
    req_json = request.form
    try:
        listid = req_json["listid"]
        the_list = Catalist.objects.get(listid=listid)
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".format(listid))

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    the_list.title = req_json["newvalue"][:list_title_max_len]
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return jsonify()  # 200 OK ^_^


@app.route("/api/deletelist", methods=['POST'])
def list_delete():
    """
    Delete a Catalist. Requires at least own permission

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the list to be deleted>
    }
    """
    try:
        listid = request.form["listid"]
        the_list = Catalist.objects.get(listid=listid)
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".foramt(listid))
    if cmp_permission(query_cur_perm(the_list), "own") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)
    the_list.delete()
    return 'OK'  # this should return a 200


@app.route("/api/deleteentry", methods=['POST'])
def entry_delete():
    """
    Delete an entry from a Catalist. Requires at least edit permission.

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the Catalist>,
        entryind: <the index of the entry to remove>
    }
    """
    try:
        listid = request.form["listid"]
        entryind = int(request.form["entryind"])
        the_list = Catalist.objects.get(listid=listid)
        if cmp_permission(query_cur_perm(the_list), "edit") < 0:
            raise InvalidAPIUsage("Forbidden", status_code=403)
        removed = the_list.contents.pop(entryind)
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".format(listid))
    except IndexError:
        raise InvalidAPIUsage("Entry index out of bounds")
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return 'OK'  # 200 OK


@app.route("/api/deletekvp", methods=['POST'])
def kvp_delete():
    """
    Delete a key-value pair from a Catalist entry.
    Requires at least edit permission.

    usage: POST a JSON associative array as follows:
    {
        listid: <the id of the Catalist>,
        entryind: <the index of the entry to remove>,
        index: <the index of the kvp within the entry>
    }
    """
    try:
        entryind = int(request.form["entryind"])
        ind = int(request.form["index"])
        listid = req_json["listid"]
        the_list = Catalist.objects.get(listid=listid)
    except KeyError, ValueError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".format(listid))

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    try:
        the_entry = the_list.contents[entryind]
    except IndexError:
        return "Entry index out of bounds"

    try:
        removed = the_entry.contents.pop(ind)
    except IndexError:
        return "KVP index out of bounds"

    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return 'OK'  # 200 OK


# # # # # # # # # # # # # #
# DOING YOUR CIVIC DUTY
# # # # # # # # # # # # # #


@app.route("/api/vote", methods=['POST'])
def vote():
    """
    Two options:
    1. Update the database to incorporate a user's vote on an entry.
    2. Find the user's current vote and the current score of the entry.
    Requires at least view permission

    usage: POST the following
    {
        listid: <listid>,
        entryind: <entryind>,
        vote: {1 (upvote) | 0 (no vote) |
               -1 (downvote) | 100 (get the current vote)}
    }

    :return: a response with the following forms:
    if vote == 100 {
        current_vote: <the user's current vote>,
        score: <the entry's current score>
    }
    if vote != 100 {
        current_vote: <the vote just made>,
        score: <the entry's new score>
    }
    """

    listid = request.form["listid"]
    entryind = int(request.form["entryind"])
    current_user = flask_security.core.current_user
    if not current_user.is_authenticated:
        headers = {'Content-Type': 'text/html'}
        message = "Oops! You must be logged in to vote. " + \
                  "Would you like to <a href='/signup'>register</a> " + \
                  "or <a href='/login'>log in</a>?"
        return make_response(render_template('home.html', message=message),
                             403, headers)
    else:
        uid = current_user.uid
    vote_val = int(request.form["vote"])
    if vote_val not in (-1, 0, 1, 100):
        raise InvalidAPIUsage("Invalid vote value")
    the_user = User.objects.get(uid=uid)

    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        raise InvalidAPIUsage("List does not exist")

    # pad the_list.contents if index eind out of bounds
    pad_len = entryind - len(the_list.contents) + 1
    the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[entryind]

    curscore = getattr(the_entry, "score", 0)

    if cmp_permission(query_cur_perm(the_list), "view") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    # find the current vote, possibly removing user from up/downvoters lists
    cur_vote = 0
    if the_user in the_entry.upvoters:
        cur_vote = 1
        if vote_val in (-1, 0, 1):
            the_entry.upvoters.remove(the_user)
    elif the_user in the_entry.downvoters:
        cur_vote = -1
        if vote_val in (-1, 0, 1):
            the_entry.downvoters.remove(the_user)

    # do we only want to look up some values?
    # TODO maybe change this to NaN instead of 100?
    if vote_val == 100:
        return jsonify({"current_vote": cur_vote, "score": curscore})

    # stick the user in the correct list
    if vote_val == 1:
        the_entry.upvoters.append(the_user)
    elif vote_val == -1:
        the_entry.downvoters.append(the_user)

    # update the score in the database
    the_entry.score += (vote_val - cur_vote)
    the_list.save()

    return jsonify(current_vote=vote_val, score=the_entry.score)


# # # # # # # # # # # # # #
# MY LISTS INTERACT
# # # # # # # # # # # # # #


def my_lists_interact(listid, addQ):
    """
    Add or remove a list with specified listid
    from "My Lists".

    :param listid: the listid of the list
    :param addQ: an integer specifying whether to add or remove:
                    1 to add, -1 to remove
    """

    if addQ not in (-1, 1):
        raise InvalidAPIUsage("Invalid arguments")
    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".format(listid))

    cur_user = flask_security.core.current_user
    if not cur_user.is_authenticated:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    cur_state = 0
    if the_list in cur_user.my_custom_lists:
        cur_state = 1
    elif the_list in cur_user.anti_my_lists:
        cur_state = -1

    # if there's nothing to do
    if cur_state == addQ:
        return None  # we are done

    # remove them from relevant lists
    if cur_state == 1:
        cur_user.my_custom_lists.remove(the_list)
    elif cur_state == -1:
        cur_user.anti_my_lists.remove(the_list)

    # else append/pop as required
    if addQ == 1:
        the_list.mylisters.append(cur_user)
    elif addQ == -1:
        the_list.mylisters.remove(cur_user)

    cur_user.save()


@app.route("/api/mylists/add", methods=['POST'])
def add_to_my_lists():
    """
    Add a specified list to "My Lists". POST
    {
        listid: <listid>
    }
    """
    try:
        listid = request.form["listid"]
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")

    my_lists_interact(listid, 1)
    return "OK"  # 200 OK ^_^


@app.route("/api/mylists/remove", methods=['POST'])
def remove_from_my_lists():
    """
    Remove a specified list from "My Lists". POST
    {
        listid: <listid>
    }
    """
    try:
        listid = request.form["listid"]
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")

    my_lists_interact(listid, -1)
    return "OK"  # 200 OK ^_^


# # # # # # # # # # # # # #
# PERMISSION EDITING
# # # # # # # # # # # # # #

@app.route("/api/setpermissions", methods=['POST'])
def permissions_set():
    """
    {
        Set permissions for a user. Requires at least own permission

        listid: <listid>,
        target: <username of user to set perms with>,
        permission: {none | view | edit | own | admin}
    }
    """
    uname = get_id()
    listid = request.form["listid"]
    perm = request.form["permission"]
    target = request.form["target"]
    print(listid)
    print(perm)
    print(target)
    if target == '':
        target = uname

    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        raise InvalidAPIUsage("List does not exist")

    if perm not in perm_list:
        raise InvalidAPIUsage("Invalid arguments")

    if cmp_permission(the_list.public_level, perm) >= 0:
        raise InvalidAPIUsage("Higher public level")

    try:
        uperm = query_permission(User.objects.get(uid=uname), the_list)
    except DoesNotExist:
        raise InvalidAPIUsage("No such user")
    print (cmp_permission(uperm, "own"))
    if cmp_permission(uperm, "own") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    try:
        the_target = User.objects.get(uid=target)
        target_cur_perm = query_permission(the_target, the_list)
    except DoesNotExist:
        raise InvalidAPIUsage("User does not exist")

    if target_cur_perm == perm:
        return "OK"  # 200 OK

    # if target user is currently on own/edit/view, remove user from that
    if target_cur_perm in ["own", "view"]:
        getattr(the_list, target_cur_perm + "ers").remove(the_target)
    elif target_cur_perm == "edit":
        the_list.editors.remove(the_target)

    # add target user to appropriate new privilege lists
    if perm in ["own", "view"]:
        getattr(the_list, perm + "ers").append(the_target)
    elif perm == "edit":
        print('editor added')
        the_list.editors.append(the_target)

    # if owners is now empty, make the list publicly editable
    if len(the_list.owners) == 0:
        the_list.public_level = "edit"

    # add the target user to the current user's acquaintances attribute
    acq = flask_security.core.current_user.acquaintances
    if the_target not in acq:
        acq.append(the_target)

    # save the list
    # should permission editing count as "modification"? prob not -txz
    # hmm actually idk -txz
    # the_list.last_visited = datetime.utcnow()
    the_list.save()
    return "OK"  # 200 OK


@app.route("/api/getpermissions", methods=['POST'])
def permissions_get():
    """
    Get the permission level a user has for a particular list.

    usage: POST the following:
    {
        listid: <the listid>
    }

    returns:
    {
        permission: <the current permission>
    }
    """
    try:
        catalist = Catalist.objects.get(listid=request.form["listid"])
    except DoesNotExist:
        raise InvalidAPIUsage("List does not exist")
    return jsonify(permission=query_cur_perm(catalist))


@app.route("/api/setpubliclevel", methods=['POST'])
def public_level_set():
    """
    Set the permission level for a list for the public at-large.
    Requires own permission.

    POST: {
        listid: <the listid>,
        permission: {none | view | edit | own | admin}
    }
    """
    try:
        the_list = Catalist.objects.get(listid=request.form["listid"])
    except DoesNotExist:
        raise InvalidAPIUsage("List does not exist")

    # check permissions
    if cmp_permission(query_cur_perm(the_list), "own") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    perm = request.form["permission"]
    if perm not in perm_list:
        raise InvalidAPIUsage("Invalid arguments")

    the_list.public_level = perm
    the_list.save()
    return "set"

# # # # # # # # # # # # # #
# CUSTOMIZATION
# # # # # # # # # # # # # #


@flask_security.login_required
@app.route("/api/customize", methods=['POST'])
def get_pref():
    """
    Get the preferred theme for the user
    POST: {
        uid: <uid>,
    }
    returns:
    {
        theme: <preferred theme [0, 1, ..]>
    }
    """
    # login required, so user must exist
    uid = flask_security.core.current_user.uid
    user = User.objects.get(uid=uid)
    return jsonify(theme=user.preferred_theme)


@app.route("/api/permissions/forfeit", methods=['POST'])
def permissions_forfeit():
    """
    Forfeit permissions to a list. Effectively sets permission
    to Catalist.public_level.

    POST: {
        listid: <listid>
    }
    """
    cur_user = flask_security.core.current_user
    try:
        the_list = Catalist.objects.get(listid=request.form["listid"])
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List does not exist")

    for priv_list in ["owners", "editors", "viewers"]:
        try:
            getattr(the_list, priv_list).remove(cur_user)
        except ValueError:
            pass

    return "OK"  # 200

# # # # # # # # # # # # # #
# WHY IS THIS STILL HERE?
# # # # # # # # # # # # # #

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


@app.route("/api/autocomplete/user", methods=['POST'])
def autocomplete_user():
    cur_user = flask_security.core.current_user
    return jsonify(acquaintances=cur_user.acquaintances)  # 200 OK ^_^

# **********************************************************
# Start Application
# **********************************************************
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005, debug=True)
