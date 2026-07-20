"""
Run:

python backend/preprocessing/schema/tests/test_log_schema.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.append(str(PROJECT_ROOT))

from backend.preprocessing.schema import LogSchema


record = LogSchema(
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
print("PHASE 3 SCHEMA TEST")
print("=" * 60)

print("\nSchema Object")

print(record)

print("\nDictionary")

print(record.to_dict())

print("\nPASS")