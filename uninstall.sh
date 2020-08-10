#!/bin/bash
docker stop simple-messenger
docker stop celery-worker
docker stop postgres-custom
docker stop redis-custom
docker rm simple-messenger
docker rm celery-worker
docker rm postgres-custom
docker rm redis-custom
docker image rm simple_messenger
docker volume rm DatabaseVolume
