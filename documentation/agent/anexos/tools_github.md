# Anexo B — Tools de GitHub

## Descripción general

Las tools de GitHub permiten al agente consultar información actualizada del perfil de GitHub del candidato en tiempo real. Se definen en `agent/tools/github.py` como funciones Python que Google ADK convierte automáticamente en herramientas disponibles para el modelo.

El username se extrae del campo `personal_info.github` del JSON del CV (parseando la URL). Si ese campo está vacío, cae al valor de la variable de entorno `GITHUB_USERNAME`.

---

## Tools disponibles

### `list_github_repos`

Lista los repositorios públicos del candidato, ordenados por actividad reciente. Excluye forks.

**Cuándo la usa el agente:** cuando el usuario pregunta por proyectos, portafolio o trabajo en GitHub en general.

**Respuesta:**
```json
{
  "repos": [
    {
      "name": "nombre-del-repo",
      "description": "Descripción del repositorio",
      "language": "Python",
      "stars": 5,
      "url": "https://github.com/usuario/repo",
      "updated_at": "2025-08-01T12:00:00Z"
    }
  ]
}
```

**En caso de error:**
```json
{ "error": "Tiempo de espera agotado al consultar GitHub. Intenta de nuevo." }
```

---

### `get_repo_details`

Obtiene los detalles de un repositorio específico.

**Parámetro:** `repo_name` — nombre exacto del repositorio.

**Cuándo la usa el agente:** cuando el usuario pregunta por un proyecto en particular y necesita contexto adicional (lenguaje, topics, actividad).

**Respuesta:**
```json
{
  "name": "nombre-del-repo",
  "description": "Descripción",
  "language": "Python",
  "stars": 5,
  "forks": 1,
  "topics": ["machine-learning", "fastapi"],
  "url": "https://github.com/usuario/repo",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2025-08-01T12:00:00Z"
}
```

**En caso de repo inexistente:**
```json
{ "error": "El repositorio 'nombre' no existe o es privado." }
```

---

### `get_repo_readme`

Lee el contenido del README de un repositorio específico.

**Parámetro:** `repo_name` — nombre exacto del repositorio.

**Cuándo la usa el agente:** cuando el usuario quiere entender qué hace un proyecto en detalle — tecnologías usadas, arquitectura, instrucciones.

**Respuesta:** texto plano del README en Markdown.

**En caso de README inexistente:** `"Este repositorio no tiene README."`

---

## Manejo de errores

Todas las tools capturan tres tipos de error y devuelven mensajes legibles en lugar de lanzar excepciones:

| Error | Causa | Mensaje |
|---|---|---|
| `TimeoutException` | Red lenta o sin respuesta | `"Tiempo de espera agotado..."` |
| `HTTPStatusError` | Error HTTP (403, 404, 500) | `"Error al consultar GitHub: {código}"` |
| `HTTPError` | Error de red general | `"Error de red: {detalle}"` |

Esto evita que un fallo de red rompa la conversación — el agente recibe el mensaje de error y puede responderle al usuario que hubo un problema de conexión.

---

## Agregar una nueva tool

1. Define una nueva función dentro de `make_github_tools()` en `agent/tools/github.py`
2. Agrega un docstring claro — ADK lo usa para decidir cuándo llamar la tool
3. Inclúyela en el `return` al final de `make_github_tools()`

Ejemplo mínimo:
```python
def get_repo_languages(repo_name: str) -> dict:
    """
    Obtiene los lenguajes de programación usados en un repositorio.
    Úsala cuando el usuario pregunte por el stack tecnológico de un proyecto.

    Args:
        repo_name: Nombre exacto del repositorio.
    """
    try:
        response = httpx.get(
            f"{_GITHUB_API}/repos/{username}/{repo_name}/languages",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        return {"error": "Tiempo de espera agotado."}
    except httpx.HTTPError as e:
        return {"error": str(e)}
```
