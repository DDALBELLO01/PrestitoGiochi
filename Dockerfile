FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3002 \
    DATABASE_PATH=/app/instance/prestiti.db

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/instance \
    && chown app:app /app/instance

COPY --chown=app:app app.py forms.py models.py ISTRUZIONI.md ./
COPY --chown=app:app templates/ ./templates/
COPY --chown=app:app static/ ./static/

USER app

EXPOSE 3002

CMD ["gunicorn", "--bind", "0.0.0.0:3002", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
