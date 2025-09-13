
#dugging dockerfile for deployment


# FROM python:3.10-slim

# WORKDIR /app

# # Copy requirements first
# COPY services/review_engine/requirements.txt /app/services/review_engine/requirements.txt
# RUN pip install --no-cache-dir -r /app/services/review_engine/requirements.txt

# # Copy the whole repo (so /services/... exists inside container)
# COPY . /app

# ENV PYTHONPATH=/app
# WORKDIR /app/services/review_engine

# CMD ["python", "-u", "engine.py"]


FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy repo root so imports like services.review_engine.* work if you prefer that layout
COPY .. /app

ENV PYTHONPATH=/app
EXPOSE 8000

# uvicorn uses PORT env var on Render; fall back to 8000
CMD ["sh", "-c", "uvicorn services.review_engine.engine:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
