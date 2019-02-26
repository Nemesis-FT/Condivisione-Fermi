import pytest
import server
import random


@pytest.fixture
def app():
    app = server.app
    app.debug = True
    app.config["TESTING"] = True
    return app.test_client()


def test_login_page(app):
    res = app.get("/login")
    assert res.status_code == 200
    res = app.post("/login", data={
        "password": "haha"
    })
    assert res.status_code == 400
    res = app.post("/login", data={
        "username": "sacripante"
    })
    assert res.status_code == 400
    res = app.post("/login")
    assert res.status_code == 400
    res = app.post("/login", data={
        "username": str(random.random()),
        "password": str(random.random())
    })
    assert res.status_code == 403
