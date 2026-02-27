import subprocess
import httpx
import os
import logging
from livekit.agents import function_tool, RunContext

PHONE_IP = os.getenv("PHONE_IP")
ADB_PORT = os.getenv("ADB_PORT", "5555")
TASKER_WEBHOOK_URL = os.getenv("TASKER_WEBHOOK_URL")
TASKER_AUTH_TOKEN = os.getenv("TASKER_AUTH_TOKEN")


def _adb(command: list[str]) -> str:
    """Run an ADB command against the phone over WiFi."""
    try:
        result = subprocess.run(
            ["adb", "-s", f"{PHONE_IP}:{ADB_PORT}"] + command,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "ADB command timed out"
    except FileNotFoundError:
        return "ADB not found - install Android Platform Tools"


async def _tasker_webhook(action: str, params: dict = {}) -> str:
    """Trigger a Tasker task via webhook."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TASKER_WEBHOOK_URL,
            json={"action": action, **params},
            headers={"Authorization": f"Bearer {TASKER_AUTH_TOKEN}"},
            timeout=10
        )
        return response.text


@function_tool()
async def control_phone(
    context: RunContext,  # type: ignore
    action: str,
    value: str = ""
) -> str:
    """
    Control the user's Android phone. Available actions:
    - 'volume_up' / 'volume_down' / 'mute'
    - 'screen_on' / 'screen_off'
    - 'play_music' / 'pause_music' / 'next_track'
    - 'open_app' (value = app package name, e.g. 'com.spotify.music')
    - 'call' (value = phone number)
    - 'get_battery' (returns battery level)
    - 'send_notification' (value = notification text, requires Tasker)
    - 'read_notifications' (requires Tasker)
    - 'take_photo' (requires Tasker)
    - 'wifi_on' / 'wifi_off' (requires Tasker)
    - 'do_not_disturb_on' / 'do_not_disturb_off' (requires Tasker)
    - 'get_location' (requires Tasker)
    - 'brightness_up' / 'brightness_down' (requires Tasker)

    Args:
        action: The action to perform on the phone
        value: Optional parameter for actions that need it (app name, phone number, etc.)
    """
    logging.info(f"Phone control: action={action}, value={value}")

    # ── ADB-based actions ────────────────────────────────────────────────────
    adb_key_actions = {
        "volume_up":    "KEYCODE_VOLUME_UP",
        "volume_down":  "KEYCODE_VOLUME_DOWN",
        "mute":         "KEYCODE_VOLUME_MUTE",
        "screen_on":    "KEYCODE_WAKEUP",
        "screen_off":   "KEYCODE_SLEEP",
        "play_music":   "KEYCODE_MEDIA_PLAY",
        "pause_music":  "KEYCODE_MEDIA_PAUSE",
        "next_track":   "KEYCODE_MEDIA_NEXT",
    }

    if action in adb_key_actions:
        result = _adb(["shell", "input", "keyevent", adb_key_actions[action]])
        return f"Executed {action}: {result or 'success'}"

    elif action == "open_app":
        if not value:
            return "Error: provide the app package name as 'value' (e.g. 'com.spotify.music')"
        result = _adb(["shell", "monkey", "-p", value, "1"])
        return f"Opened {value}: {result or 'success'}"

    elif action == "call":
        if not value:
            return "Error: provide a phone number as 'value'"
        result = _adb(["shell", "am", "start", "-a",
                       "android.intent.action.CALL", "-d", f"tel:{value}"])
        return f"Calling {value}: {result or 'success'}"

    elif action == "get_battery":
        result = _adb(["shell", "dumpsys", "battery"])
        for line in result.splitlines():
            if "level:" in line:
                return f"Battery level: {line.split(':')[1].strip()}%"
        return f"Battery info: {result}"

    # ── Tasker-based actions ─────────────────────────────────────────────────
    tasker_actions = [
        "send_notification", "take_photo", "read_notifications",
        "wifi_on", "wifi_off", "do_not_disturb_on", "do_not_disturb_off",
        "get_location", "brightness_up", "brightness_down", "unmute",
    ]

    if action in tasker_actions:
        if not TASKER_WEBHOOK_URL:
            return f"Tasker webhook not configured. Set TASKER_WEBHOOK_URL in your .env to use '{action}'."
        try:
            result = await _tasker_webhook(action, {"value": value})
            return f"Tasker executed {action}: {result}"
        except Exception as e:
            return f"Tasker webhook failed for '{action}': {e}"

    return f"Unknown action: '{action}'. Check the list of supported actions in the tool description."