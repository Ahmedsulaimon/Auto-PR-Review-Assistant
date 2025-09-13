FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the code
COPY services/review_engine /app/services/review_engine

ENV PYTHONPATH=/app
CMD ["python", "-u", "services/review_engine/engine.py"]