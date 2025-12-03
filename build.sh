#!/bin/bash
set -o errexit

python manage.py collectstatic --noinput
python manage.py migrate
