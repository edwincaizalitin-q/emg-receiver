"""Command-line interface for emg_receiver."""

from .listener import main as _listener_main

def main() -> None:
    _listener_main()
