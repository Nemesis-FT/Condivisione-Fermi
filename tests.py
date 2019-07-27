import pytest
import server
import random

# NOTE: These tests should be executed in order!


@pytest.fixture
def app():
    app = server.app
    app.debug = True
    app.config["TESTING"] = True
    # Use an in-memory database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
    with app.app_context():
        server.db.create_all()
    return app.test_client()


def test_register_page(app):
    res = app.get("/register")
    assert res.status_code == 200


def test_register_no_captcha(app):
    res = app.post("/register")
    assert res.status_code == 400


def test_register_only_captcha(app):
    res = app.post("/register", data={
        "g-recaptcha-response": "sì"
    })
    assert res.status_code == 400


def test_register_missing_fields(app):
    res = app.post("/register", data={
        "g-recaptcha-response": "sì",
        "username": "ciao",
        "password": "saaaas"
    })
    assert res.status_code == 400


def test_register_valid(app):
    res = app.post("/register", data={
        "g-recaptcha-response": "sì",
        "username": "example@example.org",
        "password": "password123",
        "nome": "Prova",
        "cognome": "Unoduetre",
        "classe": "1A",
        "usernameTelegram": "@BotFather",
        "mailGenitori": "dad@example.org"
    }, follow_redirects=True)
    assert res.status_code == 200


def test_login_page(app):
    res = app.get("/login")
    assert res.status_code == 200


def test_login_no_username(app):
    res = app.post("/login", data={
        "password": "haha"
    })
    assert res.status_code == 400


def test_login_no_password(app):
    res = app.post("/login", data={
        "username": "sacripante"
    })
    assert res.status_code == 400


def test_login_nothing(app):
    res = app.post("/login")
    assert res.status_code == 400


def test_login_invalid(app):
    res = app.post("/login", data={
        "username": str(random.random()),
        "password": str(random.random())
    })
    assert res.status_code == 403


def test_login_valid(app):
    res = app.post("/login", data={
        "username": "example@example.org",
        "password": "password123"
    }, follow_redirects=True)
    assert res.status_code == 200


@pytest.fixture
def app_user(app):
    with app.session_transaction() as ses:
        ses["username"] = "example@example.org"
        return app


def test_dashboard_redirect_not_loggedin(app):
    res = app.get("/dashboard")
    assert res.status_code == 302


def test_dashboard_display(app_user):
    res = app_user.get("/dashboard")
    assert res.status_code == 200
