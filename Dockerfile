# TODO: revert to latest image when issue will be fixed
# see: https://github.com/pypa/pip/issues/6197
# FROM python:3.7-alpine
FROM python@sha256:abc2a66d8ce0ddf14b1d51d4c1fe83f21059fa1c4952c02116cb9fd8d5cfd5c4


RUN addgroup -S -g 1000 app \
 && adduser -S -u 1000 -G app -s /bin/sh -D app \
 && mkdir /app \
 && chown -R app:app /app \
 && apk add --no-cache \
        git \
 && rm -rf /var/cache/apk/*
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn

COPY . .
RUN pip install --no-cache-dir --editable .

USER app
CMD ["gunicorn", "-c", "gunicorn-conf.py", "jwallet_updates.app:make_app"]
