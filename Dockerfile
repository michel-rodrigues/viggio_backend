FROM python:3.6-alpine3.10

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add --no-cache postgresql-dev \
    && pip install --upgrade pip \
    && pip install ipdb pytest supervisor \
    && apk del build-deps \
    && apk add --no-cache bash \
    && apk add --update --no-cache netcat-openbsd \
    && apk add --no-cache bind-tools \
    && apk add --no-cache build-base \
    && apk add --no-cache jpeg-dev \
    && apk add --no-cache zlib-dev \
    && apk add --no-cache ffmpeg

COPY ./app/requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

COPY ./app /usr/src/app/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
