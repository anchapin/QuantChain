# Environment Setup Guide

This guide provides comprehensive instructions for setting up QuantChain in various environments, from local development to production deployment.

For a quick overview and basic commands, see the [README](../README.md#quick-start-with-docker-recommended).

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS (10.15+), Windows 10/11 (WSL2)
- **Python**: 3.10+ (3.12 recommended)
- **Git**: For version control
- **NVIDIA GPU**: Required for local LLM inference (optional for CPU-only mode)
- **Docker**: 20.10+ with Docker Compose v2

### Hardware Requirements
See [Hardware Requirements Matrix](hardware-requirements.md) for detailed GPU recommendations.

## Quick Start (Docker)

### 1. Install NVIDIA Container Toolkit (Linux)

```bash
# Add NVIDIA package repositories
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Update package list and install toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker to use NVIDIA runtime
sudo systemctl restart docker

# Verify installation
sudo docker run --rm --gpus all nvidia/cuda:12.1-runtime-ubuntu22.04 nvidia-smi
```

### 2. Clone and Setup QuantChain

```bash
# Clone the repository
git clone https://github.com/anchapin/QuantChain.git
cd QuantChain

# Copy environment template
cp config.example.yaml config.yaml
cp .env.example .env

# Edit environment variables
nano .env  # Add your API keys
```

### 3. Run with GPU Support

```bash
# Build and start with GPU (uses NVIDIA runtime)
docker compose -f docker-compose.gpu.yml up --build -d

# Check logs
docker compose -f docker-compose.gpu.yml logs -f

# Stop services
docker compose -f docker-compose.gpu.yml down
```

The GPU-enabled docker-compose file automatically configures the NVIDIA runtime (`runtime: nvidia`) and sets appropriate CUDA environment variables.

### 4. Run with CPU Only

```bash
# Build and start (CPU only)
docker compose up --build -d

# Check logs
docker compose logs -f

# Stop services
docker compose down
```

## Local Development Setup

### 1. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Upgrade pip
python3 -m pip install --upgrade pip setuptools wheel
```

### 2. Install Dependencies

```bash
# Clone repository
git clone https://github.com/anchapin/QuantChain.git
cd QuantChain

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-dev build-essential curl git

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Install QuantChain in development mode
pip install -e .
```

### 3. CUDA Setup (Optional)

For Ubuntu/Debian systems with NVIDIA GPUs:

```bash
# Check NVIDIA driver installation
nvidia-smi

# Install CUDA (if not already installed)
# Visit https://developer.nvidia.com/cuda-downloads
# or use package manager:

# CUDA 12.1 example (Ubuntu 22.04)
wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda_12.1.1_530.30.02_linux.run
sudo sh cuda_12.1.1_530.30.02_linux.run

# Add CUDA to PATH (add to ~/.bashrc)
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 4. PyTorch with CUDA Support

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify CUDA availability
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}')"
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Trading APIs
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # or https://api.alpaca.markets for live

# Data APIs
POLYGON_API_KEY=your_polygon_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# LLM APIs
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
REDIS_URL=redis://localhost:6379
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Model Settings
MODEL_TYPE=local  # or openai, anthropic
MODEL_PATH=./models
QUANTIZATION=4bit
GPU_MEMORY_FRACTION=0.9
```

### 2. Application Configuration

Edit `config.yaml`:

```yaml
# Core settings
environment: development
log_level: INFO
debug: true

# Trading settings
default_symbol: SPY
risk_tolerance: MEDIUM
max_position_size: 0.1  # 10% of portfolio

# Backtesting
default_start_date: "2023-01-01"
default_end_date: "2023-12-31"
initial_cash: 100000

# Model settings
llm:
  provider: local
  model_path: ./models/Mistral-7B-Instruct-v0.2.gguf
  temperature: 0.7
  max_tokens: 2048
  context_length: 4096

# Performance
cache_enabled: true
cache_ttl: 3600  # 1 hour
parallel_processing: true
max_workers: 4
```

## Model Management

### 1. Downloading Models

```bash
# Create models directory
mkdir -p models

# Download GGUF models (recommended for CPU/GPU inference)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -O models/mistral-7b-instruct.q4.gguf

# Download using HuggingFace CLI
pip install huggingface_hub
huggingface-cli download TheBloke/DeepSeek-R1-5.7B-GGUF --local-dir ./models/deepseek-r1-5.7b-gguf --include "*.gguf"
```

### 2. Model Verification

```bash
# Verify model download
python3 -c "
import os
from pathlib import Path
models_dir = Path('models')
for model_file in models_dir.glob('**/*.gguf'):
    size_mb = model_file.stat().st_size / (1024 * 1024)
    print(f'Model: {model_file.name} - Size: {size_mb:.1f} MB')
"
```

## Service Setup

### 1. Redis (Optional)

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis
sudo systemctl enable redis

# Verify Redis is running
redis-cli ping
```

### 2. PostgreSQL (Optional)

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE quantchain;
CREATE USER quantchain_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE quantchain TO quantchain_user;
\q
```

## Development Workflow

### 1. Running Tests

```bash
# Run all tests
python3 -m pytest

# Run with coverage
python3 -m pytest --cov=quantchain --cov-report=html

# Run specific test
python3 -m pytest tests/core/test_security.py -v
```

### 2. Code Quality

```bash
# Format code
python3 -m black quantchain tests

# Lint code
python3 -m flake8 quantchain tests

# Type checking
python3 -m mypy quantchain
```

### 3. Running Examples

```bash
# Run memecoin trader example
python3 -m quantchain.examples.memecoin_trader

# Run with configuration
python3 -m quantchain.examples.memecoin_trader --config config.yaml

# Run dashboard
python3 -m streamlit run quantchain/dashboard/app.py
```

## Production Deployment

### 1. Security Hardening

```bash
# Use production configuration
cp config.production.yaml config.yaml

# Set appropriate file permissions
chmod 600 .env
chmod 600 config.yaml
chmod 700 logs/
chmod 600 logs/*

# Use non-root user in containers
# (Already configured in Dockerfile.gpu)
```

### 2. Monitoring and Logging

```bash
# Set up log rotation
sudo nano /etc/logrotate.d/quantchain

# Content for log rotation:
# /var/log/quantchain/*.log {
#     daily
#     missingok
#     rotate 30
#     compress
#     delaycompress
#     notifempty
#     create 644 quantchain quantchain
# }
```

### 3. Performance Optimization

```bash
# Tune kernel parameters for high-frequency operations
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Optimize NVIDIA GPU settings
nvidia-smi -pm 1  # Enable persistence mode
nvidia-smi -ac 877,1215  # Set memory and graphics clocks (GPU-specific)
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```bash
   # Reduce batch size or model size
   export GPU_MEMORY_FRACTION=0.8
   ```

2. **Permission Denied Errors**
   ```bash
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Import Errors**
   ```bash
   # Reinstall in development mode
   pip install -e .
   ```

4. **GPU Not Detected**
   ```bash
   # Check NVIDIA driver
   nvidia-smi
   
   # Check CUDA installation
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```

### Health Checks

```bash
# Check Docker container health
docker compose ps

# Check service logs
docker compose logs quantchain-gpu

# Check system resources
htop
nvidia-smi
df -h
```

## Support

- **Documentation**: [QuantChain Documentation](https://github.com/anchapin/QuantChain/docs)
- **Issues**: [GitHub Issues](https://github.com/anchapin/QuantChain/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anchapin/QuantChain/discussions)
- **Community**: Join our Discord server for real-time support
