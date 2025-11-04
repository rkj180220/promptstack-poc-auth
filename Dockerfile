FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Prisma schema first
COPY prisma ./prisma

# Generate Prisma client (must be done before copying app code)
RUN prisma generate

# Copy application code
COPY . .

# Create a startup script that runs migrations then starts the server
RUN echo '#!/bin/bash\nprisma db push --skip-generate\nuvicorn app.main:app --host 0.0.0.0 --port 8001' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose port
EXPOSE 8001

# Run the application
CMD ["/app/start.sh"]
