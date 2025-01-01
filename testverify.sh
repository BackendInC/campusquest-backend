curl --location 'localhost:8000/users/verify' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe5",
    "code": 222459 
}'
