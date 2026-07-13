import click
from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from blueprints.admin import admin_bp
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.tv import tv_bp
from config import Config
from csrf import init_csrf
from database import database, users_dao
from models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        row = users_dao.get_user_by_id(int(user_id))
        return User.from_row(row) if row else None

    init_csrf(app)
    database.init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tv_bp)

    register_cli_commands(app)

    return app


def register_cli_commands(app):
    @app.cli.command('init-db')
    def init_db_command():
        """Crea le tabelle del database secondo schema.sql."""
        database.init_db()
        click.echo('Database inizializzato.')

    @app.cli.command('create-admin')
    def create_admin_command():
        """Crea un utente amministratore da terminale."""
        first_name = click.prompt('Nome')
        last_name = click.prompt('Cognome')
        user_tag = click.prompt('Tag utente (senza @)').strip().lstrip('@').lower()
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

        if users_dao.user_tag_exists(user_tag):
            click.echo(f'Errore: il tag @{user_tag} è già in uso.')
            return

        password_hash = generate_password_hash(password)
        users_dao.create_user(
            first_name, last_name, user_tag, password_hash, role='admin', contributor=True
        )
        click.echo(f'Amministratore @{user_tag} creato.')


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
