from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import noise_cancellation, openai
from livekit.plugins.openai.realtime.realtime_model import (
    TurnDetection,
    InputAudioTranscription,
    InputAudioNoiseReduction,
)
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import get_weather, search_web, send_email
from phone_control import control_phone
from google_calendar import manage_google_calendar
from sms import send_sms
from mem0 import AsyncMemoryClient
from mem0_helper import load_memories, save_memories
import os
import logging

MEM0_API_KEY = os.getenv("MEM0_API_KEY")
USER_ID = "lloyd_smith"


class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=openai.realtime.RealtimeModel(
                model="gpt-4o-realtime-preview",
                voice="onyx",
                temperature=0.6,
                turn_detection=TurnDetection(
                    type="server_vad",
                    silence_duration_ms=800,
                    threshold=0.5,
                    prefix_padding_ms=300,
                    create_response=True,
                ),
                input_audio_transcription=InputAudioTranscription(
                    model="gpt-4o-transcribe",
                ),
                input_audio_noise_reduction=InputAudioNoiseReduction(
                    type="near_field",
                ),
            ),
            tools=[
                get_weather,
                search_web,
                send_email,
                control_phone,
                manage_google_calendar,
                send_sms,
            ],
            chat_ctx=chat_ctx,
        )


async def entrypoint(ctx: agents.JobContext):

    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
        logging.info("Shutting down - saving chat context to memory...")
        messages_formatted = []

        for item in chat_ctx.items:
            if not hasattr(item, "content"):
                continue
            if isinstance(item.content, list):
                content_str = ' '.join(
                    str(c) for c in item.content if c is not None
                ).strip()
            else:
                content_str = str(item.content).strip() if item.content else ''

            if not content_str:
                continue
            if memory_str and memory_str in content_str:
                continue
            if item.role in ['user', 'assistant']:
                messages_formatted.append({
                    "role": item.role,
                    "content": content_str
                })

        logging.info(f"Messages to save: {messages_formatted}")
        await save_memories(mem0, USER_ID, messages_formatted)

    # ── Initialize mem0 ───────────────────────────────────────────────────────
    mem0 = AsyncMemoryClient(api_key=MEM0_API_KEY)
    memory_str = ''
    initial_ctx = ChatContext()

    try:
        memory_str = await load_memories(mem0, USER_ID)
        if memory_str:
            logging.info(f"Loaded memories for {USER_ID}")
            initial_ctx.add_message(
                role="assistant",
                content=f"The user's name is Lloyd, and this is relevant context about them: {memory_str}."
            )
        else:
            logging.info("No existing memories found for user.")
    except Exception as e:
        logging.error(f"Failed to retrieve memories: {e}")

    # ── Start session ─────────────────────────────────────────────────────────
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=initial_ctx),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    # ── Register shutdown callback ────────────────────────────────────────────
    async def _shutdown():
        await shutdown_hook(session._agent.chat_ctx, mem0, memory_str)
    ctx.add_shutdown_callback(_shutdown)



if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

