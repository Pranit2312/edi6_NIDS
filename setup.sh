#!/bin/bash
# NIDS Project Setup and Run Script

echo "================================"
echo "NIDS - Network Intrusion Detection System"
echo "================================"
echo ""

# Check Python version
echo "[*] Checking Python version..."
python --version
if ! command -v python &> /dev/null; then
    echo "[!] Python not found. Please install Python 3.8+"
    exit 1
fi

# Check Node.js version
echo "[*] Checking Node.js version..."
node --version
npm --version
if ! command -v node &> /dev/null; then
    echo "[!] Node.js not found. Please install Node.js 16+"
    exit 1
fi

# Setup Backend
echo ""
echo "[*] Setting up Backend..."
cd backend

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[*] Creating Python virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "[*] Activating virtual environment..."
if [ -d "venv/bin" ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

# Install dependencies
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

# Train ML model
echo "[*] Training ML model..."
cd ../ml
python train_model.py

# Back to backend
cd ../backend

echo ""
echo "[*] Backend setup complete!"
echo "[*] To start backend, run: python app.py"
echo ""

# Setup Frontend
echo "[*] Setting up Frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "[*] Installing Node dependencies..."
    npm install
fi

echo ""
echo "[*] Frontend setup complete!"
echo "[*] To start frontend, run: npm run dev"
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To run the project:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "  python app.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
