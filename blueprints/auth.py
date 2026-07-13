from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from database import users_dao
from models import User
from services import duty_service
from utils import normalize_user_tag, validate_registration

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        raw_tag = request.form.get('user_tag', '')
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        errors = validate_registration(first_name, last_name, raw_tag, password, password2)
        user_tag = normalize_user_tag(raw_tag)

        if not errors and users_dao.user_tag_exists(user_tag):
            errors.append('Tag utente già registrato.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', form=request.form)

        password_hash = generate_password_hash(password)
        users_dao.create_user(first_name, last_name, user_tag, password_hash)
        duty_service.recalculate_schedule()
        flash('Registrazione completata! Effettua il login per continuare.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        raw_tag = request.form.get('user_tag', '')
        password = request.form.get('password', '')
        user_tag = normalize_user_tag(raw_tag)

        if not user_tag or not password:
            flash('Compila tutti i campi per proseguire.', 'danger')
            return render_template('auth/login.html', user_tag=raw_tag)

        row = users_dao.get_user_by_tag(user_tag)
        if row is None or not check_password_hash(row['password_hash'], password):
            flash('Tag utente o password errati.', 'danger')
            return render_template('auth/login.html', user_tag=raw_tag)

        user = User.from_row(row)
        login_user(user)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', user_tag='')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
