FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for caching
COPY services/review-engine/requirements.txt ./services/review-engine/requirements.txt
RUN pip install --no-cache-dir -r ./services/review-engine/requirements.txt

# Copy everything
COPY . .

# Start worker
CMD ["python", "-u", "services/review-engine/engine.py"]

