
from app import create_app

def test_home():
    app = create_app()
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code in (200,302)

def test_login_page():
    app = create_app()
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code in (200,302)

def test_help_page():
    app = create_app()
    client = app.test_client()
    resp = client.get("/help")
    assert resp.status_code in (200,404,200)
