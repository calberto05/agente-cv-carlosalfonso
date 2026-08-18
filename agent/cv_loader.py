import json
import os

from pipeline.storage import download_json


def load_cv() -> dict:
    local_path = os.environ.get("CV_JSON_PATH")
    if local_path:
        with open(local_path, encoding="utf-8") as f:
            return json.load(f)

    bucket = os.environ["OUTPUT_BUCKET"]
    blob = os.environ.get("CV_JSON_BLOB", "cv.json")
    return download_json(bucket, blob)


def extract_github_username(cv_data: dict) -> str:
    github_url = cv_data.get("personal_info", {}).get("github", "").rstrip("/")
    if github_url:
        username = github_url.split("/")[-1]
        if username:
            return username
    return os.environ.get("GITHUB_USERNAME", "")
