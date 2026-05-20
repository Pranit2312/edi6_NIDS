# 🚀 Professional NIDS - Complete Setup Guide

## ⚠️ CRITICAL REQUIREMENTS

This is a **professional real-time Network Intrusion Detection System** with real packet capture. Read carefully!

### System Requirements:
- **OS**: Windows, Linux, or macOS
- **Python**: 3.8+ 
- **Node.js**: 14+
- **RAM**: 4GB minimum (8GB recommended for ML training)
- **Disk**: 5GB (for ML dataset + models)
- **Network**: Active network interface for packet capture

### Administrator Privileges Required ⚠️
Packet capture requires elevated privileges:
- **Windows**: Run Command Prompt or PowerShell **as Administrator**
- **Linux/macOS**: Use `sudo` for backend startup

---

## 🔧 PLATFORM-SPECIFIC PREREQUISITES

### WINDOWS - Install Npcap for Packet Capture

1. **Download Npcap** (required for Scapy packet capture)
   - Visit: https://npcap.com/
   - Click "Download Latest Version"
   - Select the installer (e.g., `npcap-1.73.exe`)

2. **Run Installer**
   - Open Command Prompt **as Administrator**
   - Double-click the downloaded installer
   - Choose default options
   - ✅ Make sure "WinPcap API-compatible mode" is **CHECKED**
   - Complete installation

3. **Verify Installation**
   ```bash
   pip list | find "scapy"
   ```

### LINUX - Install Libpcap Development Files

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y libpcap-dev python3-dev
```

**Fedora/RHEL/CentOS:**
```bash
sudo yum install -y libpcap-devel python3-devel
```

**Arch:**
```bash
sudo pacman -S libpcap base-devel
```

### macOS - Install Libpcap (Already Installed)
macOS includes libpcap by default. No action needed.

---

## 📋 COMPLETE STEP-BY-STEP SETUP

### STEP 1: Navigate to Project Root

**Windows:**
```bash
cd c:\Users\HP\Desktop\S6\edi\nids-project
```

**Linux/macOS:**
```bash
cd ~/nids-project
```

---

### STEP 2: BACKEND SETUP (Terminal 1)

#### 2.1 Navigate to Backend
```bash
cd backend
```

#### 2.2 Create Python Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ You should see `(venv)` in your terminal prompt

#### 2.3 Install Dependencies
```bash
pip install -r requirements.txt
```

**Packages installed:**
- Flask 2.3.3 (web framework)
- Flask-CORS 4.0.0 (cross-origin requests)
- Scapy 2.5.0 (real-time packet capture)
- scikit-learn 1.3.1 (ML model training)
- pandas 2.0.3 (data processing)
- numpy 1.24.3 (numerical computing)
- joblib 1.3.2 (model serialization)

#### 2.4 Train ML Model on CICIDS2017 Dataset

Navigate to ML directory:
```bash
cd ../ml
```

**Download/Verify Dataset**

The project includes CICIDS2017 CSV files in `ml/data/`:
- Monday-WorkingHours.pcap_ISCX.csv
- Tuesday-WorkingHours.pcap_ISCX.csv
- Wednesday-workingHours.pcap_ISCX.csv
- Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
- Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
- Friday-WorkingHours-Morning.pcap_ISCX.csv
- Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
- Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv

**Run Training**
```bash
python train_model.py
```

**Expected Output:**
```
[*] NIDS ML Model Training Script
[*] Loading CICIDS2017 dataset from CSV files...
[+] Dataset loaded: X_train shape: (50000, 8)
[*] Training RandomForest model (200 trees)...
[+] Model trained in 45 seconds
[+] Training Accuracy: 95.23%
[+] Test Accuracy: 92.87%
[+] Precision: 0.91 | Recall: 0.89 | F1-Score: 0.90
[+] Models saved to ../backend/models/
```

⏱️ **First-time training takes 2-5 minutes.** Subsequent runs are faster.

Models are saved to `backend/models/`:
- `model.pkl` - RandomForest classifier
- `scaler.pkl` - StandardScaler for feature normalization
- `label_encoder.pkl` - Attack type encoder
- `feature_columns.pkl` - Feature names

#### 2.5 Return to Backend and Start Server

```bash
cd ../backend
```

**WINDOWS - Start as Administrator:**
```bash
# Must run Command Prompt as Administrator for packet capture!
python app.py
```

**LINUX/macOS - Start with sudo:**
```bash
sudo python app.py
```

**Expected Output:**
```
WARNING in app.run()
 * Running on http://127.0.0.1:5050
