from flask import Flask, jsonify, session
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
import os
import credstash

app = Flask(__name__)

try:
    secrets = credstash.getAllSecrets(
        context={'application': 'example-auth0-flask-app'},
        credential='example-auth0-flask-app:*',
        region="us-west-2"
    )
except:
    app.logger.error("Unable to load credentials with credstash")

# TODO : conditional on credstash vs env vars

client_info = dict()

# Required settings set in environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'SecretKeyGoesHere')
client_info['client_id'] = os.environ.get('OIDC_CLIENT_ID')
client_info['client_secret'] = os.environ.get('OIDC_CLIENT_SECRET')
issuer = os.environ.get('OIDC_ISSUER')

# Optional settings set in environment variables
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', 'localhost:3000')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'http')
app.config['DEBUG'] = True if os.environ.get('DEBUG', 'True').lower() == 'true' else False

app.config.update({
    'SESSION_PERMANENT': True,  # turn on flask session support
    'PERMANENT_SESSION_LIFETIME': 2592000,  # session time in seconds (30 days)
    'DEBUG': True})
client_info['session_refresh_interval_seconds'] = 900  # interval at which to check that the user attributes are valid, in seconds (15 min)

auth = OIDCAuthentication(app, client_registration_info=client_info, issuer=issuer)


@app.route('/')
def example_unauthenticated_endpoint():
    return ('This is an example page which is not protected by authentication.<br>'
            '<a href="/private">private</a><br><a href="/logout">logout</a>')


@app.route('/private')
@auth.oidc_auth
def example_authenticated_endpoint():
    return jsonify(id_token=session['id_token'],
                   access_token=session['access_token'],
                   userinfo=session['userinfo'])


@app.route('/logout')
@auth.oidc_logout
def logout():
    return "You've been successfully logged out!"


@auth.error_view
def error_view(error=None, error_description=None):
    return jsonify({'error': error, 'message': error_description})


if __name__ == '__main__':
    app_options = {
        'port': int(app.config['SERVER_NAME'].split(':')[1]),
        'debug': app.config['DEBUG'],
        'use_debugger': app.config['DEBUG'],
        'use_reloader': app.config['DEBUG']
    }
    app.run(**app_options)
