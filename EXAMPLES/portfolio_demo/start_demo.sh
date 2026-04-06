#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "Starting supported Portfolio Agent demo on http://127.0.0.1:8000/demo"
echo "The demo uses PortfolioAgent.from_settings() and may download the default HF model on first run."
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
