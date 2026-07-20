"""
Test LogRecord model.

Run:
python backend/tests/preprocessing/test_log_record.py
"""

from pathlib import Path
import sys

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.preprocessing.models import LogRecord


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
        message="Failed password for root from 192.168.1.10 port 22 ssh2"
    )

    print("=" * 60)
    print("LOG RECORD MODEL TEST")
    print("=" * 60)

    print("\nLogRecord Object")
    print(record)

    print("\nDictionary Representation")
    print(record.to_dict())

    print("\nAll tests passed successfully.")


if __name__ == "__main__":
    main()