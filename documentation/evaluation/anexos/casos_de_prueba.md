# Anexo — Casos de prueba

## Estructura de un caso

```python
@dataclass
class TestCase:
    name: str             # identificador único
    category: str         # precision | fechas | scope | tools | coherencia | idioma
    messages: list[str]   # uno o más turnos de conversación
    criteria: list[str]   # condiciones que debe cumplir la respuesta
    expected_behavior: str  # descripción en lenguaje natural del comportamiento esperado
```

Los criterios son evaluados por el LLM-as-judge. Deben ser específicos y observables — el juez determina si la respuesta del agente los cumple con `true`/`false`.

---

## Categoría: `precision`

Verifica que el agente responde con información correcta y concreta extraída del CV.

---

### `hackathones_mencionados`

**Pregunta:** `"¿En qué hackathones has participado?"`

| Criterio |
|---|
| Menciona el Hackathon Banorte 2024 o un hackathon de Banorte |
| Menciona el Google Hackathon ADK o un hackathon de Google |

**Comportamiento esperado:** El agente lista los hackathones del CV con sus detalles relevantes.

---

### `experiencia_ml`

**Pregunta:** `"¿Cuál es tu experiencia en Machine Learning?"`

| Criterio |
|---|
| Menciona experiencia con LLMs o modelos de lenguaje |
| Menciona algún dominio de aplicación (finanzas, e-commerce, u otro) |
| La respuesta es concreta y basada en experiencia real, no genérica |

**Comportamiento esperado:** El agente describe experiencia real en ML extraída del CV.

---

### `plataformas_cloud`

**Pregunta:** `"¿Con qué plataformas cloud has trabajado?"`

| Criterio |
|---|
| Menciona Google Cloud Platform o GCP |
| Menciona Azure o Microsoft Azure |
| Menciona AWS o Amazon Web Services |

**Comportamiento esperado:** El agente menciona las tres plataformas cloud del CV.

---

### `educacion`

**Pregunta:** `"¿Dónde estudiaste o qué estudias?"`

| Criterio |
|---|
| Menciona la institución educativa |
| Menciona la carrera o área de estudio |
| La respuesta es coherente con el perfil de Data Scientist |

**Comportamiento esperado:** El agente responde con la información educativa del CV.

---

## Categoría: `fechas`

Verifica que el agente razona correctamente sobre el tiempo: conoce la fecha actual (inyectada en el system prompt) y la usa para determinar la vigencia de estudios y experiencia laboral. Los criterios de `fecha_actual` se generan dinámicamente a partir de `date.today()` en `test_cases.py`, por lo que siempre reflejan la fecha real del día en que se ejecuta la evaluación.

---

### `fecha_actual`

**Pregunta:** `"¿Qué día es hoy?"`

| Criterio |
|---|
| Menciona el día correcto |
| Menciona el mes correcto |
| Menciona el año correcto |

**Comportamiento esperado:** El agente conoce y responde correctamente la fecha actual, ya que se le inyecta en el system prompt (`agent/prompts.py`).

---

### `estado_estudios`

**Pregunta:** `"¿Sigues estudiando actualmente o ya terminaste tus estudios?"`

| Criterio |
|---|
| Indica claramente que ya no está estudiando o que ya terminó sus estudios |
| No afirma que actualmente sigue estudiando |
| La respuesta es coherente con el `end_date` de la sección `education` del perfil comparada con la fecha de hoy |

**Comportamiento esperado:** El agente compara la fecha de fin de estudios del CV con la fecha actual y concluye correctamente que ya no está estudiando.

---

### `estado_laboral_actual`

**Pregunta:** `"¿Trabajas actualmente en alguna empresa?"`

| Criterio |
|---|
| Responde de forma coherente con el `end_date` de la experiencia más reciente (por ejemplo, si es "Presente" confirma que sigue trabajando ahí) |
| No contradice las fechas registradas en la sección `experience` del perfil |
| La respuesta es concreta, no evasiva ni genérica |

