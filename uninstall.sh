#!/bin/bash
docker stop simple_messenger
docker stop postgres-custom
docker rm simple_messenger
docker rm postgres-custom
docker image rm simple_messenger
docker volume rm DatabaseVolume
