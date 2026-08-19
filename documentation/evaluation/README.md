# Framework de Evaluación

## Descripción general

El framework de evaluación mide de forma automática si el agente se comporta correctamente ante preguntas reales. Usa el patrón **LLM-as-judge**: el mismo modelo que alimenta al agente (Gemini) evalúa sus respuestas contra criterios predefinidos y devuelve una puntuación estructurada.

```
python -m evaluation.main
    └── runner.py — llama al endpoint de Cloud Run
            └── Agente en producción → respuesta
    └── judge.py — evalúa con Gemini (structured output)
            └── JSON: criterios cumplidos + score 1-5 + resumen
    └── main.py — genera reporte en terminal
```

---

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `test_cases.py` | Catálogo de casos de prueba (preguntas + criterios esperados) |
| `runner.py` | Cliente HTTP que ejecuta los casos contra el endpoint real |
| `judge.py` | LLM-as-judge: evalúa respuestas con Gemini + `response_schema` |
| `main.py` | Punto de entrada, orquestación y reporte en terminal |
| `requirements.txt` | Dependencias del framework |

---

## Categorías de prueba

| Categoría | Qué mide | Casos |
|---|---|---|
| `precision` | El agente responde con información correcta del CV | 4 |
| `fechas` | El agente razona correctamente sobre la fecha actual y la vigencia de estudios/experiencia | 3 |
| `scope` | El agente rechaza preguntas fuera de su ámbito | 2 |
| `tools` | El agente usa la tool de GitHub cuando corresponde | 2 |
| `coherencia` | El agente mantiene contexto en conversaciones multi-turno | 2 |
| `idioma` | El agente responde en español aunque la pregunta sea en inglés | 1 |

Ver detalle de cada caso en [Anexo — Casos de prueba](anexos/casos_de_prueba.md).

---

## Uso

### Instalación

```bash
pip install -r evaluation/requirements.txt
```

### Ejecutar todos los casos

```bash
python -m evaluation.main
```

### Filtrar por categoría

```bash
python -m evaluation.main --category precision
python -m evaluation.main --category tools
```

### Ejecutar un caso específico

```bash
python -m evaluation.main --test hackathones_mencionados
```

### Ver detalle completo de cada caso

```bash
python -m evaluation.main --detail
python -m evaluation.main --category coherencia --detail
```

---

## Interpretación del reporte

```
  Tests ejecutados : 11
  Pasados          : 9
  Fallidos         : 2
  Score promedio   : 4.1/5
```

Un caso se considera **PASS** si `overall_score >= 3` (el juez determinó que la mayoría de los criterios fueron cumplidos). El umbral se puede ajustar en `main.py:PASS_THRESHOLD`.

El proceso devuelve **exit code 1** si algún test falla, lo que permite integrarlo en pipelines de CI/CD.

---

## Decisiones técnicas

### LLM-as-judge con structured output

En lugar de heurísticas frágiles (búsqueda de palabras clave, regex), un LLM evalúa la respuesta en lenguaje natural. Gemini recibe la conversación completa, el comportamiento esperado y la lista de criterios, y devuelve un JSON con `passed`/`reasoning` por criterio y un `overall_score` numérico.

El uso de `response_schema` garantiza que el JSON siempre es parseable, sin necesidad de post-procesar texto libre. Ver análisis completo en [Anexo — LLM-as-judge](anexos/llm_as_judge.md).

### Evaluación contra el endpoint real

El runner llama directamente al endpoint de Cloud Run en producción. Esto mide el sistema completo: prompt, tools, serialización y respuesta HTTP. No hay mocks ni stubs — si el agente falla en producción, el test falla.

### Soporte multi-turno nativo

Los casos de `coherencia` contienen múltiples mensajes. El runner construye el array `input` acumulando el historial turno a turno, replicando exactamente el formato que usa la plataforma de Banorte. Si el agente pierde contexto entre turnos, el juez lo detecta.

### Temperature 0 en el juez

El juez usa `temperature=0.0` para que evaluaciones repetidas del mismo caso produzcan resultados idénticos. La variabilidad viene del agente, no del evaluador.

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `AGENT_ENDPOINT` | No | URL del endpoint (default: URL de Cloud Run en producción) |
| `AGENT_API_KEY` | Sí | API key del agente (Bearer token) |
| `GOOGLE_CLOUD_PROJECT` | Sí | ID del proyecto para Vertex AI |
| `GOOGLE_CLOUD_LOCATION` | No | Región (default: `us-central1`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Sí | `true` para usar ADC en lugar de API key |
| `GEMINI_MODEL` | No | Modelo del juez (default: `gemini-2.5-flash`) |

---

## Dependencias

Ver [`evaluation/requirements.txt`](../../evaluation/requirements.txt).
