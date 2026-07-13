from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from database import messages_dao
from events import broadcaster
from services import duty_service
from utils import validate_message_body

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    recent_messages = messages_dao.get_recent_messages_for_user(current_user.id, limit=5)
    return render_template('main/index.html', recent_messages=recent_messages)


@main_bp.route('/messages', methods=['POST'])
@login_required
def send_message():
    body = request.form.get('body', '')
    errors = validate_message_body(body)
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('main.index'))

    row = messages_dao.create_message(current_user.id, body.strip())
    broadcaster.broadcast('chat_message', messages_dao.to_dict(row))

    flash('Messaggio inviato alla TV!', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/duty/show', methods=['POST'])
@login_required
def show_duty():
    duty_service.ensure_month_schedule()
    schedule = duty_service.get_month_schedule()
    today_duty = duty_service.get_today_duty()
    broadcaster.broadcast('duty_display', {'today': today_duty, 'schedule': schedule})

    flash('Turno piatti mostrato sulla TV.', 'success')
    return redirect(url_for('main.index'))
