"""
CV Agent — Open Responses API endpoint.

Modos:
  - Local: python -m api.main
  - Cloud Run: uvicorn api.main:app --host 0.0.0.0 --port 8080
"""

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import create_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea el agente una sola vez al arrancar el servicio."""
    print("Cargando agente...")
    cv_agent = create_agent()
    session_service = InMemorySessionService()
    app.state.runner = Runner(
        agent=cv_agent,
        app_name="cv_agent",
        session_service=session_service,
    )
    app.state.session_service = session_service
    print("Agente listo.")
    yield


app = FastAPI(title="CV Agent — Open Responses API", lifespan=lifespan)


# --------------------------------------------------------------------------- #
# Modelos de request / response
# --------------------------------------------------------------------------- #

class InputMessage(BaseModel):
    role: str
    content: str


class ResponseRequest(BaseModel):
    model: str | None = None
    input: Union[str, list[InputMessage]]
    session_id: str | None = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _validate_api_key(authorization: str | None) -> None:
    api_key = os.environ.get("AGENT_API_KEY")
    if not api_key:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header requerido: Bearer <key>",
        )
    if authorization.removeprefix("Bearer ").strip() != api_key:
        raise HTTPException(status_code=403, detail="API key inválida")


def _extract_user_message(input_data: Union[str, list[InputMessage]]) -> str:
    if isinstance(input_data, str):
        return input_data
    user_messages = [m.content for m in input_data if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=400,
            detail="No se encontró mensaje del usuario en el input",
        )
    return user_messages[-1]


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.post("/")
@app.post("/responses")
async def create_response(
    body: ResponseRequest,
    request: Request,
    authorization: str = Header(None),
):
    _validate_api_key(authorization)

    user_message = _extract_user_message(body.input)

    if len(user_message) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Mensaje demasiado largo. Máximo 2000 caracteres.",
        )

    session_id = body.session_id or str(uuid.uuid4())
    runner: Runner = request.app.state.runner
    session_service: InMemorySessionService = request.app.state.session_service

    existing = await session_service.get_session(
        app_name="cv_agent", user_id="user", session_id=session_id
    )
    if not existing:
        await session_service.create_session(
            app_name="cv_agent", user_id="user", session_id=session_id
        )

    response_text = ""
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        ),
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text

    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(time.time()),
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "output": [
            {
                "type": "message",
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "role": "assistant",
                "content": [{"type": "output_text", "text": response_text}],
            }
        ],
        "session_id": session_id,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
