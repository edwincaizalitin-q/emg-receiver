# EMG Receiver

Portable, ROS-agnostic UDP receiver for real-time EMG data.
Designed to receive normalized EMG signals (e.g., TA / GAS) from a Windows-based
EMG acquisition system and make them available on Linux or macOS.

This package focuses exclusively on **reception and logging**.
Acquisition, preprocessing, and EMG hardware (e.g., Delsys) are handled elsewhere.

---

## Features
- Passive UDP EMG receiver
- Works on macOS and Linux
- No ROS dependency (ROS adapters can be added later)
- Command-line interface: `emg-listen`
- CSV logging and atomic latest-value JSON output
- Suitable for real-time control pipelines (e.g., ELSA)

---

## Requirements
- Python **3.12.0**
- macOS or Linux
- Git
- Sender and receiver must be on the **same private network**
  (home Wi-Fi or mobile hotspot recommended)

---

## Quick Start (Recommended)

### 1) Clone the repository
```bash
git clone git@github.com:edwincaizalitin-q/emg-receiver.git
cd emg-receiver
```

### 2) Verify Python version
```bash
python3.12 --version
```

### 3) Create and activate a virtual environment (Python 3.12)
macOS / Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade `pip`:
```bash
python -m pip install --upgrade pip
```

---

## Installation

Install the package in editable mode:
```bash
pip install -e .
```

Verify that the CLI is available:
```bash
emg-listen --help
```

---

## Running the Receiver

Start the EMG receiver:
```bash
emg-listen --bind 0.0.0.0 --port 5005 --outdir out
```

### Output files
- `out/emg_log.csv` — full EMG log
- `out/emg_latest.json` — latest EMG snapshot (atomic write)

---

## Testing with Windows EMG Sender

1) Connect both machines to the same private network  
2) On macOS/Linux (receiver):
```bash
emg-listen --bind 0.0.0.0 --port 5005 --outdir out
```

3) On Windows (sender):
- Set destination IP to the receiver IP
- Set destination port to `5005`
- Start EMG streaming

---

## Network Changes

If the receiver IP changes:
- Do NOT change anything on the receiver
- Only update the destination IP on the Windows sender

Get receiver IP (macOS):
```bash
ipconfig getifaddr en0
```

---

## Common Issues

### Address already in use
```bash
lsof -i :5005
kill <PID>
```

### No data received
- Check network
- Check IP and port
- Avoid institutional networks

---

## Packet Format
```json
{"ts":0.0,"aTA":0.0,"aGAS":0.0,"valid":true}
```

---

## License
MIT License. See LICENSE file.
