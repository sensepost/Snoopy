"""Contains web-app specific code."""

from functools import wraps
from flask import request, redirect, url_for

DEBUG = False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        beaker = request.environ['beaker.session']
        if not beaker.has_key('userid') and not DEBUG:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
