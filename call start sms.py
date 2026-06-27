"""
call_start_sms.py — the "we're on it" text.

Fires the moment a call is actually placed on the customer's behalf, so they know
we're holding for them. Best-effort by design: a texting hiccup must NEVER break
the call flow, so every failure is swallowed and logged, never raised.

Reuses the same Twilio env vars your sms.py already relies on:
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

Drop this file next to app.py. No new dependencies (twilio is already installed).
"""

import os
import logging

from twilio.rest import Client

_SID   = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
_TOKEN = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
_FROM  = (os.getenv("TWILIO_FROM_NUMBER") or "").strip()


def send(customer_number: str, company: str) -> None:
    """Text the customer that we're now on hold for them at `company`.

    Args:
        customer_number: E.164 number to text (e.g. "+15595551234").
        company: friendly line name, e.g. "PG&E" (use the target's label).
    """
    if not (_SID and _TOKEN and _FROM):
        logging.warning("call-start SMS skipped: Twilio env vars not set.")
        return
    if not customer_number:
        logging.warning("call-start SMS skipped: no customer number.")
        return

    body = (
        f"Concierge Caller: We're calling {company} for you now and waiting on hold. "
        f"Keep your phone handy — we'll ring you the moment a live agent picks up. "
        f"Reply STOP to opt out."
    )

    try:
        msg = Client(_SID, _TOKEN).messages.create(
            body=body,
            from_=_FROM,
            to=customer_number,
        )
        logging.info(f"call-start SMS sent to {customer_number} (sid={msg.sid})")
    except Exception as e:
        # Never let a texting failure break the call that was just placed.
        logging.error(f"call-start SMS failed for {customer_number}: {e}")
