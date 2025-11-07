### Component: Model Fine-Tuning Module

**Location**: `quantchain/tools/model_fine_tuning.py`
**Spec**: `specs/tools/model_fine_tuning.spec.md`
**Tests**: `tests/tools/test_model_fine_tuning.py`

## Overview

A comprehensive fine-tuning module that enables parameter-efficient fine-tuning (PEFT) of state-of-the-art language models on financial data, with support for QLoRA techniques and post-training quantization workflows.

## Core Functions

### Function: `setup_fine_tuning_environment`

- **Signature:** `setup_fine_tuning_environment(model_name: str, base_model_path: str, output_dir: str) -> FineTuningConfig`
- **Description:** Initializes the fine-tuning environment with necessary configurations for PEFT/QLoRA.
- **Parameters:**
  - `model_name`: The target model (e.g., 'deepseek-r1-0528', 'qwen3-235b-instruct-2507')
  - `base_model_path`: Local path or HuggingFace model identifier
  - `output_dir`: Directory to save fine-tuned models and checkpoints
- **Returns:** `FineTuningConfig` object with model, tokenizer, and training configuration
- **Raises:** `ValueError` if model is unsupported, `EnvironmentError` if GPU resources insufficient

### Function: `prepare_financial_dataset`

- **Signature:** `prepare_financial_dataset(dataset_path: str, tokenizer: any, max_length: int = 2048) -> Dataset`
- **Description:** Preprocesses financial data for fine-tuning, including tokenization and formatting.
- **Parameters:**
  - `dataset_path`: Path to financial dataset (JSONL, CSV, or directory)
  - `tokenizer`: The model's tokenizer for processing text
  - `max_length`: Maximum sequence length for tokenization
- **Returns:** Processed `Dataset` object ready for training
- **Raises:** `DatasetError` if data format is invalid, `TokenizationError` if processing fails

### Function: `fine_tune_model_qlora`

- **Signature:** `fine_tune_model_qlora(config: FineTuningConfig, dataset: Dataset, training_args: TrainingArguments) -> TrainingResult`
- **Description:** Performs parameter-efficient fine-tuning using QLoRA technique.
- **Parameters:**
  - `config`: Fine-tuning configuration from setup_fine_tuning_environment
  - `dataset`: Preprocessed financial dataset
  - `training_args`: Training hyperparameters and settings
- **Returns:** `TrainingResult` with fine-tuned model, metrics, and checkpoint paths
- **Raises:** `TrainingError` if fine-tuning fails, `GPUMemoryError` if resources insufficient

### Function: `quantize_model`

- **Signature:** `quantize_model(model_path: str, quantization_format: str, output_path: str, bits: int = 4) -> QuantizationResult`
- **Description:** Converts fine-tuned model to quantized format for efficient deployment.
- **Parameters:**
  - `model_path`: Path to fine-tuned model
  - `quantization_format`: Target format ('gptq', 'gguf')
  - `output_path`: Directory to save quantized model
  - `bits`: Quantization precision (4 or 8 bits)
- **Returns:** `QuantizationResult` with quantized model paths and metrics
- **Raises:** `QuantizationError` if quantization fails, `ValueError` for unsupported formats

### Function: `validate_fine_tuned_model`

- **Signature:** `validate_fine_tuned_model(model_path: str, test_dataset: Dataset) -> ValidationReport`
- **Description:** Evaluates fine-tuned model performance on financial tasks.
- **Parameters:**
  - `model_path`: Path to fine-tuned model
  - `test_dataset`: Test dataset for evaluation
- **Returns:** `ValidationReport` with performance metrics and sample outputs
- **Raises:** `ValidationError` if evaluation fails

## Data Structures

### Class: `FineTuningConfig`

```python
@dataclass
class FineTuningConfig:
    model_name: str
    model_path: str
    output_dir: str
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])
    device_map: str = "auto"
    torch_dtype: str = "float16"
```

### Class: `TrainingArguments`

```python
@dataclass
class TrainingArguments:
    output_dir: str
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    fp16: bool = True
    dataloader_num_workers: int = 4
```

### Class: `TrainingResult`

```python
@dataclass
class TrainingResult:
    model: any
    tokenizer: any
    training_loss: float
    eval_loss: float
    checkpoint_path: str
    training_time_seconds: int
    gpu_memory_usage_gb: float
    training_log: List[Dict[str, Any]]
```

### Class: `QuantizationResult`

```python
@dataclass
class QuantizationResult:
    quantized_model_path: str
    original_size_gb: float
    quantized_size_gb: float
    compression_ratio: float
    quantization_time_seconds: int
    inference_speed_tokens_per_sec: float
```

## Sample Financial Datasets

### Required Dataset Formats

