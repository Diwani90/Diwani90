# ===================================
# منصة ديواني - Dockerfile
# Diwani Platform - Django Backend
# ===================================

FROM python:3.12-slim-bookworm

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
    # PostgreSQL client libraries
    libpq-dev \
    # PostGIS dependencies
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    # Build tools
    gcc \
    g++ \
    make \
    # Image processing
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
    # PDF generation
    libcairo2-dev \
    libpango1.0-dev \
    # Crypto dependencies
    libffi-dev \
    libssl-dev \
    # Other utilities
    curl \
    netcat-openbsd \
    gettext \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/static /app/media /app/logs

# Create non-root user for security
RUN groupadd -r diwani && \
    useradd -r -g diwani diwani && \
    chown -R diwani:diwani /app

# Switch to non-root user
USER diwani

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120"]
