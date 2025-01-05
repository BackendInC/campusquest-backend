<<<<<<< HEAD
from test_users import create_and_login_user, create_random_user
import random

#helper functions
def add_friend(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random user and get their info
    friend = create_random_user(client, db_session).json()

    # add the friend
    response = client.post(
        f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
    ) 

    return response, friend, jwt

def add_friends_random(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    #randomly choose number of friends to add
    random_number = random.randint(1, 10)

    #lists to store friends information and responses
    friends = []
    responses = []

    #create users and add them as friends
    for i in range(random_number):
        friend = create_random_user(client, db_session).json()

        response = client.post(
            f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {jwt}"}
        )

        if response.status_code == 200:
            friends.append(friend)

        responses.append(response)

    return friends, responses

def add_random_mutuals(client, db_session, tokens):
    #randomly choose number of friends to create
    random_number = random.randint(1, 10)

    #lists to store friends information and responses
    friends = []
    responses = []
    mutuals = []

    #create users
    for i in range(random_number):
        friend = create_random_user(client, db_session).json()
        friends.append(friend)

    added = [False] * len(friends)

    for token in tokens:
        for i, friend in enumerate(friends):
            rand_num = random.randint(1, 10)
            if rand_num % 2 == 0:
                response = client.post(
                    f"/friends/{friend['id']}", headers={"Authorization": f"Bearer {token}"}
                )
                responses.append(response)

                if token == tokens[0]:
                    added[i] = True
                elif added[i]:
                    mutuals.append(friend)

    
    return mutuals, responses

# test adding a friend
def test_add_friend(client, db_session):
    #add a friend
    response, friend, jwt = add_friend(client, db_session)

    assert response.status_code == 200
    assert response.json()["friend_data"]["friend_id"] == friend["id"]
    assert response.json()["friend_data"]["message"] == "Friend added successfully"


# test removing a friend
def test_remove_friend(client, db_session):
    #add a friend
    response, friend, jwt = add_friend(client, db_session)

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

    friends, responses = add_friends_random(client, db_session)


    # list the friends
    response = client.get("/friends", headers={"Authorization": f"Bearer {jwt}"})

    assert response.status_code == 200
 

# test checking if a user is a friend
def test_check_friend(client, db_session):
    response, friend, jwt = add_friend(client, db_session)

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

    tokens = [jwt1, jwt2]

    user1 = user1.json()
    user2 = user2.json()

    mutuals, responses = add_random_mutuals(client, db_session, tokens)

    # Now check mutual friends between user1 and user2
    response = client.get(
        f"/friends/mutual/{user2['id']}", headers={"Authorization": f"Bearer {jwt1}"}
    )

    # Assert the mutual friends response
    assert response.status_code == 200
    mutual_friends = response.json()

    # Assert that we expect 2 mutual friends
    assert len(mutual_friends) == len(mutuals)  # We expect 2 mutual friends (friend_2 and friend_3)

    # Verify the mutual friends' details
    for i in range(len(mutuals)):
        assert any(f['friend_id'] == mutuals[i]['id'] and f['username'] == mutuals[i]['username'] and f['profile_picture_url'] == f"/users/profile_picture/{mutuals[i]['username']}" for f in mutual_friends)
=======
import random
import pytest
from tests.test_users import create_and_login_user, create_random_user

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def add_friend(client, jwt, friend_id):
    """Helper to add a friend and return the response object."""
    response = client.post(
        f"/friends/{friend_id}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    return response

def remove_friend(client, jwt, friend_id):
    """Helper to remove a friend and return the response object."""
    response = client.delete(
        f"/friends/{friend_id}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    return response

def list_friends(client, jwt):
    """Helper to list friends and return the response object."""
    response = client.get(
        "/friends",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    return response

def check_friend(client, jwt, friend_id):
    """Helper to check if a user is a friend and return the response object."""
    response = client.get(
        f"/friends/{friend_id}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    return response

def get_mutual_friends(client, jwt, friend_id):
    """Helper to get mutual friends and return the response object."""
    response = client.get(
        f"/friends/mutuals/{friend_id}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    return response

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_add_friend(client, db_session):
    """
    Test that a user can add another user as a friend.
    """
    # Create and log in as user1
    user1, jwt1 = create_and_login_user(client, db_session)
    # Create another user (user2) for potential friendship
    user2_data = create_random_user(client, db_session).json()

    # Attempt to add user2 as a friend of user1
    response = add_friend(client, jwt1, user2_data["id"])
    assert response.status_code == 200, f"Failed to add friend. {response.text}"
    friend_info = response.json()
    assert friend_info["friend_id"] == user2_data["id"]
    assert friend_info["user_id"] == user1["id"]

def test_remove_friend(client, db_session):
    """
    Test that a user can remove another user from their friend list.
    """
    # Create and log in as user1
    user1, jwt1 = create_and_login_user(client, db_session)
    # Create user2, add user2 as friend, then remove them
    user2_data = create_random_user(client, db_session).json()
    add_friend_resp = add_friend(client, jwt1, user2_data["id"])
    assert add_friend_resp.status_code == 200

    # Now remove that friend
    remove_resp = remove_friend(client, jwt1, user2_data["id"])
    assert remove_resp.status_code == 200, f"Failed to remove friend. {remove_resp.text}"

def test_list_friends(client, db_session):
    """
    Test that a user can list all their friends.
    """
    # Create and log in as user1
    user1, jwt1 = create_and_login_user(client, db_session)
    # Create some random users to be friends
    user2_data = create_random_user(client, db_session).json()
    user3_data = create_random_user(client, db_session).json()

    # Add them as friends
    add_friend_resp_2 = add_friend(client, jwt1, user2_data["id"])
    add_friend_resp_3 = add_friend(client, jwt1, user3_data["id"])
    assert add_friend_resp_2.status_code == 200
    assert add_friend_resp_3.status_code == 200

    # List friends
    list_resp = list_friends(client, jwt1)
    assert list_resp.status_code == 200
    friends = list_resp.json()

    # Check both friends are present
    friend_ids = [f["friend_id"] for f in friends]
    assert user2_data["id"] in friend_ids
    assert user3_data["id"] in friend_ids

def test_check_friend(client, db_session):
    """
    Test checking if a specific user is a friend.
    """
    # Create and log in as user1
    user1, jwt1 = create_and_login_user(client, db_session)
    # Create user2 to be added as friend
    user2_data = create_random_user(client, db_session).json()

    # Add user2 as friend
    add_friend_resp = add_friend(client, jwt1, user2_data["id"])
    assert add_friend_resp.status_code == 200

    # Check if user2 is a friend
    check_resp = check_friend(client, jwt1, user2_data["id"])
    assert check_resp.status_code == 200
    friend_info = check_resp.json()
    assert friend_info["friend_id"] == user2_data["id"]

def test_get_mutual_friends(client, db_session):
    """
    Test getting mutual friends between two users.
    """
    # Create 3 users: user1, user2, user3
    user1, jwt1 = create_and_login_user(client, db_session)
    user2_data = create_random_user(client, db_session).json()
    user3_data = create_random_user(client, db_session).json()


    # user1 adds user2 and user3 as friends
    add_friend_resp_2 = add_friend(client, jwt1, user2_data["id"])
    add_friend_resp_3 = add_friend(client, jwt1, user3_data["id"])
    assert add_friend_resp_2.status_code == 200
    assert add_friend_resp_3.status_code == 200

    # Log in as user2
    # We assume create_and_login_user logs you in automatically,
    # or you can do a separate "login" if needed.
    _, jwt2 = create_and_login_user(client, db_session, user_id=user2_data["id"])

    # user2 adds user3 as friend => now user2 & user1 have a mutual friend: user3
    add_friend_resp_3_user2 = add_friend(client, jwt2, user3_data["id"])
    assert add_friend_resp_3_user2.status_code == 200

    # Now check mutual friends between user1 and user2
    mutual_resp = get_mutual_friends(client, jwt1, user2_data["id"])
    assert mutual_resp.status_code == 200
    mutuals = mutual_resp.json()

    # user3 should appear in mutual friends
    mutual_friend_ids = [m["friend_id"] for m in mutuals]
    assert user3_data["id"] in mutual_friend_ids
>>>>>>> tests
