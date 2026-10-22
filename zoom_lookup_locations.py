#!/usr/bin/env python3
"""
One-off helper — lists your Zoom Rooms locations so you can find the
LOCATION_ID to set for zoom_emergency_signage.py.

Run once, copy the ID, then you can delete this script.

REQUIRED SCOPES:
    room:read:admin

    python zoom_lookup_locations.py
"""

import os
import sys
import requests
from base64 import b64encode

# ---------------------------------------------------------------------------
ZOOM_ACCOUNT_ID    = os.getenv("ZOOM_ACCOUNT_ID",    "YOUR_ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID     = os.getenv("ZOOM_CLIENT_ID",     "YOUR_ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "YOUR_ZOOM_CLIENT_SECRET")

ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE  = "https://api.zoom.us/v2"
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


def main() -> None:
    for var, value in [
        ("ZOOM_ACCOUNT_ID",    ZOOM_ACCOUNT_ID),
        ("ZOOM_CLIENT_ID",     ZOOM_CLIENT_ID),
        ("ZOOM_CLIENT_SECRET", ZOOM_CLIENT_SECRET),
    ]:
        if value.startswith("YOUR_"):
            print(f"ERROR: {var} is not set.")
            sys.exit(1)

    try:
        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        # --- Zoom Rooms Locations ---
        resp = requests.get(f"{ZOOM_API_BASE}/rooms/locations", headers=headers, timeout=15)
        resp.raise_for_status()
        locations = resp.json().get("locations", [])

        print("\nZOOM ROOMS LOCATIONS")
        print(f"  {'ID':<30}  {'NAME':<40}  PARENT ID")
        print(f"  {'-'*30}  {'-'*40}  {'-'*30}")
        for loc in locations:
            print(
                f"  {loc.get('id', ''):<30}  {loc.get('name', ''):<40}  "
                f"{loc.get('parent_location_id', '—')}"
            )

        print("\nCopy the location ID for your building into zoom_emergency_signage.py → LOCATION_ID")

    except requests.HTTPError as exc:
        print(f"ERROR: HTTP {exc.response.status_code} — {exc.response.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
