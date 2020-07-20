#!/bin/bash
docker pull postgres:latest
docker build -t simple_messenger .
docker volume create DatabaseVolume

docker run --name postgres-custom -d \
  -e POSTGRES_USER=postgres_user \
  -e POSTGRES_PASSWORD=postgres_password \
  -e POSTGRES_DB=db_name \
  -v DatabaseVolume:/var/lib/postgresql/data \
  --restart always \
postgres:latest
  
docker run --name simple_messenger -d -p 8888:5000 \
  -e ADD_TEST_USERS=1 \
  -e MAIL_SERVER=$1 \
  -e MAIL_SENDER=$2 \
  -e MAIL_PASSWORD=$3 \
  --link postgres-custom:dbserver \
  -e DATABASE_URI=postgresql://postgres_user:postgres_password@dbserver/db_name \
  --restart always \
simple_messenger
