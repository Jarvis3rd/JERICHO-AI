from flask import Flask, jsonify
from flask_cors import CORS
from livekit import api
import os
import uuid

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Add any new frontend URLs to the ALLOWED_ORIGINS env var in Railway dashboard
# (comma-separated, no spaces). Falls back to production domains if not set.
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://apertureautomations.ai,https://jarvis3rd.github.io"
).split(",")

CORS(app, origins=ALLOWED_ORIGINS)

# ── LiveKit credentials ───────────────────────────────────────────────────────
LIVEKIT_API_KEY    = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL        = os.getenv("LIVEKIT_URL", "wss://jerichoagent-uluhgyve.livekit.cloud")
DEMO_MODE          = os.getenv("DEMO_MODE", "false").lower() == "true"

# Fail fast on boot if credentials are missing — shows a clear error in
# Railway logs instead of generating broken tokens silently.
if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise RuntimeError(
        "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set as environment "
        "variables. Go to Railway → your service → Variables and add them."
    )


@app.route("/token", methods=["GET", "POST"])
def get_token():
    if DEMO_MODE:
        room_name = "demo-" + uuid.uuid4().hex[:8]
        identity  = "demo_visitor"
    else:
        room_name = "lloyd-personal"
        identity  = "lloyd_smith"

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return jsonify({
        "serverUrl": LIVEKIT_URL,
        "token":     token,
        "roomName":  room_name,
        "identity":  identity,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":    "ok",
        "demo_mode": DEMO_MODE,
        "origins":   ALLOWED_ORIGINS,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    print(f"Token server starting on port {port} | DEMO_MODE={DEMO_MODE}")
    print(f"Allowed origins: {ALLOWED_ORIGINS}")
    app.run(host="0.0.0.0", port=port)
