import pytest
import server


@pytest.fixture
def app():
    app = server.app
    app.debug = True
    return app.test_client()


def test_login_page(app):
    res = app.get("/login")
    assert res.status_code == 200