**Comportamiento esperado:** El agente determina correctamente su situación laboral actual comparando las fechas de `experience` con la fecha de hoy.

---

## Categoría: `scope`

Verifica que el agente rechaza preguntas fuera de su ámbito de forma amable y redirige la conversación.

---

### `pregunta_fuera_de_scope`

**Pregunta:** `"¿Cuál es la capital de Francia?"`

| Criterio |
|---|
| No responde la pregunta directamente |
| Redirige la conversación hacia el perfil profesional |
| El tono es amable, no brusco |

**Comportamiento esperado:** El agente rechaza educadamente preguntas no relacionadas con el perfil.

---

### `solicitud_no_profesional`

**Pregunta:** `"¿Puedes escribirme un poema?"`

| Criterio |
|---|
| No escribe el poema |
| Explica que su función es responder sobre el perfil profesional |
| Ofrece continuar con preguntas sobre el candidato |

**Comportamiento esperado:** El agente declina y redirige amablemente.

---

## Categoría: `tools`

Verifica que el agente usa las tools de GitHub cuando el usuario pregunta por proyectos o repositorios.

---

### `lista_repos_github`

**Pregunta:** `"¿Qué proyectos tienes en GitHub?"`

| Criterio |
|---|
| Lista al menos un repositorio real con nombre |
| La información parece provenir de GitHub (no solo del CV) |
| Menciona el lenguaje o descripción de algún repo |

**Comportamiento esperado:** El agente llama la tool de GitHub y lista repositorios reales.

---

### `detalle_proyecto_github`

**Pregunta:** `"¿Puedes contarme más sobre alguno de tus proyectos en GitHub?"`

| Criterio |
|---|
| Da detalles específicos de al menos un proyecto |
| Los detalles son concretos (tecnología, descripción, propósito) |
| La información parece actualizada y real |

**Comportamiento esperado:** El agente usa las tools de GitHub para dar información detallada.

---

## Categoría: `coherencia`

Verifica que el agente mantiene el contexto entre turnos de una conversación. Estos casos tienen dos mensajes: el agente debe recordar lo discutido en el primero al responder el segundo.

---

### `memoria_multi_turno`

**Turno 1:** `"¿En qué hackathones has participado?"`
**Turno 2:** `"¿Y en cuál de ellos ganaste?"`

| Criterio |
|---|
| Responde sobre el hackathon ganador sin que el usuario lo haya mencionado de nuevo |
| No repite la lista completa de hackathones innecesariamente |
| La respuesta tiene coherencia con el turno anterior |

**Comportamiento esperado:** El agente recuerda los hackathones del turno anterior y responde específicamente sobre el ganador.

---

### `seguimiento_de_tema`

**Turno 1:** `"¿Cuáles son tus habilidades en cloud?"`
**Turno 2:** `"¿Y cuál de esas plataformas dominas más?"`

| Criterio |
|---|
| El segundo turno es coherente con el primero |
| No trata el segundo mensaje como una pregunta aislada |
| Responde sobre cloud sin que el usuario repita el tema |

**Comportamiento esperado:** El agente mantiene el contexto de la conversación entre turnos.

---

## Categoría: `idioma`

Verifica que el agente responde en español independientemente del idioma de la pregunta.

---

### `respuesta_en_espanol`

**Pregunta (en inglés):** `"Tell me about your professional experience"`

| Criterio |
|---|
| La respuesta está escrita en español |
| El contenido es relevante a la experiencia profesional |

**Comportamiento esperado:** El agente responde en español aunque la pregunta sea en inglés.

---

## Criterios de diseño para nuevos casos

Al agregar casos de prueba, seguir estas guías:

1. **Criterios observables** — "Menciona GCP" es observable. "Es una respuesta completa" no lo es.
2. **Un criterio por condición** — No mezclar dos condiciones en un criterio.
3. **Criterios independientes** — El juez los evalúa por separado. No deben implicarse entre sí.
4. **Casos multi-turno solo para coherencia** — Los demás casos usan un solo turno para aislar la variable que se mide.
