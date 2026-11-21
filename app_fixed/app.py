import logging
import os
import re

from flask import Flask, request, Response
from markupsafe import escape
from prometheus_client import (Summary, Counter, generate_latest,
                               CONTENT_TYPE_LATEST)

app = Flask(__name__)

REQUEST_TIME = Summary('request_processing_seconds',
                       'Time spent processing request')
REQUESTS = Counter('http_requests_total', 'Total HTTP requests',
                   ['endpoint', 'status'])
BLOCKED = Counter('suspicious_requests_total',
                  'Requests rejected by input validation')

# Solo letras, numeros, espacio, guion y guion bajo (max. 30 caracteres).
NAME_RE = re.compile(r'^[A-Za-z0-9 _\-]{1,30}$')

# Si LOG_FILE esta definido (Windows nativo) se escribe a archivo;
# si no (Docker), los logs salen por consola y se ven con "docker logs".
logging.basicConfig(filename=os.getenv('LOG_FILE') or None,
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('flask-app')


@app.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Content-Security-Policy'] = "default-src 'none'"
    resp.headers['Cache-Control'] = 'no-store'
    return resp


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/hello')
@REQUEST_TIME.time()
def hello():
    name = request.args.get('name', 'mundo')
    if not NAME_RE.fullmatch(name):
        BLOCKED.inc()
        REQUESTS.labels('/hello', '400').inc()
        log.warning('Entrada sospechosa rechazada desde %s', request.remote_addr)
        return Response('Parametro invalido', status=400, mimetype='text/plain')
    REQUESTS.labels('/hello', '200').inc()
    log.info('hello name=%s', name)
    return Response(f'Hello, {escape(name)}!', mimetype='text/plain')


if __name__ == '__main__':
    # Solo desarrollo local. En "produccion" se usa waitress (ver pipeline).
    app.run(host='127.0.0.1', port=5000, debug=False)
