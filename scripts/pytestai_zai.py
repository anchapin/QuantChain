#!/usr/bin/env python3
"""
PyTestAI with Z.AI GLM-4.6 support
Drop-in replacement for PyTestAI-Generator using Z.AI API
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from generate_tests import TestGenerator

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()


def main():
    """Main function."""


if len(sys.argv) != 2:
    print("Usage: pytestai_zai <python_file_path>")
    print("Example: pytestai_zai path/to/your/file.py")
    sys.exit(1)

# Get Z.AI API key
api_key = os.getenv("ZAI_API_KEY")
if not api_key or api_key == "your-zai-api-key-here":
    print("Error: ZAI_API_KEY environment variable not set or invalid")
    print("Please set your Z.AI API key in .env file")
    sys.exit(1)

    # Get base URL from environment or use default
    base_url = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print("Error: File {} not found".format(file_path))
        sys.exit(1)

    print("🚀 Generating tests using Z.AI GLM-4.6...")

    # Generate tests
    generator = TestGenerator(api_key, base_url)
    test_file = generator.create_test_file(file_path)

    if test_file:
        print(f"✅ Test file generated: {test_file}")
        print(f"Run the tests with: pytest {test_file}")
    else:
        print("❌ Failed to generate test file")
        sys.exit(1)


if __name__ == "__main__":
    main()
