FROM python:3.7-alpine

RUN adduser -D simple_messenger

WORKDIR /home/simple_messenger

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN apk update && apk add --no-cache postgresql-dev gcc python3-dev musl-dev linux-headers libffi-dev make

RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY simple_messenger.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP simple_messenger.py

RUN chown -R simple_messenger:simple_messenger ./
USER simple_messenger

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
