import os
import logging
import resend
from typing import Annotated, Optional
from livekit.agents import function_tool, RunContext

resend.api_key = os.getenv("RESEND_API_KEY")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")

CARRIER_GATEWAYS = {
    "xfinity": "vtext.com",
    "comcast": "vtext.com",
    "verizon": "vtext.com",
    "att": "txt.att.net",
    "at&t": "txt.att.net",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "metro": "mymetropcs.com",
}

@function_tool()
async def send_sms(
    context: RunContext,
    message: Annotated[str, "The SMS message to send"],
    to_number: Annotated[Optional[str], "10-digit phone number. Defaults to Lloyd's number."] = None,
    carrier: Annotated[str, "Carrier: xfinity, verizon, att, tmobile, sprint, boost, cricket, metro."] = "xfinity",
) -> str:
    """Send an SMS to anyone on any major US carrier. Ask for carrier if sending to someone other than Lloyd."""
    try:
        number = to_number if to_number else YOUR_PHONE_NUMBER
        if not number:
            return "No phone number provided."
        phone_digits = number.replace("+1", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        gateway = CARRIER_GATEWAYS.get(carrier.lower(), "vtext.com")
        sms_email = f"{phone_digits}@{gateway}"
        resend.Emails.send({
            "from": "jericho@apertureautomations.ai",
            "to": sms_email,
            "subject": " ",
            "text": message
        })
        logging.info(f"SMS sent to {sms_email}: {message}")
        return f"SMS sent to {phone_digits} via {carrier}. Message: {message}"
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}")
        return f"Failed to send SMS: {str(e)}"
    