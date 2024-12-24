#!/bin/bash

echo "Installing requirements..."
pip install -r requirements.txt >/dev/null 2>&1

docker compose -f compose.dev.yaml down
docker rm -f postgres-test >/dev/null 2>&1
docker run --name postgres-test -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=root -e POSTGRES_DB=backendinc -p 5432:5432 -d postgres

echo "Waiting for postgres to start..."
sleep 3

export TEST=1

echo "Running tests..."
python3 -m pytest -v -s
