# Production Dockerfile for PPT Generator AI
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY modules/ /app/modules/
COPY main.py /app/
COPY Input/ /app/Input/

# Create necessary directories
RUN mkdir -p /app/Output /app/logs /app/metrics

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 pptgen && \
    chown -R pptgen:pptgen /app

USER pptgen

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import sys; sys.exit(0)"

# Entry point
ENTRYPOINT ["python", "main.py"]

# Default command (show help)
CMD ["--help"]
