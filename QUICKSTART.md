# 🚀 Professional NIDS - Quick Start Guide

## ⚡ 5-Minute Quick Setup

### Prerequisites Check (< 2 minutes)
```bash
# Check Python
python --version        # Should be 3.8+
python -m pip --version # Should show pip version

# Check Node.js
node --version         # Should be 14+
npm --version          # Should be 7+
```

### ONLY ON WINDOWS: Install Npcap
- Download from https://npcap.com/
- Run installer as Administrator
- Ensure "WinPcap API-compatible mode" is checked

### ONLY ON LINUX: Install libpcap
```bash
sudo apt-get update
sudo apt-get install -y libpcap-dev python3-dev
```

---

## ⏱️ Setup (5 minutes)

### Terminal 1: Backend Setup
```bash
cd backend
python -m venv venv

# Activate:
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

pip install -r requirements.txt

# Train ML model (3 minutes)
cd ../ml
python train_model.py
cd ../backend

# Start backend (⚠️ Windows: Run as Administrator)
python app.py
```

✅ **Backend running on http://127.0.0.1:5050**

### Terminal 2: Frontend Setup
```bash
cd frontend
npm install

# Start frontend
npm run dev
```

✅ **Frontend running on http://localhost:5173**

---

## 🌐 Access Dashboard

Open browser:
```
http://localhost:5173
```

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

**Dashboard Features:**
- ✅ Real-time packet capture
- ✅ Live attack detection
- ✅ ML confidence scores
- ✅ Attack trends & analytics
- ✅ Detection logs export

---

## 🔥 Stopping the System

### To Stop Backend:
```bash
# In Terminal 1 running backend:
Ctrl + C
```

### To Stop Frontend:
```bash
# In Terminal 2 running frontend:
Ctrl + C
```

---

## 🚀 Next Runs (Much Faster!)

### Backend:
```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
sudo python app.py         # or: python app.py on Windows
```

### Frontend:
```bash
cd frontend
npm run dev
```

---

## 🛠️ Common Commands

### Python Virtual Environment
```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Deactivate
deactivate
```

### Install/Update Packages
```bash
# Install requirements
pip install -r requirements.txt

# Install single package
pip install package_name

# List installed
pip list

# Update pip
python -m pip install --upgrade pip
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Check for errors
npm run build -- --verbose

# Clean dependencies
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### ML Model Training
```bash
cd ml

# Train on CICIDS2017 dataset
python train_model.py

# Creates in backend/models/:
# - model.pkl (RandomForest classifier)
# - scaler.pkl (StandardScaler)
# - label_encoder.pkl (Attack types)
# - feature_columns.pkl (Feature names)
```

---

## 🐛 Troubleshooting

### Backend crashes with "Permission denied"
- **Windows**: Run Command Prompt as Administrator
- **Linux/macOS**: Use `sudo python app.py`

### Backend crashes with "Address already in use"
```bash
# Find what's using port 5050
# Windows:
netstat -ano | findstr :5050
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :5050
kill -9 <PID>
```

### Frontend won't load
- Check that backend is running on http://127.0.0.1:5050
- Open browser console (F12) and check for errors
- Verify CORS is enabled in backend

### "ModuleNotFoundError: No module named 'scapy'"
```bash
# Ensure venv is activated (should show (venv) in prompt)
pip install -r requirements.txt --force-reinstall
```

### "Cannot find network interface"
- **Windows**: Install Npcap from https://npcap.com/
- **Linux**: Run with `sudo`
- **macOS**: Run with `sudo`

### ML Model training fails
```bash
cd ml
# Check CSV files exist
ls data/
# Re-run training
python train_model.py
```

### Can't login to dashboard
- Default credentials: `admin` / `admin123`
- Check browser console for API errors
- Ensure backend is running

---

## 📊 Real-Time Features

Once dashboard is open and running:

1. **Live Monitoring**: Watch real packets being captured
2. **Attack Detection**: See attacks detected by ML and rule-based engine
3. **Analytics**: View attack trends, types, and severity
4. **Alerts**: Real-time notification of detected threats
5. **Export**: Download detection logs as CSV

---

## 🔑 Architecture Overview

```
Network Interface (Scapy sniffing)
         ↓
    Packet Processing
         ↓
    Feature Extraction (8 features)
         ↓
    ML Inference (RandomForest)
         ↓
    Rule-Based Fallback (if ML uncertain)
         ↓
    Detection Event + Alert
         ↓
    SQLite Database
         ↓
    REST API
         ↓
    React Frontend (Real-time display)
