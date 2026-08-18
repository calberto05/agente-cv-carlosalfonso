"""
CV Agent — Open Responses API endpoint.

Modos:
  - Local: python -m api.main
  - Cloud Run: uvicorn api.main:app --host 0.0.0.0 --port 8080
"""

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import create_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea el agente una sola vez al arrancar el servicio."""
    logger.info("Cargando agente...")
    cv_agent = create_agent()
    session_service = InMemorySessionService()
    app.state.runner = Runner(
        agent=cv_agent,
        app_name="cv_agent",
        session_service=session_service,
    )
    app.state.session_service = session_service
    logger.info("Agente listo.")
    yield


app = FastAPI(title="CV Agent — Open Responses API", lifespan=lifespan)


# --------------------------------------------------------------------------- #
# Modelos de request / response
# --------------------------------------------------------------------------- #

class ContentBlock(BaseModel):
    type: str = "input_text"
    text: str = ""


class InputMessage(BaseModel):
    role: str
    # content puede ser string o lista de bloques (formato OpenAI Responses API)
    content: Union[str, list[ContentBlock], list[Any]]


class ResponseRequest(BaseModel):
    model: str | None = None
    input: Union[str, list[InputMessage], list[Any]]
    session_id: str | None = None
    instructions: str | None = None


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


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                parts.append(block.text)
        return " ".join(p for p in parts if p)
    return str(content)


def _extract_user_message(input_data: Any) -> tuple[str, str]:
    """Devuelve (ultimo_mensaje_usuario, mensaje_con_contexto)."""
    if isinstance(input_data, str):
        return input_data, input_data

    if isinstance(input_data, list) and len(input_data) > 0:
        messages = []
        for item in input_data:
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", "")
            text = _extract_text_from_content(content)
            if role and text:
                messages.append((role, text))

        if not messages:
            raise HTTPException(status_code=400, detail="No se encontró mensaje del usuario en el input")

        last_text = messages[-1][1]

        if len(messages) > 1:
            # Sliding window: últimos 10 mensajes del historial (5 intercambios pregunta-respuesta)
            window = messages[:-1][-10:]
            history = "\n".join(
                f"{'Usuario' if r == 'user' else 'Asistente'}: {t}"
                for r, t in window
            )
            full_message = f"[Historial de conversación]\n{history}\n\n[Pregunta actual]\n{last_text}"
            return last_text, full_message

        return last_text, last_text

    raise HTTPException(
        status_code=400,
        detail="No se encontró mensaje del usuario en el input",
    )


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.post("/")
@app.post("/responses")
async def create_response(
    request: Request,
    authorization: str = Header(None),
):
    logger.info("Authorization header recibido: %s", authorization)
    _validate_api_key(authorization)

    # Leemos el body raw para loguear y parsear con flexibilidad
    raw = await request.json()
    logger.info("Payload recibido: %s", raw)

    input_data = raw.get("input")
    session_id = raw.get("session_id") or str(uuid.uuid4())

    if input_data is None:
        raise HTTPException(status_code=422, detail="Campo 'input' requerido")

    last_message, full_message = _extract_user_message(input_data)

    if len(last_message) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Mensaje demasiado largo. Máximo 2000 caracteres.",
        )

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
            parts=[types.Part(text=full_message)],
        ),
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text

    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": raw.get("model") or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "output": [
            {
                "type": "message",
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "role": "assistant",
                "status": "completed",
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
