import json
import os
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

_CV_SCHEMA = {
    "type": "object",
    "properties": {
        "personal_info": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "linkedin": {"type": "string"},
                "github": {"type": "string"},
                "location": {"type": "string"},
                "summary": {"type": "string"},
            },
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "institution": {"type": "string"},
                    "degree": {"type": "string"},
                    "field": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
            },
        },
        "skills": {
            "type": "object",
            "properties": {
                "programming_languages": {"type": "array", "items": {"type": "string"}},
                "frameworks": {"type": "array", "items": {"type": "string"}},
                "tools": {"type": "array", "items": {"type": "string"}},
                "cloud": {"type": "array", "items": {"type": "string"}},
                "other": {"type": "array", "items": {"type": "string"}},
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                    "url": {"type": "string"},
                    "github_repo": {"type": "string"},
                },
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "date": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
        "hackathons": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "organizer": {"type": "string"},
                    "date": {"type": "string"},
                    "description": {"type": "string"},
                    "result": {"type": "string"},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "proficiency": {"type": "string"},
                },
            },
        },
        "extra_sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_name": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
        },
    },
}

_PROMPT = """Analiza el siguiente CV y extrae toda la información disponible.
Sé exhaustivo: captura cada detalle de experiencia, proyectos, habilidades, educación, certificaciones y hackathones.
Si una sección no existe en el CV, usa lista vacía [] o cadena vacía "".
Cualquier sección que no encaje en los campos estándar (por ejemplo: idiomas, publicaciones, voluntariado, premios, referencias)
ponla en extra_sections con su nombre y contenido como texto.

CV:
{cv_text}"""


def structure_cv(cv_text: str, project_id: str, location: str = "us-central1") -> dict:
    vertexai.init(project=project_id, location=location)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    model = GenerativeModel(model_name)

    response = model.generate_content(
        _PROMPT.format(cv_text=cv_text),
        generation_config=GenerationConfig(
            response_mime_type="application/json",
            response_schema=_CV_SCHEMA,
        ),
    )

    return json.loads(response.text)
