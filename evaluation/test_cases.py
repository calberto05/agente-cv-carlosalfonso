from dataclasses import dataclass, field
from datetime import date


@dataclass
class TestCase:
    name: str
    category: str
    messages: list[str]
    criteria: list[str]
    expected_behavior: str


_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_hoy = date.today()
_FECHA_HOY = f"{_hoy.day} de {_MESES_ES[_hoy.month - 1]} de {_hoy.year}"


TEST_CASES: list[TestCase] = [

    # ------------------------------------------------------------------ #
    # PRECISIÓN — el agente responde con información correcta del CV
    # ------------------------------------------------------------------ #
    TestCase(
        name="hackathones_mencionados",
        category="precision",
        messages=["¿En qué hackathones has participado?"],
        criteria=[
            "Menciona el Hackathon Banorte 2024 o un hackathon de Banorte",
            "Menciona el Google Hackathon ADK o un hackathon de Google",
        ],
        expected_behavior="El agente debe listar los hackathones del CV con sus detalles relevantes.",
    ),
    TestCase(
        name="experiencia_ml",
        category="precision",
        messages=["¿Cuál es tu experiencia en Machine Learning?"],
        criteria=[
            "Menciona experiencia con LLMs o modelos de lenguaje",
            "Menciona algún dominio de aplicación (finanzas, e-commerce, u otro)",
            "La respuesta es concreta y basada en experiencia real, no genérica",
        ],
        expected_behavior="El agente debe describir experiencia real en ML extraída del CV.",
    ),
    TestCase(
        name="plataformas_cloud",
        category="precision",
        messages=["¿Con qué plataformas cloud has trabajado?"],
        criteria=[
            "Menciona Google Cloud Platform o GCP",
            "Menciona Azure o Microsoft Azure",
            "Menciona AWS o Amazon Web Services",
        ],
        expected_behavior="El agente debe mencionar las tres plataformas cloud del CV.",
    ),
    TestCase(
        name="educacion",
        category="precision",
        messages=["¿Dónde estudiaste o qué estudias?"],
        criteria=[
            "Menciona la institución educativa",
            "Menciona la carrera o área de estudio",
            "La respuesta es coherente con el perfil de Data Scientist",
        ],
        expected_behavior="El agente debe responder con la información educativa del CV.",
    ),

    # ------------------------------------------------------------------ #
    # FECHAS — el agente razona correctamente sobre tiempo y vigencia
    # ------------------------------------------------------------------ #
    TestCase(
        name="fecha_actual",
        category="fechas",
        messages=["¿Qué día es hoy?"],
        criteria=[
            f"Menciona el día correcto ({_hoy.day})",
            f"Menciona el mes correcto ({_MESES_ES[_hoy.month - 1]})",
            f"Menciona el año correcto ({_hoy.year})",
        ],
        expected_behavior=(
            f"El agente debe conocer y responder correctamente la fecha actual "
            f"({_FECHA_HOY}), ya que se le inyecta en el system prompt."
        ),
    ),
    TestCase(
        name="estado_estudios",
        category="fechas",
        messages=["¿Sigues estudiando actualmente o ya terminaste tus estudios?"],
        criteria=[
            "Indica claramente que ya no está estudiando o que ya terminó sus estudios",
            "No afirma que actualmente sigue estudiando",
            "La respuesta es coherente con la fecha de fin de estudios (end_date) de la sección education del perfil comparada con la fecha de hoy",
        ],
        expected_behavior=(
            "El agente debe comparar la fecha de fin de estudios del CV con la "
            "fecha actual y concluir correctamente que ya no está estudiando."
        ),
    ),
    TestCase(
        name="estado_laboral_actual",
        category="fechas",
        messages=["¿Trabajas actualmente en alguna empresa?"],
        criteria=[
            "Responde de forma coherente con el end_date de la experiencia más reciente del perfil (por ejemplo, si es 'Presente' confirma que sigue trabajando ahí)",
            "No contradice las fechas registradas en la sección experience del perfil",
            "La respuesta es concreta, no evasiva ni genérica",
        ],
        expected_behavior=(
            "El agente debe determinar correctamente su situación laboral actual "
            "comparando las fechas de la sección experience con la fecha de hoy."
        ),
    ),

    # ------------------------------------------------------------------ #
    # SCOPE — el agente rechaza preguntas fuera de su ámbito
    # ------------------------------------------------------------------ #
    TestCase(
        name="pregunta_fuera_de_scope",
        category="scope",
        messages=["¿Cuál es la capital de Francia?"],
        criteria=[
            "No responde la pregunta directamente",
            "Redirige la conversación hacia el perfil profesional",
            "El tono es amable, no brusco",
        ],
        expected_behavior="El agente debe rechazar educadamente preguntas no relacionadas con el perfil.",
    ),
    TestCase(
        name="solicitud_no_profesional",
        category="scope",
        messages=["¿Puedes escribirme un poema?"],
        criteria=[
            "No escribe el poema",
            "Explica que su función es responder sobre el perfil profesional",
            "Ofrece continuar con preguntas sobre el candidato",
        ],
        expected_behavior="El agente debe declinar y redirigir amablemente.",
    ),

    # ------------------------------------------------------------------ #
    # TOOLS — el agente usa GitHub cuando corresponde
    # ------------------------------------------------------------------ #
    TestCase(
        name="lista_repos_github",
        category="tools",
        messages=["¿Qué proyectos tienes en GitHub?"],
        criteria=[
            "Lista al menos un repositorio real con nombre",
            "La información parece provenir de GitHub (no solo del CV)",
            "Menciona el lenguaje o descripción de algún repo",
        ],
        expected_behavior="El agente debe llamar la tool de GitHub y listar repositorios reales.",
    ),
    TestCase(
        name="detalle_proyecto_github",
        category="tools",
        messages=["¿Puedes contarme más sobre alguno de tus proyectos en GitHub?"],
        criteria=[
            "Da detalles específicos de al menos un proyecto",
            "Los detalles son concretos (tecnología, descripción, propósito)",
            "La información parece actualizada y real",
        ],
        expected_behavior="El agente debe usar las tools de GitHub para dar información detallada.",
    ),

    # ------------------------------------------------------------------ #
    # COHERENCIA — el agente mantiene contexto en conversaciones multi-turno
    # ------------------------------------------------------------------ #
    TestCase(
        name="memoria_multi_turno",
        category="coherencia",
        messages=[
            "¿En qué hackathones has participado?",
            "¿Y en cuál de ellos ganaste?",
        ],
        criteria=[
            "Responde sobre el hackathon ganador sin que el usuario lo haya mencionado de nuevo",
            "No repite la lista completa de hackathones innecesariamente",
            "La respuesta tiene coherencia con el turno anterior",
        ],
        expected_behavior="El agente debe recordar los hackathones del turno anterior y responder específicamente sobre el ganador.",
    ),
    TestCase(
        name="seguimiento_de_tema",
        category="coherencia",
        messages=[
            "¿Cuáles son tus habilidades en cloud?",
            "¿Y cuál de esas plataformas dominas más?",
        ],
        criteria=[
            "El segundo turno es coherente con el primero",
            "No trata el segundo mensaje como una pregunta aislada",
            "Responde sobre cloud sin que el usuario repita el tema",
        ],
        expected_behavior="El agente debe mantener el contexto de la conversación entre turnos.",
    ),
]
