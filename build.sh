#!/bin/bash
# Production startup script

# Activate virtual environment
source venv/bin/activate

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn tarla.wsgi:application --config gunicorn.conf.py