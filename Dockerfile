# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip cache list

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash quantchain
RUN chown -R quantchain:quantchain /app
USER quantchain

# Expose port for potential web interface
EXPOSE 8501

# Default command
CMD ["python", "-c", "import quantchain; print('QuantChain ready!')"]
