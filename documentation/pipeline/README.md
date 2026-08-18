# Pipeline — Procesamiento de CV

## Descripción general

El pipeline transforma un CV en formato PDF a un JSON estructurado que el agente utiliza como base de conocimiento. Está diseñado para ser genérico: funciona con cualquier CV, no solo con el del autor.

```
PDF (Cloud Storage)
    └── extractor.py       → texto plano
        └── structurer.py  → JSON estructurado (Gemini 2.5 Flash)
            └── storage.py → Cloud Storage (output)
```

---

## Componentes

| Archivo | Responsabilidad |
|---|---|
| `extractor.py` | Extrae texto del PDF usando PyMuPDF |
| `structurer.py` | Llama a Gemini con schema forzado y devuelve JSON garantizado |
| `storage.py` | Lee y escribe archivos en Cloud Storage |
| `main.py` | Entry point — modo local (CLI) o servidor HTTP (Cloud Run) |

---

## ¿Por qué JSON y no PDF directamente?

La alternativa más simple sería pasarle el PDF al agente en cada conversación y dejar que el modelo lo interprete al vuelo. Se descartó por tres razones:

**Costo y latencia.** Enviar un PDF completo como contexto en cada turno de conversación multiplica el número de tokens procesados. El pipeline lo hace una sola vez; el agente solo lee el JSON resultante.

**Precisión.** Los PDFs tienen formato libre — columnas, tablas, encabezados gráficos. Los modelos pueden malinterpretar el orden o la jerarquía de la información. El JSON elimina esa ambigüedad: el agente sabe exactamente dónde está la experiencia, las habilidades o los hackathones.

**Separación de responsabilidades.** El pipeline resuelve el problema de *entender el documento*. El agente resuelve el problema de *conversar sobre él*. Mezclar ambas tareas en el agente lo hace más frágil y difícil de depurar.

---

## Decisiones técnicas

### PyMuPDF para extracción
Extrae texto directamente del PDF sin OCR. Rápido y sin dependencias externas. Limitación conocida: no funciona con PDFs escaneados (imagen pura sin capa de texto).

### Gemini con `response_schema`
Al pasar un schema JSON a la llamada de Gemini, la respuesta está garantizada en estructura y tipos. Elimina la necesidad de validar o parsear manualmente el output del modelo.

### Schema base + `extra_sections`
El schema define campos estándar (experiencia, educación, habilidades, etc.) y un campo `extra_sections` que captura cualquier sección fuera del estándar como texto libre. Esto hace el pipeline genérico sin perder información.

### Modelo configurable por variable de entorno
El nombre del modelo (`GEMINI_MODEL`) es un parámetro de entorno con default a `gemini-2.5-flash`. Si Google depreca una versión, el cambio es operacional — no requiere modificar código.

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | Sí | ID del proyecto de Google Cloud |
| `GOOGLE_CLOUD_LOCATION` | No | Región de Vertex AI (default: `us-central1`) |
| `GEMINI_MODEL` | No | Modelo de Gemini (default: `gemini-2.5-flash`) |
| `OUTPUT_BUCKET` | Solo en Cloud Run | Bucket donde se guarda el JSON resultante |

---

## Ejecución local

### Prerrequisitos

```bash
pip install -r pipeline/requirements.txt
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com --project=TU_PROJECT_ID
```

### Correr el pipeline

```bash
python -m pipeline.main --pdf ruta/al/cv.pdf --output cv.json
```

El resultado es un archivo `cv.json` con toda la información del CV estructurada. Ver [Anexo A](anexos/schema_cv.md) para el esquema completo.

---

## Ejecución en Cloud Run

El servicio expone dos endpoints HTTP:

### `POST /process`
Procesa un PDF desde Cloud Storage y guarda el JSON resultante en `OUTPUT_BUCKET`.

**Request:**
```json
{
  "bucket": "nombre-del-bucket",
  "file": "cv.pdf"
}
```

**Response:**
```json
{
  "status": "ok",
  "output": "gs://output-bucket/cv.json"
}
```

### `GET /health`
Verificación de salud del servicio.

Ver [Anexo B](anexos/deploy_cloud_run.md) para instrucciones de despliegue.

---

## Dependencias

Ver [`pipeline/requirements.txt`](../../pipeline/requirements.txt).
