# Chess Openings Tier List

A comprehensive, data-driven tier list for chess openings based on real Lichess game statistics. This application automatically collects and analyzes chess opening performance data to create an interactive tier list that you can customize and filter.

## ✨ Features

- **📊 Data-Driven Rankings**: Based on real Lichess game statistics with 100,000+ games per opening
- **🎯 Interactive Tier List**: Drag-and-drop interface for creating custom tier lists (S, A, B, C, D tiers)
- **🔍 Advanced Filtering**: Filter by rating range, time control, and minimum games played
- **📈 Performance Metrics**: Win rates, draw rates, performance scores, and average ratings
- **🔄 Automated Updates**: Hourly/daily data updates from Lichess API with rate limiting
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **⚡ Real-Time**: Live data updates and interactive statistics

## 🎮 Demo

The tier list shows the top 50 chess openings with detailed statistics:
- **ECO codes** and **opening names**
- **Performance scores** (composite rating)
- **Win rates** for White/Black/Draws
- **Total games** and **average player ratings**
- **Move sequences** in algebraic notation

## 🏗️ Architecture

```
chess-openings-tierlist/
├── 📊 data_collection/     # Lichess API data collection
│   ├── collect_openings.py    # Main data collector
│   └── data_processor.py      # Database processor
├── 🔌 api/                 # FastAPI backend server
│   └── main.py                # REST API endpoints
├── 🖥️ frontend/            # React TypeScript app
│   ├── src/components/        # UI components
│   ├── src/services/          # API integration
│   └── src/types/             # TypeScript definitions
├── 🗄️ database/            # SQLAlchemy models
│   └── models.py              # Database schema
├── 🔧 scripts/             # Automation & deployment
│   ├── setup.sh              # One-click setup
│   ├── init_db.py            # Database initialization
│   ├── update_data.py        # Automated updates
│   └── test_system.py        # System testing
└── ⚙️ config/              # Configuration files
    └── .env.example          # Environment template
```

## 🚀 Quick Start

### Option 1: Automated Setup
```bash
# Clone and setup everything
git clone <repository>
cd chess-openings-tierlist
chmod +x scripts/setup.sh
./scripts/setup.sh

# Add your Lichess API token to config/.env
# Get token from: https://lichess.org/account/oauth/token

# Collect and process initial data
python3 data_collection/collect_openings.py
python3 data_collection/data_processor.py database/openings_data_*.json

# Start the application
python3 api/main.py &          # Backend (port 8000)
cd frontend && npm start       # Frontend (port 3000)
```

### Option 2: Manual Setup
```bash
# 1. Install Python dependencies
pip3 install -r requirements.txt

# 2. Set up configuration
cp config/.env.example config/.env
# Edit config/.env and add your LICHESS_API_TOKEN

# 3. Initialize database
python3 scripts/init_db.py

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Run system tests
python3 scripts/test_system.py

# 6. Start both services
python3 api/main.py &
cd frontend && npm start
```

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Lichess API Token** (free from https://lichess.org/account/oauth/token)

## 🔧 Configuration

Key settings in `config/.env`:
```bash
LICHESS_API_TOKEN=your_token_here
DATABASE_URL=sqlite:///./chess_openings.db
UPDATE_INTERVAL_HOURS=6
MAX_REQUESTS_PER_MINUTE=60
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

## 🤖 Automated Updates

Set up continuous data updates:
```bash
# Run scheduled updates (recommended for production)
python3 scripts/update_data.py --mode schedule

# Or run single updates
python3 scripts/update_data.py --mode once --type full
```

## 🧪 Testing

Comprehensive system testing:
```bash
# Test everything
python3 scripts/test_system.py

# Test specific components
python3 scripts/test_system.py --test database
python3 scripts/test_system.py --test api
python3 scripts/test_system.py --test lichess
```

## 🚀 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions including:
- Docker containerization
- Reverse proxy setup
- Process management
- Monitoring and logging
- Performance optimization

## 🛠️ API Endpoints

- `GET /openings` - List openings with filtering
- `GET /tier-list` - Get tier list data
- `POST /tier-list` - Update tier list
- `GET /statistics/summary` - System statistics
- `GET /statistics/top-performers` - Best performing openings

## 🎨 Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- berserk (Lichess API client)
- Pydantic (Data validation)

**Frontend:**
- React 18 with TypeScript
- @dnd-kit (Drag and drop)
- Axios (HTTP client)
- CSS3 with responsive design

**Data:**
- SQLite (default) / PostgreSQL (production)
- Lichess Opening Explorer API
- Automated ETL pipeline

## 📊 Data Sources

This application uses the [Lichess Opening Explorer API](https://lichess.org/api#tag/Opening-Explorer) to collect:
- Game statistics for chess openings
- Performance data across rating ranges
- Historical trends and move popularity
- Master games and recent games examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python3 scripts/test_system.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Lichess](https://lichess.org) for providing the excellent API and chess platform
- [berserk library](https://github.com/lichess-org/berserk) for Lichess API integration
- Chess opening database maintainers and the chess community

## 📞 Support

- Create an issue for bug reports
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- See logs in the `logs/` directory for troubleshooting