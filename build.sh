#!/bin/bash
#
# Build Script for Academic Command Center
# Packages the application using PyInstaller
#

echo "==========================================="
echo "Academic Command Center - Build Script"
echo "==========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "L Virtual environment not found!"
    echo "Please run install.sh first"
    exit 1
fi

# Activate virtual environment
echo "=æ Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install PyInstaller if not present
echo "=æ Checking PyInstaller..."
pip install --quiet pyinstaller

# Clean previous builds
echo ">ù Cleaning previous builds..."
rm -rf build/ dist/

# Build with PyInstaller
echo "=( Building application..."
pyinstaller academic_command_center.spec

if [ $? -eq 0 ]; then
    echo ""
    echo " Build successful!"
    echo ""
    echo "=Á Executable location: dist/AcademicCommandCenter/"
    echo ""
    echo "To run the application:"
    echo "  cd dist/AcademicCommandCenter"
    echo "  ./AcademicCommandCenter"
    echo ""
else
    echo ""
    echo "L Build failed!"
    echo "Check the error messages above"
    exit 1
fi
