# Multi-stage Docker build for Portfolio Agent Production
FROM python:3.12-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG POETRY_VERSION=2.1.4

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==${POETRY_VERSION}

# Configure Poetry to not create virtual environment
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies to system Python
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.12-slim as production

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set labels
LABEL org.opencontainers.image.title="Portfolio Agent" \
      org.opencontainers.image.description="A persona-grounded RAG toolkit for turning documents into a citable assistant" \
      org.opencontainers.image.url="https://github.com/shelabh/portfolio-agent-package" \
      org.opencontainers.image.source="https://github.com/shelabh/portfolio-agent-package" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Shelabh Tyagi" \
      org.opencontainers.image.licenses="Apache-2.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    LOCAL_ONLY=true

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r portfolio && useradd -r -g portfolio portfolio

# Set work directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY EXAMPLES/ ./EXAMPLES/
COPY docs/ ./docs/
COPY README.md LICENSE ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R portfolio:portfolio /app

# Switch to non-root user
USER portfolio

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "portfolio_agent.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
