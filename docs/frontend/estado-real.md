# Estado real del sistema GeoVision-CLIP

> Documento de referencia: qué funciona con datos reales vs qué es placeholder.
> Última actualización: 2026-05-22

---

## 1. Backend — Endpoints

### ✅ Reales (funcionan con datos verificables)

| Endpoint | Método | Datos | Fuente | Verificación |
|---|---|---|---|---|
| `GET /health` | — | `{"status":"ok"}` | — | `curl localhost:8000/health` |
| `GET /api/estaciones` | GeoJSON 10 estaciones | `dagma/estaciones_metadata.csv` | 10 estaciones DAGMA + CVC con lat/lon real | ✅ |
| `GET /api/estaciones/promedios` | JSON `{estacion_id: {no2, so2, o3}}` | `dagma/dagma_cvc_horario_raw.parquet` (107.291 filas) | Promedio real de cada contaminante por estación | ✅ |
| `GET /api/estaciones/cobertura` | JSON `{año: cantidad}` | Mismo parquet | Conteo real de mediciones por año | ✅ |
| `GET /api/tiles-clip?limite=N` | GeoJSON N tiles | `backend/data/tiles_meta.parquet` (5.000 tiles) | Tiles reales del dataset Kaggle `geovision-tiles-sit2`, con lat/lon, clase y NDVI real | ✅ |
| `GET /api/tiles-clip/resumen` | JSON conteo por clase | Mismo parquet | Distribución real de las 5 clases | ✅ |

### 🟡 Placeholder (estructura lista, sin datos reales)

| Endpoint | Estado | Lo que falta |
|---|---|---|
| `POST /api/predict` | Devuelve 501 Not Implemented | Zarrs de S5P + S2 (83 GB), checkpoint ConvLSTM |
| `POST /api/predict/grid` | Devuelve 501 Not Implemented | Depende de predict |
| `GET /api/validate` | Devuelve 501 Not Implemented | Depende de predict |
| `GET /api/grids/{c}/{h}` | Devuelve 501 Not Implemented | Depende de predict/grid |

---

## 2. Frontend — Componentes

### ✅ Reales (visualizan datos del backend)

| Componente | Qué muestra | Dato real |
|---|---|---|
| `Navbar.tsx` | Links, modo oscuro | — |
| `EstacionMarker.tsx` | Marcador circular en mapa | Coordenadas reales de `estaciones_metadata.csv` |
| | Popup con nombre, lat, lon, altitud | Mismas coordenadas |
| | Popup con NO₂/SO₂/O₃ promedio | Promedios reales del parquet DAGMA |
| | Color del marcador según umbrales | Umbrales fijos por contaminante |
| `StatsPanel.tsx` | Promedios NO₂/SO₂/O₃ | Promedios reales del parquet DAGMA |
| | Cobertura anual | Conteo real del parquet DAGMA |
| `Leyenda.tsx` | Colores Baja/Media/Alta | — |
| `MapaCali.tsx` | Mapa base OpenStreetMap | — |
| | Círculos de estaciones DAGMA | Datos reales |
| | Rectángulos de tiles CLIP | Tiles reales del dataset Kaggle (2.000) |
| `ControlPanel.tsx` | Selector contaminante (NO₂/SO₂/O₃) | Afecta colores de marcadores |
| | Selector horizonte (T+1/T+3/T+7) | Placeholder (no cambia datos aún) |
| | Checkbox estaciones | Muestra/oculta estaciones reales |
| | Checkbox tiles CLIP | Muestra/oculta tiles reales |
| `Inicio.tsx` | Hero, cards informativas | — |
| `Acerca.tsx` | Fuentes satelitales (6), KPIs, metodología | Pesos reales del manifest (89.73 GB) |

### 🟡 Placeholder (interfaz lista, sin funcionalidad real)

| Componente | Qué hace hoy | Para qué está |
|---|---|---|
| Checkbox "Gradiente" en ControlPanel | Oculto/deshabilitado | Activar cuando predict funcione |
| Checkbox "Incertidumbre" en ControlPanel | Oculto/deshabilitado | Activar cuando predict funcione |
| Checkbox "Estratos" en ControlPanel | Oculto/deshabilitado | Activar cuando haya datos de estratos reales |
| Botón "Descargar CSV" en Mapa | No renderizado | Conectar a predict/grid |
| Botón "Descargar GeoTIFF" en ControlPanel | Deshabilitado | Conectar a /api/grids |

