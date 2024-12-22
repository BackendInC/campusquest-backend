# test_users.py
from db import models, schemas


def test_create_user(client, db_session):
    # Create a user to test with
    user_data = {
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    # Send a POST request to the endpoint
    response = client.post("/users", json=user_data)

    # Assert
    assert response.status_code == 200
