"""
Script de prueba local del agente.
Uso: python test_agent.py
"""

import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import create_agent


async def main():
    print("Cargando agente...")
    agent = create_agent()

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="cv_agent", session_service=session_service)

    session = await session_service.create_session(
        app_name="cv_agent",
        user_id="test_user",
    )

    print("Agente listo. Escribe tu pregunta (o 'salir' para terminar).\n")

    while True:
        user_input = input("Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            break

        print("Agente: ", end="", flush=True)

        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_input)],
            ),
        ):
            if event.is_final_response() and event.content:
                print(event.content.parts[0].text)
                print()


asyncio.run(main())
