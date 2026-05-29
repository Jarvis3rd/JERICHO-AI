from dotenv import load_dotenv
load_dotenv()
 
from livekit import agents
from livekit.agents import AgentSession, Agent, ChatContext, function_tool, RoomInputOptions
from livekit.plugins import noise_cancellation, openai
from livekit.plugins.openai.realtime.realtime_model import (
    TurnDetection,
    InputAudioTranscription,
    InputAudioNoiseReduction,
)
from prompts import (
    AGENT_INSTRUCTION,
    SESSION_INSTRUCTION,
    DEMO_AGENT_INSTRUCTION,
    DEMO_SESSION_INSTRUCTION,
)
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
DEMO_USER_ID = "demo_visitor"
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
 
# -- Demo-mode stub tools -----------------------------------------------------
 
@function_tool
async def demo_send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient on behalf of the user."""
    return (
        f"In a full deployment I would send an email to '{to}' with subject '{subject}'. "
        "However, this is a public demo -- real email sending is disabled. "
        "Contact Aperture Automations to see this capability in action."
    )
 
@function_tool
async def demo_control_phone(action: str, number: str = "") -> str:
    """Control the phone -- make calls, answer, hang up, or manage phone actions."""
    return (
        "In a full deployment I would carry out that phone action for you. "
        "However, this is a public demo -- phone control is disabled. "
        "Contact Aperture Automations to see this capability in action."
    )
 
@function_tool
async def demo_manage_google_calendar(action: str, details: str = "") -> str:
    """Manage Google Calendar -- create, update, read, or delete events."""
    return (
        "In a full deployment I would manage your calendar accordingly. "
        "However, this is a public demo -- calendar access is disabled. "
        "Contact Aperture Automations to see this capability in action."
    )
 
@function_tool
async def demo_send_sms(to: str, message: str) -> str:
    """Send an SMS message to a phone number."""
    return (
        f"In a full deployment I would send an SMS to '{to}'. "
        "However, this is a public demo -- SMS sending is disabled. "
        "Contact Aperture Automations to see this capability in action."
    )
 
 
class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        if DEMO_MODE:
            instructions = DEMO_AGENT_INSTRUCTION
            tools = [
                get_weather,
                search_web,
                demo_send_email,
                demo_control_phone,
                demo_manage_google_calendar,
                demo_send_sms,
            ]
        else:
            instructions = AGENT_INSTRUCTION
            tools = [
                get_weather,
                search_web,
                send_email,
                control_phone,
                manage_google_calendar,
                send_sms,
            ]
 
        super().__init__(
            instructions=instructions,
            llm=openai.realtime.RealtimeModel(
                model="gpt-4o-realtime-preview",
                voice="ash",
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
            tools=tools,
            chat_ctx=chat_ctx,
        )
 
 
async def entrypoint(ctx: agents.JobContext):
    active_user_id = DEMO_USER_ID if DEMO_MODE else USER_ID
    active_session_instruction = DEMO_SESSION_INSTRUCTION if DEMO_MODE else SESSION_INSTRUCTION
 
    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
        if DEMO_MODE:
            logging.info("Demo mode -- skipping memory save for demo_visitor.")
            return
 
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
 
    mem0 = None
    memory_str = ''
    initial_ctx = ChatContext()
 
    try:
        mem0 = AsyncMemoryClient(api_key=MEM0_API_KEY)
        memory_str = await load_memories(mem0, active_user_id)
        if memory_str:
            logging.info(f"Loaded memories for {active_user_id}")
            if DEMO_MODE:
                initial_ctx.add_message(
                    role="assistant",
                    content=f"Here is context from previous demo interactions: {memory_str}."
                )
            else:
                initial_ctx.add_message(
                    role="assistant",
                    content=f"The user's name is Lloyd, and this is relevant context about them: {memory_str}."
                )
        else:
            logging.info("No existing memories found for user.")
    except Exception as e:
        logging.error(f"mem0 unavailable, continuing without memory: {e}")
 
    await ctx.connect()
 
    session = AgentSession()
 
    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=initial_ctx),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
 
    await session.generate_reply(
        instructions=active_session_instruction,
    )
 
    async def _shutdown():
        if mem0 is not None:
            await shutdown_hook(session._agent.chat_ctx, mem0, memory_str)
    ctx.add_shutdown_callback(_shutdown)
 
 
async def request_fnc(req):
    try:
        room_name = req.room.name
    except Exception:
        room_name = str(getattr(req, 'room', 'unknown'))
    logging.info(f'[request_fnc] Job received for room: {room_name}')
    await req.accept()
    logging.info(f'[request_fnc] Accepted job for room: {room_name}')
 
 
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_fnc,
    ))
