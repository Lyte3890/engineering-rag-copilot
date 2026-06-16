#!/bin/bash

# Engineering RAG Copilot - Automated Enterprise Installer
# --------------------------------------------------------

# Strict mode: exit on error
set -e

echo "=========================================================="
echo "    Engineering RAG Copilot - Setup Initialization        "
echo "=========================================================="

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] CRITICAL ERROR: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi
echo "[+] Python 3 detected."

# 2. Virtual Environment Setup
echo "[*] Creating virtual environment (venv)..."
python3 -m venv venv
echo "[+] Virtual environment created."

echo "[*] Activating virtual environment..."
source venv/bin/activate

# 3. Installing Dependencies
echo "[*] Installing Python dependencies from requirements.txt..."
# Use python -m pip to ensure we use the venv's pip
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
    echo "[+] Dependencies installed successfully."
else
    echo "[!] CRITICAL ERROR: requirements.txt not found!"
    exit 1
fi

# 4. Environment Variables Setup (.env)
if [ ! -f ".env" ]; then
    echo "=========================================================="
    echo "    API Key Configuration                                 "
    echo "=========================================================="
    echo "This RAG system requires a Groq API key to function."
    read -p "Enter your GROQ_API_KEY: " user_api_key
    echo "GROQ_API_KEY=$user_api_key" > .env
    echo "[+] .env file created."
else
    echo "[*] .env file already exists. Skipping API key prompt."
fi

# 5. Directory Initialization
echo "[*] Initializing storage directories..."
mkdir -p docs_storage
echo "[+] docs_storage/ created."

# 6. Optional: Download Test Data
echo "=========================================================="
read -p "Do you want to download sample technical documentation for testing? (y/n) " download_choice
if [[ "$download_choice" == "y" || "$download_choice" == "Y" ]]; then
    if [ -f "download_test_data.py" ]; then
        echo "[*] Running automated download pipeline..."
        python download_test_data.py
    else
        echo "[-] download_test_data.py not found. Skipping."
    fi
fi

echo "=========================================================="
echo "    Setup Complete!                                       "
echo "=========================================================="
echo ""
echo "To start the application in development mode, run:"
echo "  source venv/bin/activate"
echo "  python api.py"
echo ""
echo "For production deployment (Systemd + Gunicorn), please refer to the README.md"