FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for caching
COPY services/review_engine/requirements.txt ./services/review_engine/requirements.txt
RUN pip install --no-cache-dir -r ./services/review_engine/requirements.txt

# Copy everything
COPY . .

# Start worker
CMD ["python", "-u", "services/review_engine/engine.py"]
