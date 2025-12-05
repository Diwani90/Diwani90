# ===================================
# منصة ديواني - Backend Dockerfile
# Python 3.12 + Django 5.x
# ===================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client
    libpq-dev \
    # PostGIS dependencies
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    # Other utilities
    curl \
    gettext \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Create non-root user for security
RUN addgroup --system --gid 1001 diwani \
    && adduser --system --uid 1001 --gid 1001 diwani \
    && chown -R diwani:diwani /app

# Switch to non-root user
USER diwani

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
