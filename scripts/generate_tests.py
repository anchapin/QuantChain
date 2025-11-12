#!/usr/bin/env python3
"""
Custom test generation script using Z.AI API.
This script generates pytest-compatible test cases for Python files.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestGenerator:
    """Generates pytest test cases for Python files using Z.AI API."""

    def __init__(
        self, api_key: str, base_url: str = "https://api.z.ai/api/coding/paas/v4"
    ):
        """Initialize with Z.AI API key and base URL."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def extract_functions_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions and classes from a Python file."""
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract function signature and docstring
                func_info = {
                    "name": node.name,
                    "type": "function",
                    "lineno": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "args": [arg.arg for arg in node.args.args],
                }
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                # Extract class methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": f"{node.name}.{item.name}",
                            "type": "method",
                            "lineno": item.lineno,
                            "docstring": ast.get_docstring(item),
                            "args": [
                                arg.arg for arg in item.args.args[1:]
                            ],  # Skip 'self'
                        }
                        functions.append(method_info)

        return functions

    def generate_test_cases(self, file_path: str) -> str:
        """Generate test cases for a Python file."""
        # Extract functions/classes from the file
        functions = self.extract_functions_from_file(file_path)

        # Read the source file
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Create prompt for OpenAI
        module_name = Path(file_path).stem
        prompt = f"""Generate comprehensive pytest test cases for the following Python module: {module_name}

Source Code:
```python
{source_code}
```

Functions/Classes to test:
{chr(10).join(f"- {func['name']} (line {func['lineno']})" for func in functions)}

Requirements:
1. Generate pytest-compatible test cases
2. Include edge cases, error handling, and boundary conditions
3. Use appropriate fixtures and mocking for external dependencies
4. Ensure tests are independent and follow AAA pattern (Arrange-Act-Assert)
5. Include descriptive test names that explain what is being tested
6. Use type hints where applicable
7. Mock external API calls and database interactions
8. Test both success and failure scenarios

Generate only the test code without explanations:"""

        try:
            data = {
                "model": "glm-4.6",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a Python testing expert. Generate comprehensive pytest test cases.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            print(f"Error generating tests: {e}")
            return ""

    def create_test_file(self, source_path: str) -> str:
        """Create a test file for the given source file."""
        # Generate test content
        test_content = self.generate_test_cases(source_path)

        if not test_content:
            print(f"Failed to generate tests for {source_path}")
            return ""

        # Determine test file path
        source_path = Path(source_path)
        test_dir = source_path.parent / "tests"
        test_file = test_dir / f"test_{source_path.name}"

        # Ensure test directory exists
        test_dir.mkdir(exist_ok=True)

        # Create the test file
        test_path = str(test_file)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(
                f"""# Auto-generated test file for {source_path.name}
# Generated using Z.AI GLM-4.6 API

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

{test_content}
"""
            )

        return test_path


def main():
    """Main function to generate tests."""
    if len(sys.argv) != 2:
        print("Usage: python generate_tests.py <python_file_path>")
        sys.exit(1)

    # Get Z.AI API key
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key or api_key == "your-zai-api-key-here":
        print("Error: ZAI_API_KEY environment variable not set or invalid")
        print("Please set your Z.AI API key in the .env file")
        sys.exit(1)

    # Get base URL from environment or use default
    base_url = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File {file_path} not found")
        sys.exit(1)

    # Generate tests
    generator = TestGenerator(api_key, base_url)
    test_file = generator.create_test_file(file_path)

    if test_file:
        print(f"Test file generated: {test_file}")
        print("Run the tests with: pytest " + test_file)
    else:
        print("Failed to generate test file")
        sys.exit(1)


if __name__ == "__main__":
    main()
