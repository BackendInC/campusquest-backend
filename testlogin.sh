curl --location 'localhost:8000/user/login' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe4",
    "password": "secretpass"
}'
