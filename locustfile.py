from locust import HttpUser, task, between
import json
from PIL import Image
import io
import random
import string
import time

class UserBehavior(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """ On start of the test, create a user and log them in """
        self.create_user()
        self.login_user()

    def random_string(self, length=8):
        """ Utility function to generate a random string """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def create_user(self):
        """ Create a new user """
        self.username = self.random_string()
        self.email = f"{self.username}@example.com"
        self.password = self.random_string(12)
        payload = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "date_of_birth": "2000-01-01"
        }
        self.client.post("/users", json=payload)

    @task
    def login_user(self):
        """ Log in the previously created user """
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.client.post("/users/login", json=payload)
        if response.status_code == 200:
            self.token = response.json()["jwt_token"]
            self.logged_in = True

    @task(2)
    def upload_profile_picture(self):
        """ Upload a profile picture, only after login """
        if hasattr(self, 'logged_in'):
            headers = {"Authorization": f"Bearer {self.token}"}
            image = Image.new("RGB", (100, 100), color=(73, 109, 137))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            files = {"profile_picture": ("test.jpg", buffer, "image/jpeg")}
            self.client.post("/users/profile_picture/upload", headers=headers, files=files)

    @task(3)
    def get_profile_picture(self):
        """ Retrieve the profile picture for the user """
        if hasattr(self, 'logged_in'):
            headers = {"Authorization": f"Bearer {self.token}"}
            time.sleep(7)  # Wait for 3 seconds before making the request
            self.client.get(f"/users/profile_picture/{self.username}", headers=headers)
