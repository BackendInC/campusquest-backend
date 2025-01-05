from locust import HttpUser, task, between
import json
from PIL import Image
import io
import random
import string
import time
from datetime import datetime, timezone


# Shared user pool to store credentials
class UserPool:
    _users = []

    @classmethod
    def add_user(cls, username, password, token=None, user_id=None):
        cls._users.append({
            "username": username,
            "password": password,
            "token": token,
            "user_id": user_id
        })

    @classmethod
    def get_random_user(cls):
        return random.choice(cls._users) if cls._users else None


class UserBehavior(HttpUser):
    wait_time = between(1, 5)

    def random_string(self, length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def on_start(self):
        self.create_user()
        self.login_user()

    def create_user(self):
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
        # Add user to the shared pool
        UserPool.add_user(self.username, self.password)

    @task
    def login_user(self):
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.client.post("/users/login", json=payload)
        if response.status_code == 200:
            self.token = response.json()["jwt_token"]
            self.logged_in = True
            # Update token in user pool
            UserPool.add_user(self.username, self.password, self.token)

    @task(2)
    def upload_profile_picture(self):
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
        if hasattr(self, 'logged_in'):
            headers = {"Authorization": f"Bearer {self.token}"}
            time.sleep(7)
            self.client.get(f"/users/profile_picture/{self.username}", headers=headers)

    tasks = {login_user: 1, upload_profile_picture: 2, get_profile_picture: 3}


class QuestBehavior(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.login_existing_user()
        self.quest_ids = []  # Store created quest IDs

    def login_existing_user(self):
        user = UserPool.get_random_user()
        if user:
            self.username = user["username"]
            self.token = user["token"]
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            print("No users available in pool")

    @task(2)
    def read_quests(self):
        """Read all quests and store their IDs"""
        if hasattr(self, 'headers'):
            response = self.client.get("/quests", headers=self.headers)
            if response.status_code == 200:
                # Store quest IDs from the response
                quests = response.json()
                self.quest_ids = [quest["id"] for quest in quests]

    @task(1)
    def create_quest(self):
        """Create a new quest"""
        if hasattr(self, 'headers'):
            quest_data = {
                "name": f"New Adventure {self.random_string(4)}",
                "description": "Discover the hidden treasures.",
                "location_long": round(random.uniform(34.0, 35.0), 4),
                "location_lat": round(random.uniform(-118.0, -119.0), 4),
                "start_date": str(datetime.now(timezone.utc).date()),
                "end_date": str(datetime.now(timezone.utc).date()),
                "points": random.randint(50, 200),
                "image": "base64EncodedImageString"
            }
            response = self.client.post("/quests", json=quest_data, headers=self.headers)
            if response.status_code == 200:
                new_quest_id = response.json().get("id")
                if new_quest_id:
                    self.quest_ids.append(new_quest_id)

    @task(1)
    def read_specific_quest(self):
        """Read a specific quest"""
        if hasattr(self, 'headers') and self.quest_ids:
            quest_id = random.choice(self.quest_ids)
            self.client.get(f"/quests/{quest_id}", headers=self.headers)
        else:
            # If no quests exist, try to read all quests first
            self.read_quests()

    @task(1)
    def update_quest(self):
        """Update a specific quest"""
        if hasattr(self, 'headers') and self.quest_ids:
            quest_id = random.choice(self.quest_ids)
            quest_data = {
                "name": f"Updated Adventure {self.random_string(4)}",
                "description": "Explore the new world.",
                "location_long": round(random.uniform(34.0, 35.0), 4),
                "location_lat": round(random.uniform(-118.0, -119.0), 4),
                "start_date": str(datetime.now(timezone.utc).date()),
                "end_date": str(datetime.now(timezone.utc).date()),
                "points": random.randint(100, 250),
                "image": "base64EncodedImageString"
            }
            self.client.put(f"/quests/{quest_id}", json=quest_data, headers=self.headers)

    @task(1)
    def delete_quest(self):
        """Delete a specific quest"""
        if hasattr(self, 'headers') and self.quest_ids:
            quest_id = random.choice(self.quest_ids)
            response = self.client.delete(f"/quests/{quest_id}", headers=self.headers)
            if response.status_code == 200:
                self.quest_ids.remove(quest_id)

    def random_string(self, length=8):
        """Generate a random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    tasks = {read_quests: 2, create_quest: 1, read_specific_quest: 1, update_quest: 1, delete_quest: 1}


class AchievementBehavior(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.login_existing_user()

    def login_existing_user(self):
        user = UserPool.get_random_user()
        if user:
            self.username = user["username"]
            self.token = user["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print("No users available in pool")

    @task
    def read_achievements(self):
        if hasattr(self, 'headers'):
            self.client.get("/achievements", headers=self.headers)

    @task
    def create_achievement(self):
        if hasattr(self, 'headers'):
            achievement_data = {
                "description": "Complete all modules",
                "award_tokens": 50
            }
            self.client.post("/achievements", json=achievement_data, headers=self.headers)

    @task
    def read_user_achievements(self):
        if hasattr(self, 'headers'):
            self.client.get(f"/achievements/user/{self.username}", headers=self.headers)

    tasks = {read_achievements: 2, create_achievement: 1, read_user_achievements: 1}


class PostBehavior(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.login_existing_user()
        self.post_ids = []  # Store created post IDs for later use

    def login_existing_user(self):
        user = UserPool.get_random_user()
        if user:
            self.username = user["username"]
            self.token = user["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print("No users available in pool")

    def create_test_image(self):
        """Create a test image for post creation"""
        image = Image.new("RGB", (100, 100), color=(random.randint(0, 255),
                                                    random.randint(0, 255),
                                                    random.randint(0, 255)))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer

    @task(2)
    def create_post(self):
        """Create a new post with an image"""
        if hasattr(self, 'headers'):
            image_buffer = self.create_test_image()
            files = {
                "image": ("test.jpg", image_buffer, "image/jpeg")
            }
            data = {
                "caption": f"Test post created at {datetime.now(timezone.utc)}",
                "quest_id": random.randint(1, 5)  # Assuming quest IDs 1-5 exist
            }
            try:
                response = self.client.post("/posts",
                                            headers=self.headers,
                                            data=data,
                                            files=files)
                if response.status_code == 200:
                    post_data = response.json()
                    if post_data and "id" in post_data:
                        self.post_ids.append(post_data["id"])
            except Exception as e:
                print(f"Failed to create post: {str(e)}")

    @task(3)
    def read_posts(self):
        """Read all posts"""
        if hasattr(self, 'headers'):
            try:
                # Use the image URL endpoint instead of base64 encoded images
                response = self.client.get("/posts", headers=self.headers,
                                           catch_response=True)
                if response.status_code == 200:
                    posts = response.json()
                    # Update post_ids list with valid post IDs
                    self.post_ids = [post["id"] for post in posts if "id" in post]
                    response.success()
                else:
                    response.failure(f"Failed to read posts: {response.status_code}")
            except Exception as e:
                print(f"Error reading posts: {str(e)}")

    @task(1)
    def read_specific_post(self):
        """Read a specific post"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            try:
                self.client.get(f"/posts/{post_id}", headers=self.headers)
            except Exception as e:
                print(f"Error reading post {post_id}: {str(e)}")

    @task(1)
    def update_post(self):
        """Update a post's caption"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            data = {
                "caption": f"Updated caption at {datetime.now(timezone.utc)}"
            }
            try:
                self.client.put(f"/posts/{post_id}",
                                headers=self.headers,
                                json=data)
            except Exception as e:
                print(f"Error updating post {post_id}: {str(e)}")

    @task(1)
    def like_unlike_post(self):
        """Toggle like on a post"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            try:
                self.client.post(f"/posts/{post_id}/like", headers=self.headers)
            except Exception as e:
                print(f"Error toggling like on post {post_id}: {str(e)}")

    @task(2)
    def add_comment(self):
        """Add a comment to a post"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            data = {
                "content": f"Test comment at {datetime.now(timezone.utc)}"
            }
            try:
                self.client.post(f"/posts/{post_id}/comment",
                                 headers=self.headers,
                                 json=data)
            except Exception as e:
                print(f"Error adding comment to post {post_id}: {str(e)}")

    @task(3)
    def read_comments(self):
        """Read comments on a post"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            try:
                self.client.get(f"/posts/{post_id}/comments", headers=self.headers)
            except Exception as e:
                print(f"Error reading comments for post {post_id}: {str(e)}")

    @task(1)
    def get_post_image(self):
        """Retrieve a post's image"""
        if hasattr(self, 'headers') and self.post_ids:
            post_id = random.choice(self.post_ids)
            try:
                self.client.get(f"/posts/image/{post_id}", headers=self.headers)
            except Exception as e:
                print(f"Error getting image for post {post_id}: {str(e)}")

    tasks = {
        read_posts: 3,
        create_post: 2,
        read_specific_post: 1,
        update_post: 1,
        like_unlike_post: 1,
        add_comment: 2,
        read_comments: 3,
        get_post_image: 1
    }

#
# class FriendBehavior(HttpUser):
#     wait_time = between(1, 5)
#
#     def on_start(self):
#         """Ensure user is logged in before proceeding with friend-related tasks."""
#         self.login_existing_user()
#
#     def login_existing_user(self):
#         """Attempt to login with a user from the shared pool."""
#         user = UserPool.get_random_user()
#         if user and user["token"]:
#             self.username = user["username"]
#             self.token = user["token"]
#
#             # Get user ID from profile endpoint
#             headers = {'Authorization': f'Bearer {self.token}'}
#             profile_response = self.client.get("/users/profile", headers=headers)
#
#             if profile_response.ok:
#                 self.user_id = profile_response.json().get("id")
#                 self.headers = headers
#                 self.logged_in = True
#
#                 # Update user pool with user_id
#                 UserPool.add_user(self.username, user["password"], self.token, self.user_id)
#             else:
#                 print("Failed to get user profile")
#                 self.create_and_login_user()
#         else:
#             print("No valid user in pool, attempting to login anew.")
#             self.create_and_login_user()
#
#     def create_and_login_user(self):
#         """Create a new user and login to generate a token."""
#         username = f"user_{random.randint(1000, 9999)}"
#         password = "password123"  # Made password more secure
#         payload = {
#             "username": username,
#             "password": password,
#             "email": f"{username}@example.com",
#             "date_of_birth": "1990-01-01"
#         }
#
#         # Create user
#         create_resp = self.client.post("/users", json=payload)
#         if create_resp.ok:
#             # Login user
#             login_resp = self.client.post("/users/login", json={"username": username, "password": password})
#             if login_resp.ok:
#                 self.token = login_resp.json().get("jwt_token")
#                 self.headers = {'Authorization': f'Bearer {self.token}'}
#
#                 # Get user ID from profile
#                 profile_resp = self.client.get("/users/profile", headers=self.headers)
#                 if profile_resp.ok:
#                     self.user_id = profile_resp.json().get("id")
#                     UserPool.add_user(username, password, self.token, self.user_id)
#                     self.logged_in = True
#                     self.username = username
#                 else:
#                     print("Failed to get user profile for new user")
#             else:
#                 print(f"Failed to login newly created user {username}")
#         else:
#             print(f"Failed to create user {username}")
#
#     @task(3)
#     def add_friend(self):
#         """Attempt to add a friend if logged in."""
#         if hasattr(self, 'logged_in') and hasattr(self, 'user_id'):
#             potential_friend = UserPool.get_random_user()
#             if (potential_friend and
#                     potential_friend.get("user_id") and
#                     potential_friend["user_id"] != self.user_id):
#                 try:
#                     self.client.post(
#                         "/friends",
#                         json={"friend_id": potential_friend["user_id"]},
#                         headers=self.headers
#                     )
#                 except Exception as e:
#                     print(f"Error adding friend: {str(e)}")
#
#     @task(5)
#     def list_friends(self):
#         """List all friends of the current user."""
#         if hasattr(self, 'logged_in'):
#             try:
#                 response = self.client.get("/friends", headers=self.headers)
#                 if response.ok:
#                     self.friends = response.json()
#             except Exception as e:
#                 print(f"Error listing friends: {str(e)}")
#
#     @task(1)
#     def remove_friend(self):
#         """Remove a friend from the current user's friend list."""
#         if hasattr(self, 'logged_in') and hasattr(self, 'friends'):
#             try:
#                 # Get random friend from actual friend list
#                 if self.friends:
#                     friend = random.choice(self.friends)
#                     friend_id = friend.get("id")
#                     if friend_id:
#                         self.client.delete(f"/friends/{friend_id}", headers=self.headers)
#             except Exception as e:
#                 print(f"Error removing friend: {str(e)}")
#
#     tasks = {add_friend: 3, list_friends: 5, remove_friend: 1}