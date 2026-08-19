"""
LLM-as-judge: evalúa si la respuesta del agente cumple cada criterio.
Usa Gemini con structured output (response_schema) para obtener
una evaluación determinista y parseable.
"""

import os
import json
from datetime import date

import vertexai
from google.genai import types
from google import genai
from dotenv import load_dotenv

load_dotenv()

_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _fecha_hoy() -> str:
    hoy = date.today()
    return f"{hoy.day} de {_MESES_ES[hoy.month - 1]} de {hoy.year}"


_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "reasoning": {"type": "string"},
                },
                "required": ["criterion", "passed", "reasoning"],
            },
        },
        "overall_score": {
            "type": "integer",
            "description": "Puntuación de 1 a 5 basada en los criterios cumplidos",
        },
        "summary": {"type": "string"},
    },
    "required": ["criteria_results", "overall_score", "summary"],
}

_SYSTEM_PROMPT_TEMPLATE = """\
Eres un evaluador experto de agentes conversacionales de IA.
Tu tarea es analizar la respuesta de un agente y determinar si cumple
con cada uno de los criterios de evaluación proporcionados.

Hoy es {today}. Úsalo como referencia real para evaluar criterios sobre \
fechas o vigencia (por ejemplo, si el agente evaluado menciona "hoy" o \
calcula cuánto tiempo lleva estudiando/trabajando) — no asumas la fecha \
de tu propio entrenamiento.

Sé objetivo y preciso. Basa tu evaluación únicamente en el contenido
de la respuesta del agente.

La puntuación overall_score debe ser:
5 — Todos los criterios cumplidos
4 — La mayoría cumplidos (uno fallido)
3 — Mitad cumplidos
2 — Minoría cumplidos
1 — Ningún criterio cumplido
"""


def _build_judge_prompt(
    messages: list[str],
    responses: list[str],
    criteria: list[str],
    expected_behavior: str,
) -> str:
    conversation = ""
    for user_msg, agent_resp in zip(messages, responses):
        conversation += f"Usuario: {user_msg}\nAgente: {agent_resp}\n\n"

    criteria_text = "\n".join(f"- {c}" for c in criteria)

    return f"""\
## Conversación evaluada

{conversation.strip()}

## Comportamiento esperado
{expected_behavior}

## Criterios de evaluación
{criteria_text}

Evalúa si la respuesta del agente cumple cada criterio.
"""


def evaluate(
    messages: list[str],
    responses: list[str],
    criteria: list[str],
    expected_behavior: str,
) -> dict:
    """
    Evalúa las respuestas del agente contra los criterios dados.
    Devuelve un dict con criteria_results, overall_score y summary.
    """
    use_vertexai = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"

    if use_vertexai:
        client = genai.Client(vertexai=True, project=_PROJECT, location=_LOCATION)
    else:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))

    prompt = _build_judge_prompt(messages, responses, criteria, expected_behavior)

    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT_TEMPLATE.format(today=_fecha_hoy()),
            response_mime_type="application/json",
            response_schema=_JUDGE_SCHEMA,
            temperature=0.0,
        ),
    )

    return json.loads(response.text)
