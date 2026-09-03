# Use Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install uv for fast dependency resolution and management
RUN pip install --no-cache-dir uv

# Copy project specification files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv pip install --system --no-cache .

# Copy application source code
COPY config.py cache_service.py main.py benchmark.py README.md ./
COPY benchmark/ ./benchmark/

# Expose container port
EXPOSE 8080

# Run application
CMD ["python", "main.py"]
