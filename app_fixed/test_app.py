from app import app


def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_hello_ok():
    r = client().get('/hello?name=Ana')
    assert r.status_code == 200
    assert b'Hello, Ana!' in r.data


def test_xss_blocked():
    r = client().get('/hello?name=<script>alert(1)</script>')
    assert r.status_code == 400
    assert b'<script>' not in r.data


def test_security_headers():
    r = client().get('/hello?name=Ana')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'Content-Security-Policy' in r.headers


def test_metrics():
    r = client().get('/metrics')
    assert r.status_code == 200
    assert b'http_requests_total' in r.data
