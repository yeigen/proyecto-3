# Dockerfile multi-stage para HuggingFace Spaces (un solo contenedor)
# Stage 1: build del frontend React/Vite
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: backend FastAPI + frontend estático
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pandas pyarrow

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend /fe/dist frontend/dist

ENV GEOVISION_DATA=/app/data
ENV GEOVISION_FRONTEND=/app/frontend/dist
ENV PYTHONPATH=/app

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
