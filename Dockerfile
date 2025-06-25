# Gotcha Guardian Payment Server - Docker Configuration
# Multi-stage build for optimized production image

# =============================================================================
# BUILD STAGE
# =============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM python:3.11-slim as production

# Set metadata labels
LABEL maintainer="Gotcha Guardian Team <support@gotchaguardian.com>" \
      description="Gotcha Guardian Payment Server - Secure payment processing for software sales" \
      version="${VERSION:-1.0.0}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      org.opencontainers.image.title="Gotcha Guardian Payment Server" \
      org.opencontainers.image.description="Secure payment processing server for software sales" \
      org.opencontainers.image.version="${VERSION:-1.0.0}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Gotcha Guardian" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/yourusername/gotcha-guardian-payment-server"

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=False \
    PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
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

# Copy Python dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

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
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "sync", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "payment_server:app"]

# =============================================================================
# DEVELOPMENT STAGE (optional)
# =============================================================================
FROM production as development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-flask \
    pytest-cov \
    flake8 \
    black \
    ipython \
    flask-debugtoolbar

# Set development environment variables
ENV FLASK_ENV=development \
    FLASK_DEBUG=True

# Switch back to appuser
USER appuser

# Override command for development
CMD ["python", "payment_server.py"]

# =============================================================================
# BUILD INSTRUCTIONS
# =============================================================================

# To build the production image:
# docker build --target production -t gotcha-guardian-payment-server:latest .

# To build the development image:
# docker build --target development -t gotcha-guardian-payment-server:dev .

# To build with build arguments:
# docker build \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VERSION=1.0.0 \
#   --build-arg VCS_REF=$(git rev-parse --short HEAD) \
#   --target production \
#   -t gotcha-guardian-payment-server:1.0.0 .

# To run the container:
# docker run -d \
#   --name gotcha-guardian-payment \
#   -p 5000:5000 \
#   -v $(pwd)/data:/app/data \
#   -v $(pwd)/logs:/app/logs \
#   -v $(pwd)/products:/app/products \
#   --env-file .env \
#   gotcha-guardian-payment-server:latest

# To run in development mode:
# docker run -it \
#   --name gotcha-guardian-payment-dev \
#   -p 5000:5000 \
#   -v $(pwd):/app \
#   --env-file .env \
#   gotcha-guardian-payment-server:dev

# =============================================================================
# DOCKER COMPOSE USAGE
# =============================================================================

# For production deployment with docker-compose:
# version: '3.8'
# services:
#   payment-server:
#     build:
#       context: .
#       target: production
#     ports:
#       - "5000:5000"
#     volumes:
#       - ./data:/app/data
#       - ./logs:/app/logs
#       - ./products:/app/products
#     env_file:
#       - .env
#     restart: unless-stopped
#     healthcheck:
#       test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
#       interval: 30s
#       timeout: 10s
#       retries: 3
#       start_period: 40s

# =============================================================================
# SECURITY CONSIDERATIONS
# =============================================================================

# 1. Non-root user: Application runs as 'appuser' for security
# 2. Minimal base image: Using slim Python image to reduce attack surface
# 3. No cache: Pip cache disabled to reduce image size
# 4. Health checks: Built-in health monitoring
# 5. Volume mounts: Sensitive data stored in volumes, not in image
# 6. Environment variables: Secrets passed via environment, not hardcoded
# 7. Multi-stage build: Build dependencies not included in final image
# 8. Regular updates: Base image should be updated regularly

# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================

# 1. Multi-stage build: Smaller final image size
# 2. Layer caching: Requirements copied separately for better caching
# 3. Gunicorn: Production WSGI server with multiple workers
# 4. Health checks: Automatic container health monitoring
# 5. Resource limits: Can be set via docker run or docker-compose
# 6. Volume mounts: Persistent data storage

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================

# Logs are written to stdout/stderr and can be collected by:
# - Docker logs: docker logs <container_name>
# - Log aggregation: Fluentd, Logstash, etc.
# - Monitoring: Prometheus, Grafana, etc.

# Health check endpoint: http://localhost:5000/api/health
# Metrics endpoint: http://localhost:5000/api/metrics (if implemented)

# =============================================================================
# DEPLOYMENT NOTES
# =============================================================================

# 1. Always use specific version tags in production
# 2. Set resource limits (CPU, memory) in production
# 3. Use secrets management for sensitive environment variables
# 4. Implement proper backup strategies for volumes
# 5. Monitor container health and performance
# 6. Keep base images updated for security patches
# 7. Use container orchestration (Kubernetes, Docker Swarm) for scaling
# 8. Implement proper logging and monitoring solutions
