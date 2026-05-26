# Plan de migración frontend: modelo viejo → nuevo + datos Sit 3

Estado de partida: rama `rama-fronted-prueba` tiene frontend React+Leaflet + backend FastAPI funcional, pero apunta a **recursos viejos** y los endpoints de predicción están en 501.

## Arquitectura decidida (híbrido, según PDF)

- **`/api/predict` puntual**: on-demand. Tile S2 del punto → CLIP-SAE → predicción. Cumple KPI latencia <8s (PDF pág. 9). El backend ya carga el modelo en `lifespan` (main.py).
- **`/api/predict/grid` + `/api/grids`**: sirven artefactos pre-computados de Sit 3 (`grids_prediccion.json` + overlays PNG). Los 9 mapas son fijos por gas×horizonte.
- **`/api/validate`**: sirve `loocv.json` + `kpis.json`.

## Migración de datos viejos → nuevos (backend/config.py)

| variable | viejo | nuevo |
|----------|-------|-------|
| `CHECKPOINT_CLIP` | `geovision-clip-modelo-v2v/clip_finetuned_best.pt` | `geovision-clip-sit2-model/geovision_clip_sit2_best.pt` |
| `BASE_TILES` | `GeoVision Tiles Sit 2` (5000) | `tiles-rescate-1500` (1500) |
| `RUTA_DAGMA` | `dagma_cvc_horario_raw.parquet` (107K, 10 est) | `df_dagma_unificado_coordenadas_limpias.parquet` (300K, 9 est coords corregidas) |
| `RUTA_ESTACIONES` | `estaciones_metadata.csv` (coords viejas) | regenerado (9 est, coords del parquet limpio) |
| nuevo | — | `SIT3_DATA = geovision-sit3-embeddings/frontend_data/` |

## Cambios por archivo

### backend/config.py
- Actualizar las 4 rutas de arriba.
- Agregar `SIT3_FRONTEND_DATA` apuntando a `frontend_data/`.

### backend/modelo/clip_sae.py
- **Arquitectura cambió**: el modelo nuevo tiene `band_projector` (13→3 bandas), `visual_encoder` (ViT-B/32, 2 bloques entrenables), `sae_visual` (512→2048→256), `proj_visual`, `tabular_gate`, `classifier`.
- `cargar_modelo()` debe reconstruir esta arquitectura y cargar `model_state` del checkpoint nuevo.
- Las llaves del checkpoint: `ckpt['model_state']`, `ckpt['config']`, `ckpt['candidate_texts']`.

### backend/api/predict.py
- `/api/predict` (punto): ya funciona parcial (devuelve embedding). Extender para devolver `valor` + `varianza` consultando el grid pre-computado más cercano O kriging puntual ligero.
- `/api/predict/grid`: leer `grids_prediccion.json[{gas}_{horizonte}]`, devolver lista de `CeldaGrid {lat, lon, valor, varianza}`.

### backend/api/grids.py
- `/api/grids/{gas}/{horizonte}`: servir el PNG `overlays/{gas}_T{h}_pred.png` (predicción) y `_sigma.png` (incertidumbre).

### backend/api/validate.py
- `/api/validate`: devolver `loocv.json` + `kpis.json` (tabla LOO-CV + KPIs PDF).

### backend/data/estaciones.py
- Actualizar para leer el `estaciones.json` nuevo (9 estaciones, coords corregidas) o el parquet limpio.

## Cambios frontend (React)

### src/components/ControlPanel.tsx
- Activar checkbox **Gradiente** → mostrar overlay `/api/grids/{gas}/{h}` (pred).
- Activar checkbox **Incertidumbre** → mostrar overlay sigma con opacidad.
- Slider temporal **T+1/T+3/T+7** → cambiar `horizonte` y recargar overlay.

### src/components/MapaCali.tsx
- `ImageOverlay` de Leaflet con el PNG del gradiente + bounds del JSON.
- Click en punto → `POST /api/predict` → tooltip `valor ± σ`.

### src/components/StatsPanel.tsx
- Conectar a `/api/validate` → mostrar tabla LOO-CV + KPIs Sit 3.

### src/pages/Mapa.tsx
- Activar botones descarga CSV (de `grids_prediccion.json`) y GeoTIFF.

## Orden de ejecución sugerido

1. Merge `rama-fronted-prueba` → `release/sit-1-2-3-final`.
2. Traer artefactos Sit 3 a `pagina_web/backend/data/sit3/`.
3. Actualizar `config.py` (rutas nuevas).
4. Reescribir `clip_sae.py` (arquitectura nueva).
5. Implementar los 4 endpoints 501.
6. Activar componentes frontend (gradiente, incertidumbre, slider, descargas).
7. `docker-compose up` → probar local.
8. Desplegar HuggingFace Spaces.

## Bonus ya logrado
- **Modo oscuro**: ya implementado en `Navbar.tsx` → +2 puntos PDF.

## Pendiente de decisión
- ¿`/api/predict` puntual hace forward CLIP real (cumple latencia <8s medible) o busca celda en grid pre-computado (latencia <0.1s)? El PDF tiene KPI de latencia, sugiere forward real.
