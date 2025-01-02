import pytest
from fastapi.testclient import TestClient

import api
from api import app

import db
from db import get_db

# Initialize the database
db.Base.metadata.create_all(bind=db.engine)


@pytest.fixture
def db_session():
    yield from get_db()


@pytest.fixture
def client(db_session):
    return TestClient(app)
    app.dependency_overrides[get_db] = lambda: db_session
