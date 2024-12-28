#!/bin/bash

echo "Installing requirements..."
pip install -r requirements.txt >/dev/null 2>&1

docker compose -f compose.dev.yaml down
docker rm -f postgres-test >/dev/null 2>&1
docker run --name postgres-test -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=root -e POSTGRES_DB=backendinc -p 5432:5432 -d postgres

echo "Waiting for postgres to start..."
sleep 3

export TEST=1
export DATABASE_URL=postgresql://root:1234@localhost:5432/backendinc

# if there is a command argument that run that test
if [ $# -eq 1 ]; then
    echo "Running tests in $1..."
    python3 -m pytest $1 --cov --cov-report=html:coverage_re -v -s
else
    echo "Running all tests..."
    python3 -m pytest --cov --cov-report=html:coverage_re -v -s
fi
