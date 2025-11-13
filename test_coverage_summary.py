#!/usr/bin/env python3
"""Analyze test coverage and identify modules that need more tests."""

import json

# Load coverage data
with open('htmlcov/status.json', 'r') as f:
    coverage_data = json.load(f)

# Calculate coverage for each module
modules = []
total_statements = 0
total_missing = 0

for file_id, file_data in coverage_data['files'].items():
    nums = file_data['index']['nums']
    statements = nums['n_statements']
    missing = nums['n_missing']
    covered = statements - missing
    coverage_pct = (covered / statements * 100) if statements > 0 else 0
    
    modules.append({
        'file': file_data['index']['file'],
        'statements': statements,
        'missing': missing,
        'covered': covered,
        'coverage_pct': coverage_pct
    })
    
    total_statements += statements
    total_missing += missing

# Sort by coverage percentage (lowest first)
modules.sort(key=lambda x: x['coverage_pct'])

# Calculate overall coverage
total_covered = total_statements - total_missing
overall_coverage = (total_covered / total_statements * 100) if total_statements > 0 else 0

print(f"\nOverall Test Coverage: {overall_coverage:.1f}%")
print(f"Total Statements: {total_statements}")
print(f"Covered: {total_covered}")
print(f"Missing: {total_missing}")
print("\n" + "="*80)
print("MODULES THAT NEED MORE TEST COVERAGE:")
print("="*80)

for module in modules:
    if module['coverage_pct'] < 80:  # Show modules below 80% coverage
        print(f"\n{module['file']}:")
        print(f"  Coverage: {module['coverage_pct']:.1f}% ({module['covered']}/{module['statements']} statements)")
        print(f"  Missing: {module['missing']} lines")
