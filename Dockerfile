FROM python:3.11.5-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY reqs.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r reqs.txt

COPY . .

RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "Waiting for PostgreSQL..."' >> /app/start.sh && \
    echo 'while ! nc -z db 5432; do' >> /app/start.sh && \
    echo '  sleep 0.1' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo 'echo "PostgreSQL started"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "Running database migrations..."' >> /app/start.sh && \
    echo 'alembic revision --autogenerate -m "First"' >> /app/start.sh && \
    echo 'alembic upgrade head' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "Starting application..."' >> /app/start.sh && \
    echo 'uvicorn app.main:app --host 0.0.0.0 --port 8080' >> /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]