"""
    catalist.views
    ~~~~~~~~~~~~~~

    This module contains most of the views (read: non-error views)
    for our web app.

    :copyright: (c) 2016 Rachel Wu, Tony Zhang
    :license: lol don't steal this code pls
"""

from flask import render_template, request
import flask.ext.security as flask_security
from flask.ext import mongoengine
from datetime import datetime, date, timedelta

from catalist import app, db, HOSTNAME
from database import Role, User, Catalist, CatalistEntry, \
                     CatalistKVP, user_datastore, security
from permissions import cmp_permission, query_cur_perm

from database import user_datastore
from flask.ext.mongoengine import *

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
                           message="Welcome to Catalist, {}!".format(user_id),
                           newuser=1)


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
    try:
        the_list = Catalist.objects.get(listid=listid)
    except DoesNotExist:
        abort(404)
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
    now = datetime.utcnow()
    then = tiem
    delta = now - then  # in units of seconds

    # >10 days ago: just display the date instead.
    if delta.days > 10:
        yearQ = (then.timetuple()[0] != now.timetuple()[0])
        if yearQ:
            return then.strftime("%-* %Y %b %d")  # format as '1776 Jul 4'
        else:
            return then.strftime("%-* %b %d")  # format as 'Jul 4'

    # resolution should be in days if within [1, 10] days
    if delta.days > 0:
        return "{} day{} ago".format(delta.days,
                                     '' if delta.days == 1 else 's')

    secs = delta.seconds
    if secs < 60:
        return "just now"
    mins = secs / 60
    if mins < 60:
        return "{} minute{} ago".format(mins, '' if mins == 1 else 's')
    hrs = mins / 60
    return "{} hour{} ago".format(hrs, '' if hrs == 1 else 's')


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
