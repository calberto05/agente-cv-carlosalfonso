# Anexo — Manejo del historial de conversación

## El problema

Conforme avanza una conversación, el historial inyectado en cada mensaje crece linealmente. Sin un límite, esto produce:

- **Costo creciente:** cada request procesa más tokens de los necesarios
- **Latencia creciente:** el modelo tarda más conforme el contexto es mayor
- **Riesgo de límite de contexto:** aunque Gemini soporta hasta 1M tokens, una conversación sin límite es impredecible en producción

---

## Opciones evaluadas

### Opción A — Sin límite (descartada)
Incluir todo el historial en cada request.

| | |
|---|---|
| **Ventaja** | El agente nunca pierde contexto |
| **Desventaja** | Costo y latencia crecen ilimitadamente. Una conversación larga puede acumular decenas de miles de tokens innecesarios |
| **Veredicto** | Inviable en producción |

---

### Opción B — Sliding window ✅ (elegida)
Conservar solo los últimos N intercambios del historial.

| | |
|---|---|
| **Ventaja** | Costo y latencia acotados. Simple de implementar y explicar |
| **Desventaja** | El agente puede perder contexto de mensajes muy antiguos |
| **Veredicto** | Solución estándar en sistemas conversacionales. Suficiente para un agente de CV donde las preguntas relevantes suelen estar en los últimos turnos |

**Configuración elegida:** últimos **10 mensajes** del historial = **5 intercambios pregunta-respuesta**.

```python
window = messages[:-1][-10:]
```

5 intercambios son suficientes para mantener el hilo de cualquier conversación sobre un CV. El contexto del CV completo ya está en el system prompt, así que el historial solo necesita cubrir el flujo reciente de la conversación.

---

### Opción C — Resumen con LLM (descartada)
Cuando el historial supera un umbral, usar Gemini para resumirlo en un párrafo compacto y sustituir los mensajes antiguos por ese resumen.

| | |
|---|---|
| **Ventaja** | El agente nunca pierde información relevante |
| **Desventaja** | Agrega una llamada LLM adicional por request cuando el historial es largo — latencia y costo extra. Complejidad de implementación significativa |
| **Veredicto** | Justificado en asistentes de soporte de larga duración. Overkill para un agente de CV donde las conversaciones son cortas por naturaleza |

---

### Opción D — Resumen progresivo (descartada)
Mantener un resumen acumulativo que se actualiza con cada turno nuevo.

| | |
|---|---|
| **Ventaja** | Contexto completo comprimido |
| **Desventaja** | Requiere estado del lado del servidor y una llamada LLM adicional por turno |
| **Veredicto** | Demasiada infraestructura para el caso de uso actual |

---

## Decisión final

**Sliding window de 5 intercambios (10 mensajes).**

La justificación técnica es directa: el CV completo ya está en el system prompt, lo que significa que el agente siempre tiene la información base del candidato. El historial solo sirve para mantener el hilo conversacional reciente — 5 intercambios cubren cualquier flujo de preguntas relacionadas sin acumular tokens innecesarios.

Si el caso de uso escalara a conversaciones muy largas o con múltiples sesiones, la Opción C (resumen con LLM) sería el siguiente paso natural.
