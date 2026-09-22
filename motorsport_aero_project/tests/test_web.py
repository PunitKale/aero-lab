"""Public deployment transport must preserve the local simulator's contract."""
import gzip
from src.realtrack.web import app


def test_routes_and_asset_isolation():
    client = app.test_client()
    assert client.get('/').location == '/reports/dashboard'
    assert client.get('/healthz').json['circuits'] == 5
    assert client.get('/reports/dashboard').status_code == 200
    assert client.get('/reports/dynamic.js').status_code == 200
    for path in ['/reports/.env', '/reports/../.env', '/.env', '/src/realtrack/api.py']:
        assert client.get(path).status_code == 404


def test_compression_and_validation():
    client = app.test_client()
    response = client.get('/api/circuits', headers={'Accept-Encoding': 'gzip'})
    assert response.headers['Content-Encoding'] == 'gzip'
    assert b'silverstone' in gzip.decompress(response.data)
    assert 'Content-Encoding' not in client.get('/api/circuits', headers={'Accept-Encoding': 'gzip;q=0'}).headers
    assert client.post('/api/simulate', json={}, headers={'Origin': 'https://other.example'}).status_code == 403
    assert client.post('/api/simulate', json={'parameters': {'mass_kg': -1}}).status_code == 400
    assert client.post('/api/simulate', data='bad', content_type='application/json').status_code == 400
    assert client.post('/api/simulate', data='x'*1_000_001, content_type='application/json').status_code == 413


def test_simulation_endpoint():
    response = app.test_client().post('/api/simulate', json={'circuit_id': 'monza', 'parameters': {}})
    assert response.status_code == 200
    result = response.json
    recommendation = next(iter(result['recommendations'].values()))
    assert recommendation['baseline']['lap_time_s'] > 0
    assert recommendation['lap_delta_s'] == 0
