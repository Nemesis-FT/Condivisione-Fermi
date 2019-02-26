import pytest
import server
import random


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


def register_page(app):
    res = app.get("/register")
    assert res.status_code == 200


def register_no_captcha(app):
    res = app.post("/register")
    assert res.status_code == 403


def register_only_captcha(app):
    res = app.post("/register", data={
        "g-recaptcha-response": "sì"
    })
    assert res.status_code == 400


def register_missing_fields(app):
    res = app.post("/register", data={
        "g-recaptcha-response": "sì",
        "username": "ciao",
        "password": "saaaas"
    })
    assert res.status_code == 400


def register_valid(app):
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


def login_page(app):
    res = app.get("/login")
    assert res.status_code == 200


def login_no_username(app):
    res = app.post("/login", data={
        "password": "haha"
    })
    assert res.status_code == 400


def login_no_password(app):
    res = app.post("/login", data={
        "username": "sacripante"
    })
    assert res.status_code == 400


def login_nothing(app):
    res = app.post("/login")
    assert res.status_code == 400


def login_invalid(app):
    res = app.post("/login", data={
        "username": str(random.random()),
        "password": str(random.random())
    })
    assert res.status_code == 403


def login_valid(app):
    res = app.post("/login", data={
        "username": "example@example.org",
        "password": "password123"
    }, follow_redirects=True)
    assert res.status_code == 200


def dashboard_redirect(app):
    res = app.get("/dashboard")
    assert res.status_code == 302


def dashboard_display(app):
    with app.session_transaction() as ses:
        ses["username"] = "example@example.org"
        res = app.get("/dashboard")
        assert res.status_code == 200
