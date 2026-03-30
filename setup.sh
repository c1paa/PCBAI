#!/bin/bash
# Setup script for PCBAI
# Run this to install dependencies and setup the project

set -e

echo "=== PCBAI Setup ==="
echo ""

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python not found! Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYTHON_VERSION found: $PYTHON"

# Check Java
echo ""
echo "Checking Java..."
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo "✓ Java found: $JAVA_VERSION"
else
    echo "⚠ Java not found. Install Java for FreeRouting:"
    echo "  macOS: brew install java"
    echo "  Ubuntu: sudo apt install default-jre"
    echo "  Windows: Download from https://www.java.com/download/"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
$PYTHON -m venv venv
echo "✓ Virtual environment created"

# Activate and install
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Check system: pcba check"
echo "  3. Download FreeRouting: pcba download-freerouting"
echo "  4. Try example: pcba inspect examples/simple_led.kicad_pcb"
echo ""
