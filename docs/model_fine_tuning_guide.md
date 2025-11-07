# Model Fine-Tuning Guide for QuantChain

This guide provides comprehensive instructions for fine-tuning language models on financial data using the QuantChain fine-tuning module.

## Overview

QuantChain's Model Fine-Tuning Module enables parameter-efficient fine-tuning (PEFT) of state-of-the-art language models using QLoRA techniques, followed by post-training quantization for efficient deployment.

## Prerequisites

### Hardware Requirements

**Minimum Requirements:**
- **GPU**: NVIDIA GPU with 16GB+ VRAM (RTX 3080/4080 or better)
- **RAM**: 32GB minimum, 64GB recommended for large models
- **Storage**: 100GB+ free space for models and datasets

**Recommended for Production:**
- **GPU**: RTX 3090/4090 (24GB VRAM) for large models
- **RAM**: 64GB+ for optimal performance
- **Storage**: 500GB+ SSD for multiple models and datasets

### Software Dependencies

Install the fine-tuning dependencies:

```bash
pip install transformers>=4.35.0
pip install peft>=0.6.0
pip install bitsandbytes>=0.41.0
pip install datasets>=2.14.0
pip install auto-gptq>=0.7.0  # For GPTQ quantization
pip install llama-cpp-python>=0.2.0  # For GGUF quantization
```

## Supported Models

The fine-tuning module supports the following models with optimized configurations:

### Primary Target Models

| Model | Parameter Count | Min VRAM | Quantization Support | Recommended Use Case |
|--------|----------------|-------------|---------------------|-------------------|
| DeepSeek-R1-0528 | 67B | 24GB | 4-bit/8-bit | Code generation, reasoning |
| Qwen3-235B-Instruct-2507 | 235B | 48GB | 4-bit/8-bit | Instruction following, analysis |
| Llama-3.1-8B | 8B | 12GB | 4-bit/8-bit | General purpose, cost-effective |
| Llama-3.1-70B | 70B | 48GB | 4-bit/8-bit | High-performance tasks |
| Mistral-7B | 7B | 12GB | 4-bit/8-bit | Fast inference, efficiency |
| Mistral-34B | 34B | 24GB | 4-bit/8-bit | Balance of performance/efficiency |

## Quick Start Guide

### 1. Environment Setup

```python
from quantchain.tools.model_fine_tuning import setup_fine_tuning_environment

# Setup environment for DeepSeek model
config = setup_fine_tuning_environment(
    model_name="deepseek-r1-0528",
    base_model_path="deepseek-ai/deepseek-coder-6.7b-base",
    output_dir="./fine_tuned_models"
)

print(f"Environment configured for {config.model_name}")
print(f"Target modules: {config.target_modules}")
```

### 2. Dataset Preparation

Prepare your financial dataset in one of the supported formats:

**Format 1: Text-only dataset**
```jsonl
{"text": "Federal Reserve signals potential rate cuts in response to economic slowdown"}
{"text": "Tech stocks rally as AI companies beat earnings expectations"}
```

**Format 2: Prompt/Completion dataset**
```jsonl
{"prompt": "Analyze AAPL stock with current technical indicators", "completion": "Based on RSI and MACD, short-term bullish momentum expected"}
{"prompt": "Evaluate cryptocurrency market sentiment for Bitcoin", "completion": "Bitcoin shows accumulation phase with positive on-chain metrics"}
```

```python
from quantchain.tools.model_fine_tuning import prepare_financial_dataset
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-6.7b-base")
dataset = prepare_financial_dataset(
    dataset_path="./data/financial_news.jsonl",
    tokenizer=tokenizer,
    max_length=2048
)

print(f"Dataset prepared with {len(dataset)} samples")
```

### 3. QLoRA Fine-Tuning

```python
from quantchain.tools.model_fine_tuning import (
    fine_tune_model_qlora,
    TrainingArguments,
    TrainingResult
)

# Configure training arguments
training_args = TrainingArguments(
    output_dir=config.output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=10,
    save_steps=500,
    eval_steps=500,
    fp16=True,
    dataloader_num_workers=4
)

# Start fine-tuning
result = fine_tune_model_qlora(config, dataset, training_args)

print(f"Training completed in {result.training_time_seconds} seconds")
print(f"Final model saved to: {result.checkpoint_path}")
print(f"Peak GPU memory usage: {result.gpu_memory_usage_gb:.2f}GB")
```

### 4. Model Quantization

