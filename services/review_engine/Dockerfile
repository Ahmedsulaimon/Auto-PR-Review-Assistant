FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the code
COPY . /app

ENV PYTHONPATH=/app
CMD ["python", "-u", "engine.py"]
