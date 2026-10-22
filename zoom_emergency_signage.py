#!/usr/bin/env python3
"""
Zoom Rooms — Fire Emergency Alert  (ACTIVATE)
===============================================
Run this script when a fire alarm is triggered in the building.
It pushes an emergency alert to every Zoom Rooms display in the
pre-configured location (red background, caution icon).

    python zoom_emergency_signage.py

The event_id is automatically saved to .active_event_id so the clear
script can pick it up without any manual copy-pasting.

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

# Location ID for the target building.
# Run zoom_lookup_locations.py once to find this value.
LOCATION_ID = os.getenv("ZOOM_LOCATION_ID", "YOUR_ZOOM_LOCATION_ID")

# Alert message shown on Zoom Rooms displays.
ALERT_MESSAGE = (
    "EMERGENCY - Evacuate now. Follow the posted evacuation routes."
)

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


def activate_alert(token: str) -> str:
    """
    PATCH /v2/rooms/events
    Displays the emergency alert on all Zoom Rooms in the target location.
    Returns the event_id needed to clear the alert later.
    """
    url = f"{ZOOM_API_BASE}/rooms/events"
    payload = {
        "method": "zoomroom.emergency_alert_displayed",
        "params": {
            "content":     ALERT_MESSAGE,
            "target_type": "location",
            "target_ids":  [LOCATION_ID],
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

    body = resp.json() if resp.text.strip() else {}
    return body.get("event_id", "")


def main() -> None:
    for var, value in [
        ("ZOOM_ACCOUNT_ID", ZOOM_ACCOUNT_ID),
        ("ZOOM_CLIENT_ID",  ZOOM_CLIENT_ID),
        ("ZOOM_CLIENT_SECRET", ZOOM_CLIENT_SECRET),
        ("LOCATION_ID",     LOCATION_ID),
    ]:
        if value.startswith("YOUR_"):
            print(f"ERROR: {var} is not configured.")
            sys.exit(1)

    try:
        print("--- Authenticating ---")
        token = get_access_token()
        print("  OK")

        print("\n--- Activating fire alert ---")
        event_id = activate_alert(token)

        STATE_FILE.write_text(event_id)
        print(f"\n  Alert is LIVE  (event_id: {event_id})")
        print(f"  ID saved to {STATE_FILE.name}")
        print(f"\n  Run zoom_emergency_signage_clear.py when the emergency is over.")

    except requests.HTTPError as exc:
        print(f"ERROR: HTTP {exc.response.status_code} — {exc.response.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
