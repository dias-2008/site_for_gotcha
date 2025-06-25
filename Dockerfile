# Gotcha Guardian Payment Server - Docker Configuration
# Optimized single-stage build for Railway deployment
FROM python:3.11-slim

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=False

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /bin/bash appuser \
    && mkdir -p /home/appuser/.local \
    && chown -R appuser:appuser /home/appuser

# Set working directory
WORKDIR /app

# Copy production requirements for better caching
COPY requirements-production.txt .

# Install production Python dependencies
RUN pip install --user --no-cache-dir -r requirements-production.txt

# Set metadata labels
LABEL maintainer="Gotcha Guardian Team <support@gotchaguardian.com>" \
      description="Gotcha Guardian Payment Server - Secure payment processing for software sales" \
      version="${VERSION:-1.0.0}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      org.opencontainers.image.title="Gotcha Guardian Payment Server" \
      org.opencontainers.image.description="Secure payment processing server for software sales" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Gotcha Guardian" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/yourusername/gotcha-guardian-payment-server"

# Set environment variables
ENV PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/backups /app/temp /app/products \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Note: Volume mount points will be configured via Railway volumes
# Railway volumes should be mounted to: /app/data, /app/logs, /app/backups, /app/products

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "sync", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "payment_server:app"]
