from tests.test_users import create_random_user
from tests.test_quest import create_random_quest
from tests.test_users import create_and_login_user
from api import utils
import random


def create_random_user_quest(client, db_session, jwt):
    quest = create_random_quest(client, db_session, jwt).json()
    user_quest = client.post(
        f"/quests/start/{quest['id']}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert user_quest.status_code == 200
    return user_quest


def test_create_user_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    user_quest = create_random_user_quest(client, db_session, jwt)
    print(user_quest.json())


def test_read_user_quests(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    user = user.json()
    user_quest = create_random_user_quest(client, db_session, jwt).json()
    response = client.get(f"/quests/user/{user['id']}")
    assert response.status_code == 200
    # todo solve the list issue
    assert response.json()[0]["id"] == user_quest["id"]


def test_complete_user_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    user_quest = create_random_user_quest(client, db_session, jwt).json()
    response = client.put(
        f"/quests/complete/{user_quest['id']}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Quest completed successfully"


def create_and_complete_user_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    user_quest = create_random_user_quest(client, db_session, jwt).json()
    response = client.put(
        f"/quests/complete/{user_quest['id']}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Quest completed successfully"
    return user_quest


def test_verify_user_quest(client, db_session):
    # the verifier
    verifier, jwt = create_and_login_user(client, db_session)
    user_quest = create_and_complete_user_quest(client, db_session)
    # validate the user quest
    response = client.post(
        f"/quest/verify/{user_quest['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Verification successful"
    assert response.json()["total_verifications"] == 1
