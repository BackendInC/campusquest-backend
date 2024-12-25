# test_users.py
import random
from api import utils
from PIL import Image
import numpy as np
import io


def create_user(client, db_session, user):
    response = client.post("/users", json=user)
    return response


def create_random_user(client, db_session):
    user_data = {
        "username": utils.get_random_string(10),
        "email": f"test_user_{random.randint(1, 1000)}@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    response = create_user(client, db_session, user_data)
    return response


def create_and_login_user(client, db_session):
    user_data = {
        "username": utils.get_random_string(10),
        "email": f"test_user_{random.randint(1, 1000)}@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    user_create_response = create_user(client, db_session, user_data)
    assert user_create_response.status_code == 200
    login_response = client.post(
        "/user/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )

    assert login_response.status_code == 200
    assert "jwt_token" in login_response.json()
    return user_create_response, login_response.json()["jwt_token"]


# Create a random image
def create_random_image(width, height, encoding="RGB", format="PNG"):
    # Generate random pixel values for an RGB image
    random_pixels = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    # Create a PIL image from the numpy array
    img = Image.fromarray(random_pixels, encoding)

    # Save the image to a BytesIO object
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)  # Reset the file pointer to the beginning

    return img_bytes


def test_create_user(client, db_session):
    response = create_random_user(client, db_session)

    # Assert
    assert response.status_code == 200


def test_create_duplicate_user(client, db_session):
    user_data = {
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "password",
        "date_of_birth": "2004-12-22",
    }

    response = create_user(client, db_session, user_data)

    assert response.status_code == 200

    # Create the same user again
    response = create_user(client, db_session, user_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "username or email already exists"}


def test_create_user_incorrect_params(client, db_session):
    user_data = {"username": "test_user", "email": "test_user@example.com"}

    response = create_user(client, db_session, user_data)

    assert response.status_code == 422


def test_login_user(client, db_session):
    user_create_response, jwt_token = create_and_login_user(client, db_session)

    assert jwt_token is not None


def test_user_upload_profile_picture(client, db_session):
    user_create_response, jwt_token = create_and_login_user(client, db_session)
    client.headers.update({"Authorization": f"Bearer {jwt_token}"})

    image_file = create_random_image(100, 100)

    response = client.post(
        "/user/profile_picture/upload",
        files={"profile_picture": ("test_image.png", image_file, "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Profile picture uploaded successfully"}


def test_user_upload_profile_picture_invalid_file(client, db_session):
    user_create_response, jwt_token = create_and_login_user(client, db_session)
    client.headers.update({"Authorization": f"Bearer {jwt_token}"})

    image_file = create_random_image(100, 100, "RGB", "TIFF")

    response = client.post(
        "/user/profile_picture/upload",
        files={"profile_picture": ("test_image.tiff", image_file, "image/tiff")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type"}


def test_user_upload_profile_picture_big_file(client, db_session):
    user_create_response, jwt_token = create_and_login_user(client, db_session)
    client.headers.update({"Authorization": f"Bearer {jwt_token}"})
    image_file = create_random_image(5000, 5000)

    response = client.post(
        "/user/profile_picture/upload",
        files={"profile_picture": ("test_image.png", image_file, "image/png")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File size too large"}


def test_user_get_profile_picture(client, db_session):
    user_create_response, jwt_token = create_and_login_user(client, db_session)
    client.headers.update({"Authorization": f"Bearer {jwt_token}"})

    image_file = create_random_image(100, 100, "RGB", "JPEG")
    response = client.post(
        "/user/profile_picture/upload",
        files={"profile_picture": ("test_image.jpeg", image_file, "image/jpeg")},
    )

    image_file.seek(0)

    assert response.status_code == 200

    # Get the profile
    response = client.get(
        f"/user/profile_picture/{user_create_response.json()['username']}"
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/jpeg"

    retrieved_image = Image.open(io.BytesIO(response.content))
    assert retrieved_image.size == (100, 100)
    assert retrieved_image.format == "JPEG"
    assert retrieved_image.mode == "RGB"
