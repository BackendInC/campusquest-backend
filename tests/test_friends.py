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