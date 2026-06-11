import os
import re
import asyncio
import logging
from typing import Annotated

from livekit.agents import function_tool, RunContext
from twilio.rest import Client

# ── Twilio config (set these in .env) ─────────────────────────────────────────
TWILIO_ACCOUNT_SID = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
TWILIO_AUTH_TOKEN  = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
TWILIO_FROM_NUMBER = (os.getenv("TWILIO_FROM_NUMBER") or "").strip()   # your Twilio number, E.164 e.g. +15559876543
DEFAULT_TO_NUMBER  = (os.getenv("YOUR_PHONE_NUMBER") or "").strip()    # fallback recipient (Lloyd's own phone)


def _normalize_e164(number: str) -> str:
    """Best-effort convert a spoken/loose US number into E.164 (+1XXXXXXXXXX)."""
    n = number.strip()
    if n.startswith("+"):
        return "+" + re.sub(r"\D", "", n[1:])
    digits = re.sub(r"\D", "", n)
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    # Fall back to whatever we have, prefixed — Twilio will reject if truly invalid.
    return "+" + digits if digits else n


@function_tool()
async def send_sms(
    context: RunContext,  # type: ignore
    message: Annotated[str, "The text message body to send."],
    to_number: Annotated[
        str,
        "Recipient phone number (any format, e.g. '555-123-4567' or '+15551234567'). "
        "Leave blank to text the owner's own phone.",
    ] = "",
) -> str:
    """
    Send an SMS text message to any U.S. phone number via Twilio.
    Works for any recipient regardless of carrier — no carrier information is needed.
    """
    try:
        if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
            return ("SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                    "and TWILIO_FROM_NUMBER in the environment.")

        raw_to = (to_number or DEFAULT_TO_NUMBER).strip()
        if not raw_to:
            return "No recipient number was provided and no default number is set."

        to = _normalize_e164(raw_to)

        # Twilio's SDK is synchronous; run it off the event loop so we don't block the agent.
        msg = await asyncio.to_thread(
            lambda: Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
                body=message,
                from_=TWILIO_FROM_NUMBER,
                to=to,
            )
        )
        logging.info(f"SMS sent to {to} via Twilio (sid={msg.sid}, status={msg.status})")
        return f"Text message sent to {to}."

    except Exception as e:
        logging.error(f"Twilio SMS failed: {e}")
        return f"Error sending SMS: {e}"
