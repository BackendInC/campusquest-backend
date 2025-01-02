curl --location '3.95.204.226:8000/users/verify' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe5",
    "code": 257584 
}'
