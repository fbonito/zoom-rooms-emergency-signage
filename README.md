# Zoom Rooms emergency signage

Push an emergency alert to every Zoom Rooms display in a building with one
command, or one webhook call, and clear it again when the emergency is over.

Zoom Rooms displays are already on the walls of meeting rooms across an office.
This turns them into emergency signage: when a fire alarm goes off, every
display in the target location shows your evacuation message instead of
whatever it was showing before.

> ### ⚠️ Safety notice
> This is a **supplementary** notification tool. It is **not** a certified
> fire-safety or life-safety system and must never be your only way of
> alerting people. Test it thoroughly in your own environment (ideally on a
> test location), keep your certified alarm and evacuation procedures as the
> primary system, and confirm that your credentials, network path and Zoom
> service availability are monitored. Provided as-is with no warranty (see
> [LICENSE](LICENSE)).

## How it works

```
 Fire alarm / operator / automation tool
                │  run script or call webhook
                ▼
   Script authenticates to Zoom (Server-to-Server OAuth)
                │
                ▼
   PATCH /v2/rooms/events
     zoomroom.emergency_alert_displayed  → alert shows on all Rooms in the location
     zoomroom.emergency_alert_removed    → displays return to normal
```

Both actions use Zoom's Rooms events API against a **location**, so the alert
reaches every Zoom Rooms display in that building (or whichever location you
target), with no per-room configuration.

## Two ways to run it

| | Command-line scripts | Webhook / cloud scripts |
|---|---|---|
| Activate | `zoom_emergency_signage.py` | `zoom_emergency_signage_webhook.py` |
| Clear | `zoom_emergency_signage_clear.py` | `zoom_emergency_signage_clear_webhook.py` |
| State | Saves the alert's `event_id` to a local `.active_event_id` file, and the clear script reads it | **Stateless.** No filesystem needed. The clear script uses `force_remove` so no `event_id` is required |
| Good for | A server, jump box or laptop where you run commands | Automation tools and serverless platforms (a function triggered by an alarm system, a workflow tool, a chatbot command) |

`zoom_lookup_locations.py` is a one-off helper that lists your Zoom Rooms
locations and their IDs so you can find the one to target.

## Triggering it with a physical button

In my setup the trigger is a physical button: a key on a Logitech Creative
Console that calls the webhook version of the activate script. One key shows
the alert and another clears it, so whoever is on site can raise the alarm
without opening a laptop or logging in to anything.

You don't need that specific device. Anything that can call a webhook or run
a command will work, for example a macro pad, a Stream Deck-style controller,
a smart or panic button, a hotkey tool, a chat command, or the output of your
alarm panel:

```
 [ physical button ] ──HTTP POST──►  automation platform / serverless function
                                       runs zoom_emergency_signage_webhook.py
                                                     │
                                                     ▼
                                     alert shown on every Zoom Rooms display
```

For example, a button (or any script) can fire the trigger with a plain HTTP
request to the URL your platform gives you:

```bash
curl -X POST "https://<your-automation-platform>/<activate-webhook-url>"
```

Use a second button or URL pointing at `zoom_emergency_signage_clear_webhook.py`
to clear the alert. Because the webhook versions are stateless, the clear
button needs no memory of the activation.

Whatever you use, protect the trigger URL like a credential, because anyone who
can call it can put an alert on your displays. Prefer a platform that supports
authentication or a secret token on the webhook.

## Setup

1. **Create a Server-to-Server OAuth app** in the Zoom App Marketplace and
   activate it. Grant it these scopes:
   - `room:write:admin` to show and clear alerts
   - `room:read:admin` to list locations (only needed for the lookup helper)

   Note the **Account ID**, **Client ID** and **Client Secret**.
2. **Provide the credentials as environment variables.** Never commit them:

   ```bash
   export ZOOM_ACCOUNT_ID="..."
   export ZOOM_CLIENT_ID="..."
   export ZOOM_CLIENT_SECRET="..."
   ```

3. **Find your location ID:**

   ```bash
   pip install -r requirements.txt
   python3 zoom_lookup_locations.py
   export ZOOM_LOCATION_ID="..."   # the building you want to alert
   ```

4. **Set your message.** Edit `ALERT_MESSAGE` near the top of the activate
   script you use. The default is a generic placeholder. Write the instruction
   people should actually follow, and keep it short, because it is shown on a
   wall display.
5. **Test on a test location first**, then run it for real.

## Usage

Command line:

```bash
python3 zoom_emergency_signage.py          # alert is live, event_id saved
python3 zoom_emergency_signage_clear.py    # clears it
```

Webhook / serverless: run `zoom_emergency_signage_webhook.py` (activate) and
`zoom_emergency_signage_clear_webhook.py` (clear) from your platform. Both
expose `main(event=None, context=None)`, so they can be used as the handler of
a function-style runtime, and they read configuration from the same
environment variables.

Each script exits non-zero and prints the HTTP error if authentication or the
API call fails, so your automation can alert on failure.

## Security notes

- **Keep credentials out of the code.** The scripts only read credentials from
  environment variables. In production, inject them from your platform's
  secret store.
- Anyone who can run these scripts, or trigger the webhook that does, can put
  an emergency alert on your displays. Restrict that access, and authenticate
  whatever endpoint triggers the webhook version.
- The OAuth app's `room:write:admin` scope is broad. Use a dedicated app for
  this, not one shared with other tooling.

## Repository contents

| File | Purpose |
|------|---------|
| `zoom_emergency_signage.py` | Activate the alert (CLI, saves `event_id`) |
| `zoom_emergency_signage_clear.py` | Clear the alert (CLI, reads saved `event_id`) |
| `zoom_emergency_signage_webhook.py` | Activate the alert (stateless) |
| `zoom_emergency_signage_clear_webhook.py` | Clear the alert (stateless, `force_remove`) |
| `zoom_lookup_locations.py` | List Zoom Rooms locations and IDs |

## Disclaimer

This is an independent project and is not affiliated with or endorsed by Zoom
or Logitech. Zoom, Zoom Rooms and Logitech Creative Console are trademarks of
their respective owners. Provided as-is
under the MIT license.

## License

[MIT](LICENSE)
