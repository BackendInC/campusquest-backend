# Name of your Python file
APP_FILE = app.py

# Default target to run the app locally with uvicorn
run:
	uvicorn $(APP_FILE:%.py=%):app --reload

# Build the Docker image
docker-build:
	docker build -t fastapi-hello-world .

# Run the Docker container
docker-run:
	@if [ $(shell docker ps -q -f name=fastapi-container) ]; then \
		echo "Container is already running."; \
	else \
		docker run -d --name fastapi-container -p 8000:8000 fastapi-hello-world; \
	fi

# Stop the Docker container
docker-stop:
	docker stop fastapi-container || echo "Container is not running."

# Remove the Docker container
docker-remove:
	docker rm fastapi-container || echo "Container does not exist."


