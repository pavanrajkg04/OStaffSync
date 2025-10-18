# Use official Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install -r requirements.txt

# Build Reflex app
RUN uv run reflex init

# Optional: upgrade Reflex to latest stable
RUN uv pip install reflex --upgrade

# Expose default Reflex port
EXPOSE 3000

# Start Reflex production server
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
