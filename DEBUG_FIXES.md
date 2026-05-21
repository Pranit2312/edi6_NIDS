# NIDS Real-Time Monitoring - Debug Analysis & Fixes

## Issues Identified

### 1. **Why all destination IPs are the same?**
- **Observed**: All packets show destination IP as `224.0.0.251` (a multicast address)
- **Root Cause**: 
  - Scapy packet capture IS working and capturing real network traffic
  - The system traffic is limited to multicast packets (224.0.0.0/4 range)
  - Limited network activity means only multicast discovery packets are visible

### 2. **Why time and date are not updated?**
- **Root Cause**: Packets aren't being generated after initial load
- **Why**: The mock packet fallback was broken (see Issue #3)

### 3. **Why packets are not increasing at runtime?**
- **CRITICAL BUG FOUND**: Duplicate/malformed exception handling in `packet_capture.py`
  
```python
# BROKEN CODE:
except Exception as e:
    self.running = False  # ❌ Sets to False
    self._mock_sniff()    # ❌ Expects running=True for while loop
except Exception as e:    # ❌ Unreachable code
    ...
```

- **Impact**: When Scapy fails (requires admin/root), the code tried to fall back to mock packets BUT set `self.running = False` FIRST, so the mock packet while loop never executes

---

## Fixes Applied

### ✅ Fix #1: Corrected Exception Handling
**File**: `backend/utils/packet_capture.py`
- Removed duplicate except blocks
- Separated `PermissionError` from generic exceptions
- Removed the premature `self.running = False` that prevented mock fallback

### ✅ Fix #2: Increased Mock Packet Generation Speed
- Changed sleep interval from `0.01-0.1s` to `0.01-0.05s`
- Packets now generate 2x faster for better real-time experience
- Added logging to track mock packet generation

---

## How to Verify Fixes

### Check Backend Logs
Run the backend in verbose mode to see which mode is active:
```bash
cd backend
python app_professional.py
```

Look for logs like:
- `"Using mock packet generation (Scapy not available)"` = Mock mode
- `"Starting real-time sniff on..."` = Real packet capture mode
- `"Falling back to mock packet generation..."` = Fallback triggered

### Expected Behavior After Fix
✅ **Packets will increase** - New packets generated every 10-50ms  
✅ **Timestamps will update** - Each packet has current timestamp  
✅ **Destination IPs vary** - Mock packets generate random 10.0.x.x IPs  
✅ **Stats update in real-time** - Dashboard totals increase  

---

## Why Different IPs in Production vs Mock

### Real Packet Capture (Scapy - requires admin)
- Captures actual network traffic
- Limited to available traffic on the interface
- May show multicast (224.x.x.x) or broadcast traffic
- IPs depend on actual network activity

### Mock Mode (Fallback)
- Generates synthetic packets
- Random source: `192.168.x.x`
- Random destination: `10.0.x.x`
- Runs even without network activity

---

## Configuration Options

### Force Mock Mode
If you want guaranteed varied IPs and traffic simulation, set environment variable:
```bash
# Windows PowerShell
$env:FORCE_MOCK_PACKETS = "true"
python app_professional.py

# Linux/Mac
export FORCE_MOCK_PACKETS=true
python app_professional.py
```

### (Optional) To Implement Force Mock
Add this to `backend/app_professional.py` near imports:
```python
import os
FORCE_MOCK_MODE = os.getenv('FORCE_MOCK_PACKETS', '').lower() == 'true'
```

Then in `_sniff_thread()`:
```python
if FORCE_MOCK_MODE or not SCAPY_AVAILABLE:
    self._mock_sniff()
    return
```

---

## Testing Checklist
- [ ] Restart backend - verify logs show packet generation mode
- [ ] Frontend loads - Dashboard shows increasing packet count
- [ ] Live Monitoring tab - packets update with different IPs
- [ ] Timestamps change - show latest capture time
- [ ] All 3 issues resolved ✅

---

## Next Steps if Issues Persist

1. **Admin Privileges**: Run terminal as Administrator on Windows (for real packet capture)
2. **Check Database**: Old data in `nids.db` might still show static IPs
3. **Clear Data**: 
   ```bash
   rm nids.db  # Linux/Mac
   del nids.db  # Windows PowerShell
   ```
4. **Restart**: Kill and restart backend + frontend

