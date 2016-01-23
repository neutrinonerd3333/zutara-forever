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
# HOSTBASE = 'catalist.eastus2.cloudapp.azure.com'
HOSTBASE = 'localhost'
PORTNO = 6005
HOSTNAME = HOSTBASE + (':' + str(PORTNO)) if PORTNO != 80 else ''

db = MongoEngine(app)

# import database
# from permissions import *
import views  # /about, /mylists, etc.
import errorviews  # 404 pages, etc.
# import api
from api import api_blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')

# **********************************************************
# Start Application
# **********************************************************
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005, debug=True)
