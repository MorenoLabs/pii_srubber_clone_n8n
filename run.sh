#!/bin/bash

# Quick start script for PII Scrubber API

echo "Starting PII Scrubber API..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Download spacy model if not present
echo "Checking NLP models..."
python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null || {
    echo "Downloading language model..."
    python -m spacy download en_core_web_lg
}

# Start the API
echo "=========================================="
echo "Starting API server on http://localhost:8000"
echo "API Docs available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo "=========================================="

uvicorn app:app --reload --host 0.0.0.0 --port 8000