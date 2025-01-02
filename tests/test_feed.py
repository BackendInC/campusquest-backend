from tests.test_users import create_random_user
from tests.test_quest import create_random_quest
from tests.test_users import create_and_login_user
from api import utils
import random
from io import BytesIO


def create_random_post(client, db_session, jwt):
    # Create a user quest first to get user_quest_id
    quest_id = create_random_quest(client, db_session, jwt).json()["id"]

    # Prepare post data
    files = {
        'image': ('test.jpg', BytesIO(b"test image content"), 'image/jpeg')
    }
    data = {
        'caption': f"Test Post {random.randint(1, 1000)}",
        'quest_id': str(quest_id)
    }

    # Make request
    response = client.post(
        "/posts",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {jwt}"}
    )

    return response

def test_read_posts(client, db_session):
   user, jwt = create_and_login_user(client, db_session)
   post = create_random_post(client, db_session, jwt)
   response = client.get("/posts/feed").json()
   assert response.status_code == 200

