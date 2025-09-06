# Deployment Guide

## Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 16+** with npm (for frontend)
3. **Lichess API Token** from https://lichess.org/account/oauth/token

## Quick Start

1. **Run the setup script:**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **Configure your API token:**
   Edit `config/.env` and add your Lichess API token:
   ```
   LICHESS_API_TOKEN=your_token_here
   ```

3. **Collect initial data:**
   ```bash
   cd data_collection
   python3 collect_openings.py
   ```

4. **Process the collected data:**
   ```bash
   cd data_collection
   python3 data_processor.py ../database/openings_data_*.json
   ```

5. **Start the API server:**
   ```bash
   cd api
   python3 main.py
   ```

6. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm start
   ```

7. **Visit http://localhost:3000** to see your tier list!

## Manual Deployment Steps

### 1. Environment Setup

```bash
# Create logs directory
mkdir -p logs

# Install Python dependencies
pip3 install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configuration

Copy the example config file:
```bash
cp config/.env.example config/.env
```

Edit `config/.env` with your settings:
- `LICHESS_API_TOKEN`: Your Lichess API token
- `DATABASE_URL`: Database connection string (default: SQLite)
- `API_HOST` and `API_PORT`: API server settings
- Update interval and rate limiting settings

### 3. Database Setup

```bash
python3 scripts/init_db.py
```

### 4. Data Collection

```bash
# Collect opening data from Lichess
python3 data_collection/collect_openings.py

# Process and load into database
python3 data_collection/data_processor.py database/openings_data_*.json
```

### 5. Testing

```bash
# Run comprehensive system tests
python3 scripts/test_system.py

# Test specific components
python3 scripts/test_system.py --test database
python3 scripts/test_system.py --test api
```

### 6. Production Deployment

#### API Server
```bash
# Install production dependencies
pip3 install gunicorn

# Start with gunicorn
cd api
gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend
```bash
cd frontend
npm run build

# Serve with nginx or your preferred web server
# Point to the build/ directory
```

#### Process Management
For production, use a process manager like systemd or supervisord:

```ini
# /etc/systemd/system/chess-openings-api.service
[Unit]
Description=Chess Openings API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/chess-openings-tierlist/api
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/gunicorn main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Automated Updates

### Set up scheduled data updates:

```bash
# Run once
python3 scripts/update_data.py --mode once --type full

# Run continuously with scheduling
python3 scripts/update_data.py --mode schedule
```

### Cron job alternative:
```bash
# Add to crontab for 6-hour updates
0 */6 * * * cd /path/to/chess-openings-tierlist && python3 scripts/update_data.py --mode once --type incremental
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LICHESS_API_TOKEN` | Required | Your Lichess API token |
| `DATABASE_URL` | `sqlite:///./chess_openings.db` | Database connection string |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `UPDATE_INTERVAL_HOURS` | `6` | Hours between automated updates |
| `MAX_REQUESTS_PER_MINUTE` | `60` | Rate limit for Lichess API |
| `LOG_LEVEL` | `INFO` | Logging level |

## Monitoring

### Health Checks
- API: `GET /` returns system status
- Database: `GET /statistics/summary` returns data summary

### Logs
- API logs: Check console output or configure logging
- Update logs: `logs/update_system.log`
- Data collection logs: `logs/data_collection.log`

### Metrics to Monitor
- API response times
- Database query performance
- Data update success rate
- Lichess API rate limit usage

## Troubleshooting

### Common Issues

1. **"LICHESS_API_TOKEN not found"**
   - Make sure `config/.env` exists and contains your API token

2. **Database connection errors**
   - Check `DATABASE_URL` in config
   - Ensure database file has write permissions (for SQLite)

3. **API server won't start**
   - Check if port 8000 is already in use
   - Verify all Python dependencies are installed

4. **Frontend can't connect to API**
   - Ensure API server is running
   - Check `REACT_APP_API_URL` in frontend/.env

5. **Rate limiting errors**
   - Reduce `MAX_REQUESTS_PER_MINUTE` in config
   - Increase delays between requests

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

Run components individually for debugging:
```bash
# Test data collection only
python3 data_collection/collect_openings.py

# Test database operations only
python3 scripts/test_system.py --test database

# Test API endpoints only
python3 scripts/test_system.py --test api
```

## Performance Optimization

### Database
- For PostgreSQL/MySQL: Add appropriate indexes
- Monitor query performance with `EXPLAIN`
- Consider connection pooling for high traffic

### API
- Use Redis for caching frequently requested data
- Implement response compression
- Add API rate limiting for public deployments

### Frontend
- Enable service worker for offline capability
- Implement lazy loading for large tier lists
- Use CDN for static assets

## Security Considerations

- Never commit API tokens to version control
- Use HTTPS in production
- Implement proper CORS settings
- Consider API key authentication for public deployments
- Regular security updates for dependencies

## Scaling

### Horizontal Scaling
- Run multiple API server instances behind a load balancer
- Use a shared database (PostgreSQL/MySQL instead of SQLite)
- Implement distributed caching

### Data Growth
- Archive old statistics periodically
- Implement data partitioning for large datasets
- Consider separate read/write database instances