# Overmanifold Protocol - Production Dockerfile
# Multi-stage build for optimal image size and security

FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 overmanifold

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --user

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/overmanifold/.local/bin:$PATH \
    OVERMANIFOLD_HOME=/home/overmanifold \
    OVERMANIFOLD_LOGS=/var/log/overmanifold \
    OVERMANIFOLD_DATA=/var/lib/overmanifold

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 overmanifold

# Create necessary directories
RUN mkdir -p ${OVERMANIFOLD_LOGS} ${OVERMANIFOLD_DATA} && \
    chown -R overmanifold:overmanifold ${OVERMANIFOLD_LOGS} ${OVERMANIFOLD_DATA}

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/overmanifold/.local

# Set working directory
WORKDIR ${OVERMANIFOLD_HOME}

# Copy application code
COPY --chown=overmanifold:overmanifold overmanifold ./overmanifold
COPY --chown=overmanifold:overmanifold *.py ./
COPY --chown=overmanifold:overmanifold *.md ./

# Create logs directory structure
RUN mkdir -p logs && chown overmanifold:overmanifold logs

# Switch to non-root user
USER overmanifold

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "overmanifold.api.server"]