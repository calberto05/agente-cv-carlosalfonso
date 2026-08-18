# Deploy — Cloud Run

## Descripción general

El agente se despliega como un servicio HTTP en Google Cloud Run. Cloud Build construye la imagen Docker desde el código fuente y la almacena en Artifact Registry. Cloud Run ejecuta el contenedor y expone un endpoint público compatible con la API Open Responses.

```
Código fuente (GitHub)
    └── gcloud run deploy --source .
            └── Cloud Build → imagen Docker → Artifact Registry
                    └── Cloud Run (cv-agent)
                            └── https://cv-agent-512646778802.us-central1.run.app
```

---

## Endpoint público

| Campo | Valor |
|---|---|
| **URL base** | `https://cv-agent-512646778802.us-central1.run.app` |
| **Health check** | `GET /health` |
| **Endpoint principal** | `POST /` |
| **Autenticación** | `Authorization: Bearer <AGENT_API_KEY>` |
| **Región** | `us-central1` |
| **Proyecto** | `banortepruebatecninca` |

---

## Primer deploy

### Prerrequisitos

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com \
  --project=banortepruebatecninca
```

### Crear bucket y subir el JSON del CV

```bash
gcloud storage buckets create gs://banortepruebatecninca-cv-json \
  --location=us-central1 --project=banortepruebatecninca

gcloud storage cp cv.json gs://banortepruebatecninca-cv-json/cv.json
```

### Build y deploy

```bash
gcloud run deploy cv-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=banortepruebatecninca,\
GOOGLE_CLOUD_LOCATION=us-central1,\
GEMINI_MODEL=gemini-2.5-flash,\
GOOGLE_GENAI_USE_VERTEXAI=true,\
OUTPUT_BUCKET=banortepruebatecninca-cv-json,\
CV_JSON_BLOB=cv.json,\
GITHUB_USERNAME=calberto05,\
AGENT_API_KEY=<TU_API_KEY>" \
  --project=banortepruebatecninca
```

> `--allow-unauthenticated` permite que Banorte llame al endpoint sin credenciales de GCP. La protección se hace con `AGENT_API_KEY`.

---

## Actualizar el agente (redeploy)

Cada vez que hagas cambios al código, un solo comando actualiza el servicio sin tiempo de inactividad:

```bash
gcloud run deploy cv-agent \
  --source . \
  --region us-central1 \
  --project=banortepruebatecninca
```

Cloud Run crea una nueva revisión y le transfiere el tráfico automáticamente.

---

## Actualizar el CV (sin redeploy)

Si subes un CV nuevo, solo necesitas correr el pipeline y subir el JSON al bucket:

```bash
python -m pipeline.main --pdf nuevo_cv.pdf --output cv.json
gcloud storage cp cv.json gs://banortepruebatecninca-cv-json/cv.json
```

El agente carga el JSON al arrancar. Para que tome el nuevo CV, reinicia el servicio:

```bash
gcloud run services update cv-agent --region us-central1 --project=banortepruebatecninca
```

---

## Rollback

Cloud Run guarda todas las revisiones anteriores. Para volver a una versión previa:

```bash
# Ver revisiones disponibles
gcloud run revisions list --service=cv-agent --region=us-central1 --project=banortepruebatecninca

# Regresar a una revisión anterior
gcloud run services update-traffic cv-agent \
  --to-revisions=NOMBRE_REVISION=100 \
  --region us-central1 \
  --project=banortepruebatecninca
```

---

## Cambiar el modelo sin redeploy

El modelo es una variable de entorno. Para cambiarlo sin tocar código:

```bash
gcloud run services update cv-agent \
  --update-env-vars GEMINI_MODEL=gemini-2.0-flash \
  --region us-central1 \
  --project=banortepruebatecninca
```

---

## Variables de entorno en producción

| Variable | Valor en producción |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | `banortepruebatecninca` |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `GOOGLE_GENAI_USE_VERTEXAI` | `true` |
| `OUTPUT_BUCKET` | `banortepruebatecninca-cv-json` |
| `CV_JSON_BLOB` | `cv.json` |
| `GITHUB_USERNAME` | `calberto05` |
| `AGENT_API_KEY` | *(secreto)* |

> `CV_JSON_PATH` **no** se configura en producción — su ausencia hace que el agente lea de Cloud Storage en lugar del sistema de archivos local.

---

## Decisiones técnicas

### `--allow-unauthenticated` + API key propia
Cloud Run permite dos modelos de autenticación: IAM (credenciales de GCP) o pública. Se eligió pública con API key propia porque Banorte necesita llamar al endpoint sin tener credenciales del proyecto. La API key en el header `Authorization: Bearer` provee el control de acceso necesario.

### `--source .` con Dockerfile
`gcloud run deploy --source .` delega el build a Cloud Build, que detecta el `Dockerfile` en la raíz y construye la imagen automáticamente. Esto evita tener que gestionar Artifact Registry manualmente.

### Solo `pipeline/storage.py` en la imagen del agente
El agente solo necesita leer el JSON del CV desde Cloud Storage — no procesar PDFs. Copiar únicamente `pipeline/__init__.py` y `pipeline/storage.py` mantiene la imagen ligera sin incluir dependencias de PyMuPDF.
