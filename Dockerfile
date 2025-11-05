# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimized caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user first
RUN useradd --create-home --shell /bin/bash quantchain

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/quantchain/.local

# Copy source code
COPY . .

# Set ownership and permissions
RUN chown -R quantchain:quantchain /app

# Switch to non-root user
USER quantchain

# Update PATH to include user local packages
ENV PATH=/home/quantchain/.local/bin:$PATH
ENV PYTHONPATH=/home/quantchain/.local/lib/python3.12/site-packages:$PYTHONPATH

# Expose port for potential web interface
EXPOSE 8501

# Default command
CMD ["python", "-c", "import quantchain; print('QuantChain ready!')"]
