# GeoVision-CLIP — Aplicación web (backend + frontend)

Mapa interactivo de estimación de contaminación (NO₂/SO₂/O₃) en Cali.
- **Backend**: FastAPI que sirve los artefactos pre-computados de la Situación 3 (malla de
  predicción, KPIs, estaciones DAGMA, tiles CLIP) — no carga el modelo en runtime.
- **Frontend**: React 18 + Vite + TypeScript + Tailwind + Leaflet (react-leaflet).

> Para despliegue en Hugging Face Spaces ver [README_SPACE.md](README_SPACE.md) y el [Dockerfile](Dockerfile).

---

## Requisitos
- **Node.js 20+** (frontend)
- **Python 3.12 + [uv](https://docs.astral.sh/uv/)** (backend)

---

## Ejecución en desarrollo (2 terminales)

El frontend (Vite) hace **proxy de `/api` y `/static` al backend en `http://localhost:8000`**
(ver [frontend/vite.config.ts](frontend/vite.config.ts)). Por eso hay que tener el **backend corriendo**
o el mapa quedará sin datos (errores `http proxy error … AggregateError` en la consola de Vite).

### 1) Backend — FastAPI (puerto 8000)
Desde la **raíz del repo** (`proyecto-3/`):

```bash
# Instalar dependencias del backend en el entorno (una sola vez)
uv pip install fastapi "uvicorn[standard]" pandas pyarrow

# Levantar el servidor (recarga en caliente)
uv run uvicorn backend.main:app --app-dir pagina_web --host 0.0.0.0 --port 8000 --reload
```

Comprobar: <http://localhost:8000/health> → `{"status":"ok",...}` y <http://localhost:8000/docs> (Swagger).

### 2) Frontend — Vite (puerto 5173)
En otra terminal:

```bash
cd pagina_web/frontend
npm install        # una sola vez (instala React, Leaflet, lucide-react, etc.)
npm run dev
```

Abrir 👉 **<http://localhost:5173>**
(si el 5173 está ocupado, Vite usa 5174 — revisa la URL que imprime).

> **Nota Windows (IPv4/IPv6)**: Vite escucha en `localhost` (a veces `::1`). Usa siempre
> `http://localhost:<puerto>`, no `http://127.0.0.1:<puerto>`, para evitar fallos de conexión.

---

## Build de producción

```bash
cd pagina_web/frontend
npm run build      # genera frontend/dist (tsc -b && vite build)
```

Si existe `frontend/dist`, el backend lo sirve como SPA en `/`, así que basta con levantar solo el
backend (no necesitas Vite). El [Dockerfile](Dockerfile) hace exactamente esto: build del frontend +
FastAPI sirviendo `dist` en el puerto 7860.

```bash
# Opción Docker (todo en un contenedor)
docker compose up --build          # ver docker-compose.yml
```

---

## Endpoints principales (backend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/estaciones` | Estaciones DAGMA (GeoJSON) |
| GET | `/api/estaciones/promedios` · `/cobertura` | Promedios por gas · cobertura anual |
| GET | `/api/tiles-clip` · `/api/tiles-clip/resumen` | Tiles CLIP (clase, NDVI/NDBI) · conteo por clase |
| GET | `/api/cobertura?lat=&lon=&radio_km=` | **Qué zona ve el modelo** en un punto (clase dominante + NDVI/NDBI) |
| POST | `/api/predict` | Predicción valor ± σ en el punto (SO₂/O₃) |
| GET | `/api/predict/grid?contaminante=&horizonte=` | Malla completa (descarga CSV) |
| GET | `/api/grids/bounds/{gas}/{h}` | Bounds + vmin/vmax del overlay |
| GET | `/api/grids/{gas}/{h}/{pred\|sigma}` | PNG georreferenciado del overlay |
| GET | `/api/validate` · `/lisa` · `/variogramas` · `/perfiles` | Métricas LOO-CV/KPIs y geoestadística |

Datos servidos desde `data/sit3/frontend_data/` y `data/tiles/rescate-1500/tiles_meta.parquet`
(rutas configurables con la variable de entorno `GEOVISION_DATA`; ver [backend/config.py](backend/config.py)).

---

## Notas
- **NO₂** no tiene mapa de Kriging (solo 2 estaciones DAGMA, insuficiente para variograma n≥3); sí
  tiene cobertura y aparece en estaciones.
- La **intro del planeta** se reproduce una vez por sesión (flag `intro_visto` en `sessionStorage`);
  para volver a verla, abre una pestaña nueva o limpia el `sessionStorage`.
- El **modo oscuro** (toggle en la navbar) cambia toda la UI y el basemap (CARTO `voyager`↔`dark_all`).
