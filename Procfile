web: uvicorn server.api:app --host 0.0.0.0 --port $PORT
worker: celery -A core.queue.celery_app worker --loglevel=info
