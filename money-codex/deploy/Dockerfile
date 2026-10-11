FROM python:3.12-slim
WORKDIR /app
COPY money_codex ./money_codex
COPY web ./web
COPY config/resource_sources.json ./config/resource_sources.json
ENV MONEY_STATE_DIR=/state MONEY_EXECUTION_MODE=READ_ONLY
VOLUME ["/state"]
# Loopback only. On Linux use --network host for local dashboard access.
CMD ["python", "-m", "money_codex", "serve", "--host", "127.0.0.1", "--port", "8787"]
