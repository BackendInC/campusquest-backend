# test_users.py
import random
from api import utils


def create_user(client, db_session, user):
    response = client.post("/users", json=user)
    return response


def create_random_user(client, db_session):
    user_data = {
        "username": utils.get_random_string(10),
        "email": f"test_user_{random.randint(1, 1000)}@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    response = create_user(client, db_session, user_data)
    return response


def test_create_user(client, db_session):
    response = create_random_user(client, db_session)

    # Assert
    assert response.status_code == 200


def test_create_duplicate_user(client, db_session):
    user_data = {
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    response = create_user(client, db_session, user_data)

    assert response.status_code == 200

    # Create the same user again
    response = create_user(client, db_session, user_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "username or email already exists"}


def test_create_user_incorrect_params(client, db_session):
    user_data = {"username": "test_user", "email": "test_user@example.com"}

    response = create_user(client, db_session, user_data)

    assert response.status_code == 422
