import queue
import threading


class EventBroadcaster:
    def __init__(self):
        self._lock = threading.Lock()
        self._listeners = []

    def listen(self):
        q = queue.Queue(maxsize=50)
        with self._lock:
            self._listeners.append(q)
        return q

    def stop_listen(self, q):
        with self._lock:
            if q in self._listeners:
                self._listeners.remove(q)

    def broadcast(self, event_type, data):
        with self._lock:
            listeners = list(self._listeners)
        for q in listeners:
            try:
                q.put_nowait({'type': event_type, 'data': data})
            except queue.Full:
                pass


broadcaster = EventBroadcaster()
