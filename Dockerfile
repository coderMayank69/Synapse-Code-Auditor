FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV PIP_DEFAULT_TIMEOUT=240
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd -m -u 1000 appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
		&& pip install --no-cache-dir --retries 10 -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
