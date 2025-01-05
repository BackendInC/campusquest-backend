curl --location 'localhost:8000/users' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "john-doe4",
    "email": "kenanbanda2004@gmail.com",
    "password": "secretpass",
    "date_of_birth": "1940-10-10"
}'
