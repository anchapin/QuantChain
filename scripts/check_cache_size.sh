#!/bin/bash
# Script to check pip cache size in GitHub Actions

echo "=== Pip Cache Information ==="
pip cache info

echo -e "\n=== Pip Cache Directory Size ==="
if [ -d ~/.cache/pip ]; then
    du -sh ~/.cache/pip
    echo -e "\n=== Top 10 Largest Items in Pip Cache ==="
    find ~/.cache/pip -type f -exec du -h {} + | sort -rh | head -10
else
    echo "No pip cache directory found"
fi

echo -e "\n=== System Memory Usage ==="
free -h

echo -e "\n=== Disk Usage ==="
df -h
