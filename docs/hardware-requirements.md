# Hardware Requirements Matrix

This document provides detailed hardware requirements for running QuantChain agents with common quantized models. Requirements vary based on model size, quantization level, and expected workload.

## Model Categories and Requirements

### 1. Lightweight Models (1-8B Parameters)
**Examples**: Llama 3.1 8B, Qwen2 7B, DeepSeek-Coder 6.7B

| Quantization | VRAM Required | RAM Required | GPU Recommendations | CPU Fallback |
|--------------|---------------|--------------|---------------------|--------------|
| FP16 | 16GB | 8GB | RTX 3080/4080, RTX A4000 | ✅ (slower) |
| 8-bit | 8GB | 6GB | RTX 3060/4060, GTX 1660 | ✅ |
| 4-bit | 5GB | 4GB | RTX 3050/4050, GTX 1060+ | ✅ |

### 2. Medium Models (13-34B Parameters)
**Examples**: Llama 3.1 13B/34B, Qwen2 13B/32B, DeepSeek-R1 14B

| Quantization | VRAM Required | RAM Required | GPU Recommendations | CPU Fallback |
|--------------|---------------|--------------|---------------------|--------------|
| FP16 | 68GB | 32GB | RTX A6000, A100 | ❌ |
| 8-bit | 34GB | 20GB | RTX 3090/4090, RTX A5000 | ✅ (very slow) |
| 4-bit | 20GB | 12GB | RTX 3080/4080+, RTX A4000 | ✅ (slow) |

### 3. Large Models (70B+ Parameters)
**Examples**: Llama 3.1 70B, Qwen2 72B, DeepSeek-R1 67B

| Quantization | VRAM Required | RAM Required | GPU Recommendations | CPU Fallback |
|--------------|---------------|--------------|---------------------|--------------|
| FP16 | 140GB | 64GB | 2x A100/H100, 2x RTX A6000 | ❌ |
| 8-bit | 70GB | 40GB | 2x RTX 3090/4090, A100 | ❌ |
| 4-bit | 40GB | 24GB | RTX 3090/4090, RTX A6000 | ✅ (very slow) |

## Agent-Specific Workload Requirements

### Memecoin Vibe Trader Agent
**Characteristics**: Low to medium complexity, frequent API calls, moderate inference requirements

| Model Size | VRAM | RAM | Recommended GPU | Performance |
|------------|------|-----|-----------------|-------------|
| Small (7B) | 5-8GB | 4GB | RTX 3060+ | Excellent |
| Medium (34B) | 15-25GB | 8GB | RTX 3080+ | Good |
| Large (70B) | 35-45GB | 16GB | RTX 3090+ | Fair |

### Multimodal Chart Reader Agent
**Characteristics**: High memory usage for image processing, less frequent but complex inferences

| Model Size | VRAM | RAM | Recommended GPU | Performance |
|------------|------|-----|-----------------|-------------|
| Small (7B) | 8-12GB | 6GB | RTX 3060+ | Good |
| Medium (34B) | 25-35GB | 12GB | RTX 3080+ | Good |
| Large (70B) | 45-60GB | 24GB | RTX 3090+ | Fair |

### Smart Contract Auditor Agent
**Characteristics**: High context window requirements, intensive processing, less real-time needs

| Model Size | VRAM | RAM | Recommended GPU | Performance |
|------------|------|-----|-----------------|-------------|
| Small (7B) | 6-10GB | 8GB | RTX 3060+ | Good |
| Medium (34B) | 20-30GB | 16GB | RTX 3080+ | Good |
| Large (70B) | 40-55GB | 32GB | RTX 3090+ | Good |

## Storage Requirements

### Model Files
| Model Size | 4-bit (GGUF) | 8-bit | 16-bit | Notes |
|------------|--------------|-------|--------|-------|
| 7B | 4.5GB | 7.5GB | 14GB | Recommended: 4-bit |
| 34B | 20GB | 35GB | 65GB | Recommended: 8-bit |
| 70B | 40GB | 70GB | 130GB | Recommended: 8-bit |

### Additional Storage
- **System**: 50GB minimum (OS, dependencies)
- **Market Data Cache**: 10-100GB (depends on trading pairs and history)
- **Backtest Results**: 5-50GB (depends on simulation length)
- **Logs**: 1-10GB monthly

## System Recommendations by Budget

### Budget Setup (<$1000)
- **GPU**: RTX 3060 12GB or RTX 4060 8GB
- **RAM**: 32GB DDR4
- **Storage**: 1TB NVMe SSD
- **CPU**: Ryzen 5 5600X or Intel i5-12600K
- **Use Case**: Small to medium models, hobbyist trading

### Mid-Range Setup ($1000-$2500)
- **GPU**: RTX 3080/4080 16GB or RTX 3090/4090 24GB
- **RAM**: 64GB DDR4/DDR5
- **Storage**: 2TB NVMe SSD
- **CPU**: Ryzen 7 7800X3D or Intel i7-13700K
- **Use Case**: Medium to large models, serious trading

### Professional Setup ($2500+)
- **GPU**: RTX 3090/4090 24GB (SLI) or RTX A6000 48GB
- **RAM**: 128GB DDR4/DDR5
- **Storage**: 4TB NVMe SSD + backup
- **CPU**: Ryzen 9 7950X or Intel i9-13900K
- **Use Case**: Large models, multi-agent systems, production

## Performance Benchmarks

### Inference Speed (tokens/second)
| GPU Model | 7B (4-bit) | 13B (4-bit) | 34B (8-bit) | 70B (8-bit) |
|-----------|------------|--------------|--------------|--------------|
| RTX 3050 | 15-20 | 8-12 | 2-4 | 1-2 |
| RTX 3060 | 20-30 | 12-18 | 4-6 | 2-3 |
| RTX 3080 | 35-45 | 20-28 | 8-12 | 4-6 |
| RTX 3090 | 40-55 | 25-35 | 10-15 | 5-8 |
| RTX 4090 | 60-80 | 35-45 | 15-20 | 8-12 |

### Memory Bandwidth Impact
- **RTX 30 Series**: 448-936 GB/s
- **RTX 40 Series**: 504-1008 GB/s  
- **RTX A Series**: 616-936 GB/s
- **Higher bandwidth = better performance for large models**

## Optimization Tips

1. **Use quantization**: 4-bit for real-time, 8-bit for better accuracy
2. **Enable GPU memory optimization**: Use `vLLM` with tensor parallelism
3. **Cache frequently used data**: Reduce I/O bottlenecks
4. **Use fast storage**: NVMe SSD for model loading
5. **Monitor resource usage**: Adjust batch sizes based on available VRAM

## Cloud Alternatives

When local hardware is insufficient, consider:
- **RunPod**: GPU rental with hourly pricing
- **Lambda Labs**: On-demand GPU instances
- **AWS EC2**: P4/P5 instances for production
- **Google Cloud**: A2/A3 instances with NVIDIA GPUs
- **Paperspace**: Gradient platform for ML workloads

**Note**: Cloud costs can exceed $5-10/hour for large GPU instances, making local hardware more cost-effective for continuous operation.
