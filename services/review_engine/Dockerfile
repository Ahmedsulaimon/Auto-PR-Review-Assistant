FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for caching
COPY services/review_engine/requirements.txt /app/services/review_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/review_engine/requirements.txt

# Copy the rest of the code
COPY . .

ENV PYTHONPATH=/app
CMD ["python", "-u", "services/review_engine/engine.py"]
