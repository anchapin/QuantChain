#!/usr/bin/env python3
"""
QuantChain Installation Script
Comprehensive quantitative trading framework
"""

import os
import sys
from pathlib import Path

# Try to use setuptools, fallback to distutils
try:
    from setuptools import setup, find_packages
    HAS_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    HAS_SETUPTOOLS = False

# Version information
VERSION = "0.1.0"

# Core dependencies (always installed)
CORE_REQUIREMENTS = [
    "langchain>=0.2.0,<2.0.0",
    "openai>=1.0.0,<3.0.0", 
    "pandas>=1.5.0,<3.0.0",
    "numpy>=1.24.0,<3.0.0",
    "PyYAML>=6.0,<7.0.0",
    "gymnasium>=0.26.0,<1.0.0",
    "yfinance>=0.2.0",
    "scikit-learn>=1.3.0",
    "scipy>=1.10.0",
    "matplotlib>=3.6.0",
    "requests>=2.28.0",
    "python-dotenv>=1.0.0",
]

# Development requirements
DEV_REQUIREMENTS = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "pytest-timeout>=2.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-xdist>=3.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "pre-commit>=3.0.0",
]

# ML requirements (heavy dependencies)
ML_REQUIREMENTS = [
    "torch>=2.0.0",
    "transformers>=4.30.0",
    "sentence-transformers>=2.2.0",
    "finrl>=0.3.0",
]

# Visualization requirements
VISUALIZATION_REQUIREMENTS = [
    "plotly>=5.15.0",
    "streamlit>=1.25.0",
    "seaborn>=0.12.0",
    "dash>=2.10.0",
    "jupyter>=1.0.0",
    "notebook>=6.5.0",
]

# Conditional dependencies
PYTHON_VERSION = sys.version_info
if PYTHON_VERSION >= (3, 10):
    CORE_REQUIREMENTS.append("ib_async>=1.0.0")

# Optional dependencies for different use cases
OPTIONAL_DEPENDENCIES = {
    'dev': DEV_REQUIREMENTS,
    'ml': ML_REQUIREMENTS,
    'visualization': VISUALIZATION_REQUIREMENTS,
    'all': DEV_REQUIREMENTS + ML_REQUIREMENTS + VISUALIZATION_REQUIREMENTS,
    'ci': ['pytest>=7.0.0', 'pytest-cov>=4.0.0', 'plotly>=5.15.0', 'streamlit>=1.25.0'],
}

# Long description
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        LONG_DESCRIPTION = f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = "Comprehensive quantitative trading framework with AI-powered strategies"

# Setup configuration
setup_config = {
    'name': 'quantchain',
    'version': VERSION,
    'author': 'QuantChain Team',
    'author_email': 'contact@quantchain.ai',
    'description': 'Comprehensive quantitative trading framework',
    'long_description': LONG_DESCRIPTION,
    'long_description_content_type': 'text/markdown',
    'url': 'https://github.com/anchapin/QuantChain',
    'project_urls': {
        'Bug Tracker': 'https://github.com/anchapin/QuantChain/issues',
        'Documentation': 'https://github.com/anchapin/QuantChain/docs',
        'Source Code': 'https://github.com/anchapin/QuantChain',
    },
    'packages': find_packages(exclude=['tests*', 'docs*', 'examples*']),
    'include_package_data': True,
    'python_requires': '>=3.9',
    'install_requires': CORE_REQUIREMENTS,
    'extras_require': OPTIONAL_DEPENDENCIES,
    'entry_points': {
        'console_scripts': [
            'quantchain=quantchain.cli.main:main',
        ],
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Office/Business :: Financial',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    'keywords': 'quantitative trading, finance, machine learning, ai, blockchain',
    'license': 'MIT',
    'zip_safe': False,
}

# Add setuptools-specific options
if HAS_SETUPTOOLS:
    setup_config.update({
        'test_suite': 'tests',
        'tests_require': DEV_REQUIREMENTS,
    })

# Run setup
if __name__ == '__main__':
    try:
        setup(**setup_config)
        print("QuantChain setup completed successfully")
    except Exception as e:
        print(f"Error during setup: {e}")
        print(f"Setup config: {setup_config}")
        sys.exit(1)

