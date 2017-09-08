from future.standard_library import install_aliases
install_aliases()

from functools import wraps
from urllib.parse import urlparse
from os import environ as env
import json

from auth0.v3.authentication import GetToken
from auth0.v3.authentication import Users
from flask import Flask
from flask import redirect
from flask import request
from flask import send_from_directory
from flask import session

AUTH0_CLIENT_ID = 'g34TCGI95PfOHugnurKY15sW0tCGOfjW'
AUTH0_CLIENT_SECRET = 'uhlF5fPGMvyr-0PEjdUBHXNW08oYVrYnsgsyNmxyVhWRsXIzaNliNvWJrKo_uOTK'
AUTH0_CALLBACK_URL = 'http://localhost:3000/callback'
AUTH0_DOMAIN = 'auth-dev.mozilla.auth0.com'
CODE_KEY = 'code'
PROFILE_KEY = 'profile'
SECRET_KEY = '1cgtDJVwxLXhhWNCZbIz6DpcDZ03SOYC'

APP = Flask(__name__, static_url_path='')
APP.secret_key = SECRET_KEY
APP.debug = True


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if PROFILE_KEY not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


# Controllers API
@APP.route('/')
def home():
    return "home - no auth"


@APP.route('/dashboard')
@requires_auth
def dashboard():
    return "dashboard - authenticated"

@APP.route('/logout')
def logout():
    session.clear()
    parsed_base_url = urlparse(AUTH0_CALLBACK_URL)
    base_url = parsed_base_url.scheme + '://' + parsed_base_url.netloc
    return redirect('https://%s/v2/logout?returnTo=%s&client_id=%s' % (AUTH0_DOMAIN, base_url, AUTH0_CLIENT_ID))

@APP.route('/public/<path:filename>')
def static_files(filename):
    return send_from_directory('./public', filename)


@APP.route('/callback')
def callback_handling():
    code = request.args.get(CODE_KEY)
    get_token = GetToken(AUTH0_DOMAIN)
    auth0_users = Users(AUTH0_DOMAIN)
    token = get_token.authorization_code(AUTH0_CLIENT_ID,
                                         AUTH0_CLIENT_SECRET, code, AUTH0_CALLBACK_URL)
    user_info = auth0_users.userinfo(token['access_token'])
    session[PROFILE_KEY] = json.loads(user_info)
    return redirect('/dashboard')

if __name__ == "__main__":
    APP.run(host='0.0.0.0', port=3000)
