#!/bin/bash
docker build -t simple_messenger:latest .
docker volume create DatabaseVolume

docker run --name redis-custom -d \
  --restart always \
redis:latest

docker run --name postgres-custom -d \
  -e POSTGRES_USER=postgres_user \
  -e POSTGRES_PASSWORD=postgres_password \
  -e POSTGRES_DB=db_name \
  -v DatabaseVolume:/var/lib/postgresql/data \
  --restart always \
postgres:latest

docker run --name celery-worker -d \
  --entrypoint "./start_celery_worker.sh" \
  --link redis-custom:redis-server \
  -e CELERY_BROKER_URL=redis://redis-server/0 \
  -e MAIL_SERVER=$1 \
  -e MAIL_SENDER=$2 \
  -e MAIL_PASSWORD=$3 \
  -e MAIL_PORT=${4:-587} \
  --restart always \
simple_messenger:latest

docker run --name simple-messenger -d -p 8888:5000 \
  -e ADD_TEST_USERS=1 \
  -e MAIL_SERVER=$1 \
  -e MAIL_SENDER=$2 \
  -e MAIL_PASSWORD=$3 \
  -e MAIL_PORT=${4:-587} \
  --link celery-worker \
  --link postgres-custom:db-server \
  -e DATABASE_URI=postgresql://postgres_user:postgres_password@db-server/db_name \
  --link redis-custom:redis-server \
  -e CELERY_BROKER_URL=redis://redis-server/0 \
  --restart always \
simple_messenger:latest

