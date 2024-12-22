#!/bin/bash

pip install -r requirements.txt

docker compose -f compose.dev.yaml down
docker rm -f postgres-test >/dev/null 2>&1
docker run --name postgres-test -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=root -e POSTGRES_DB=backendinc -p 5432:5432 -d postgres

sleep 3
python3 -m pytest
