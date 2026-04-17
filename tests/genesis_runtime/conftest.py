"""
GENESIS Runtime Test Suite — Shared Fixtures & Configuration
Provides common test helpers and path setup for all test modules.
"""

import sys
import os

# Ensure project root is on sys.path so `core.*`, `server.*` etc. can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set environment variables for safe test execution
os.environ.setdefault("CLOUD_MODE", "true")
os.environ.setdefault("GENESIS_SAFE_MODE", "true")


def sprint(label: str, status: str, detail: str = ""):
    """Standardized test output printer."""
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    suffix = f" — {detail}" if detail else ""
    print(f"  {icon} {label} ... {status}{suffix}")
