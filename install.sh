#!/bin/bash
#
# Installation Script for Academic Command Center
# Sets up virtual environment and installs dependencies
#

echo "==========================================="
echo "Academic Command Center - Installation"
echo "==========================================="
echo ""

# Check Python version
echo "= Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Python 3.11+ is available
if ! python3 -c 'import sys; assert sys.version_info >= (3,11)' 2>/dev/null; then
    echo "L Python 3.11 or higher is required!"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Create virtual environment
echo ""
echo "=æ Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "L Failed to create virtual environment!"
    exit 1
fi

# Activate virtual environment
echo "=æ Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "=æ Upgrading pip..."
pip install --quiet --upgrade pip

# Install dependencies
echo "=æ Installing dependencies..."
pip install --quiet -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo " Installation complete!"
    echo ""
    echo "To run the application:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run: python src/main.py"
    echo ""
    echo "To build standalone executable:"
    echo "  ./build.sh"
    echo ""
else
    echo ""
    echo "L Installation failed!"
    echo "Check the error messages above"
    exit 1
fi
