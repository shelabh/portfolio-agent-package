#!/usr/bin/env python3
"""Deprecated compatibility wrapper for the canonical manual E2E verifier."""

from manual_e2e import main


if __name__ == "__main__":
    print("scripts/integration_test.py is deprecated. Running scripts/manual_e2e.py instead.\n")
    main()
