
FROM python:3.10-slim
WORKDIR /app

COPY services/review_engine/requirements.txt /app/services/review_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/review_engine/requirements.txt


# Copy repo root so imports like services.review_engine.* work if you prefer that layout
COPY . /app

ENV PYTHONPATH=/app
WORKDIR /app/services/review_engine

EXPOSE 8000

# uvicorn uses PORT env var on Render; fall back to 8000
CMD ["sh", "-c", "uvicorn engine:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
