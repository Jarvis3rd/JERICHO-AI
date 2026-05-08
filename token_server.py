import os
import time
import uuid
import jwt
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

LIVEKIT_API_KEY    = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL        = os.getenv("LIVEKIT_URL", "wss://jerichoagent-uluhgyve.livekit.cloud")
DEMO_MODE          = os.getenv("DEMO_MODE", "false").lower() == "true"

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://apertureautomations.ai,https://jarvis3rd.github.io"
).split(",")

CORS(app, origins=ALLOWED_ORIGINS)

DEGRADED = not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET

print(f"token_server boot | KEY={LIVEKIT_API_KEY[:4]}... | DEGRADED={DEGRADED}", flush=True)


def make_livekit_token(api_key, api_secret, identity, room):
    now = int(time.time())
    payload = {
        "iss": api_key,
        "sub": identity,
        "name": identity,
        "nbf": now,
        "exp": now + 6 * 3600,
        "video": {
            "roomJoin": True,
            "room": room,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
    }
    return jwt.encode(payload, api_secret, algorithm="HS256")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok" if not DEGRADED else "degraded", "livekit_url": LIVEKIT_URL})


@app.route("/token", methods=["GET", "POST"])
def get_token():
    if DEGRADED:
        return jsonify({"error": "LIVEKIT_API_KEY/SECRET not configured"}), 503
    if DEMO_MODE:
        room_name = "demo-" + uuid.uuid4().hex[:8]
        identity = "demo_visitor"
    else:
        room_name = "lloyd-personal"
        identity = "lloyd_smith"
    token = make_livekit_token(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, identity, room_name)
    return jsonify({"token": token, "identity": identity, "roomName": room_name, "serverUrl": LIVEKIT_URL})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
