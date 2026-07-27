"""
test_log_record.py

Tests the LogRecord model.
"""

from pathlib import Path
import sys

# ------------------------------------------------------------------
# Project Root
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.preprocessing.models import LogRecord


# ------------------------------------------------------------------
# Main Test
# ------------------------------------------------------------------

def main():

    record = LogRecord(
        log_type="auth",
        source_file="auth.log",
        timestamp="2026-07-20T12:30:15",
        hostname="osboxes",
        process="sshd",
        pid=1234,
        severity="HIGH",
        event="Failed password",
        user="root",
        ip="192.168.1.10",
        port=22,
        protocol="ssh2",
        message="Failed password for root from 192.168.1.10 port 22 ssh2",
    )

    print("=" * 70)
    print("LOG RECORD MODEL TEST")
    print("=" * 70)

    print("\nLogRecord Object")
    print(record)

    print("\nDictionary Representation")
    print(record.to_dict())

    print("\n" + "=" * 70)
    print("LOG RECORD MODEL TEST PASSED")
    print("=" * 70)


# ------------------------------------------------------------------

if __name__ == "__main__":

    main()