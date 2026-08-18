# Anexo B — Despliegue en Cloud Run

## Prerrequisitos

- Google Cloud SDK instalado y autenticado
- APIs habilitadas en el proyecto:

```bash
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  --project=TU_PROJECT_ID
```

---

## 1. Crear los buckets de Cloud Storage

```bash
# Bucket de entrada (PDFs)
gcloud storage buckets create gs://TU_PROJECT_ID-cv-pdfs \
  --location=us-central1 \
  --project=TU_PROJECT_ID

# Bucket de salida (JSONs)
gcloud storage buckets create gs://TU_PROJECT_ID-cv-json \
  --location=us-central1 \
  --project=TU_PROJECT_ID
```

---

## 2. Construir y subir la imagen Docker

```bash
gcloud builds submit \
  --tag gcr.io/TU_PROJECT_ID/cv-pipeline \
  --project=TU_PROJECT_ID
```

> Asegúrate de tener un `Dockerfile` en la raíz del proyecto. Ver sección 5.

---

## 3. Desplegar el servicio en Cloud Run

```bash
gcloud run deploy cv-pipeline \
  --image gcr.io/TU_PROJECT_ID/cv-pipeline \
  --region us-central1 \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=TU_PROJECT_ID,OUTPUT_BUCKET=TU_PROJECT_ID-cv-json,GEMINI_MODEL=gemini-2.5-flash \
  --project=TU_PROJECT_ID
```

> `--no-allow-unauthenticated` protege el endpoint — solo llamadas autenticadas pueden invocarlo.

---

## 4. Invocar el pipeline desde Cloud Run

```bash
# Obtener el token de autenticación
TOKEN=$(gcloud auth print-identity-token)

# Llamar al endpoint
curl -X POST https://TU_PIPELINE_URL/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bucket": "TU_PROJECT_ID-cv-pdfs", "file": "cv.pdf"}'
```

---

## 5. Dockerfile del pipeline

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ ./pipeline/

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "pipeline.main"]
```

---

## Notas

- El servicio usa Application Default Credentials (ADC) dentro de Cloud Run — no se necesitan service account keys explícitas si el servicio tiene los permisos de IAM correctos.
- Para que el servicio pueda llamar a Vertex AI y Cloud Storage, la service account de Cloud Run necesita los roles: `roles/aiplatform.user` y `roles/storage.objectAdmin`.
