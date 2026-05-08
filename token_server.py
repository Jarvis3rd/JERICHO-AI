from flask import Flask, jsonify
from flask_cors import CORS
from livekit import api
import os
import uuid

app = Flask(__name__)

# ── Diagnostic: what env vars does Railway actually see? ──────────────────────
print("=" * 60, flush=True)
print("ENV DIAGNOSTIC — token_server.py boot", flush=True)
print("=" * 60, flush=True)

interesting = [k for k in os.environ.keys() if any(
    s in k.upper() for s in ("LIVEKIT", "ALLOWED_ORIGINS", "DEMO_MODE", "PORT")
)]
if not interesting:
    print("⚠️  No LIVEKIT_* / DEMO_MODE / ALLOWED_ORIGINS / PORT vars found.", flush=True)
else:
    for k in sorted(interesting):
        v = os.environ[k]
        # Mask secrets — show length + first/last 3 chars only
        if "SECRET" in k or "KEY" in k:
            shown = f"<len={len(v)} | {v[:3]}…{v[-3:]}>" if len(v) > 6 else f"<len={len(v)}>"
        else:
            shown = v
        print(f"  {k} = {shown}", flush=True)

print("=" * 60, flush=True)

# ── CORS ──────────────────────────────────────────────────────────────────────
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

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    # Stay alive so /health still responds — easier to debug than a crash loop.
    print(
        "❌ LIVEKIT_API_KEY / LIVEKIT_API_SECRET missing. "
        "Server is starting in degraded mode — /token will 503, /health still works.",
        flush=True,
    )
    DEGRADED = True
else:
    print("✅ LiveKit credentials loaded.", flush=True)
    DEGRADED = False


@app.route("/token", methods=["GET", "POST"])
def get_token():
    if DEGRADED:
        return jsonify({"error": "LIVEKIT_API_KEY/SECRET not set on server"}), 503

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
        "status":      "degraded" if DEGRADED else "ok",
        "demo_mode":   DEMO_MODE,
        "origins":     ALLOWED_ORIGINS,
        "have_key":    bool(LIVEKIT_API_KEY),
        "have_secret": bool(LIVEKIT_API_SECRET),
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    print(f"Token server starting on port {port} | DEMO_MODE={DEMO_MODE}", flush=True)
    print(f"Allowed origins: {ALLOWED_ORIGINS}", flush=True)
    app.run(host="0.0.0.0", port=port)
