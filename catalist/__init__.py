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

import database

# **********************************************************
# Permissions
# **********************************************************

from permissions import *

# **********************************************************
# User Interaction Section
# **********************************************************

import catalist.views

# **********************************************************
# Error Handlers
# **********************************************************


import errorviews


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

import api

# **********************************************************
# Start Application
# **********************************************************
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005, debug=True)
