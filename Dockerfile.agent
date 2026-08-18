FROM python:3.12-slim

WORKDIR /app

COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY api/ ./api/
COPY pipeline/__init__.py ./pipeline/__init__.py
COPY pipeline/storage.py ./pipeline/storage.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "api.main"]
