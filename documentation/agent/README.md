# Agente Orquestador

## Descripción general

El agente es el núcleo conversacional del sistema. Recibe preguntas sobre el perfil profesional del candidato, las responde usando el JSON generado por el pipeline como contexto, y consulta GitHub en tiempo real cuando el usuario pregunta por proyectos o repositorios específicos.

```
Pregunta del usuario
    └── Agente Orquestador (Google ADK + Gemini)
            ├── Contexto: JSON del CV (cargado al arrancar)
            └── Tools: GitHub API (en tiempo real)
                    ├── list_github_repos
                    ├── get_repo_details
                    └── get_repo_readme
```

---

## Componentes

| Archivo | Responsabilidad |
|---|---|
| `cv_loader.py` | Carga el JSON del CV desde archivo local o Cloud Storage |
| `prompts.py` | Construye el system prompt con el CV y la fecha actual inyectados |
| `tools/github.py` | Tools de GitHub vinculadas al username extraído del CV |
| `agent.py` | Factory que ensambla el Agent de Google ADK |

---

## Decisiones técnicas

### Google ADK como framework
ADK maneja el ciclo de vida de la conversación, el historial de sesión y la orquestación de tool calls. Permite definir tools como funciones Python puras con docstrings, sin boilerplate adicional.

### JSON del CV como contexto en el prompt
El CV completo se inyecta en el system prompt al arrancar el agente. Dado que un CV es pequeño (2-4 páginas ≈ 3,000-6,000 tokens), cabe cómodamente en el contexto de Gemini sin necesidad de búsqueda semántica ni RAG. Esto simplifica la arquitectura y elimina latencia de retrieval.

### Tools de GitHub como closures
Las funciones de GitHub capturan el `username` extraído del campo `github` del JSON del CV. Esto hace al agente genérico: si se procesa el CV de otro candidato con su propio GitHub, las tools apuntan automáticamente al perfil correcto sin cambiar código.

### Separación de datos estáticos y dinámicos
La información del CV (experiencia, educación, habilidades) vive en el JSON — es estática y predecible. Los datos de GitHub (repos, READMEs) se consultan en tiempo real — son dinámicos y cambian frecuentemente. Cada tipo de dato se maneja con la herramienta adecuada.

### Fecha actual en el system prompt
Se inyecta la fecha del día al construir el prompt. Esto permite al agente calcular antigüedad en trabajos, identificar si el candidato sigue activo en alguna actividad, y responder preguntas temporales con precisión.

### Un solo agente (sin Guardian)
Se descartó un agente Guardian separado porque el dato que se protege es público (un CV) y el threat model no lo justifica. La validación de inputs se maneja en la capa de API, y las instrucciones del system prompt delimitan el scope de las respuestas.

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | Sí | ID del proyecto de Google Cloud |
| `GOOGLE_CLOUD_LOCATION` | No | Región de Vertex AI (default: `us-central1`) |
| `GEMINI_MODEL` | No | Modelo de Gemini (default: `gemini-2.5-flash`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Sí | Debe ser `true` para usar Vertex AI con ADC en lugar de API key |
| `CV_JSON_PATH` | Local | Ruta al archivo JSON del CV (desarrollo local) |
| `CV_JSON_BLOB` | Cloud Run | Nombre del blob en Cloud Storage (default: `cv.json`) |
| `OUTPUT_BUCKET` | Cloud Run | Bucket donde vive el JSON del CV |
| `GITHUB_TOKEN` | No | Token de GitHub con scope `public_repo` (evita rate limiting) |
| `GITHUB_USERNAME` | No | Fallback si el CV no tiene URL de GitHub |

---

## Prueba local

### Prerrequisitos

```bash
pip install -r agent/requirements.txt
gcloud auth application-default login
```

### Correr el agente en modo interactivo

```bash
python test_agent.py
```

Preguntas recomendadas para validar el comportamiento:

| Pregunta | Qué valida |
|---|---|
| `"¿Cuál es tu experiencia en Machine Learning?"` | Lectura correcta del JSON |
| `"¿En qué hackathones has participado?"` | Sección custom del CV |
| `"¿Sigues estudiando?"` | Uso correcto de la fecha actual |
| `"¿Qué proyectos tienes en GitHub?"` | Llamada a `list_github_repos` |
| `"Cuéntame sobre el proyecto X"` | Llamada a `get_repo_readme` |
| `"¿Cuál es la capital de Francia?"` | Rechazo de preguntas fuera de scope |

---

## Modificar el comportamiento del agente

El tono, idioma y restricciones del agente se controlan en `agent/prompts.py` dentro de `_TEMPLATE`. Es texto puro — no requiere cambios de lógica. Ver [Anexo A](anexos/system_prompt.md) para una guía de personalización.

Las tools disponibles y su comportamiento se documentan en [Anexo B](anexos/tools_github.md).

---

## Dependencias

Ver [`agent/requirements.txt`](../../agent/requirements.txt).
