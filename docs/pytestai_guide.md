# PyTestAI Guide for QuantChain

This guide explains how to use AI-powered test generation tools to achieve and maintain the required 80% test coverage for the QuantChain project.

## Overview

QuantChain requires a minimum of 80% test coverage for all code contributions. To help developers achieve this efficiently, we've set up AI-powered test generation tools.

## Tools Available

### 1. PyTestAI with Z.AI (Recommended)

We've created a custom PyTestAI implementation that uses Z.AI's GLM-4.6 model for high-quality test generation.

**Location:** `scripts/pytestai_zai.py`

**Prerequisites:**
- Z.AI API key set in `.env` file
- Dependencies installed: `requests` and `python-dotenv`

**Setup:**
```bash
# Add to your .env file
ZAI_API_KEY="your-zai-api-key-here"
ZAI_BASE_URL="https://api.z.ai/api/coding/paas/v4"
```

**Usage:**
```bash
# Generate tests for a file
python scripts/pytestai_zai.py "path/to/your/file.py"
```

### 2. Custom Test Generator (Advanced)

For more control over test generation, use the enhanced custom script that now supports Z.AI API.

**Location:** `scripts/generate_tests.py`

**Prerequisites:**
- Z.AI API key set in `.env` file
- Dependencies installed: `requests` and `python-dotenv`

**Usage:**
```bash
# Generate tests for a file (uses Z.AI by default)
python scripts/generate_tests.py "path/to/your/file.py"
```

### 3. PyTestAI-Generator (Legacy)

The original PyTestAI-Generator tool using DeepSeek API is still available if needed.

**Installation:**
```bash
pip install PyTestAI-Generator
```

**Usage:**
```bash
# Set DeepSeek API key
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"

# Generate tests for a file
pytestai "path/to/your/file.py"
```

**Limitations:**
- Only supports DeepSeek API
- Requires DeepSeek API key
- May have encoding issues on Windows

## Best Practices for Test Generation

### 1. Before Generating Tests

1. **Identify Low Coverage Files:**
   ```bash
   pytest tests/unit -v --cov=quantchain --cov-report=term-missing
   ```
   Look for files with coverage below 80%.

2. **Review the Source Code:**
   - Understand the main functionality
   - Identify key methods and classes
   - Note external dependencies

### 2. Generating Tests

1. **For Simple Modules:**
   - Use the custom generator: `python scripts/generate_tests.py path/to/module.py`
   - The test will be created in `tests/unit/path/to/test_module.py`

2. **For Complex Modules:**
   - Generate initial tests with AI
   - Review and enhance manually
   - Add integration tests if needed

### 3. After Generating Tests

1. **Run the Tests:**
   ```bash
   pytest tests/unit/path/to/test_module.py -v
   ```

2. **Fix Any Issues:**
   - Resolve import errors
   - Fix failing assertions
   - Add missing mocks

3. **Verify Coverage:**
   ```bash
   pytest tests/unit/path/to/test_module.py --cov=path/to/module --cov-report=term-missing
   ```

## Example Workflow

Let's walk through an example of improving test coverage for `backtestingpy_engine.py`:

1. **Check Current Coverage:**
   ```bash
   pytest tests/unit -v --cov=quantchain/backtesting/backtestingpy_engine
   # Result: 0% coverage
   ```

2. **Generate Tests:**
   ```bash
   python scripts/generate_tests.py "quantchain/backtesting/backtestingpy_engine.py"
   ```

3. **Run Generated Tests:**
   ```bash
   pytest tests/unit/backtesting/test_backtestingpy_engine.py -v
   ```

4. **Check New Coverage:**
   ```bash
   pytest tests/unit -v --cov=quantchain/backtesting/backtestingpy_engine
   # Result: 89.3% coverage
   ```

## Manual Test Enhancement Tips

When AI-generated tests need improvement:

1. **Add More Edge Cases:**
   - Test with null/None values
   - Test boundary conditions
   - Test with empty collections

2. **Improve Mocking:**
   - Mock all external dependencies
   - Use `unittest.mock.patch` effectively
   - Test both success and failure paths

3. **Add Integration Tests:**
   - Test component interactions
   - Use real data where safe
   - Test end-to-end workflows

## CI/CD Integration

The project's CI/CD pipeline enforces 80% test coverage:

1. **Pre-commit Hook:**
   - Automatically checks coverage before each commit
   - Blocks commits if coverage < 80%

2. **GitHub Actions:**
   - Runs tests on pull requests
   - Fails PR if coverage requirements not met

3. **Codecov:**
   - Tracks coverage over time
   - Provides detailed coverage reports

## Common Issues and Solutions

### Issue 1: Unicode Errors on Windows
**Solution:** Use the custom Python script instead of PyTestAI-Generator

### Issue 2: Missing API Keys
**Solution:** Ensure API keys are set in environment variables:
```bash
# For Z.AI (recommended)
ZAI_API_KEY="your-zai-api-key-here"
ZAI_BASE_URL="https://api.z.ai/api/coding/paas/v4"

# For OpenAI (legacy)
$env:OPENAI_API_KEY="your-key"

# For DeepSeek (legacy)
$env:DEEPSEEK_API_KEY="your-key"
```

### Issue 3: Generated Tests Don't Run
**Solution:**
- Check import paths
- Ensure all dependencies are mocked
- Verify test file location

### Issue 4: Coverage Not Improving
**Solution:**
- Ensure test file follows naming convention `test_*.py`
- Check that tests are in the correct directory
- Verify tests are actually testing the target module

## Target Files for Test Generation

Priority files needing better test coverage (based on current reports):

1. **Backtesting Module:**
   - `backtesting/finrl_adapter.py` (13% coverage)
   - `backtesting/langgraph_adapter.py` (26% coverage)
   - `backtesting/vector_backtester.py` (0% coverage)

2. **Connectors:**
   - `connectors/ccxt_connector.py` (11% coverage)
   - `connectors/dexscreener_connector.py` (68% coverage)

3. **Secret Managers:**
   - `core/secret_managers/aws.py` (9% coverage)
   - `core/secret_managers/gcp.py` (9% coverage)
   - `core/secret_managers/vault.py` (13% coverage)

## Conclusion

Using AI-powered test generation tools can significantly accelerate achieving the 80% test coverage requirement. However, always review and enhance generated tests to ensure they properly validate your code's functionality.

Remember: High test coverage is important, but test quality is paramount. Focus on testing critical paths, error handling, and edge cases.
