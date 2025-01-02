curl --location '3.95.204.226:8000/users/login' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe5",
    "password": "secretpass"
}'
