FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY lockerline ./lockerline
COPY seed ./seed
RUN mkdir -p /data

EXPOSE 8080
# Runtime defaults (overridden by an env-file when provided): HOST=0.0.0.0, PORT=8080.
CMD ["sh", "-c", "uvicorn lockerline.app:app --host \"${HOST:-0.0.0.0}\" --port \"${PORT:-8080}\""]