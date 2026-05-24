#!/bin/bash

# Dependency installation script for DepthOS C++
# This script installs required dependencies on macOS

set -e

echo "=== Installing Dependencies for DepthOS C++ ==="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install dependencies
echo "Installing cmake, openssl, curl, and boost..."
brew install cmake openssl curl boost

# Verify installations
echo ""
echo "=== Verifying Installations ==="
echo "cmake: $(cmake --version | head -n1)"
echo "openssl: $(openssl version | head -n1)"
echo "curl: $(curl --version | head -n1)"
echo "boost: $(brew list boost 2>/dev/null | head -n1 || echo 'Not found')"

echo ""
echo "=== Dependencies Installed Successfully ==="
echo "You can now run: ./build.sh"
