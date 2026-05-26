FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dirs uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY backend/ backend/
COPY dagma/ dagma/
COPY checkpoint-kaggle/ checkpoint-kaggle/
COPY fuentes-proyecto-3/ fuentes-proyecto-3/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
