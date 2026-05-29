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