After fine-tuning, quantize the model for efficient deployment:

#### GGUF Quantization (Recommended for CPU/local inference)

```python
from quantchain.tools.model_fine_tuning import quantize_model

# Quantize to 4-bit GGUF for maximum efficiency
gguf_result = quantize_model(
    model_path=result.checkpoint_path,
    quantization_format="gguf",
    output_path="./quantized_models",
    bits=4
)

print(f"GGUF quantization completed in {gguf_result.quantization_time_seconds} seconds")
print(f"Compression ratio: {gguf_result.compression_ratio:.2f}x")
print(f"Quantized model: {gguf_result.quantized_model_path}")
```

#### GPTQ Quantization (Recommended for GPU inference)

```python
# Quantize to 4-bit GPTQ for GPU inference
gptq_result = quantize_model(
    model_path=result.checkpoint_path,
    quantization_format="gptq",
    output_path="./quantized_models",
    bits=4
)

print(f"GPTQ quantization completed in {gptq_result.quantization_time_seconds} seconds")
print(f"Inference speed: {gptq_result.inference_speed_tokens_per_sec:.1f} tokens/sec")
```

### 5. Model Validation

```python
from quantchain.tools.model_fine_tuning import validate_fine_tuned_model

# Validate the fine-tuned model
validation_report = validate_fine_tuned_model(
    model_path=gptq_result.quantized_model_path,
    test_dataset=eval_dataset
)

print(f"Validation Results:")
print(f"  Test Loss: {validation_report.test_loss:.4f}")
print(f"  Perplexity: {validation_report.perplexity:.2f}")
print(f"  BLEU Score: {validation_report.bleu_score:.3f}")
print(f"  Sample Outputs: {len(validation_report.sample_outputs)}")
```

## Advanced Usage

### Custom Training Configurations

#### Optimizing for Memory Constraints

```python
# For limited VRAM (16GB)
low_memory_config = TrainingArguments(
    output_dir=config.output_dir,
    num_train_epochs=2,  # Fewer epochs
    per_device_train_batch_size=1,  # Smaller batch size
    gradient_accumulation_steps=16,  # Increase accumulation
    learning_rate=1e-4,  # Lower learning rate
    fp16=True,  # Use mixed precision
    dataloader_num_workers=2  # Fewer workers
)
```

#### High-Performance Configuration

```python
# For ample VRAM (48GB+)
high_perf_config = TrainingArguments(
    output_dir=config.output_dir,
    num_train_epochs=5,  # More epochs
    per_device_train_batch_size=8,  # Larger batch size
    gradient_accumulation_steps=1,  # Direct optimization
    learning_rate=5e-4,  # Higher learning rate
    fp16=True,
    dataloader_num_workers=8  # More workers
)
```

### Model-Specific Optimizations

#### DeepSeek-R1 Fine-Tuning

```python
# DeepSeek-specific configuration
deepseek_config = FineTuningConfig(
    model_name="deepseek-r1-0528",
    model_path="deepseek-ai/deepseek-coder-6.7b-base",
    output_dir="./deepseek_fine_tuned",
    lora_r=32,  # Higher rank for larger model
    lora_alpha=64,  # Higher alpha
    lora_dropout=0.05,  # Lower dropout
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
```

#### Llama Fine-Tuning

```python
# Llama-specific configuration
llama_config = FineTuningConfig(
    model_name="llama-3.1-8b",
    model_path="meta-llama/Meta-Llama-3.1-8B",
    output_dir="./llama_fine_tuned",
    lora_r=16,  # Standard rank
    lora_alpha=32,  # Standard alpha
    lora_dropout=0.1,  # Standard dropout
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
```

## Troubleshooting

### Common Issues and Solutions

#### GPU Memory Issues

**Problem**: Out of Memory (OOM) errors during training
```python
# Solutions:
# 1. Reduce batch size
training_args.per_device_train_batch_size = 2

# 2. Increase gradient accumulation
training_args.gradient_accumulation_steps = 8

# 3. Use 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_use_double_quant=True
)

# 4. Enable CPU offloading
config.device_map = {"": 0, "layer.0": 1, "layer.1": "cpu"}
```

#### Training Instability

**Problem**: Training loss becomes NaN or infinite
```python
# Solutions:
# 1. Lower learning rate
training_args.learning_rate = 1e-4

# 2. Enable gradient clipping
# In TrainingArguments, add:
# max_grad_norm=1.0

# 3. Use warmup steps
# In TrainingArguments, add:
# warmup_steps=100
```

