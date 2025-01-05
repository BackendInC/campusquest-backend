import pytest
from io import BytesIO
from PIL import Image
from tests.test_users import create_and_login_user
from tests.test_quest import create_random_quest  # or however you create quests

def _create_test_image(size=(50, 50), color=(255, 0, 0)):
    """
    Helper to create a simple in-memory JPEG image
    using Pillow (PIL).
    """
    img = Image.new("RGB", size, color)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

@pytest.fixture
def test_image_file():
    """
    Pytest fixture that yields a small in-memory image
    suitable for upload.
    """
    image_buffer = _create_test_image()
    yield ("test_image.jpg", image_buffer, "image/jpeg")


@pytest.fixture
def create_post(client, db_session, test_image_file):
    """
    Fixture to create (and return) a post easily in tests.
    Usage:
        post_data = create_post(user_jwt=<JWT>, quest_id=<QuestID>)
    Returns the JSON response from the /posts endpoint.
    """
    def _create_post(user_jwt, quest_id, caption="Test Caption"):
        files = {
            "image": test_image_file,
        }
        data = {
            "caption": caption,
            "quest_id": str(quest_id),  # must be a string if using Form(...) on the server
        }

        resp = client.post(
            "/posts",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {user_jwt}"},
        )
        return resp
    return _create_post


# ------------------------------------------------------------------------------
# Test: Create a Post
# ------------------------------------------------------------------------------
def test_create_post(client, db_session, create_post):
    """
    Test creating a new post with an image, caption, and quest_id.
    """
    # 1. Create a user & login
    user_data, jwt_token = create_and_login_user(client, db_session)

    # 2. Create a quest (if your test_quests has a helper)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # 3. Attempt to create a post
    resp = create_post(jwt_token, quest_data["id"], caption="My first post!")
    assert resp.status_code == 200, f"Post creation failed: {resp.text}"
    json_resp = resp.json()

    # 4. Assert the post data
    assert json_resp["id"] is not None
    assert json_resp["user_id"] == user_data.json()["id"]
    assert json_resp["caption"] == "My first post!"
    assert json_resp["quest_id"] == quest_data["id"]
    # image_url may look like /posts/image/<post_id>
    assert "image_url" in json_resp


