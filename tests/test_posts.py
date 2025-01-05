from test_users import create_and_login_user, create_random_user, create_random_image
from test_quest import create_random_quest
import random
import db.models

# helper functions
def create_post(client, db_session):
    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    # create a random image
    image = create_random_image(100, 100)
    quest = create_random_quest(client, db_session, jwt).json()

    # create a post
    post = client.post(
        "/posts",
        data={
            "caption": "This is a test post",
            "quest_id": quest["id"],
        },
        files = {"image": ("test_image.png", image, "image/png")},
        headers={"Authorization": f"Bearer {jwt}"},
    )

    return post, quest, jwt

def create_posts(client, db_session):
    random_number = random.randint(1, 10)
    posts = []
    quests = []

    # create a user and log in
    user, jwt = create_and_login_user(client, db_session)

    for i in range(random_number):
        image = create_random_image(100, 100)
        quest = create_random_quest(client, db_session, jwt).json()

        # create a post
        post = client.post(
            "/posts",
            data={
                "caption": "This is a test post",
                "quest_id": quest["id"],
            },
            files = {"image": ("test_image.png", image, "image/png")},
            headers={"Authorization": f"Bearer {jwt}"},
        )

        posts.append(post.json())
        quests.append(quest)

    return posts, quests, jwt

def test_create_post(client, db_session):
    # create a post
    response, quest, jwt = create_post(client, db_session)

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert "id" in response_data
    assert "user_id" in response_data
    assert response_data["caption"] == "This is a test post"
    assert response_data["quest_id"] == quest["id"]
    assert response_data["image_url"].startswith("/posts/image/")

def test_get_posts(client, db_session):
    # create a posts
    posts, quests, jwt = create_posts(client, db_session)

    # get the posts
    response = client.get(
        "/posts",
        headers={"Authorization": f"Bearer {jwt}"}
    )
    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert len(response_data) >= len(posts)

    for post, quest in zip(posts, quests):
        assert any(
            response_post["caption"] == "This is a test post" and
            response_post["quest_id"] == quest["id"] and
            response_post["image_url"].startswith("/posts/image/")
            for response_post in response_data
        )

def test_get_post_by_ID(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # get the post
    response = client.get(f"/posts/{post['id']}")

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data["caption"] == "This is a test post"
    assert response_data["quest_id"] == quest["id"]
    assert response_data["image_url"].startswith("/posts/image/")

def test_get_post_by_user_ID(client, db_session):
    # create a post
    posts, quests, jwt = create_posts(client, db_session)

    post = posts[0]

    # get the post
    response = client.get(
        f"/users/posts/{post['user_id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert any(
        response_post["caption"] == "This is a test post" and
        response_post["quest_id"] == quests[i]["id"] and
        response_post["image_url"].startswith("/posts/image/")
        for i, response_post in enumerate(response_data)
    )

def test_get_post_image(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # get the post image
    response = client.get(f"/posts/image/{post['id']}")

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.content

    # verify response contains expected data
    assert response_data

def test_delete_post(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # delete the post
    response = client.delete(
        f"/posts/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data == {"detail": "Post and UserQuest deleted successfully"}


def test_like_post(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # like the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data['message'] == "Post liked successfully"


def test_unlike_post(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # like the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # unlike the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data['message'] == "Post unliked successfully"

def test_dislike_post(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # dislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data['message'] == "Post disliked successfully"


def test_undislike_post(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # dislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # undislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data['message'] == "Dislike removed successfully"

def test_check_user_like(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # like the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the user liked the post
    response = client.get(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data == True

def test_check_user_dislike(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # dislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the user disliked the post
    response = client.get(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data == True

def test_get_post_likedby(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # like the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # get the users who liked the post
    response = client.get(
        f"/posts/likedby/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert any(
        response_user["id"] == post["user_id"]
        for response_user in response_data
    )

def test_get_post_dislikedby(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # dislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # get the users who disliked the post
    response = client.get(
        f"/posts/dislikedby/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert any(
        response_user["id"] == post["user_id"]
        for response_user in response_data
   )


def test_get_likes_count(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # like the post
    response = client.post(
        f"/posts/like/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # get the likes count
    response = client.get(
        f"/posts/likes/count/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data == 1

def test_get_dislikes_count(client, db_session):
    # create a post
    post, quest, jwt = create_post(client, db_session)

    post = post.json()

    # dislike the post
    response = client.post(
        f"/posts/dislike/{post['id']}",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    # get the dislikes count
    response = client.get(
        f"/posts/dislikes/count/{post['id']}"
    )

    # check if the response status code is 200
    assert response.status_code == 200

    response_data = response.json()

    # verify response contains expected data
    assert response_data == 1