```

✅ **LEAVE THIS TERMINAL OPEN** - The backend is now:
- ✅ Capturing live network packets (real-time)
- ✅ Extracting 8 ML features from each packet
- ✅ Running ML inference for attack detection
- ✅ Falling back to rule-based detection if ML confidence is low
- ✅ Storing packets & detection events in SQLite database
- ✅ Broadcasting real-time stats via REST API

---

### STEP 3: FRONTEND SETUP (Terminal 2)

#### 3.1 Navigate to Frontend (from project root)
```bash
cd frontend
```

#### 3.2 Install Dependencies
```bash
npm install
```

This installs:
- React 18 (UI framework)
- Vite 5 (bundler)
- Tailwind CSS (styling)
- Axios (HTTP client)

**Time**: 1-3 minutes depending on internet speed

#### 3.3 Start Development Server
```bash
npm run dev
```

**Expected Output:**
```
➜  Local:   http://localhost:5173/
➜  press h + enter to show help
```

✅ **Frontend is now running!**

---

### STEP 4: Access the NIDS Dashboard

1. **Open your browser** and navigate to:
   ```
   http://localhost:5173
   ```

2. **Login** with credentials:
   - Username: `admin`
   - Password: `admin123`

3. **Dashboard Shows Real-Time Data:**
   - Live packet capture count
   - Real-time attack detection
   - Attack types and severity
   - Network traffic trends
   - Detection confidence scores
   - ML vs Rule-based detection breakdown

---

## 🔧 RUNNING EXISTING SETUP

After initial setup, subsequent runs are simpler:

### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
sudo python app.py  # or just: python app.py on Windows
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

---

## 🐛 TROUBLESHOOTING

### "Permission denied" on Linux/macOS
- Packet capture requires root privileges
- Always use `sudo python app.py`
- Or run terminal with sudo: `sudo -i` then `python app.py`

### "Scapy cannot find network interface"
- Windows: Install Npcap (see above)
- Linux: Run with sudo
- macOS: Run with sudo

### Backend crashes with "ModuleNotFoundError"
```bash
# Verify virtual environment is activated
# (venv) should appear at start of terminal prompt
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows
```

### Frontend won't connect to backend
- Verify backend is running on http://127.0.0.1:5050
- Check that both terminals show no error messages
- Frontend browser console: Press F12 > Console > check for errors

### ML Model training fails
```bash
# Ensure you're in ml directory
cd ml

# Run training again
python train_model.py

