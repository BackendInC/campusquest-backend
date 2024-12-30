curl --location 'localhost:8000/users/verify' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "user_id": 68,
    "code": 373087
}'
