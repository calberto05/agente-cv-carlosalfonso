"""
Pipeline entry point.

Modes:
  - Cloud Run Service: POST /process {"bucket": "...", "file": "cv.pdf"}
  - Local CLI: python -m pipeline.main --pdf path/to/cv.pdf --output cv.json
"""

import argparse
import json
import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

from pipeline.extractor import extract_text_from_bytes, extract_text_from_pdf
from pipeline.storage import download_bytes, upload_json
from pipeline.structurer import structure_cv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CV Pipeline")


class ProcessRequest(BaseModel):
    bucket: str
    file: str


@app.post("/process")
def process(request: ProcessRequest):
    if not request.file.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    return _process(request.bucket, request.file)


@app.get("/health")
def health():
    return {"status": "ok"}


def _process(bucket_name: str, file_name: str) -> dict:
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    output_bucket = os.environ["OUTPUT_BUCKET"]

    logger.info("Downloading %s from %s", file_name, bucket_name)
    pdf_bytes = download_bytes(bucket_name, file_name)

    logger.info("Extracting text from PDF")
    text = extract_text_from_bytes(pdf_bytes)

    logger.info("Structuring CV with Gemini")
    cv_data = structure_cv(text, project_id)

    output_blob = os.path.splitext(file_name)[0] + ".json"
    logger.info("Uploading JSON to %s/%s", output_bucket, output_blob)
    upload_json(output_bucket, output_blob, cv_data)

    logger.info("Done")
    return {"status": "ok", "output": f"gs://{output_bucket}/{output_blob}"}


def _run_local(pdf_path: str, output_path: str) -> None:
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]

    logger.info("Extracting text from %s", pdf_path)
    text = extract_text_from_pdf(pdf_path)

    logger.info("Structuring CV with Gemini")
    cv_data = structure_cv(text, project_id)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cv_data, f, ensure_ascii=False, indent=2)

    logger.info("Saved to %s", output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CV pipeline")
    parser.add_argument("--pdf", help="Local PDF path (dev mode)")
    parser.add_argument("--output", default="cv.json", help="Local output JSON path")
    parser.add_argument("--port", type=int, default=8080, help="Port for server mode")
    args = parser.parse_args()

    if args.pdf:
        _run_local(args.pdf, args.output)
    else:
        uvicorn.run(app, host="0.0.0.0", port=args.port)