1. **Financial News Sentiment Dataset**
   - Fields: `text` (news headline/article), `label` (positive/negative/neutral)
   - Format: JSONL with `{"text": "...", "label": "positive"}`

2. **Earnings Call Transcripts Dataset**
   - Fields: `text` (transcript segment), `context` (company, quarter, sentiment indicators)
   - Format: JSONL with `{"text": "...", "context": {...}}`

3. **Trading Analysis Dataset**
   - Fields: `prompt` (trading scenario), `completion` (analysis/recommendation)
   - Format: JSONL with `{"prompt": "...", "completion": "..."}`

## Supported Models

### Primary Target Models
- **DeepSeek-R1-0528**: Specialized reasoning model
- **Qwen3-235B-Instruct-2507**: Large instruction-tuned model
- **Llama-3.1-8B/70B**: Open-source base models
- **Mistral-7B/34B**: Efficient instruction models

### Model-Specific Configurations
- Each supported model has predefined optimal LoRA target modules
- Hardware requirement matrices for different model sizes
- Pre-tested quantization parameters per model

## Error Handling

### Exception Hierarchy
- `FineTuningError`: Base exception class
- `EnvironmentError`: GPU/memory/resource issues
- `DatasetError`: Data processing problems
- `TrainingError`: Fine-tuning process failures
- `QuantizationError`: Model quantization issues
- `ValidationError`: Model evaluation problems

### Recovery Strategies
- Automatic GPU memory optimization
- Checkpoint-based training resumption
- Fallback quantization methods
- Graceful degradation for resource constraints

## Integration Points

### With Core Framework
- Uses existing security module for API key management
- Integrates with logging system for training monitoring
- Compatible with existing configuration management

### With Model Serving
- Fine-tuned models work seamlessly with vLLM integration
- Quantized models compatible with Ollama/llama.cpp
- Support for existing model deployment pipelines

### With Testing Framework
- Integration with pytest for unit tests
- Backtesting support for fine-tuned models
- Performance benchmarking capabilities

## Performance Requirements

### Training Performance
- Support for consumer GPUs (24GB VRAM minimum)
- Training time: < 12 hours for 7B models on financial datasets
- Memory optimization for large models (>70B parameters)

### Quantization Performance
- GPTQ quantization: < 2 hours for 70B models
- GGUF conversion: < 1 hour for 70B models
- Inference speed improvement: 2-4x over FP16

### Quality Metrics
- BLEU score improvement: > 15% over base model
- Financial task accuracy: > 85% on test datasets
- Coherence score: > 4.0/5.0 on human evaluation

## Dependencies

### Required Libraries
- `transformers>=4.35.0`: Model fine-tuning
- `peft>=0.6.0`: Parameter-efficient fine-tuning
- `bitsandbytes>=0.41.0`: 4-bit quantization support
- `auto-gptq>=0.7.0`: GPTQ quantization
- `llama-cpp-python>=0.2.0`: GGUF conversion
- `accelerate>=0.24.0`: Distributed training
- `datasets>=2.14.0`: Dataset handling

### Hardware Requirements
- GPU: RTX 3080+ (24GB VRAM recommended)
- RAM: 64GB minimum for large models
- Storage: 100GB+ for model files and datasets

## Usage Examples

### Basic Fine-Tuning Workflow
```python
from quantchain.tools.model_fine_tuning import (
    setup_fine_tuning_environment,
    prepare_financial_dataset,
    fine_tune_model_qlora,
    quantize_model
)

# Setup environment
config = setup_fine_tuning_environment(
    model_name="deepseek-r1-0528",
    base_model_path="deepseek-ai/deepseek-coder-6.7b-base",
    output_dir="./fine_tuned_models"
)

# Prepare dataset
dataset = prepare_financial_dataset(
    dataset_path="./data/financial_news.jsonl",
    tokenizer=config.tokenizer,
    max_length=2048
)

# Fine-tune model
result = fine_tune_model_qlora(
    config=config,
    dataset=dataset,
    training_args=TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4
    )
)

# Quantize for deployment
quant_result = quantize_model(
    model_path=result.checkpoint_path,
    quantization_format="gguf",
    output_path="./quantized_models",
    bits=4
)
```

## Testing Strategy

### Unit Tests
- Configuration validation
- Dataset preprocessing accuracy
- Error handling and recovery

### Integration Tests
- End-to-end fine-tuning workflow
- Model quantization pipeline
- Quality assessment metrics

### Performance Tests
- Training speed benchmarks
- Memory usage validation
- Inference performance comparison

## Documentation Requirements

### User Documentation
- Getting started guide with step-by-step workflows
- Hardware requirement matrix
- Troubleshooting common issues
- Best practices for financial fine-tuning

### Developer Documentation
- API reference for all functions
- Code architecture overview
- Extension guidelines for new models
- Testing and validation procedures
