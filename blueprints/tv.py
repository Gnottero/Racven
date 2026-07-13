import json
import queue

from flask import Blueprint, Response, current_app, render_template, stream_with_context

from database import messages_dao
from events import broadcaster

tv_bp = Blueprint('tv', __name__)


@tv_bp.route('/tv')
def display():
    messages = [messages_dao.to_dict(row) for row in messages_dao.get_today_messages()]
    return render_template(
        'tv/display.html',
        initial_messages=messages,
        carousel_interval=current_app.config['TV_CAROUSEL_INTERVAL_SECONDS'],
        message_display_seconds=current_app.config['TV_MESSAGE_DISPLAY_SECONDS'],
        duty_display_seconds=current_app.config['TV_DUTY_DISPLAY_SECONDS'],
    )


@tv_bp.route('/tv/stream')
def stream():
    def event_stream():
        q = broadcaster.listen()
        try:
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield f"event: {payload['type']}\ndata: {json.dumps(payload['data'])}\n\n"
                except queue.Empty:
                    yield ': ping\n\n'
        finally:
            broadcaster.stop_listen(q)

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')
