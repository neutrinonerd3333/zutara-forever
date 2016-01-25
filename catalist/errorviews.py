"""
	catalist.errorviews
	~~~~~~~~~~~~~~~~~~~

	This module contains error handlers for HTTP errors.

    :copyright: (c) 2016 Rachel Wu, Tony Zhang
    :license: lol don't steal this code pls
"""

from catalist import app
from flask import render_template


@app.errorhandler(403)
def forbidden(e):
    return render_template('error/403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('error/405.html'), 405


@app.errorhandler(410)
def page_gone(e):
    return render_template('error/410.html'), 410


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500
