import logging
import json
import httpx
import os

MEM0_API_KEY = os.getenv("MEM0_API_KEY")
MEM0_ORG_ID = os.getenv("MEM0_ORG_ID")
MEM0_PROJECT_ID = os.getenv("MEM0_PROJECT_ID")
MEM0_BASE_URL = "https://api.mem0.ai/v2"

async def load_memories(mem0, user_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MEM0_BASE_URL}/memories/search/",
                headers={"Authorization": f"Token {MEM0_API_KEY}"},
                json={
                    "query": "Lloyd personal preferences schedule",
                    "filters": {"user_id": user_id},
                    "org_id": MEM0_ORG_ID,
                    "project_id": MEM0_PROJECT_ID
                }
            )
            response.raise_for_status()
            results = response.json()
            if not results:
                return ""
            memories = [{"memory": r["memory"]} for r in results if r.get("memory")]
            logging.info(f"Loaded {len(memories)} memories for {user_id}")
            return json.dumps(memories)
    except Exception as e:
        logging.error(f"Failed to load memories: {e}")
        return ""

async def save_memories(mem0, user_id, messages):
    try:
        if messages:
            await mem0.add(messages, user_id=user_id)
            logging.info(f"Saved {len(messages)} messages to memory.")
    except Exception as e:
        logging.error(f"Failed to save memories: {e}")