```

---

## 🚀 Performance Tips

1. **First ML training**: 2-5 minutes (one-time)
2. **Subsequent runs**: < 30 seconds to start
3. **Live packet capture**: Real-time (< 100ms latency)
4. **Dashboard updates**: 1-2 second intervals

---

## 📞 Need Help?

Check detailed documentation:
- [INSTALLATION_COMMANDS.md](INSTALLATION_COMMANDS.md) - Complete setup guide
- [BACKEND_README.md](backend/BACKEND_README.md) - Backend architecture
- [FRONTEND_README.md](frontend/FRONTEND_README.md) - Frontend features
- [ML_README.md](ml/ML_README.md) - ML training details
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - System design

# Will be recreated on next backend start
```

### View Backend Logs
```bash
# Backend runs with debug enabled, so check console
# For production, add logging:
# python app.py > logs.txt 2>&1
```

## 📊 Database Commands

### Access SQLite Database

**Windows:**
```bash
# Install sqlite3 if needed
# Then:
sqlite3 nids.db
```

**Linux/macOS:**
```bash
sqlite3 nids.db
```

**Inside SQLite shell:**
```sql
-- List all tables
.tables

-- Show users
SELECT * FROM users;

-- Show recent packets
SELECT * FROM packets LIMIT 10;

-- Show logs
SELECT * FROM logs LIMIT 10;

-- Exit
.exit
```

## 🔄 Development Workflow

### 1. Make Frontend Changes
```bash
cd frontend
# Edit files in src/
# Changes auto-reload at http://localhost:3000
```

### 2. Make Backend Changes
```bash
cd backend
# Edit files in routes/, utils/, etc.
# Restart `python app.py` to reload
```

### 3. Retrain ML Model
```bash
cd ml
python train_model.py
# Restart backend to use new model
```

## 📦 Project Structure

```
nids-project/
├── README.md                 # Main documentation
├── setup.bat                # Windows setup script
├── setup.sh                 # Linux/macOS setup script
│
├── frontend/                # React application
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── FRONTEND_README.md
│   └── src/
│
├── backend/                 # Flask application
│   ├── app.py
│   ├── requirements.txt
│   ├── BACKEND_README.md
│   ├── routes/
│   ├── utils/
│   └── models/              # Trained ML models
│
└── ml/                       # ML Training
    ├── train_model.py
    ├── ML_README.md
    └── data/
```

## ✅ Verification Checklist

Before starting, verify:
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] npm 7+ installed
- [ ] Port 5000 is free (backend)
- [ ] Port 3000 is free (frontend)
- [ ] All files downloaded/created

After setup:
- [ ] Backend starts without errors
- [ ] Frontend starts at http://localhost:3000
- [ ] Can login with demo/demo123
- [ ] Dashboard loads with data
- [ ] All pages accessible

## 🆘 Getting Help

### Check Logs
1. Frontend: Browser console (F12)
2. Backend: Terminal output
3. Database: Check nids.db with sqlite3

### Common Issues

**"Port already in use"**
- Kill the process using the port (see Port Usage section)
- Or change port in vite.config.js (frontend) or app.py (backend)

**"Module not found"**
- Reinstall dependencies
- Check Python/Node versions

**"Database locked"**
- Close any sqlite3 terminals
- Restart backend

**"API connection error"**
- Check backend is running on :5000
- Check CORS is enabled
- Check firewall settings

## 📱 Mobile Access

To access from other machines on network:

1. Find your machine IP:
   - Windows: `ipconfig`
   - Linux/macOS: `ifconfig`

2. Backend: `http://<YOUR_IP>:5000/api/health`
3. Frontend: `http://<YOUR_IP>:3000`

## 🚢 Production Deployment

### Build Frontend
```bash
cd frontend
npm run build
# Creates dist/ folder
```

### Deploy Backend
```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables
Create `.env` file in backend:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE=nids.db
```

## 🎓 Learning Resources

- Frontend: FRONTEND_README.md
- Backend: BACKEND_README.md
- ML: ML_README.md
- Full docs: README.md

## 💡 Tips

- Use VS Code for development
- Install "Python" and "ES7+ React extensions
- Keep backend and frontend terminals visible
- Use Chrome DevTools for frontend debugging
- Check browser console for API errors

---

**Total Setup Time**: ~5-10 minutes  
**First Run**: ~30 seconds  
**Status**: ✅ Ready to Go!

For detailed information, see the appropriate README file.
