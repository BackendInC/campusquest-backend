curl --location 'localhost:8000/users/verification' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "user_id": 34,
    "code": 228774
}'
