# Multi-stage Docker build for production-ready Context7 Agent v2.0

# Stage 1: Node.js base for MCP server
FROM node:18-alpine AS mcp-base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Python base
FROM python:3.11-slim AS python-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r context7 && useradd -r -g context7 context7

# Set working directory
WORKDIR /app

# Create directories
RUN mkdir -p /app/data /app/logs && \
    chown -R context7:context7 /app

# Stage 3: Python dependencies
FROM python-base AS dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 4: Final image
FROM python-base AS final

# Copy Python dependencies
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=context7:context7 src/ /app/src/
COPY --chown=context7:context7 pyproject.toml /app/
COPY --chown=context7:context7 .env.docker /app/.env

# Install Node.js for MCP server
COPY --from=mcp-base /usr/local/bin/node /usr/local/bin/
COPY --from=mcp-base /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install MCP server globally
RUN npm install -g @upstash/context7-mcp@latest

# Switch to non-root user
USER context7

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.config import Config; Config.load()" || exit 1

# Set default command
CMD ["python", "-m", "src.cli"]

# Labels for metadata
LABEL maintainer="Context7 Team <team@context7.ai>"
LABEL version="2.0.0"
LABEL description="Production-ready terminal AI agent with Pydantic-AI v0.5+"
