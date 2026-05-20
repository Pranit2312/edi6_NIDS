# NIDS Backend - Quick Start Guide

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Setup Steps

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Train ML Model (Optional, but recommended)
```bash
cd ml
python train_model.py
cd ..
```

### 5. Run Backend
```bash
python app.py
```

Backend will start on `http://localhost:5000`

## API Endpoints

- **Health Check**: `GET http://localhost:5000/api/health`
- **Login**: `POST http://localhost:5000/api/auth/login`
- **Get Packets**: `GET http://localhost:5000/api/packets`
- **Get Stats**: `GET http://localhost:5000/api/stats`

## Database

SQLite database (`nids.db`) will be automatically created on first run with the following tables:
- users
- packets
- logs
- alerts

## Troubleshooting

### Port already in use
```bash
# Find process using port 5000
netstat -tulpn | grep :5000

# Kill process
kill <PID>
```

### Module not found
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Database issues
```bash
# Delete old database
rm nids.db

# Restart to recreate
python app.py
```

## Project Structure

```
backend/
├── app.py                 # Main Flask app
├── requirements.txt       # Python dependencies
├── routes/
│   ├── auth.py           # Authentication endpoints
│   ├── monitoring.py     # Monitoring endpoints
│   ├── analytics.py      # Analytics endpoints
│   ├── logs.py           # Logs endpoints
│   └── settings.py       # Settings endpoints
├── utils/
│   ├── packet_capture.py # Packet capture simulation
│   └── predictor.py      # ML prediction engine
└── models/
    └── (ML models stored here)
```

## Configuration

All settings can be modified in `app.py`:
- `SECRET_KEY` - Flask secret key
- `DATABASE` - SQLite database path
- `DEBUG` - Debug mode
- `HOST` - Server host
- `PORT` - Server port

## Performance Tips

- Increase `n_estimators` in RandomForest for better accuracy (slower)
- Reduce `max_depth` for faster predictions
- Use connection pooling in production
- Enable caching for static responses
