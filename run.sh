#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Setting up..."
    python3 -m venv venv
    source venv/bin/activate
    pip install beautifulsoup4 --quiet
else
    source venv/bin/activate
fi

python3 extract_answers.py