### ❌ Eliminado (contenido inventado)

| Lo que se quitó | Razón |
|---|---|
| `mock.ts`: `estaciones` con valores inventados | Las estaciones se obtienen del backend |
| `mock.ts`: `tilesClip` con 30 tiles aleatorios | Los tiles se obtienen del backend (2.000 reales) |
| `mock.ts`: `stats` con promedios, máximos y cobertura inventados | Los promedios y cobertura vienen del backend real |
| `mock.ts`: `estratos` con valores inventados | No hay datos reales de estratos aún |
| `mock.ts`: `generarGridMock` | No hay modelo real que genere grillas |
| `Mapa.tsx`: `handleMapaClick` → genera grilla fake | Los valores no significaban nada |
| `Mapa.tsx`: `handleDescargar` → CSV con datos fake | Los valores no significaban nada |
| `Mapa.tsx`: `ultimoClick` overlay con descarga | Misma razón |
| `StatsPanel.tsx`: sección "Máximos" | Valores inventados |
| `StatsPanel.tsx`: sección "X por estrato" | Valores inventados |
| `ControlPanel.tsx`: sección "Equidad" | Valores inventados |
| `MapaCali.tsx`: renderizado de `gridPrediccion` | Datos inventados |

---

## 3. Datos — Qué falta para tener predicciones reales

| Recurso | Dónde está | Tamaño | Estado |
|---|---|---|---|
| Checkpoint CLIP+SAE | `checkpoint-kaggle/clip_finetuned_best.pt` | 640 MB | ✅ Descargado |
| Tiles Situación 2 | `backend/data/tiles_meta.parquet` | 297 KB | ✅ Descargado |
| Zarr S5P NO₂ | Kaggle `geovision-fuentes` / HF bucket | 20.4 GB | ❌ No descargado |
| Zarr S5P SO₂ | Kaggle `geovision-fuentes` / HF bucket | 8.1 GB | ❌ No descargado |
| Zarr S5P O₃ | Kaggle `geovision-fuentes` / HF bucket | 14.8 GB | ❌ No descargado |
| Zarr Sentinel-2 | Kaggle `geovision-fuentes` / HF bucket | 89.67 GB | ❌ No descargado |
| Zarr ERA5 | Kaggle `geovision-fuentes` / HF bucket | 4.7 GB | ❌ No descargado |
| Checkpoint ConvLSTM | — | ~100 MB | ❌ No existe (entrenar con notebook Sit3) |
| Módulo ConvLSTM inferencia | `backend/modelo/convlstm.py` | — | ✅ Código listo |
| Módulo ST-Kriging | `backend/modelo/kriging.py` | — | ✅ Código listo (probado) |
| Módulo CLIP+SAE | `backend/modelo/clip_sae.py` | — | ✅ Código listo |

---

## 4. Pipeline completo (cuando todo esté listo)

```
Frontend (click en mapa)
  → (lat, lon, contaminante, horizonte)
  → POST /api/predict
    → loader.py: abre Zarr S2 en coordenada → tile 64×64
    → loader.py: abre Zarr S5P → serie temporal (8 fechas)
    → clip_sae.py: CLIP+SAE → embedding 256-d
    → convlstm.py: ConvLSTM → predicción (3×3×H×W)
    → kriging.py: ST-Kriging → valor ± varianza
    → Response {valor, varianza}
  → Frontend: muestra tooltip + colorea gradiente + overlay incertidumbre
```

---

## 5. Cómo verificar que todo funciona

```bash
# Backend
curl http://localhost:8000/health                    # → {"status":"ok"}
curl http://localhost:8000/api/estaciones            # → 10 estaciones reales
curl http://localhost:8000/api/estaciones/promedios  # → Promedios reales
curl http://localhost:8000/api/estaciones/cobertura  # → Cobertura real
curl http://localhost:8000/api/tiles-clip?limite=5   # → 5 tiles reales

# Frontend
Abrir http://localhost:5173
  → Mapa con estaciones reales en posiciones correctas
  → Popups con valores reales al hacer click
  → Tiles CLIP reales coloreados por clase
  → Stats panel con promedios y cobertura reales
```
