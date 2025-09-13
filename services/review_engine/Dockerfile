# FROM python:3.10-slim

# WORKDIR /app

# # Copy requirements first
# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# # Copy the rest of the code
# COPY . /app

# ENV PYTHONPATH=/app
# CMD ["python", "-u", "engine.py"]
#dugging dockerfile for deployment


FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY services/review_engine/requirements.txt /app/services/review_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/review_engine/requirements.txt

# Copy the whole repo (so /services/... exists inside container)
COPY . /app

ENV PYTHONPATH=/app
WORKDIR /app/services/review_engine

CMD ["python", "-u", "engine.py"]
