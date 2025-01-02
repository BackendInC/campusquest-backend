from test_users import create_and_login_user
from api import utils


def create_achievement(client, db_session, achievement_data, user_jwt):
    response = client.post(
        "/achievements",
        json=achievement_data,
        headers={"Authorization": f"Bearer {user_jwt}"},
    )

    assert response.status_code == 200

    achievement = response.json()
    assert achievement["description"] == achievement_data["description"]
    assert achievement["award_tokens"] == achievement_data["award_tokens"]

    return achievement


def create_random_achievement(client, db_session, user_data, user_jwt):
    # Create a user
    if user_data is None:
        user, jwt = create_and_login_user(client, db_session)
        user_data = user.json()
        user_jwt = jwt

    achievement_data = {
        "description": utils.get_random_string(20),
        "award_tokens": utils.get_random_int(),
    }

    return create_achievement(client, db_session, achievement_data, user_jwt)


def test_create_achievement(client, db_session):
    # Create a random achievement
    achievement = create_random_achievement(client, db_session, None, None)

    # Check that the achievement was added to the database
    response = client.get("/achievements")
    assert response.status_code == 200

    exists = False
    for achievement in response.json():
        if (
            achievement["description"] == achievement["description"]
            and achievement["award_tokens"] == achievement["award_tokens"]
        ):
            exists = True
            break

    assert exists


def test_create_user_achievemnt(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    achievement = create_random_achievement(client, db_session, user.json(), jwt)

    user_achievement_data = {
        "user_id": user.json()["id"],
        "achievement_id": achievement["id"],
    }

    response = client.put("/achievements", json=user_achievement_data)

    assert response.status_code == 200
    assert response.json() == {"message": "Achievement added successfully"}

    response = client.get(f"/achievements/user/{user.json()['username']}")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_duplicate_user_achievemnt(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    achievement = create_random_achievement(client, db_session, user.json(), jwt)
    user_achievement_data = {
        "user_id": user.json()["id"],
        "achievement_id": achievement["id"],
    }
    response = client.put("/achievements", json=user_achievement_data)
    assert response.status_code == 200
    response = client.put("/achievements", json=user_achievement_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "User already has this achievement"}


def test_create_user_achievement_invalid_user(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    achievement = create_random_achievement(client, db_session, user.json(), jwt)
    user_achievement_data = {
        "user_id": 1000,
        "achievement_id": achievement["id"],
    }

    response = client.put("/achievements", json=user_achievement_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_create_user_achievement_invalid_achievement(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    create_random_achievement(client, db_session, user.json(), jwt)
    user_achievement_data = {
        "user_id": user.json()["id"],
        "achievement_id": 1000,
    }

    response = client.put("/achievements", json=user_achievement_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Achievement not found"}
