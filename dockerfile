# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install netcat (or nc) for wait-for-it.sh
RUN apt-get update && apt-get install -y netcat-traditional

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
RUN ls;

RUN pip install -r requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Define the command to run the FastAPI app using Uvicorn
CMD ["./wait-for.sh", "10.5.0.2:5432", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
