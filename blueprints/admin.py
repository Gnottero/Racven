from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from database import users_dao
from decorators import admin_required
from services import duty_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def dashboard():
    users = users_dao.get_all_users()
    return render_template('admin/dashboard.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-contributor', methods=['POST'])
@admin_required
def toggle_contributor(user_id):
    user_row = users_dao.get_user_by_id(user_id)
    if user_row is None:
        abort(404)

    users_dao.set_contributor(user_id, not user_row['contributor'])
    duty_service.recalculate_schedule()

    flash('Stato contributore aggiornato e turno piatti ricalcolato.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user_row = users_dao.get_user_by_id(user_id)
    if user_row is None:
        abort(404)

    if user_id == current_user.id:
        flash('Non puoi eliminare il tuo stesso account.', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Elimina anche i messaggi e le appartenenze ai gruppi turno piatti
    # dell'utente (ON DELETE CASCADE, vedi database/schema.sql).
    users_dao.delete_user(user_id)
    duty_service.recalculate_schedule()

    flash('Utente eliminato e turno piatti ricalcolato.', 'success')
    return redirect(url_for('admin.dashboard'))
