# API — Endpoint Open Responses

## Descripción general

El endpoint expone el agente como un servicio HTTP compatible con la **OpenAI Responses API**. Está desplegado en Cloud Run y es el punto de entrada que registra la plataforma de Banorte.

```
Cliente (Banorte)
    └── POST /responses
            └── FastAPI (api/main.py)
                    ├── Validación de API key
                    ├── Extracción y reconstrucción del mensaje
                    └── Google ADK Runner → respuesta
```

---

## Endpoints

### `POST /responses` y `POST /`

Ambas rutas apuntan al mismo handler. `/responses` es la convención de la OpenAI Responses API que usa la plataforma de Banorte; `/` se mantiene para compatibilidad general.

**Headers requeridos:**
```
Authorization: Bearer <AGENT_API_KEY>
Content-Type: application/json
```

**Formato del payload (OpenAI Responses API):**
```json
{
  "model": "gemini-2.5-flash",
  "input": [
    {
      "role": "user",
      "type": "message",
      "content": [
        { "type": "input_text", "text": "¿Cuál es tu experiencia en ML?" }
      ]
    }
  ],
  "instructions": "...",
  "stream": false,
  "store": false
}
```

El campo `input` también acepta string simple:
```json
{ "input": "¿Cuál es tu experiencia en ML?" }
```

**Response:**
```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1724000000,
  "status": "completed",
  "model": "gemini-2.5-flash",
  "output": [
    {
      "type": "message",
      "id": "msg_abc123",
      "role": "assistant",
      "status": "completed",
      "content": [{ "type": "output_text", "text": "..." }]
    }
  ],
  "session_id": "uuid-de-la-sesion"
}
```

### `GET /health`

Verificación de salud del servicio. No requiere autenticación.

```json
{ "status": "ok" }
```

---

## Manejo del historial de conversación

### El problema

La plataforma de Banorte no reenvía el `session_id` entre turnos de conversación. Cada request llega como una nueva sesión sin contexto previo.

### La solución

La plataforma sí manda el **historial completo** de la conversación en el campo `input` como array de mensajes. El endpoint aprovecha esto:

1. Extrae todos los mensajes del array (usuario y asistente)
2. Construye un bloque de contexto con el historial previo
3. Lo inyecta en el mensaje actual antes de enviarlo al agente

**Ejemplo de lo que construye internamente:**
```
[Historial de conversación]
Usuario: ¿Qué proyectos tienes en GitHub?
Asistente: Carlos tiene los siguientes proyectos...

[Pregunta actual]
¿Y cuál es el más reciente?
```

Esto permite que el agente tenga plena consciencia del contexto de la conversación aunque cada request sea técnicamente una sesión nueva.

---

## Validación de inputs

| Validación | Detalle |
|---|---|
| API key | `Authorization: Bearer <key>` debe coincidir con `AGENT_API_KEY` |
| Campo `input` | Requerido. Acepta string, array de mensajes, o array con content blocks |
| Longitud del mensaje | El **último mensaje del usuario** no puede superar 2000 caracteres. El límite aplica al mensaje original, no al historial completo inyectado |

---

## Evolución del endpoint

### Cambios realizados durante la integración con Banorte

**1. Ruta `/responses`**
La plataforma de Banorte llama a `POST /responses` (convención OpenAI). Se añadió como alias de `POST /`.

**2. Schema flexible (raw JSON)**
El Pydantic model original era demasiado estricto. Se reemplazó por lectura del body raw + extracción manual, para aceptar cualquier variación del payload de la plataforma.

**3. `status: "completed"`**
La plataforma rechazaba la respuesta con "respuesta no terminal". Se añadió `status: "completed"` tanto al objeto raíz como al mensaje de output.

**4. Historial de conversación**
Las sesiones en memoria no funcionan entre requests de la plataforma porque no reenvía el `session_id`. Se resolvió inyectando el historial del `input` array como contexto en cada mensaje.

**5. Validación de longitud**
El límite de 2000 caracteres se aplicaba al mensaje ya con el historial inyectado, fallando en conversaciones largas. Se corrigió para validar solo el último mensaje original del usuario.

---

## Control del historial (sliding window)

Para evitar que el historial inyectado crezca ilimitadamente, se conservan solo los **últimos 10 mensajes** del historial (5 intercambios pregunta-respuesta). Mensajes más antiguos se descartan.

Ver análisis completo de opciones en [Anexo — Manejo del historial](anexos/manejo_historial.md).

---

## Limitaciones conocidas

### Sin rate limiting propio

La única protección del endpoint es el `AGENT_API_KEY` estático validado en cada request (`_validate_api_key`). No hay throttling por IP, por key ni por sesión.

| | |
|---|---|
| **Riesgo** | Una API key filtrada (o adivinada por fuerza bruta, dado que es una sola cadena estática sin rotación) permite volumen ilimitado de requests — impacto directo en costo de Gemini y en el rate limit de la API de GitHub |
| **Por qué no se implementó** | El dato protegido es público (un CV) y el único consumidor esperado es la plataforma de Banorte con un solo key. El riesgo real es de **costo/abuso**, no de fuga de datos sensibles |
| **Siguiente paso si escala** | Cloud Armor (rate limiting a nivel de Cloud Run/Load Balancer), o un middleware en FastAPI (p. ej. `slowapi`) con límite por IP o por API key. Alternativamente, restringir el servicio a las IPs conocidas de Banorte |

### Sesión en memoria, no compartida entre instancias

`InMemorySessionService` (ver `api/main.py:lifespan`) guarda el estado de sesión de ADK únicamente en la memoria del proceso de **una** instancia de Cloud Run. Cloud Run puede correr varias instancias en paralelo y reemplazarlas (nuevas revisiones, scale-to-zero, reinicios) sin avisar.

**Por qué no rompe la conversación de todos modos:** la continuidad multi-turno **no depende** de esta sesión interna. Como se explica en [Manejo del historial](#manejo-del-historial-de-conversación), el historial completo se reconstruye en cada request a partir del array `input` que reenvía el cliente. Si un `session_id` aterriza en una instancia distinta (sesión ADK vacía ahí), el mensaje que recibe el agente ya trae el contexto completo inyectado como texto — la sesión de ADK actúa más como un contenedor técnico que exige el `Runner`, no como la fuente de verdad de la memoria conversacional.

| Limitación | Detalle |
|---|---|
| Sin persistencia entre instancias/reinicios | Esperado y mitigado por el diseño (historial del lado del cliente) |
| Sin eviction/TTL de sesiones | El diccionario interno de `InMemorySessionService` crece con cada `session_id` nuevo y nunca se libera dentro del ciclo de vida de una instancia — a la escala de este proyecto es despreciable, pero sería un memory leak real bajo tráfico alto y sostenido |
| Siguiente paso si se requiere persistencia real | `DatabaseSessionService` o `VertexAiSessionService` de ADK, respaldados por Firestore/Cloud SQL, en vez de la variante en memoria |

---

## Logging

El endpoint loguea en Cloud Logging:
- `Authorization header presente: true/false` — para auditar si llegó el header, **sin loguear el valor** (evita exponer el API key en los logs)
- `Payload recibido: ...` — el body completo de cada request

Para ver los logs en tiempo real:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cv-agent" \
  --limit=50 --format="value(textPayload)" --project=banortepruebatecninca
```
