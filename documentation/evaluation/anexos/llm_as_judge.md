# Anexo — LLM-as-judge

## El problema de evaluar agentes conversacionales

Las respuestas de un LLM no tienen una "respuesta correcta" única. La misma información puede expresarse de formas muy distintas, y comparar strings o buscar palabras clave produce falsos negativos en cuanto el agente parafrasea o cambia el orden de los elementos.

Ejemplos del problema con heurísticas:

```python
# El test busca "Banorte" en la respuesta
"Gané el hackathon organizado por Banorte" → pasa
"Fui ganador del evento tech de Banorte 2024" → pasa
"Obtuve el primer lugar en el Hackathon Banorte" → pasa
"Participé en el Banorte Hack y lo gané" → pasa — pero ¿cómo lo detectas?
"Me lo adjudicaron en la competencia de Banorte" → falla con regex

# El test busca que no responda preguntas fuera de scope
"No puedo responder eso" → pasa
"Mi función es hablar sobre mi perfil" → pasa
"¡Vaya pregunta! Hablemos mejor de mi experiencia..." → pasa — ¿cómo lo detectas?
```

---

## La solución: LLM-as-judge

Un LLM evalúa la respuesta del agente en lenguaje natural, del mismo modo en que lo haría un evaluador humano. Recibe:

1. La conversación completa (preguntas del usuario + respuestas del agente)
2. El comportamiento esperado
3. La lista de criterios a evaluar

Y devuelve una evaluación estructurada con `passed`/`reasoning` por criterio y un `overall_score` numérico.

---

## Por qué `response_schema` es crítico

Sin schema, el LLM devuelve texto libre que hay que parsear con regex o `json.loads` envuelto en try/except. Con schema, el modelo garantiza que el output es JSON válido y con la estructura exacta esperada.

```python
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
            },
        },
        "overall_score": {"type": "integer"},
        "summary": {"type": "string"},
    },
}
```

Esto hace que `json.loads(response.text)` nunca falle — el modelo no puede devolver JSON malformado con `response_mime_type="application/json"` y un schema activo.

---

## Por qué `temperature=0`

El juez usa `temperature=0.0` para garantizar que evaluaciones repetidas del mismo caso produzcan resultados idénticos. Si el juez tuviera temperatura alta, podrías ver el mismo caso pasar en una ejecución y fallar en la siguiente — no porque el agente cambiara, sino porque el juez varió su interpretación.

La variabilidad legítima viene del agente (que sí tiene temperatura > 0). El juez debe ser estable.

---

## Opciones evaluadas

### Opción A — Heurísticas (regex / búsqueda de keywords)

| | |
|---|---|
| **Ventaja** | Sin costo de LLM, determinista, instantáneo |
| **Desventaja** | Frágil ante paráfrasis. Requiere mantenimiento constante cuando el agente cambia su estilo |
| **Veredicto** | Solo viable para criterios binarios muy simples ("responde en español") |

---

### Opción B — Embeddings + similaridad semántica

Generar embeddings de la respuesta esperada y la real, y comparar por coseno.

| | |
|---|---|
| **Ventaja** | Más robusto que regex ante paráfrasis |
| **Desventaja** | Solo mide si la respuesta es semánticamente similar a un texto de referencia, no si cumple criterios de comportamiento (ej: "no responde la pregunta directamente") |
| **Veredicto** | Bueno para Q&A factual, insuficiente para criterios de comportamiento como scope o coherencia |

---

### Opción C — LLM-as-judge ✅ (elegida)

| | |
|---|---|
| **Ventaja** | Evalúa comportamiento en lenguaje natural. Funciona igual ante cualquier paráfrasis. Genera razonamiento legible por humanos. Escala a cualquier tipo de criterio |
| **Desventaja** | Costo adicional de tokens por evaluación. El juez puede tener sesgos propios. Latencia extra |
| **Veredicto** | Estándar de la industria para evaluar agentes conversacionales. Los sesgos se mitigan con temperature=0 y criterios específicos |

---

## Sesgos conocidos del LLM-as-judge

### Sesgo de verbosidad
Los LLM tienden a puntuar mejor respuestas más largas, asumiendo que más texto = más completo. Se mitiga con criterios de evaluación específicos y medibles en lugar de "¿qué tan buena es la respuesta?"

### Sesgo de autopreferencia
Gemini evaluando respuestas de Gemini puede ser más benévolo que un juez externo. Es un sesgo conocido y aceptado en este contexto: el objetivo es detectar regresiones, no establecer una métrica absoluta.

### Juez ≠ usuario
Un LLM puede considerar que un criterio se cumple aunque un usuario real no quede satisfecho. Por eso el framework complementa (no reemplaza) pruebas manuales en la plataforma de Banorte.

### Desconocimiento de la fecha real
El conocimiento de Gemini termina en su fecha de entrenamiento, así que sin ayuda el juez no sabe qué día es "hoy" en el momento de la evaluación. Esto generaba falsos negativos en la categoría `fechas`: el agente respondía correctamente la fecha actual, pero el juez la marcaba como incorrecta por no coincidir con su propia noción de "hoy". Se corrigió inyectando la fecha real (`date.today()`) en el system prompt del juez (`judge.py:_SYSTEM_PROMPT_TEMPLATE`), igual que ya se hacía en el prompt del agente (`agent/prompts.py`).

---

## Flujo completo de una evaluación

```
1. runner.py  — Construye el input array con el historial de turnos
2. runner.py  — POST /responses → Cloud Run → Agente → respuesta
3. judge.py   — Construye el prompt: conversación + criterios
4. judge.py   — Gemini (temperature=0, response_schema) → JSON
5. main.py    — Parsea JSON → TestResult.passed (score >= 3)
6. main.py    — Imprime tabla con rich + exit code
```

---

## Criterio de aprobación

Un test se considera **PASS** si `overall_score >= 3` de 5, lo que equivale a que la mayoría de los criterios fueron cumplidos. La escala completa:

| Score | Significado |
|---|---|
| 5 | Todos los criterios cumplidos |
| 4 | La mayoría cumplidos (uno fallido) |
| 3 | Mitad cumplidos — umbral mínimo de PASS |
| 2 | Minoría cumplidos |
| 1 | Ningún criterio cumplido |
