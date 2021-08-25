FROM python:3.8.7-slim-buster
MAINTAINER youngha.park <dndnjdnjdnjd@gmail.com>

USER root

RUN apt-get -yqq update && apt-get -yqq upgrade && apt-get -yqq dist-upgrade
RUN apt-get -yqq install --no-install-recommends \
        $buildDeps \
        freetds-bin \
        build-essential \
        default-libmysqlclient-dev \
        apt-utils \
        curl \
        rsync \
        netcat \
        locales \
        python-dev

# add user
RUN useradd -rm -s /bin/bash -d /app django

# user name
USER django

WORKDIR /app

# python env
ENV PIP_DEFAULT_TIMEOUT=50000
ENV PATH=${PATH}:/app/.local/bin
ENV PYTHONPATH=/app/.local/lib/python3.8/site-packages:/app/src

# django env
ENV DJANGO_SECRET_KEY=pJ|gIytVJ8xd;rJWg3j7/+4@QAph)xj|lC<5_1WFnpO$Zjv4*C

RUN pip install --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# working directory: /app/src
WORKDIR /app/src

EXPOSE 8000

CMD ["gunicorn3", "app.wsgi", "-b", "0.0.0.0:8000"]
