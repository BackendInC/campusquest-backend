curl --location '3.95.204.226:8000/users' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe9",
    "email": "kizilboga20@yopmail.com",
    "password": "secretpass",
    "date_of_birth": "1940-10-10"
}'
