release: python manage.py migrate
web: gunicorn web.wsgi --log-file -
worker: REMAP_SIGTERM=SIGQUIT celery worker -A web -E --loglevel=info --without-gossip --without-mingle --without-heartbeat --max-tasks-per-child 15 --concurrency=3 -O fair