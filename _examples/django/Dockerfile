FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN SECRET_KEY=build-only-placeholder \
    DATABASE_URL=postgresql://build:build@127.0.0.1:1/build \
    ALLOWED_HOSTS=localhost CSRF_TRUSTED_ORIGINS=http://localhost \
    python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
