# emg-receiver (V1)

Portable, passive UDP EMG receiver/logger.

## Install (local)
From the repo root:
```bash
python -m pip install -e .
```

## Run
```bash
emg-listen --bind 0.0.0.0 --port 5005 --outdir out
```

Outputs:
- `out/emg_log.csv`
- `out/emg_latest.json`

## Packet format (JSON)
```json
{"ts": 0.0, "aTA": 0.0, "aGAS": 0.0, "valid": true}
```