#### Slow Convergence

**Problem**: Model converges too slowly
```python
# Solutions:
# 1. Increase learning rate
training_args.learning_rate = 5e-4

# 2. Adjust LoRA parameters
config.lora_r = 32  # Higher rank
config.lora_alpha = 64  # Higher alpha

# 3. Use learning rate scheduler
# In TrainingArguments, add:
# lr_scheduler_type="cosine"
```

## Integration with QuantChain

### Using Fine-Tuned Models in Trading Agents

```python
from quantchain.agents.memecoin_vibe_trader import MemecoinVibeTrader
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load fine-tuned model
tokenizer = AutoTokenizer.from_pretrained("./fine_tuned_models/deepseek_final")
model = AutoModelForCausalLM.from_pretrained("./fine_tuned_models/deepseek_final")

# Initialize agent with fine-tuned model
agent = MemecoinVibeTrader(
    config=trader_config,
    model=model,
    tokenizer=tokenizer,
    # ... other components
)
```

### Integration with Model Serving

#### vLLM Integration

```python
# Start vLLM server with quantized model
import subprocess

cmd = [
    "python3", "-m", "vllm.entrypoints.openai.api_server",
    "--model", "./quantized_models/model_4bit.gguf",
    "--port", "8000",
    "--tensor-parallel-size", "1"
]

subprocess.run(cmd)
```

#### Ollama Integration

```bash
# Start Ollama with GGUF model
ollama serve ./quantized_models/model_4bit.gguf --port 11434

# Use in applications
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "model_4bit", "prompt": "Analyze AAPL stock..."}'
```

## Performance Benchmarks

### Expected Performance Metrics

| Model Size | Quantization | VRAM Usage | Inference Speed | Model Size |
|-------------|---------------|--------------|----------------|-------------|
| 7B | 4-bit GGUF | 6GB | 45-60 t/s | 4.5GB |
| 7B | 4-bit GPTQ | 8GB | 75-100 t/s | 4.2GB |
| 34B | 4-bit GGUF | 16GB | 20-30 t/s | 18GB |
| 34B | 4-bit GPTQ | 20GB | 35-50 t/s | 16GB |
| 70B | 4-bit GGUF | 24GB | 8-15 t/s | 38GB |
| 70B | 4-bit GPTQ | 32GB | 15-25 t/s | 35GB |

### Training Time Estimates

| Model Size | Dataset Size | GPU | Training Time |
|-------------|---------------|-----|--------------|
| 7B | 10K samples | RTX 3080 | 2-4 hours |
| 34B | 10K samples | RTX 3090 | 6-10 hours |
| 70B | 10K samples | A100 | 12-20 hours |

## Best Practices

### Data Quality

1. **Consistent Formatting**: Ensure uniform data structure throughout dataset
2. **Diverse Examples**: Include various financial scenarios and market conditions
3. **Quality Control**: Remove duplicates, fix typos, ensure proper labeling
4. **Balanced Classes**: Maintain balanced positive/negative/neutral distribution
5. **Domain-Specific Content**: Focus on financial terminology and market analysis patterns

### Training Optimization

1. **Start Small**: Begin with smaller datasets to debug configuration
2. **Monitor Metrics**: Track loss, perplexity, and sample quality continuously
3. **Checkpoint Regularly**: Save intermediate results for recovery
4. **Validate Often**: Test model performance during training
5. **Hardware Utilization**: Monitor GPU memory and utilization

### Model Evaluation

1. **Multiple Metrics**: Use BLEU, perplexity, and domain-specific evaluations
2. **Qualitative Assessment**: Review sample outputs for coherence and accuracy
3. **A/B Testing**: Compare different quantization levels and configurations
4. **Real-World Testing**: Validate in actual trading scenarios

## Next Steps

1. **Explore Advanced Techniques**: Implement full fine-tuning with instruction following
2. **Multi-Task Training**: Enable models to handle multiple financial tasks
3. **Continuous Learning**: Setup pipelines for ongoing model improvement
4. **Production Deployment**: Integrate with QuantChain's serving infrastructure

## Support

For issues, questions, or contributions:

1. **Documentation**: Refer to [AGENTS.md](../AGENTS.md) for development guidelines
2. **Issues**: Report bugs and feature requests via GitHub Issues
3. **Community**: Join discussions and share fine-tuning experiences
4. **Examples**: Contribute example configurations and use cases
