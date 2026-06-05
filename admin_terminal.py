"""
admin_terminal.py
Terminal de logs en tiempo real para el Admin.
Captura stdout/stderr y los sirve via Server-Sent Events (SSE).
"""

import sys
import logging
import threading
from collections import deque
from datetime import datetime
from flask import Response, render_template, stream_with_context

# ──────────────────────────────────────────────────────────────
# BUFFER CIRCULAR — guarda los últimos 500 mensajes en memoria
# ──────────────────────────────────────────────────────────────
MAX_LOGS = 500
_log_buffer: deque = deque(maxlen=MAX_LOGS)
_lock = threading.Lock()
_subscribers: list = []       # lista de colas para SSE activos


def _push(nivel: str, mensaje: str):
    """Agrega una entrada al buffer y notifica a todos los SSE activos."""
    entrada = {
        'ts':      datetime.now().strftime('%H:%M:%S'),
        'nivel':   nivel,
        'msg':     mensaje.rstrip('\n'),
    }
    with _lock:
        _log_buffer.append(entrada)
        # Notificar a los listeners SSE
        muertos = []
        for q in _subscribers:
            try:
                q.put_nowait(entrada)
            except Exception:
                muertos.append(q)
        for q in muertos:
            try:
                _subscribers.remove(q)
            except ValueError:
                pass


# ──────────────────────────────────────────────────────────────
# INTERCEPTOR DE LOGGING (captura todo lo que Flask/gunicorn loguea)
# ──────────────────────────────────────────────────────────────

class _MemHandler(logging.Handler):
    NIVEL_MAP = {
        logging.DEBUG:    'DEBUG',
        logging.INFO:     'INFO',
        logging.WARNING:  'WARNING',
        logging.ERROR:    'ERROR',
        logging.CRITICAL: 'CRITICAL',
    }

    def emit(self, record: logging.LogRecord):
        nivel = self.NIVEL_MAP.get(record.levelno, 'INFO')
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        _push(nivel, msg)


# ──────────────────────────────────────────────────────────────
# INTERCEPTOR DE STDOUT/STDERR (captura print() y errores crudos)
# ──────────────────────────────────────────────────────────────

class _StreamInterceptor:
    def __init__(self, original, nivel: str):
        self._orig  = original
        self._nivel = nivel

    def write(self, txt):
        if txt.strip():
            _push(self._nivel, txt)
        self._orig.write(txt)

    def flush(self):
        self._orig.flush()

    def __getattr__(self, name):
        return getattr(self._orig, name)


def instalar_interceptores():
    """
    Llama esta función UNA VEZ al arrancar la app (en principal.py).
    Registra el handler en el logger raíz y redirige stdout/stderr.
    """
    handler = _MemHandler()
    handler.setFormatter(logging.Formatter('%(name)s — %(message)s'))
    handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Solo añadir si no está ya
    if not any(isinstance(h, _MemHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)

    # Redirigir print() y errores
    if not isinstance(sys.stdout, _StreamInterceptor):
        sys.stdout = _StreamInterceptor(sys.stdout, 'INFO')
    if not isinstance(sys.stderr, _StreamInterceptor):
        sys.stderr = _StreamInterceptor(sys.stderr, 'ERROR')


# ──────────────────────────────────────────────────────────────
# VISTAS
# ──────────────────────────────────────────────────────────────

def vista_terminal():
    """Renderiza la página HTML del terminal."""
    with _lock:
        logs_iniciales = list(_log_buffer)
    return render_template('admin_terminal.html', logs_iniciales=logs_iniciales)


def sse_stream():
    """
    Endpoint SSE: envía eventos al cliente en tiempo real.
    El cliente se suscribe y recibe cada nuevo log como evento.
    """
    import queue

    q: queue.Queue = queue.Queue(maxsize=200)
    with _lock:
        _subscribers.append(q)

    def generate():
        # Enviar heartbeat inicial
        yield "data: {\"tipo\":\"ping\"}\n\n"
        try:
            while True:
                try:
                    entry = q.get(timeout=25)        # timeout = heartbeat
                    import json
                    yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield "data: {\"tipo\":\"ping\"}\n\n"   # mantener conexión viva
        except GeneratorExit:
            pass
        finally:
            with _lock:
                try:
                    _subscribers.remove(q)
                except ValueError:
                    pass

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':  'no-cache',
            'X-Accel-Buffering': 'no',    # necesario para Nginx / Render
        }
    )
