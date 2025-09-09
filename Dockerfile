# System Image, using python 3.11, keep it like this, change only if conflicts occur
FROM python:3.11-slim

# Author is Subhanshu Dwivedi
LABEL authors="Kami"

WORKDIR /app

# System Dependencies if needed, add more
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Running command to install all requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads static/outputs

# Exposed to port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

# Run your app.py
CMD ["python", "app.py"]
