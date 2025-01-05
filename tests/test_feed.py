from tests.test_users import create_random_user
from tests.test_quest import create_random_quest
from tests.test_users import create_and_login_user, create_random_image
from api import utils
import random
from io import BytesIO


def create_random_post(client, db_session, jwt):
    # Create a user quest first to get user_quest_id
    quest_id = create_random_quest(client, db_session, jwt).json()["id"]
    image = create_random_image(100, 100)

    # Prepare post data
    files = {"image": ("test.jpg", image, "image/png")}
    data = {
        "caption": f"Test Post {random.randint(1, 1000)}",
        "quest_id": str(quest_id),
    }

    # Make request
    response = client.post(
        "/posts", data=data, files=files, headers={"Authorization": f"Bearer {jwt}"}
    )

    assert response.status_code == 200
    return response


def test_read_posts(client, db_session):
    user, jwt = create_and_login_user(client, db_session)
    post = create_random_post(client, db_session, jwt)
    response = client.get("/feed")
    assert response.status_code == 200


def test_read_friends_posts(client, db_session):
    friend, friend_jwt = create_and_login_user(client, db_session)
    post = create_random_post(client, db_session, friend_jwt)
    user, jwt = create_and_login_user(client, db_session)
    make_friend = client.post(
        "/friends",
        json={"friend_id": friend.json()["id"]},
        headers={"Authorization": f"Bearer {jwt}"},
    )
    response = client.get("/feed/friends", headers={"Authorization": f"Bearer {jwt}"})
    assert response.status_code == 200
