from flask import Flask, jsonify
from flask_cors import CORS
from livekit import api
import os
import uuid

app = Flask(__name__)
CORS(app)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://jerichoagent-uluhgyve.livekit.cloud")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

@app.route("/token", methods=["GET", "POST"])
def get_token():
    if DEMO_MODE:
        room_name = "demo-" + uuid.uuid4().hex[:8]
        identity = "demo_visitor"
    else:
        room_name = "lloyd-personal"
        identity = "lloyd_smith"
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    return jsonify({"serverUrl": LIVEKIT_URL, "token": token, "roomName": room_name, "identity": identity})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "demo_mode": DEMO_MODE})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    app.run(host="0.0.0.0", port=port)