# ------------------------------------------------------------------------------
# Test: Read All Posts
# ------------------------------------------------------------------------------
def test_read_posts(client, db_session, create_post):
    """
    Test retrieving all posts.
    """
    # 1. Create user, login, and quest
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # 2. Create a couple of posts
    create_post(jwt_token, quest_data["id"], caption="Post #1")

    # 3. Retrieve all posts
    resp = client.get("/posts", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp.status_code == 200
    all_posts = resp.json()

    # 4. Check that at least the two posts we created are present
    captions = [p["caption"] for p in all_posts]
    assert "Post #1" in captions



# ------------------------------------------------------------------------------
# Test: Read Single Post
# ------------------------------------------------------------------------------
def test_read_single_post(client, db_session, create_post):
    """
    Test retrieving a single post by its ID.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "ReadSingle")
    post_id = resp_create.json()["id"]

    # Retrieve the post
    resp_get = client.get(f"/posts/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_get.status_code == 200, f"Could not read post {post_id}"
    post_data = resp_get.json()

    assert post_data["id"] == post_id
    assert post_data["caption"] == "ReadSingle"


# ------------------------------------------------------------------------------
# Test: Get Post Image
# ------------------------------------------------------------------------------
def test_get_post_image(client, db_session, create_post):
    """
    Test retrieving the raw image data of a post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "Pic")
    post_id = resp_create.json()["id"]

    # Retrieve the image
    resp_img = client.get(f"/posts/image/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_img.status_code == 200
    # The response should be bytes with media_type="image/jpeg"
    assert resp_img.headers["content-type"] == "image/jpeg"
    # We won't do an extensive test on image content, but we confirm we got data
    assert len(resp_img.content) > 0


# ------------------------------------------------------------------------------
# Test: Read All Posts by a User
# ------------------------------------------------------------------------------
def test_read_user_posts(client, db_session, create_post):
    """
    Test retrieving all posts made by a specific user.
    """
    # 1. Create user & quest
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # 2. Create two posts for user1
    create_post(jwt_token, quest_data["id"], caption="User Post #1")

    # 3. Retrieve those posts
    user_id = user_data.json()["id"]
    resp = client.get(f"/users/posts/{user_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp.status_code == 200
    posts_data = resp.json()
    assert len(posts_data) >= 1
    captions = [p["caption"] for p in posts_data]
    assert "User Post #1" in captions


# ------------------------------------------------------------------------------
# Test: Update a Post
# ------------------------------------------------------------------------------
def test_update_post(client, db_session, create_post):
    """
    Test updating the caption of an existing post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "Before update")
    post_id = resp_create.json()["id"]

    # Update it
    update_payload = {"caption": "After update"}
    resp_update = client.put(
        f"/posts/{post_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert resp_update.status_code == 200, resp_update.text
    updated_post = resp_update.json()
    assert updated_post["caption"] == "After update"


# ------------------------------------------------------------------------------
# Test: Delete a Post
# ------------------------------------------------------------------------------
def test_delete_post(client, db_session, create_post):
    """
    Test deleting a post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "To be deleted")
    post_id = resp_create.json()["id"]

    # Delete it
    resp_del = client.delete(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert resp_del.status_code == 200, f"Failed to delete post {post_id}"

    # Attempt to fetch the post again (should fail with 404 or similar)
    resp_check = client.get(f"/posts/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_check.status_code == 404, f"Deleted post {post_id} was still accessible."


# ------------------------------------------------------------------------------
# Test: Like and Unlike a Post
# ------------------------------------------------------------------------------
def test_toggle_like_post(client, db_session, create_post):
    """
    Test that a user can like and then unlike a post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "Like me!")
    post_id = resp_create.json()["id"]

    # Like the post
    resp_like = client.post(f"/posts/like/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_like.status_code == 200

    # Check user liked the post
    resp_check_like = client.get(f"/posts/like/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_check_like.status_code == 200
    assert resp_check_like.json() is True

    # Unlike the post (call /posts/like/{post_id} again toggles it off)
    resp_unlike = client.post(f"/posts/like/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_unlike.status_code == 200

    # Check like status again
    resp_check_like_2 = client.get(f"/posts/like/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_check_like_2.status_code == 200
    assert resp_check_like_2.json() is False


# ------------------------------------------------------------------------------
# Test: Dislike and Remove Dislike
# ------------------------------------------------------------------------------
def test_toggle_dislike_post(client, db_session, create_post):
    """
    Test that a user can dislike and then remove a dislike on a post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "Dislike me!")
    post_id = resp_create.json()["id"]

    # Dislike the post
    resp_dislike = client.post(f"/posts/dislike/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_dislike.status_code == 200

    # Check user disliked the post
    resp_check_dislike = client.get(f"/posts/dislike/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_check_dislike.status_code == 200
    assert resp_check_dislike.json() is True

    # Remove the dislike (call /posts/dislike/{post_id} again toggles it off)
    resp_remove_dislike = client.post(f"/posts/dislike/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_remove_dislike.status_code == 200

    # Check dislike status again
    resp_check_dislike_2 = client.get(f"/posts/dislike/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_check_dislike_2.status_code == 200
    assert resp_check_dislike_2.json() is False


# ------------------------------------------------------------------------------
# Test: Count Likes & Dislikes
# ------------------------------------------------------------------------------
def test_count_likes_and_dislikes(client, db_session, create_post):
    """
    Test counting likes and dislikes for a post.
    """
    user_data, jwt_token = create_and_login_user(client, db_session)
    quest_data = create_random_quest(client, db_session, jwt_token).json()

    # Create a post
    resp_create = create_post(jwt_token, quest_data["id"], "Count me!")
    post_id = resp_create.json()["id"]

    # Like the post
    client.post(f"/posts/like/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})

    # Check counts
    resp_likes = client.get(f"/posts/likes/count/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    resp_dislikes = client.get(f"/posts/dislikes/count/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_likes.status_code == 200
    assert resp_likes.json() == 1
    assert resp_dislikes.status_code == 200
    assert resp_dislikes.json() == 0

    # Dislike the post from the same user (this toggles off like, toggles on dislike)
    client.post(f"/posts/dislike/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})

    # Check counts again
    resp_likes_2 = client.get(f"/posts/likes/count/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    resp_dislikes_2 = client.get(f"/posts/dislikes/count/{post_id}", headers={"Authorization": f"Bearer {jwt_token}"})
    assert resp_likes_2.json() == 0
    assert resp_dislikes_2.json() == 1
