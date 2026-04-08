FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV PIP_DEFAULT_TIMEOUT=240

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --retries 10 -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
