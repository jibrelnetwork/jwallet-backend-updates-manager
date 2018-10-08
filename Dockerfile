FROM python:3.7

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . /app
RUN pip install --no-cache-dir --editable .

ENTRYPOINT ["/app/run.sh"]