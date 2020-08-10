#!/bin/sh
source venv/bin/activate
exec celery -A simple_messenger.celery worker
