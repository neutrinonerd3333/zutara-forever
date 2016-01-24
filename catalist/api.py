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
#
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

from flask import Flask, render_template, jsonify, \
    request, redirect, url_for, make_response, Blueprint
from flask.ext.security import Security, login_required
import flask.ext.security as flask_security
from flask.ext.mongoengine import *

from datetime import datetime, date, timedelta
import uuid as uuid_module

from permissions import *
from database import Role, User, Catalist, CatalistEntry, CatalistKVP
import database as dbase

# **********************************************************
# THE API!!!
# **********************************************************

api_blueprint = Blueprint('api', __name__)

# # # # # # # # # # # # # #
# EXCEPTION HANDLING
# # # # # # # # # # # # # #


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


@api_blueprint.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    print("\033[93m{} -- {}\033[0m".format(error.status_code, error.message))
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# # # # # # # # # # # # # #
# MISCELLANEOUS
# # # # # # # # # # # # # #


@api_blueprint.route("/loggedin", methods=['POST'])
def logged_in():
    # print("hi")
    """ Used for .js to call """
    if flask_security.core.current_user.is_authenticated:
        return jsonify(loggedin=1)
    return jsonify(loggedin=0)


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


@api_blueprint.route("/makelist", methods=['GET'])
def make_list():
    """
    Upon making the first edit, an empty list will be
    created for the insertion of more data
    """
    list_id = create_list()
    return jsonify(listid=list_id)


@api_blueprint.route("/savelist", methods=['POST'])
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
    max_len = dbase.key_max_len if key_or_val == "key" else dbase.val_max_len

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

    if eind < 0 or ind < 0:
        i = min(eind, ind)
        raise InvalidAPIUsage("Invalid index value {}".format(i))

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


@api_blueprint.route("/savekey", methods=['POST'])
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


@api_blueprint.route("/savevalue", methods=['POST'])
def value_save():
    """
    Save the value in a particular key-value pair. Requires
    at least edit permission.

    The API is virtually identical the that of key_save()
    """
    return key_val_save(request.form, "value")


@api_blueprint.route("/saveentrytitle", methods=['POST'])
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
        val = req_json["newvalue"][:dbase.entry_title_max_len]
        the_list = Catalist.objects.get(listid=lid)
    except KeyError:
        raise InvalidAPIUsage("Invalid arguments")
    except DoesNotExist:
        raise InvalidAPIUsage("List {} does not exist".foramt(lid))

    if cmp_permission(query_cur_perm(the_list), "edit") < 0:
        raise InvalidAPIUsage("Forbidden", status_code=403)

    if eind < 0:
        raise InvalidAPIUsage("Invalid index value {}".format(eind))

    pad_len = eind - len(the_list.contents) + 1
    the_list.contents += [CatalistEntry() for i in xrange(pad_len)]
    the_entry = the_list.contents[eind]
    the_entry.title = val
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return "OK"  # 200 OK ^_^


@api_blueprint.route("/savelisttitle", methods=['POST'])
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

    the_list.title = req_json["newvalue"][:dbase.list_title_max_len]
    the_list.last_visited = datetime.utcnow()
    the_list.save()
    return jsonify()  # 200 OK ^_^


@api_blueprint.route("/deletelist", methods=['POST'])
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


@api_blueprint.route("/deleteentry", methods=['POST'])
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


@api_blueprint.route("/deletekvp", methods=['POST'])
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
        listid = request.form["listid"]
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


@api_blueprint.route("/vote", methods=['POST'])
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
    if entryind < 0:
        raise InvalidAPIUsage("Invalid entry index {}".format(entryind))

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


@api_blueprint.route("/mylists/add", methods=['POST'])
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


@api_blueprint.route("/mylists/remove", methods=['POST'])
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


@api_blueprint.route("/permissions/set", methods=['POST'])
@api_blueprint.route("/setpermissions", methods=['POST'])
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


@api_blueprint.route("/permissions/get", methods=['POST'])
@api_blueprint.route("/getpermissions", methods=['POST'])
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


@api_blueprint.route("/permissions/public-set", methods=['POST'])
@api_blueprint.route("/setpubliclevel", methods=['POST'])
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


@api_blueprint.route("/permissions/forfeit", methods=['POST'])
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
# CUSTOMIZATION
# # # # # # # # # # # # # #


@flask_security.login_required
@api_blueprint.route("/customize", methods=['POST'])
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

# # # # # # # # # # # # # #
# WHY IS THIS STILL HERE?
# # # # # # # # # # # # # #

autocomplete_dict = ["contacts", "groceries", "movie", "shopping"]
autocomplete_dict.sort()


@api_blueprint.route("/autocomplete", methods=['POST'])
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


@api_blueprint.route("/autocomplete/user", methods=['POST'])
def autocomplete_user():
    cur_user = flask_security.core.current_user
    return jsonify(acquaintances=cur_user.acquaintances)  # 200 OK ^_^
