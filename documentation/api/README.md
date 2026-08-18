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

## Logging

El endpoint loguea en Cloud Logging:
- `Authorization header recibido: ...` — para auditar la API key que llega
- `Payload recibido: ...` — el body completo de cada request

Para ver los logs en tiempo real:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cv-agent" \
  --limit=50 --format="value(textPayload)" --project=banortepruebatecninca
```
