from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from database import users_dao
from decorators import admin_required
from services import duty_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _move(ordered_ids, item_id, direction):
    """Swap item_id with its adjacent neighbor in ordered_ids, in place.
    Returns False if item_id is missing, True if a swap happened, None if
    item_id exists but is already at the boundary in that direction (no-op)."""
    if item_id not in ordered_ids:
        return False
    idx = ordered_ids.index(item_id)
    swap_idx = idx - 1 if direction == 'up' else idx + 1
    if 0 <= swap_idx < len(ordered_ids):
        ordered_ids[idx], ordered_ids[swap_idx] = ordered_ids[swap_idx], ordered_ids[idx]
        return True
    return None


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

    flash(
        'Stato contributore aggiornato e turno piatti ricalcolato. '
        "L'eventuale ordine di rotazione personalizzato è stato reimpostato.",
        'success',
    )
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

    flash(
        'Utente eliminato e turno piatti ricalcolato. '
        "L'eventuale ordine di rotazione personalizzato è stato reimpostato.",
        'success',
    )
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/duty')
@admin_required
def duty_dashboard():
    contributors = users_dao.get_contributors_ordered()
    contributors_by_id = {c['id']: c for c in contributors}
    preview_groups = [
        [contributors_by_id[user_id] for user_id in group]
        for group in duty_service.partition_into_groups(
            [c['id'] for c in contributors]
        )
    ]
    groups = duty_service.get_current_groups()
    return render_template(
        'admin/duty.html',
        contributors=contributors,
        preview_groups=preview_groups,
        groups=groups,
    )


@admin_bp.route('/duty/contributors/<int:user_id>/move', methods=['POST'])
@admin_required
def move_contributor(user_id):
    ordered_ids = [c['id'] for c in users_dao.get_contributors_ordered()]
    direction = request.form.get('direction')
    if _move(ordered_ids, user_id, direction):
        users_dao.set_contributor_order(ordered_ids)
    return redirect(url_for('admin.duty_dashboard'))


@admin_bp.route('/duty/recalculate', methods=['POST'])
@admin_required
def recalculate_duty():
    duty_service.recalculate_schedule()
    flash(
        'Turno piatti ricalcolato con il nuovo ordine contributori. '
        "L'eventuale ordine di rotazione personalizzato è stato reimpostato.",
        'success',
    )
    return redirect(url_for('admin.duty_dashboard'))


@admin_bp.route('/duty/groups/<int:group_id>/move', methods=['POST'])
@admin_required
def move_duty_group(group_id):
    ordered_ids = [g['id'] for g in duty_service.get_current_groups()]
    direction = request.form.get('direction')
    result = _move(ordered_ids, group_id, direction)
    if result is False:
        flash(
            'Questo gruppo non fa più parte del turno piatti corrente '
            '(probabilmente ricalcolato nel frattempo).',
            'danger',
        )
    elif result is True:
        duty_service.reorder_groups(ordered_ids)
        flash('Ordine di rotazione aggiornato.', 'success')
    return redirect(url_for('admin.duty_dashboard'))
