import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.api import predict, validate, grids
from backend.data import estaciones, tiles
from backend.modelo.clip_sae import cargar_modelo
from backend.estado import modelo_global, DISPOSITIVO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando servidor (device: {DISPOSITIVO})")
    visual, fusion, band_mean, band_std = cargar_modelo(DISPOSITIVO)
    modelo_global["visual"] = visual
    modelo_global["fusion"] = fusion
    modelo_global["band_mean"] = band_mean
    modelo_global["band_std"] = band_std
    logger.info("Modelo CLIP cargado en memoria")
    yield
    modelo_global.clear()
    logger.info("Modelo descargado")


app = FastAPI(
    title="GeoVision-CLIP -- Estimacion de contaminacion en Cali",
    description="""
## Que hace esta API?

Predice la clase de cobertura del suelo y genera embeddings visuales
a partir de imagenes satelitales Sentinel-2 para cualquier punto de Cali.

## Endpoints principales

* **GET /api/estaciones** -- Ubicacion de las 10 estaciones DAGMA
* **GET /api/tiles-clip** -- Tiles CLIP con clase y NDVI
* **POST /api/predict** -- **El principal**: envia un punto y obten su clase

## Como usar /predict

1. Elige un contaminante (NO2, SO2, O3) -- solo referencia, aun no afecta
2. Elige un horizonte (T+1, T+3, T+7) -- solo referencia, aun no afecta
3. Ingresa lat y lon dentro del area de Cali
4. Ejecuta y obten la clase del tile mas cercano

## Coordenadas de ejemplo

| Lugar | lat | lon |
|-------|-----|-----|
| Centro de Cali | 3.45 | -76.53 |
| Yumbo (industrial) | 3.52 | -76.49 |
| Pance (verde) | 3.31 | -76.56 |
| Ladera | 3.38 | -76.49 |
    """,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(validate.router)
app.include_router(grids.router)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.get("/api/estaciones")
async def get_estaciones():
    return estaciones.estaciones_geojson()


@app.get("/api/estaciones/promedios")
async def get_promedios():
    return estaciones.promedios_contaminantes()


@app.get("/api/estaciones/cobertura")
async def get_cobertura():
    return estaciones.coverage_por_anio()


@app.get("/api/tiles-clip")
async def get_tiles(limite: int = 5000):
    return tiles.tiles_clip_geojson(limite)


@app.get("/api/tiles-clip/resumen")
async def get_tiles_resumen():
    return tiles.resumen_clases()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", include_in_schema=False)
async def home():
    return HTMLResponse("""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>GeoVision-CLIP</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:800px;margin:auto;padding:2rem;background:#f8fafc;color:#1e293b}
  h1{color:#0d9488;border-bottom:2px solid #0d9488;padding-bottom:0.5rem}
  h2{color:#334155;margin-top:2rem}
  pre{background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:8px;overflow-x:auto}
  code{background:#e2e8f0;padding:0.1rem 0.3rem;border-radius:4px;font-size:0.9em}
  pre code{background:transparent;padding:0}
  a{color:#0d9488;text-decoration:none}
  a:hover{text-decoration:underline}
  ul{line-height:1.8}
  table{border-collapse:collapse;width:100%}
  th,td{text-align:left;padding:0.5rem;border-bottom:1px solid #cbd5e1}
  th{background:#f1f5f9}
</style></head>
<body>
<h1>GeoVision-CLIP</h1>
<p>API para clasificacion de cobertura del suelo en Cali usando CLIP + Sentinel-2</p>

<h2>Enlaces utiles</h2>
<ul>
  <li><a href="/docs">Documentacion interactiva (Swagger)</a></li>
  <li><a href="/api/estaciones">Ver estaciones DAGMA</a></li>
  <li><a href="/api/tiles-clip?limite=5">Ver tiles CLIP (5 ejemplos)</a></li>
  <li><a href="/health">Health check</a></li>
</ul>

<h2>Probar /predict con curl</h2>
<pre><code>curl -X POST http://localhost:8000/api/predict ^
  -H "Content-Type: application/json" ^
  -d "{\\"lat\\": 3.45, \\"lon\\": -76.53, \\"contaminante\\": \\"NO2\\", \\"horizonte\\": \\"T+1\\"}"</code></pre>

<h2>Coordenadas de ejemplo</h2>
<table>
<tr><th>Lugar</th><th>lat</th><th>lon</th></tr>
<tr><td>Centro de Cali</td><td>3.45</td><td>-76.53</td></tr>
<tr><td>Yumbo (industrial)</td><td>3.52</td><td>-76.49</td></tr>
<tr><td>Pance (verde)</td><td>3.31</td><td>-76.56</td></tr>
<tr><td>Ladera</td><td>3.38</td><td>-76.49</td></tr>
</table>

<p style="margin-top:2rem;color:#94a3b8;font-size:0.9rem">
  GeoVision-CLIP v1.0.0 &middot; Universidad Autonoma de Occidente &middot; 2026
</p>
</body></html>""")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
