# ClubiFy Dockerfile
# Multi-stage build for production-ready Django application
# Optimized for CPU-only PyTorch (much faster builds, ~150MB vs ~2GB+)

# ============================================
# Stage 1: Build stage
# ============================================
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (excluding torch - will be installed as CPU-only in final stage)
# This creates wheels for faster installation in final stage
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# Stage 2: Production stage
# ============================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=clubify.settings

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set work directory
WORKDIR /app

# Install runtime dependencies including Node.js for Tailwind
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and requirements from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install torch CPU-only FIRST (much smaller/faster: ~150MB vs ~2GB+)
# Using PyTorch's official CPU-only builds - no CUDA dependencies
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch>=2.0.0

# Install other Python dependencies from wheels (much faster than pip install from source)
RUN pip install --no-cache /wheels/*

# Copy project files (this happens late for better caching)
COPY --chown=appuser:appgroup . .

# Install Node.js dependencies for Tailwind (cached if package.json doesn't change)
RUN npm install

# Copy and set up entrypoint script
COPY --chown=appuser:appgroup docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Collect static files (can fail if DB not ready, that's OK)
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/clubs/')" || exit 1

# Default to entrypoint script (for development)
# Override in docker-compose.yml for production
ENTRYPOINT ["/app/docker-entrypoint.sh"]
