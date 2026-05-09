#!/bin/bash
cd "$(dirname "$0")"
echo "Setting up Auto Data Scientist Backend..."

python -m venv venv
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
echo "Backend setup complete!"
echo "Run with: uvicorn main:app --reload --port 8000"
