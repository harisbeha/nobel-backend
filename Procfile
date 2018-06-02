# web: waitress-serve --expose-tracebacks --port=$PORT --channel-timeout=7200 --connection-limit=1000 --backlog=5000 --asyncore-use-poll --max-request-body-size=21474836480 --recv-bytes=1048576 base.wsgi:application
web: gunicorn base.wsgi:application --log-file out --timeout 1500 
beat: celery beat -A base
worker: celery worker -A base --without-gossip --without-mingle --loglevel=DEBUG -Ofair -c ${CONCURRENCY:-16}
release: ./manage.py migrate
