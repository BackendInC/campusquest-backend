from tests.test_users import create_random_user
# TODO add admin functionality
def login(client, db_session, user):
    response = client.post("/user/login", json={
        "username": user["username"],
        "password": "password"
    })
    return response.json()

def test_create_quest(client, db_session):
    user = create_random_user(client, db_session).json()
    print(user)
    jwt = login(client, db_session, user)
    quest = client.post(
        "/quests",
        json={
            "name": "Test Quest",
            "description": "Test Description",
            "location_long": 1.0,
            "location_lat": 1.0,
            "points": 10,
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt['jwt_token']}"},
    )

    assert quest.status_code == 200

def test_get_quest(client, db_session):
    user = create_random_user(client, db_session).json()
    jwt = login(client, db_session, user)
    quest = client.post(
        "/quests",
        json={
            "name": "Test Quest",
            "description": "Test Description",
            "location_long": 1.0,
            "location_lat": 1.0,
            "points": 10,
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt['jwt_token']}"},
    ).json()

    print(quest)

    response = client.get(f"/quests/{quest['id']}")
    print(response.json())
    assert response.status_code == 200
    assert response.json()["name"] == "Test Quest"

def test_non_admin_quest_create(client, db_session):
    assert True == True
    # TODO: Implement this test ADD ADMIN FUNC.

def test_delete_quest(client, db_session):
    user = create_random_user(client, db_session).json()
    jwt = login(client, db_session, user)
    quest = client.post(
        "/quests",
        json={
            "name": "Test Quest",
            "description": "Test Description",
            "location_long": 1.0,
            "location_lat": 1.0,
            "points": 10,
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt['jwt_token']}"},
    ).json()

    response = client.delete(f"/quests/{quest['id']}")
    assert response.status_code == 204

def test_update_quest(client, db_session):
    user = create_random_user(client, db_session).json()
    jwt = login(client, db_session, user)
    quest = client.post(
        "/quests",
        json={
            "name": "Test Quest",
            "description": "Test Description",
            "location_long": 1.0,
            "location_lat": 1.0,
            "points": 10,
            "start_date": "2022-01-01",
            "end_date": "2022-01-02",
            "image": "image",
        },
        headers={"Authorization": f"Bearer {jwt['jwt_token']}"},
    ).json()

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
        headers={"Authorization": f"Bearer {jwt['jwt_token']}",
    })

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Quest"

