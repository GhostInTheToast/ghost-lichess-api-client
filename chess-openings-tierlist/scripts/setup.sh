#!/bin/bash
# Setup script for Chess Openings Tier List

set -e

echo "🏁 Starting Chess Openings Tier List setup..."

# Create logs directory
mkdir -p logs
echo "📁 Created logs directory"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not installed. Please install pip."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if .env file exists
if [ ! -f "config/.env" ]; then
    echo "⚙️ Creating configuration file..."
    cp config/.env.example config/.env
    echo "📝 Please edit config/.env and add your Lichess API token"
    echo "   You can get a token from: https://lichess.org/account/oauth/token"
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 scripts/init_db.py

# Check if Node.js is available for frontend
if command -v npm &> /dev/null; then
    echo "🌐 Setting up frontend..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend setup complete"
else
    echo "⚠️ Node.js/npm not found. Frontend setup skipped."
    echo "   To set up the frontend later, run: cd frontend && npm install"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config/.env and add your Lichess API token"
echo "2. Collect initial data: python3 data_collection/collect_openings.py"
echo "3. Process data: python3 data_collection/data_processor.py database/openings_data_*.json"
echo "4. Start API server: python3 api/main.py"
echo "5. Start frontend: cd frontend && npm start"
echo ""
echo "For automated updates: python3 scripts/update_data.py --mode schedule"