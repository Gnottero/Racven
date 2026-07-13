import secrets
from hmac import compare_digest

from flask import abort, request, session


def generate_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_hex(32)
        session['csrf_token'] = token
    return token


def validate_csrf_token():
    session_token = session.get('csrf_token')
    submitted_token = request.form.get('csrf_token', '')
    if not session_token or not compare_digest(session_token, submitted_token):
        abort(400, description='Token CSRF non valido o mancante.')


def init_csrf(app):
    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    @app.before_request
    def _check_csrf():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            validate_csrf_token()
