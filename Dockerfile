FROM python:3.10-alpine

RUN apk update && \
    apk add bash openssl curl tzdata && \
    cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime

RUN mkdir -p /data/app

COPY cloudflare /data/app/cloudflare
COPY requirements.txt /data/app/

WORKDIR /data/app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1

VOLUME /data/env

CMD [ "python", "-m", "cloudflare.main" ]
