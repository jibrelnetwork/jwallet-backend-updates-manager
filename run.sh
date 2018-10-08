#!/bin/bash

gunicorn --bind 0.0.0.0:80 jwallet_updates.app:make_app  --worker-class aiohttp.worker.GunicornWebWorker