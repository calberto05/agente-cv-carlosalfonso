"""
Ejecuta casos de prueba contra el endpoint de Cloud Run.
Soporta conversaciones multi-turno construyendo el historial en el formato
de la OpenAI Responses API que usa la plataforma de Banorte.
"""

import os
import httpx
from dotenv import load_dotenv

from evaluation.test_cases import TestCase

load_dotenv()

_ENDPOINT = os.environ.get(
    "AGENT_ENDPOINT",
    "https://cv-agent-512646778802.us-central1.run.app/responses",
)
_API_KEY = os.environ.get("AGENT_API_KEY", "")
_TIMEOUT = 60.0


def _build_input(history: list[dict], user_text: str) -> list[dict]:
    """Construye el array `input` con el historial más el nuevo mensaje."""
    return history + [
        {
            "role": "user",
            "type": "message",
            "content": [{"type": "input_text", "text": user_text}],
        }
    ]


def run_test_case(test: TestCase) -> list[str]:
    """
    Ejecuta todos los turnos del caso de prueba.
    Devuelve la lista de respuestas del agente (una por turno).
    """
    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type": "application/json",
    }
    history: list[dict] = []
    responses: list[str] = []

    with httpx.Client(timeout=_TIMEOUT) as client:
        for user_text in test.messages:
            input_array = _build_input(history, user_text)
            payload = {
                "model": "gemini-2.5-flash",
                "input": input_array,
                "stream": False,
                "store": False,
            }
            resp = client.post(_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()

            data = resp.json()
            agent_text = (
                data.get("output", [{}])[0]
                .get("content", [{}])[0]
                .get("text", "")
            )
            responses.append(agent_text)

            # Extender el historial para el siguiente turno
            history = input_array + [
                {
                    "role": "assistant",
                    "type": "message",
                    "content": [{"type": "output_text", "text": agent_text}],
                }
            ]

    return responses
