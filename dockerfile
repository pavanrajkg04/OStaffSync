# Use Python 3.12 slim as base (matches your traceback)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies: curl (for downloading Bun), unzip (to extract it)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bun (Reflex will use this instead of trying to install it at runtime)
RUN curl -fsSL https://bun.sh/install | bash

# Add Bun to PATH
ENV PATH="/root/.bun/bin:${PATH}"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install reflex --upgrade

# Copy the rest of your app
COPY . .

# Build the app (optional but recommended for prod)
RUN reflex export --no-zip

# Expose backend port
EXPOSE 3000 8000

# Run in production mode
CMD ["reflex", "run", "--env", "prod"]