# Name of your Python file
APP_FILE = app.py

# Default target to run the app locally with uvicorn
run:
	uvicorn $(APP_FILE:%.py=%):app --reload

docker-build:
	docker compose build

# Run the Docker container
docker-run:
	docker compose up

# Stop the Docker container
docker-stop:
	docker compose down
