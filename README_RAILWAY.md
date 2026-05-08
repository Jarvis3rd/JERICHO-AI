# Jericho AI — Railway Deployment Guide

## Architecture

Two separate Railway services talk to each other via LiveKit Cloud:

```
Browser (apertureautomations.ai)
    │
    ├─ GET /token ──────────► Service 1: Token Server   (token_server.py)
    │                          Flask · PORT env var
    │
    └─ WebRTC ─────────────► LiveKit Cloud Room
                                   │
                              Service 2: Agent Worker   (agent.py)
                              LiveKit Agents · connects to same room
```

---

## Step 1 — Service 1: Token Server

This is your existing Railway service. It should already be running.

**Start command (in Railway → Settings → Deploy):**
```
python token_server.py
```

**Required environment variables:**
| Variable | Value |
|---|---|
| `LIVEKIT_API_KEY` | From LiveKit Cloud dashboard |
| `LIVEKIT_API_SECRET` | From LiveKit Cloud dashboard |
| `LIVEKIT_URL` | `wss://jerichoagent-uluhgyve.livekit.cloud` |
| `DEMO_MODE` | `true` or `false` |
| `ALLOWED_ORIGINS` | `https://apertureautomations.ai,https://jarvis3rd.github.io` |
| `PORT` | Set automatically by Railway — do not override |

✅ Test it: `curl https://your-token-service.up.railway.app/health`

---

## Step 2 — Service 2: Agent Worker (NEW)

Create a **second service** in Railway from the same GitHub repo.

1. In Railway dashboard → **New Service** → **GitHub Repo** → select `JERICHO-AI`
2. Go to **Settings → Deploy**
3. Set **Start Command** to:
   ```
   python agent.py start
   ```
4. Add all the same environment variables as Service 1, PLUS:

| Variable | Value |
|---|---|
| `LIVEKIT_API_KEY` | Same as Service 1 |
| `LIVEKIT_API_SECRET` | Same as Service 1 |
| `LIVEKIT_URL` | Same as Service 1 |
| `DEMO_MODE` | `true` or `false` |
| `MEM0_API_KEY` | Your Mem0 API key |
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your login password) |
| `RESEND_API_KEY` | Your Resend API key |
| `YOUR_PHONE_NUMBER` | Your phone number with country code |
| `OPENAI_API_KEY` | Your OpenAI key (for GPT-4o Realtime) |

> **Tip:** Use Railway's **Shared Variables** feature to define keys once
> and reference them in both services — avoids copy-paste drift.

5. Deploy. Check logs — you should see the agent connect to LiveKit.

---

## Step 3 — Verify the full flow

1. Open `https://apertureautomations.ai`
2. Trigger a connection — the frontend fetches a token from Service 1
3. The browser connects to LiveKit Cloud using that token
4. LiveKit dispatches a job to your agent worker (Service 2)
5. Jericho joins the room and starts the session

**Check Service 2 logs for:**
```
INFO     livekit.agents - agent connected to room: lloyd-personal
```

If you see that line, Jericho is live. 🎉

---

## Alternative: single-service quick start (dev only)

If you want both processes in one service temporarily:

**Start command:**
```
bash start.sh
```

This runs both `agent.py` and `token_server.py` in the same container.
Not recommended for production — if either crashes, both go down.

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `RuntimeError: LIVEKIT_API_KEY must be set` | Missing env var | Add to Railway Variables tab |
| Token returns but no agent joins | Worker service not running | Complete Step 2 above |
| CORS error in browser console | Your frontend URL not in `ALLOWED_ORIGINS` | Add it to the env var |
| `SMTPAuthenticationError` | Wrong Gmail App Password | Generate a new one at myaccount.google.com → Security → App Passwords |
