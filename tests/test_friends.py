from test_users import create_and_login_user, create_random_user


# test adding a friend
def test_add_friend(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random user and get their info
    friend = create_random_user(client, db_session).json()

    # add the friend
    response = client.post(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert response.status_code == 200
    assert response.json()["friend_data"]["friend_id"] == friend["id"]
    assert response.json()["friend_data"]["message"] == "Friend added successfully"


# test removing a friend
def test_remove_friend(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random user and get their info
    friend = create_random_user(client, db_session).json()

    # add the friend
    response = client.post(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )

    # remove the friend
    response = client.delete(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Friend removed successfully"}

# test listing friends
def test_list_friends(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random users and get their info
    friend_1 = create_random_user(client, db_session).json()
    friend_2 = create_random_user(client, db_session).json()
    friend_3 = create_random_user(client, db_session).json()

    # add the friends
    response = client.post(
        f"/friends/{friend_1['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )

    response = client.post(
        f"/friends/{friend_2['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )

    response = client.post(
        f"/friends/{friend_3['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )


    # list the friends
    response = client.get("/friends", headers={"Authorization": f"Bearer {jwt}"})
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert any(friend["friend_id"] == friend_1["id"] for friend in response.json())
    assert any(friend["friend_id"] == friend_2["id"] for friend in response.json())
    assert any(friend["friend_id"] == friend_3["id"] for friend in response.json())

# test checking if a user is a friend
def test_check_friend(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random user and get their info
    friend = create_random_user(client, db_session).json()

    # add the friend
    response = client.post(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the user is a friend
    response = client.get(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert response.status_code == 200
    assert response.json() == True


def test_mutual_friends(client, db_session):
    # Create two users and log in
    user1, jwt1 = create_and_login_user(client, db_session)
    user2, jwt2 = create_and_login_user(client, db_session)

    user1 = user1.json()
    user2 = user2.json()


    # Create random users and get their info
    friend_1 = create_random_user(client, db_session).json()
    friend_2 = create_random_user(client, db_session).json()
    friend_3 = create_random_user(client, db_session).json()

    # Add friend_1 and friend_2 for user1
    response = client.post(
        f"/friends/{friend_1['id']}", headers={"Authorization": f"Bearer {jwt1}"}
    )
    assert response.status_code == 200

    response = client.post(
        f"/friends/{friend_2['id']}", headers={"Authorization": f"Bearer {jwt1}"}
    )
    assert response.status_code == 200

    # Add friend_2 and friend_3 for user2
    response = client.post(
        f"/friends/{friend_2['id']}", headers={"Authorization": f"Bearer {jwt2}"}
    )
    assert response.status_code == 200

    response = client.post(
        f"/friends/{friend_3['id']}", headers={"Authorization": f"Bearer {jwt2}"}
    )
    assert response.status_code == 200

    # Add friend_3 for user1, making it a mutual friend between user1 and user2
    response = client.post(
        f"/friends/{friend_3['id']}", headers={"Authorization" : f"Bearer {jwt1}"}
    )
    assert response.status_code == 200

    # Now check mutual friends between user1 and user2
    response = client.get(
        f"/friends/mutual/{user2['id']}", headers={"Authorization": f"Bearer {jwt1}"}
    )

    # Assert the mutual friends response
    assert response.status_code == 200
    mutual_friends = response.json()

    # Assert that we expect 2 mutual friends
    assert len(mutual_friends) == 2  # We expect 2 mutual friends (friend_2 and friend_3)

    # Verify the mutual friends' details
    assert any(f['friend_id'] == friend_2['id'] and f['username'] == friend_2['username'] and f['profile_picture_url'] == f"/users/profile_picture/{friend_2['username']}" for f in mutual_friends)
    assert any(f['friend_id'] == friend_3['id'] and f['username'] == friend_3['username'] and f['profile_picture_url'] == f"/users/profile_picture/{friend_3['username']}" for f in mutual_friends)