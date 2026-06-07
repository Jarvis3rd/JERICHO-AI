import logging
import json


async def load_memories(mem0, user_id):
    """
    Load relevant memories for the user via the mem0 SDK.

    Uses the same AsyncMemoryClient passed in from agent.py, so the SDK builds
    and authenticates the request itself. No hand-built 'Authorization' header
    (that was the source of the 'Illegal header value' crash) and no raw httpx.
    Both load and save now go through the SDK on the client's default project,
    so they stay in sync.
    """
    try:
        results = await mem0.search(
            query="Lloyd personal preferences schedule",
            filters={"user_id": user_id},
        )

        # mem0 returns a list (v1) or {"results": [...]} (v2) — handle both.
        if isinstance(results, dict):
            results = results.get("results", [])

        if not results:
            logging.info(f"No memories found for {user_id}.")
            return ""

        memories = [
            {"memory": r["memory"]}
            for r in results
            if isinstance(r, dict) and r.get("memory")
        ]
        logging.info(f"Loaded {len(memories)} memories for {user_id}.")
        return json.dumps(memories)

    except Exception as e:
        logging.error(f"Failed to load memories: {e}")
        return ""


async def save_memories(mem0, user_id, messages):
    """Persist conversation messages to mem0 via the SDK."""
    try:
        if messages:
            await mem0.add(messages, user_id=user_id)
            logging.info(f"Saved {len(messages)} messages to memory.")
    except Exception as e:
        logging.error(f"Failed to save memories: {e}")
