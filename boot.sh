#!/bin/sh
source venv/bin/activate
flask db upgrade
if [ -n "$ADD_TEST_USERS" ]; then
  flask add_test_users
fi

exec gunicorn -b :5000 --access-logfile - --error-logfile - -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 simple_messenger:app
