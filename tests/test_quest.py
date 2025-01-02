from tests.test_users import create_random_user
from tests.test_users import create_and_login_user
from api import utils
import random

# TODO add admin functionality


def create_random_quest(client, db_session, jwt):
    quest = client.post(
        "/quests",
        json={
            "name": f"quest name {random.randint(1, 1000)}",
            "description": "Test Quest",
            "location_long": random.uniform(-180, 180),
            "location_lat": random.uniform(-90, 90),
            "points": random.randint(1, 100),
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt}"},
    )

    assert quest.status_code == 200

    return quest


def test_create_quest(client, db_session):

    user, jwt = create_and_login_user(client, db_session)
    quest = create_random_quest(client, db_session, jwt)
    assert quest.status_code == 200


def test_get_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    quest = create_random_quest(client, db_session, jwt).json()

    response = client.get(f"/quests/{quest['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == quest["name"]


def test_non_admin_quest_create(client, db_session):
    assert True == True
    # TODO: Implement this test ADD ADMIN FUNC.


def test_delete_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    quest = create_random_quest(client, db_session, jwt).json()
    response = client.delete(f"/quests/{quest['id']}")
    assert response.status_code == 204


def test_update_quest(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    quest = create_random_quest(client, db_session, jwt).json()

    response = client.put(
        f"/quests/{quest['id']}",
        json={
            "name": "Updated Quest",
            "description": "Updated Description",
            "location_long": 2.0,
            "location_lat": 2.0,
            "points": 20,
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Quest"
