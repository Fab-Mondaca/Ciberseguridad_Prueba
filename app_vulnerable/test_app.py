from app import app


def test_hello_ok():
    r = app.test_client().get('/hello?name=Ana')
    assert r.status_code == 200
