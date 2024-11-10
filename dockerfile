# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install netcat (or nc) for wait-for-it.sh
RUN apt-get update && apt-get install -y netcat-traditional

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt /app

RUN pip install -r /app/requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Define the command to run the FastAPI app using Uvicorn
CMD ["./wait-for.sh", "10.5.0.2:5432", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
