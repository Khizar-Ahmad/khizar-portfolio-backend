#!/bin/bash
echo "🚀 Starting Portfolio Backend..."

# Check if .env exists
if [ ! -f .env ]; then
  echo "⚠️  No .env found — copying from .env.example"
  cp .env.example .env
  echo "📝 Edit .env with your values before running again!"
  exit 1
fi

# Install deps if needed
if [ ! -d venv ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Start server
echo "✅ Starting FastAPI on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
