"""
EMG UDP Listener (SAFE / PASSIVE / HEADLESS)

PURPOSE
-------
This script listens for EMG features sent over UDP as JSON packets
(e.g. ~100 Hz), prints basic status information, and logs all data to disk.

DESIGN PRINCIPLES
-----------------
- Passive: it only RECEIVES data (no control, no feedback)
- Safe: logging and reception never block each other
- Portable: works on macOS and Linux (GUI-free)
- Headless: no graphical dependencies, safe for servers / ELSA

EXPECTED UDP JSON FORMAT
------------------------
{
  "ts": float,        # timestamp from sender
  "aTA": float,       # Tibialis Anterior activation [0,1]
  "aGAS": float,      # Gastrocnemius activation [0,1]
  "valid": bool       # EMG validity flag
}
"""

import argparse
import csv
import json
import os
import socket
import time
from typing import Any, Dict


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def clamp01(x: float) -> float:
    """Clamp a float value to the [0, 1] range."""
    return max(0.0, min(1.0, x))


def to_float(v: Any) -> float:
    """Convert incoming value to float."""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return float(v.strip())
    raise ValueError("Cannot convert to float")


def to_bool(v: Any) -> bool:
    """Convert incoming value to bool."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y")
    raise ValueError("Cannot convert to bool")


def parse_packet(raw: bytes) -> Dict[str, Any]:
    """
    Parse and validate a UDP JSON packet.
    Raises an exception if malformed.
    """
    msg = json.loads(raw.decode("utf-8"))
    return {
        "ts": to_float(msg["ts"]),
        "aTA": clamp01(to_float(msg["aTA"])),
        "aGAS": clamp01(to_float(msg["aGAS"])),
        "valid": to_bool(msg["valid"]),
    }


def atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    """
    Atomically write a JSON file to disk.
    Prevents partial reads by other processes.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
        f.write("\n")
    os.replace(tmp, path)


# ------------------------------------------------------------
# Main listener
# ------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Passive EMG UDP listener")
    parser.add_argument("--bind", default="0.0.0.0",
                        help="IP address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5005,
                        help="UDP port to listen on (default: 5005)")
    parser.add_argument("--outdir", default="out",
                        help="Output directory for logs")
    parser.add_argument("--print_every", type=float, default=0.2,
                        help="Live print period in seconds")
    parser.add_argument("--status_every", type=float, default=2.0,
                        help="Status print period in seconds")
    parser.add_argument("--max_packet", type=int, default=4096,
                        help="Maximum UDP packet size")
    args = parser.parse_args()

    # Prepare output directory and files
    os.makedirs(args.outdir, exist_ok=True)
    csv_path = os.path.join(args.outdir, "emg_log.csv")
    latest_path = os.path.join(args.outdir, "emg_latest.json")

    new_file = not os.path.exists(csv_path)
    csv_file = open(csv_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(
        csv_file,
        fieldnames=["recv_ts", "ts", "aTA", "aGAS", "valid"]
    )
    if new_file:
        writer.writeheader()
        csv_file.flush()

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    sock.settimeout(1.0)

    print("\n================ EMG UDP LISTENER =================")
    print(f"Listening on {args.bind}:{args.port}")
    print(f"Logging to {csv_path}")
    print("Mode: PASSIVE / HEADLESS")
    print("Press Ctrl+C to stop")
    print("===================================================\n")

    ok = 0
    bad = 0
    last_live_print = 0.0
    last_status_print = time.time()
    last_sample: Dict[str, Any] | None = None

    try:
        while True:
            try:
                raw, addr = sock.recvfrom(args.max_packet)
                recv_ts = time.time()

                try:
                    emg = parse_packet(raw)
                except Exception:
                    bad += 1
                    continue

                # Log to CSV (ground truth)
                writer.writerow({
                    "recv_ts": recv_ts,
                    **emg
                })
                csv_file.flush()

                # Write latest sample
                atomic_write_json(latest_path, emg)

                ok += 1
                last_sample = emg

                # Live print (rate-limited)
                now = time.time()
                if (now - last_live_print) >= args.print_every:
                    last_live_print = now
                    v = 1 if emg["valid"] else 0
                    print(
                        f"[LIVE] aTA={emg['aTA']:.3f} "
                        f"aGAS={emg['aGAS']:.3f} "
                        f"valid={v} from={addr[0]}"
                    )

            except socket.timeout:
                pass

            # Periodic status
            t = time.time()
            if (t - last_status_print) >= args.status_every:
                last_status_print = t
                if last_sample is None:
                    print(f"[STATUS] ok={ok} bad={bad} (waiting for data)")
                else:
                    print(f"[STATUS] ok={ok} bad={bad} "
                          f"(last valid={int(last_sample['valid'])})")

    except KeyboardInterrupt:
        print("\nStopping listener...")

    finally:
        csv_file.close()
        sock.close()


if __name__ == "__main__":
    main()