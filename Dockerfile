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
RUN pip install prisma && python -m prisma generate

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Start the server (migrations are handled by backend service only)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

