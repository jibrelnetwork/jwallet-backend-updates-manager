FROM python:3.7-alpine

RUN addgroup -S -g 1000 app \
 && adduser -S -u 1000 -G app -s /bin/sh -D app \
 && mkdir /app \
 && chown -R app:app /app

WORKDIR /app

COPY requirements.txt .

RUN set -x \
 && apk add --no-cache --virtual .build-deps \
        build-base \
        gcc \
        git \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn \
 && apk del --no-cache .build-deps \
 && rm -rf /var/cache/apk/*

COPY . .
RUN pip install --no-cache-dir --editable .

USER app
CMD ["gunicorn", "-c", "gunicorn-conf.py", "jwallet_updates.app:make_app"]
