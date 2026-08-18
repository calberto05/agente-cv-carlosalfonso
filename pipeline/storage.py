import json
from google.cloud import storage


def download_bytes(bucket_name: str, blob_name: str) -> bytes:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    return bucket.blob(blob_name).download_as_bytes()


def upload_json(bucket_name: str, blob_name: str, data: dict) -> None:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json",
    )


def download_json(bucket_name: str, blob_name: str) -> dict:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    content = bucket.blob(blob_name).download_as_text(encoding="utf-8")
    return json.loads(content)
