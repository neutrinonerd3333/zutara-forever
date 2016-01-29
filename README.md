zutara-forever
==============

# Catalist

A web app for making lists. Like, really nice lists.
To use, first make sure `mongod` is running in another shell (or in the background). Then, run `sudo python routes.py` (`sudo` required since we're running on port 80).

Catalist was built at MIT for 6.148 by Rachel Wu '19 and Tony Zhang '19 with Flask and relies on MongoDB for data persistence.

## Requirements
* A modern browser that supports JQuery 2 (in particular, IE 6/7/8 are not supported)
* All the Flask dependencies (Flask itself; Flask-Security, Flask-MongoEngine, ...)
* A copy of MongoDB

## Acknowledgements
* API error exception class taken from the [Flask docs](http://flask.pocoo.org/docs/0.10/patterns/apierrors/)
* Safety Pig brought to us by [Quora](http://qr.ae/RgLMU8)

