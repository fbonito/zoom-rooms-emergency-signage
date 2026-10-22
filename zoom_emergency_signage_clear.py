#!/usr/bin/env python3
"""
Zoom Rooms — Fire Emergency Alert  (CLEAR)
============================================
Run this script when the emergency is over to remove the alert from
all Zoom Rooms displays in the building.

    python zoom_emergency_signage_clear.py

The event_id is read automatically from .active_event_id (written by
zoom_emergency_signage.py). No manual copy-pasting needed.

AUTH: Server-to-Server OAuth 2.0
REQUIRED SCOPE: room:write:admin
REQUIRED ENV VARS (or set them in the CONFIG block below):
    ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET
"""

import os
import sys
import json
import requests
from base64 import b64encode
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ZOOM_ACCOUNT_ID    = os.getenv("ZOOM_ACCOUNT_ID",    "YOUR_ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID     = os.getenv("ZOOM_CLIENT_ID",     "YOUR_ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "YOUR_ZOOM_CLIENT_SECRET")

ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE  = "https://api.zoom.us/v2"

# Location ID — must match the value used in zoom_emergency_signage.py.
LOCATION_ID = os.getenv("ZOOM_LOCATION_ID", "YOUR_ZOOM_LOCATION_ID")

STATE_FILE = Path(__file__).parent / ".active_event_id"
# ---------------------------------------------------------------------------


def get_access_token() -> str:
    credentials = b64encode(
        f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}".encode()
    ).decode()
    resp = requests.post(
        ZOOM_TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": ZOOM_ACCOUNT_ID},
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def clear_alert(token: str, event_id: str) -> None:
    """
    PATCH /v2/rooms/events
    Removes the active emergency alert from all Zoom Rooms in the target location.
    """
    url = f"{ZOOM_API_BASE}/rooms/events"
    payload = {
        "method": "zoomroom.emergency_alert_removed",
        "params": {
            "event_id":     event_id,
            "target_type":  "location",
            "target_ids":   [LOCATION_ID],
            "force_remove": False,
        },
    }

    print(f"  PATCH {url}")
    print(f"  Payload:\n{json.dumps(payload, indent=4)}")

    resp = requests.patch(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=15,
    )
    print(f"  Status : {resp.status_code}")
    print(f"  Body   : {resp.text}")
    resp.raise_for_status()


def main() -> None:
    for var, value in [
        ("ZOOM_ACCOUNT_ID",    ZOOM_ACCOUNT_ID),
        ("ZOOM_CLIENT_ID",     ZOOM_CLIENT_ID),
        ("ZOOM_CLIENT_SECRET", ZOOM_CLIENT_SECRET),
        ("LOCATION_ID",        LOCATION_ID),
    ]:
        if value.startswith("YOUR_"):
            print(f"ERROR: {var} is not configured.")
            sys.exit(1)

    if not STATE_FILE.exists():
        print(f"ERROR: No active alert found ({STATE_FILE.name} does not exist).")
        print("       Has zoom_emergency_signage.py been run?")
        sys.exit(1)

    event_id = STATE_FILE.read_text().strip()
    if not event_id:
        print(f"ERROR: {STATE_FILE.name} is empty.")
        sys.exit(1)

    try:
        print("--- Authenticating ---")
        token = get_access_token()
        print("  OK")

        print(f"\n--- Clearing alert (event_id: {event_id}) ---")
        clear_alert(token, event_id)
        STATE_FILE.unlink()
        print("\n  Alert cleared.  Zoom Rooms displays have returned to normal.")

    except requests.HTTPError as exc:
        print(f"ERROR: HTTP {exc.response.status_code} — {exc.response.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
