"""Production WSGI entry point; reuses the exact local simulation and view."""
import gzip
import json
from urllib.parse import urlsplit

from flask import Flask, Response, abort, redirect, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .api import (CATALOGUE, COMPOUNDS, DEFAULTS, FIELDS, ROOT,
                  SIMULATION_LOCK, render_dashboard, run_request, verify_request)

app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 1_000_000


def json_response(data, status=200):
    payload = json.dumps(data, allow_nan=False, separators=(',', ':')).encode()
    headers = {'Vary': 'Accept-Encoding', 'Cache-Control': 'no-store'}
    if request.accept_encodings['gzip'] > 0:
        payload = gzip.compress(payload, compresslevel=1)
        headers['Content-Encoding'] = 'gzip'
    return Response(payload, status=status, mimetype='application/json', headers=headers)


@app.after_request
def response_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@app.get('/')
def index():
    return redirect('/reports/dashboard')


@app.get('/healthz')
def health():
    return json_response({'status': 'ok', 'circuits': len(CATALOGUE['circuits'])})


@app.get('/reports/dashboard')
@app.get('/reports/dashboard.html')
def dashboard():
    return Response(render_dashboard(), mimetype='text/html', headers={'Cache-Control': 'no-cache'})


@app.get('/reports/<path:filename>')
def asset(filename):
    # Only public report assets; no project source, credentials or dotfiles.
    if any(part.startswith('.') for part in filename.split('/')):
        abort(404)
    return send_from_directory(ROOT / 'reports', filename, max_age=300)


@app.get('/api/circuits')
def circuits():
    return json_response({**CATALOGUE, 'defaults': DEFAULTS, 'fields': FIELDS,
                          'compounds': list(COMPOUNDS)})


@app.post('/api/simulate')
@app.post('/api/verify')
def simulation():
    origin = request.headers.get('Origin')
    if origin and urlsplit(origin).netloc != request.host:
        return json_response({'error': 'Use the same-origin dashboard'}, 403)
    if request.mimetype != 'application/json':
        return json_response({'error': 'Content-Type must be application/json'}, 400)
    body = request.get_json()
    # One calculation at a time per worker: bound CPU/memory on small hosts.
    if not SIMULATION_LOCK.acquire(blocking=False):
        response = json_response({'error': 'A simulation is running. Please retry shortly.'}, 429)
        response.headers['Retry-After'] = '2'
        return response
    try:
        calculate = verify_request if request.path == '/api/verify' else run_request
        return json_response(calculate(body))
    except (ValueError, TypeError, KeyError) as exc:
        return json_response({'error': str(exc)}, 400)
    finally:
        SIMULATION_LOCK.release()


@app.errorhandler(HTTPException)
def http_error(exc):
    return json_response({'error': exc.description}, exc.code)


@app.errorhandler(Exception)
def unexpected_error(exc):
    app.logger.exception('Request failed')
    return json_response({'error': 'Simulation failed. Please retry later.'}, 500)
