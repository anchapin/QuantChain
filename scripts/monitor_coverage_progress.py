#!/usr/bin/env python3
"""
Monitor progress towards 80% test coverage goal.
Provides detailed analysis and tracking of coverage improvements.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CoverageMonitor:
    """Monitor and track test coverage progress."""
    
    def __init__(self, history_file: str = "coverage_history.json"):
        self.history_file = Path(history_file)
        self.load_history()
    
    def load_history(self):
        """Load coverage history from file."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def save_history(self):
        """Save coverage history to file."""
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)
    
    def add_coverage_entry(self, coverage_data: Dict):
        """Add a new coverage entry to history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
            "files": coverage_data.get("files", {}),
            "summary": {
                "total_lines": coverage_data.get("totals", {}).get("num_statements", 0),
                "covered_lines": coverage_data.get("totals", {}).get("covered_lines", 0),
                "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0)
            }
        }
        self.history.append(entry)
        self.save_history()
        return entry
    
    def get_latest_coverage(self) -> Optional[Dict]:
        """Get the latest coverage entry."""
        return self.history[-1] if self.history else None
    
    def get_improvement_trend(self, entries: int = 5) -> List[float]:
        """Get coverage improvement trend over recent entries."""
        recent = self.history[-entries:] if len(self.history) >= entries else self.history
        return [entry["total_coverage"] for entry in recent]
    
    def analyze_low_coverage_files(self, coverage_data: Dict, threshold: float = 50) -> List[Dict]:
        """Analyze files with coverage below threshold."""
        low_coverage = []
        
        for file_path, file_data in coverage_data.get("files", {}).items():
            coverage = file_data.get("summary", {}).get("percent_covered", 0)
            if coverage < threshold:
                low_coverage.append({
                    "file": file_path,
                    "coverage": coverage,
                    "missing_lines": file_data.get("summary", {}).get("missing_lines", 0),
                    "total_lines": file_data.get("summary", {}).get("num_statements", 0),
                    "priority": self._get_priority(coverage)
                })
        
        return sorted(low_coverage, key=lambda x: x["coverage"])
    
    def _get_priority(self, coverage: float) -> str:
        """Determine priority based on coverage percentage."""
        if coverage < 20:
            return "CRITICAL"
        elif coverage < 40:
            return "HIGH"
        elif coverage < 60:
            return "MEDIUM"
        else:
            return "LOW"
    
    def generate_report(self) -> str:
        """Generate a comprehensive coverage report."""
        latest = self.get_latest_coverage()
        if not latest:
            return "No coverage data available."
        
        trend = self.get_improvement_trend()
        
        report = []
        report.append("=" * 60)
        report.append("TEST COVERAGE MONITORING REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Current Status
        report.append("📊 CURRENT STATUS")
        report.append("-" * 30)
        report.append(f"Total Coverage: {latest['total_coverage']:.2f}%")
        report.append(f"Target Coverage: 80.00%")
        report.append(f"Gap: {80 - latest['total_coverage']:.2f}%")
        report.append("")
        
        # Progress
        if len(trend) > 1:
            improvement = trend[-1] - trend[0]
            report.append("📈 PROGRESS")
            report.append("-" * 30)
            report.append(f"Recent Trend: {trend[-1]:.2f}% (from {trend[0]:.2f}%)")
            report.append(f"Improvement: {improvement:+.2f}%")
            
            if improvement > 0:
                report.append("✅ Improving")
            elif improvement < 0:
                report.append("⚠️ Declining")
            else:
                report.append("➡️ Stable")
            report.append("")
        
        # Milestones
        report.append("🎯 MILESTONES")
        report.append("-" * 30)
        milestones = [70, 75, 80, 85, 90]
        for milestone in milestones:
            if latest['total_coverage'] >= milestone:
                report.append(f"✅ {milestone}% - Achieved")
            else:
                remaining = milestone - latest['total_coverage']
                report.append(f"⏳ {milestone}% - {remaining:.2f}% to go")
        report.append("")
        
        # Recommendations based on current coverage
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 30)
        
        if latest['total_coverage'] < 60:
            report.append("🔴 Priority: Focus on critical modules with 0-30% coverage")
            report.append("   - ib_async_execution.py")
            report.append("   - Secret managers")
            report.append("   - High-priority backtesting modules")
        elif latest['total_coverage'] < 70:
            report.append("🟡 Priority: Address medium-coverage modules (30-60%)")
            report.append("   - vector_backtester.py")
            report.append("   - performance_metrics.py")
            report.append("   - langgraph_adapter.py")
        elif latest['total_coverage'] < 80:
            report.append("🟢 Priority: Polish edge cases and integration tests")
            report.append("   - Modules with 60-80% coverage")
            report.append("   - Error handling scenarios")
            report.append("   - Integration test coverage")
        else:
            report.append("✅ Target achieved! Focus on maintenance.")
        
        report.append("")
        
        return "\n".join(report)
    
    def print_file_analysis(self, coverage_data: Dict):
        """Print detailed file analysis."""
        print("\n📋 FILE COVERAGE ANALYSIS")
        print("=" * 60)
        
        low_coverage = self.analyze_low_coverage_files(coverage_data)
        
        if not low_coverage:
            print("✅ All files above coverage threshold!")
            return
        
        # Group by priority
        by_priority = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for file_info in low_coverage:
            by_priority[file_info["priority"]].append(file_info)
        
        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            files = by_priority[priority]
            if files:
                print(f"\n{priority} PRIORITY ({len(files)} files):")
                print("-" * 40)
                for file_info in files:
                    print(f"  {file_info['file']}")
                    print(f"    Coverage: {file_info['coverage']:.1f}%")
                    print(f"    Missing: {file_info['missing_lines']} lines")
                    print(f"    Total: {file_info['total_lines']} lines")


def main():
    """Main execution function."""
    monitor = CoverageMonitor()
    
    # Try to load current coverage data
    try:
        with open("coverage.json") as f:
            coverage_data = json.load(f)
        
        # Add to history
        monitor.add_coverage_entry(coverage_data)
        
        # Generate and print report
        print(monitor.generate_report())
        monitor.print_file_analysis(coverage_data)
        
    except FileNotFoundError:
        print("❌ coverage.json not found. Run coverage tests first:")
        print("   python -m pytest tests/unit --cov=quantchain --cov-report=json")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
