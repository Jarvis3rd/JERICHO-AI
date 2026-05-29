import os, time, uuid, asyncio, jwt
from flask import Flask, jsonify, request
from flask_cors import CORS
 
app = Flask(__name__)
 
LIVEKIT_API_KEY    = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL        = os.getenv("LIVEKIT_URL", "wss://jerichoagent-uluhqyve.livekit.cloud")
DEMO_MODE          = os.getenv("DEMO_MODE", "false").lower() == "true"
AGENT_NAME         = "jericho"
 
CORS(app)  # Allow all origins
 
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
 
 
async def _dispatch_agent(room_name):
    """Create room then dispatch Jericho — order matters!"""
    try:
        from livekit import api as lk_api
        lk = lk_api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )
        try:
            # Step 1: ensure room exists before dispatching
            await lk.room.create_room(lk_api.CreateRoomRequest(name=room_name))
            print(f"[dispatch] Room created: {room_name}", flush=True)
            # Step 2: dispatch agent to the now-existing room
            await lk.agent_dispatch.create_dispatch(
                lk_api.CreateAgentDispatchRequest(
                    agent_name=AGENT_NAME,
                    room=room_name,
                )
            )
            print(f"[dispatch] Agent dispatched to room: {room_name}", flush=True)
        finally:
            await lk.aclose()
    except Exception as e:
        print(f"[dispatch] Failed: {e}", flush=True)
 
 
def dispatch_agent_sync(room_name):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_dispatch_agent(room_name))
    finally:
        loop.close()
 
 
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok" if not DEGRADED else "degraded", "livekit_url": LIVEKIT_URL})
 
 
@app.route("/token", methods=["GET", "POST"])
def get_token():
    if DEGRADED:
        return jsonify({"error": "LIVEKIT_API_KEY/SECRET not configured"}), 503
 
    if DEMO_MODE:
        room_name = "demo-" + uuid.uuid4().hex[:8]
        identity  = "demo_visitor"
    else:
        room_name = "lloyd-personal"
        identity  = "lloyd_smith"
 
    token = make_livekit_token(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, identity, room_name)
 
    # Dispatch in background so token returns immediately
    import threading
    threading.Thread(target=dispatch_agent_sync, args=(room_name,), daemon=True).start()
 
    return jsonify({
        "token":     token,
        "identity":  identity,
        "roomName":  room_name,
        "serverUrl": LIVEKIT_URL
    })
 
 
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
