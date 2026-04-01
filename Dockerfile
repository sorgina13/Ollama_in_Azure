FROM ollama/ollama:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY olama.py ./
COPY self-hosted-ollama.py ./
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODEL=mxbai-embed-large \
    APP_SCRIPT=

EXPOSE 11434

ENTRYPOINT ["/entrypoint.sh"]