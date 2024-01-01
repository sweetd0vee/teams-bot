#!/usr/bin/env bash

gunicorn app:get_web_app -b 0.0.0.0:80 --worker-class aiohttp.GunicornWebWorker