# Check that CICIDS2017 CSV files exist
ls data/  # Linux/macOS
dir data  # Windows
```

---

## 📊 ARCHITECTURE OVERVIEW

```
User Browser (http://localhost:5173)
         ↓
    [React Frontend]
         ↓
    API Calls (/api/*)
         ↓
    [Flask Backend] ← Real-time Packet Capture (Scapy)
         ↓
    ML Detection Engine
    (RandomForest + Rule Engine)
         ↓
    SQLite Database (nids.db)
    - packets table (all traffic)
    - detection_events (attacks only)
    - alerts
    - statistics
```

---

## 📈 ML DETECTION PIPELINE

1. **Packet Capture**: Scapy sniffs real network traffic
2. **Feature Extraction**: Converts packets to 8 ML features:
   - Protocol (TCP/UDP/ICMP)
   - Source/Destination ports
   - Packet size
   - TCP flags
   - Traffic rate (packets/sec)
   - Byte rate (bytes/sec)
   - Connection duration

3. **ML Prediction**: RandomForest evaluates features
   - If confidence ≥ 0.7: Use ML classification
   - If confidence < 0.7: Fallback to rule-based detection

4. **Rule-Based Fallback**: 8 detection rules
   - Port scanning detection
   - DDoS detection (pps/bps thresholds)
   - SYN flood detection
   - ICMP flood detection
   - Suspicious port access
   - Jumbo packet anomalies
   - Unusual traffic patterns
   - Botnet C&C communication

5. **Storage**: All events logged to SQLite
6. **Dashboard**: Real-time visualization

---

## ✅ SUCCESS CHECKLIST

- [ ] Npcap (Windows) or libpcap (Linux) installed
- [ ] Python venv created and activated
- [ ] `pip install -r requirements.txt` successful
- [ ] `python train_model.py` completed (models saved to backend/models/)
- [ ] Backend running with `sudo python app.py` (shows http://127.0.0.1:5050)
- [ ] Frontend running with `npm run dev` (shows http://localhost:5173)
- [ ] Dashboard accessible at http://localhost:5173
- [ ] Login successful (admin / admin123)
- [ ] Dashboard shows real-time packet counts and statistics

---

## 🚀 Next Steps

After successful setup:
1. **Monitor Live Traffic**: Watch packets and attacks in real-time
2. **Analyze Attacks**: View attack types, severity, and trends
3. **Export Logs**: Download detection logs as CSV
4. **Customize Rules**: Edit `backend/utils/rule_engine.py` to add custom detection rules
5. **Deploy to Production**: Use Docker or cloud deployment

---

## 📞 SUPPORT

For issues or questions:
- Check [BACKEND_README.md](backend/BACKEND_README.md)
- Check [FRONTEND_README.md](frontend/FRONTEND_README.md)
- Check [ML_README.md](ml/ML_README.md)
- Review [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for architecture details

---

### STEP 4: ACCESS THE APPLICATION

Open your web browser and go to:
```
http://localhost:3000
```

#### Login with Demo Credentials:
- **Username:** `demo`
- **Password:** `demo123`

✅ **YOU'RE IN! Application should now be running**

---

## 📊 WHAT'S RUNNING

### Terminal 1 (Backend - Port 5000):
```
Backend Server: http://localhost:5000
API Endpoints: http://localhost:5000/api/...
```

### Terminal 2 (Frontend - Port 3000):
```
Frontend Server: http://localhost:3000
Auto-reloads when you edit code
```

### Database:
```
SQLite: nids.db (created automatically in backend folder)
```

---

## 🔧 INSTALLATION SUMMARY TABLE

| Component | Command | Time | Result |
|-----------|---------|------|--------|
| Python venv | `python -m venv venv` | 10s | Virtual environment created |
| Activate venv | `venv\Scripts\activate` | 1s | (venv) prefix appears |
| Python deps | `pip install -r requirements.txt` | 2-3min | 7 packages installed |
| ML Model | `python train_model.py` | 1-2min | Model trained & saved |
| Backend start | `python app.py` | 5s | Server on :5000 |
| Node deps | `npm install` | 1-3min | 48 packages installed |
| Frontend start | `npm run dev` | 5s | Server on :3000 |

**Total Time: 10-15 minutes**

---

## ✅ VERIFICATION CHECKLIST

After running all commands:

- [ ] Backend terminal shows: `Running on http://0.0.0.0:5000`
- [ ] Frontend terminal shows: `➜  Local:   http://localhost:3000/`
- [ ] Browser opens http://localhost:3000
- [ ] Landing page displays with NIDS logo
- [ ] Can login with demo/demo123
- [ ] Dashboard loads with charts and stats
- [ ] Navigation menu works

If all checked ✅, **PROJECT IS WORKING!**

---

## 🛑 TROUBLESHOOTING DURING SETUP

### Issue: "Command not found: python"
**Solution:**
```bash
# Try python3 instead
python3 --version
python3 -m venv venv
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

### Issue: "Port 5000 already in use"
**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
lsof -i :5000
kill -9 <PID>
```

### Issue: "Port 3000 already in use"
**Windows:**
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
lsof -i :3000
kill -9 <PID>
```

### Issue: "Permission denied" (Linux/macOS)
```bash
chmod +x setup.sh
sudo chmod +x /path/to/backend/app.py
```

### Issue: "Module not found: flask"
```bash
# Make sure venv is activated (should see (venv) prefix)
# Then reinstall:
pip install -r requirements.txt --force-reinstall
```

### Issue: "npm: command not found"
- Node.js not installed
- Download from https://nodejs.org/
- Install and restart terminal

### Issue: "pip install" is very slow
```bash
# Use a different package index:
pip install -r requirements.txt -i https://pypi.tsinghua.edu.cn/simple
```

---

## 🔄 DAILY USAGE (After Initial Setup)

Once everything is set up, to run the project again:

**Terminal 1:**
```bash
cd backend
venv\Scripts\activate       # Windows
# or
source venv/bin/activate    # Linux/macOS
python app.py
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

Then open: `http://localhost:3000`

---

## 📦 WHAT GETS INSTALLED

### Python Packages (backend/requirements.txt):
1. **flask** - Web framework
2. **flask-cors** - Cross-origin requests
3. **scikit-learn** - Machine learning
4. **pandas** - Data processing
5. **numpy** - Numerical computing
6. **scapy** - Network packets (optional)
7. **joblib** - Model serialization

### Node Packages (frontend/package.json):
1. **react** - UI library
2. **react-router-dom** - Navigation
3. **axios** - HTTP client
4. **tailwindcss** - Styling
5. **framer-motion** - Animations
6. **recharts** - Charts
7. **And 41 more...**

---

## 🎯 COMMON TASKS AFTER SETUP

### Stop Services
Press `Ctrl + C` in each terminal

### Restart Backend
```bash
cd backend
python app.py
```

### Restart Frontend
```bash
cd frontend
npm run dev
```

### Rebuild Frontend (if issues)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Retrain ML Model
```bash
cd ml
python train_model.py
```

### Clear Database
```bash
# Delete nids.db in backend folder
# Backend will recreate it on next run
```

---

## 🚀 NEXT STEPS

1. ✅ Run all setup commands above
2. ✅ Verify all services are running
3. ✅ Login to application
4. ✅ Explore the dashboard
5. ✅ Try different features:
   - Go to Dashboard
   - Check Live Monitoring
   - View Threat Analytics
   - Review Logs & Alerts
   - Configure Settings

---

## 📞 QUICK REFERENCE

| Action | Command |
|--------|---------|
| Check Python | `python --version` |
| Check Node | `node --version` |
| Activate venv (Windows) | `venv\Scripts\activate` |
| Activate venv (Linux/Mac) | `source venv/bin/activate` |
| Install Python deps | `pip install -r requirements.txt` |
| Train ML model | `python train_model.py` |
| Start backend | `python app.py` |
| Install Node deps | `npm install` |
| Start frontend | `npm run dev` |
| Open browser | `http://localhost:3000` |
| Stop service | `Ctrl + C` |

---

## ✨ YOU'RE READY!

Follow these commands in order and your NIDS application will be running!

If you get stuck, check the detailed READMEs:
- Main guide: README.md
- Backend: backend/BACKEND_README.md
- Frontend: frontend/FRONTEND_README.md
- ML: ml/ML_README.md

**Good luck! 🚀**
