# Anexo A — System Prompt

## Estructura del prompt

El system prompt se construye dinámicamente en `agent/prompts.py` cada vez que el agente arranca. Tiene tres partes:

```
1. Fecha actual          → permite razonamiento temporal
2. Rol y comportamiento  → define cómo debe actuar el agente
3. JSON del CV           → única fuente de verdad sobre el candidato
```

---

## Variables inyectadas

| Variable | Origen | Descripción |
|---|---|---|
| `{today}` | `datetime.date.today()` | Fecha actual en formato legible |
| `{name}` | `cv_data["personal_info"]["name"]` | Nombre del candidato |
| `{cv_json}` | JSON completo del CV | Toda la información del candidato |

---

## Cómo personalizar el comportamiento

### Cambiar el idioma
En `_TEMPLATE`, modifica la línea:
```
- Responde siempre en español.
```
Por ejemplo, para responder en el idioma del usuario:
```
- Detecta el idioma del usuario y responde en el mismo idioma (español o inglés).
```

### Cambiar el tono
Modifica la instrucción de tono:
```
- Mantén un tono profesional pero cercano.
```
Opciones: `formal`, `técnico`, `amigable`, etc.

### Agregar restricciones específicas
Añade instrucciones al bloque `## Comportamiento`. Ejemplo:
```
- No reveles el número de teléfono ni el correo del candidato directamente; 
  indica que pueden contactarlo a través de LinkedIn.
```

### Cambiar el idioma del prompt base
El prompt está escrito en español. Si el agente necesita responder en inglés por defecto, reescribe `_TEMPLATE` en inglés.

---

## Consideraciones

- El JSON del CV se incluye completo en el prompt. Para un CV típico esto representa entre 3,000 y 6,000 tokens adicionales por sesión — costo marginal con modelos modernos.
- El prompt se construye una vez al arrancar el agente (`create_agent()`), no en cada mensaje. Si el CV se actualiza, el agente debe reiniciarse para reflejar los cambios.
