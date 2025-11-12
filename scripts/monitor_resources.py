#!/usr/bin/env python3
"""
Resource monitoring script for QuantChain testing.
This script monitors disk, memory, and CPU usage during test execution.
"""

import os
import time
import psutil
import subprocess
import json
from datetime import datetime


def get_disk_usage(path="/"):
    """Get disk usage statistics."""
    disk = psutil.disk_usage(path)
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "percent": disk.percent,
    }


def get_memory_usage():
    """Get memory usage statistics."""
    memory = psutil.virtual_memory()
    return {
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "percent": memory.percent,
    }


def get_cpu_usage():
    """Get CPU usage statistics."""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "count": psutil.cpu_count(),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
    }


def get_pip_cache_size():
    """Get pip cache directory size."""
    try:
        result = subprocess.run(
            ["pip", "cache", "dir"], capture_output=True, text=True, check=True
        )
        cache_dir = result.stdout.strip()
        if os.path.exists(cache_dir):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return round(total_size / (1024**2), 2)  # Size in MB
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def monitor_resources(output_file=None):
    """Monitor system resources and optionally save to file."""
    timestamp = datetime.now().isoformat()

    stats = {
        "timestamp": timestamp,
        "disk": get_disk_usage(),
        "memory": get_memory_usage(),
        "cpu": get_cpu_usage(),
        "pip_cache_mb": get_pip_cache_size(),
    }

    # Print to console
    print(f"\n=== Resource Monitor at {timestamp} ===")
    print(
        f"Disk: {stats['disk']['used_gb']}/{stats['disk']['total_gb']} GB "
        f"({stats['disk']['percent']}%)"
    )
    print(
        f"Memory: {stats['memory']['used_gb']}/{stats['memory']['total_gb']} GB "
        f"({stats['memory']['percent']}%)"
    )
    print(f"CPU: {stats['cpu']['percent']}% across {stats['cpu']['count']} cores")
    if stats["pip_cache_mb"]:
        print(f"Pip Cache: {stats['pip_cache_mb']} MB")

    # Save to file if specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "a") as f:
            json.dump(stats, f)
            f.write("\n")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor system resources")
    parser.add_argument(
        "--output",
        help="Output file path for JSON logs",
        default="logs/resource_monitor.jsonl",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Monitoring interval in seconds (for continuous monitoring)",
        default=0,
    )

    args = parser.parse_args()

    if args.interval > 0:
        print(f"Starting continuous monitoring every {args.interval} seconds...")
        try:
            while True:
                monitor_resources(args.output)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        monitor_resources(args.output)
