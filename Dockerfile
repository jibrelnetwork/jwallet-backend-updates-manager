FROM python:3.7-alpine

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
