#!/bin/bash

# Get absolute path to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define virtual environment paths
VENV_PATH="${SCRIPT_DIR}/venv"
VENV_PYTHON="${VENV_PATH}/bin/python3"
VENV_SITE_PACKAGES="${VENV_PATH}/lib/python3.11/site-packages"

# Set capabilities for virtual environment Python
sudo setcap 'cap_sys_nice=eip' "${VENV_PYTHON}"

# Run with sudo, preserving environment and adding virtual environment to Python path
sudo -E PYTHONPATH="${VENV_SITE_PACKAGES}:${SCRIPT_DIR}" "${VENV_PYTHON}" setup.py \
    --led-gpio-slowdown=4 \
    --led-brightness=70 \
    --led-rows=64 \
    --led-cols=64 \
    --led-chain=1 \
    --led-parallel=1 2>&1 | tee setup_debug.log