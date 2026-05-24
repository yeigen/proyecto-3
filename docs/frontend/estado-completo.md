# GeoVision-CLIP — Estado completo del proyecto

> Documento resumen de todo lo implementado hasta el momento.
> Fecha: 2026-05-23

---

## 1. Estructura del proyecto

```
proyecto-3/
├── pagina_web/                     # Todo el código desplegable
│   ├── backend/                    # FastAPI + modelos
│   │   ├── main.py                 # Punto de entrada, routers, HTML inicio
│   │   ├── config.py               # Constantes, rutas a datos locales
│   │   ├── estado.py               # Estado global del modelo en memoria
│   │   ├── data/
│   │   │   ├── loader.py           # Carga tiles .npz, lookup por lat/lon
│   │   │   ├── estaciones.py       # DAGMA ground truth (parquet)
│   │   │   └── tiles.py            # Metadata de tiles CLIP
│   │   ├── modelo/
│   │   │   ├── clip_sae.py         # RemoteCLIP ViT-B/32 + fusion
│   │   │   ├── convlstm.py         # ConvLSTM 2 capas (pendiente)
│   │   │   └── kriging.py          # Kriging + Moran (pendiente)
│   │   └── api/
│   │       ├── predict.py          # POST /api/predict (funcional)
│   │       ├── validate.py         # 501 (pendiente)
│   │       └── grids.py            # 501 (pendiente)
│   ├── frontend/                   # React + Vite + Tailwind
│   │   └── src/
│   │       ├── App.tsx             # Router + dark mode
│   │       ├── pages/
│   │       │   ├── Mapa.tsx        # Orquestador + fetch a predict
│   │       │   ├── Inicio.tsx      # Landing page
│   │       │   └── Acerca.tsx      # Info del proyecto
│   │       └── components/
│   │           ├── MapaCali.tsx    # Mapa Leaflet + click + tooltip
│   │           ├── ControlPanel.tsx
│   │           ├── StatsPanel.tsx
│   │           ├── EstacionMarker.tsx
│   │           └── Leyenda.tsx
│   ├── run_api.py                  # Script para iniciar backend
│   ├── Dockerfile
│   └── docker-compose.yml
├── fuentes-proyecto-3/             # Datos descargados de Kaggle (89 GB)
├── dagma/                          # DAGMA ground truth local
├── checkpoint-kaggle/              # Checkpoints adicionales
└── docs/                           # Documentacion del proyecto
```

---

## 2. Backend — Endpoints

### 2.1 Funcionales (con datos reales)

| Endpoint | Metodo | Que devuelve | Datos |
|---|---|---|---|
| `GET /` | HTML | Pagina informativa con enlaces y ejemplos | — |
| `GET /health` | JSON | `{"status": "ok"}` | — |
| `GET /api/estaciones` | GeoJSON | 10 estaciones DAGMA con coordenadas | `dagma/estaciones_metadata.csv` |
| `GET /api/estaciones/promedios` | JSON | Promedios NO2/SO2/O3 por estacion | `dagma/*.parquet` (107k filas) |
| `GET /api/estaciones/cobertura` | JSON | Conteo de mediciones por ano | `dagma/*.parquet` |
| `GET /api/tiles-clip` | GeoJSON | Hasta 5000 tiles CLIP con clase y NDVI | `tiles_meta.parquet` |
| `GET /api/tiles-clip/resumen` | JSON | Conteo de tiles por clase | `tiles_meta.parquet` |
| `POST /api/predict` | JSON | Clasificacion CLIP del punto clickeado | `tiles_train.npz` + checkpoint |

### 2.2 Pendientes (devuelven 501)

| Endpoint | Depende de |
|---|---|
| `POST /api/predict/grid` | ConvLSTM + Kriging |
| `GET /api/validate` | Pipeline completo de validacion |
| `GET /api/grids/{c}/{h}` | predict/grid funcionando |

---

## 3. Pipeline de prediccion (POST /api/predict)

### 3.1 Flujo completo

```
Usuario hace click en (lat, lon)
  |
  v
backend.data.loader.buscar_tile_cercano(lat, lon)
  |->  tiles_meta.parquet: distancia euclidea O(1)
  |->  tiles_train.npz[indice]: tile de 12 bandas x 64x64
  v
backend.data.loader.preprocesar_tile(tile, band_mean, band_std)
  |->  Selecciona 12 bandas (indices 0-11, excluye SCL)
  |->  Redimensiona 64x64 -> 224x224 (F.interpolate bilinear)
  |->  Normaliza: (valor - band_mean) / band_std
  |->  Clamp a [-3, 3]
  v
backend.modelo.clip_sae.generar_embedding(visual, fusion, tensor)
  |->  RemoteCLIP ViT-B/32 (conv1 adaptado a 12 canales)
  |->  embedding 512-d
  |->  fusion: Linear(512, 512)
  |->  L2 normalize
  v
Response JSON:
  {
    "clase": "suelo_urbano",
    "clase_descripcion": "Zona urbana o suelo construido",
    "ndvi": 0.0254,
    "tile_id": 4911,
    "latencia_ms": 185,
    "embedding_dim": 512,
    "embedding_sample": [...primeros 8 valores...]
  }
```

### 3.2 Modelo CLIP (checkpoint)

| Propiedad | Valor |
|---|---|
| Checkpoint | `geovision-clip-modelo-v2v/clip_finetuned_best.pt` |
| Arquitectura | RemoteCLIP ViT-B/32 con LoRA (bloques 6-11) |
| Canales de entrada | 12 bandas Sentinel-2 |
| Patch size | 32x32 |
| Transformer blocks | 12, hidden=768, heads=12 |
| Visual embedding | 512-d (visual.proj: Linear(768, 512)) |
| Fusion | Linear(512, 512) |
| band_mean | Calculado de tiles_train.npz, cacheado en JSON |
| val_loss | 3.39 |
| Epoca | 11 |

### 3.3 Preprocesamiento de tiles

```python
# Los tiles se almacenan como (5000, 13, 64, 64) float32
# 13 bandas: B1-B12 + SCL (Scene Classification Layer)
# Se usan solo las 12 bandas opticas (indices 0-11)
# Se excluye SCL por ser categorica, no reflectancia

# Normalizacion:
band_mean = [840.99, 901.78, 1081.30, 1019.18, 1394.18,
             2333.21, 2732.17, 2691.02, 2938.79, 2913.74,
             2218.68, 1614.18]

band_std = [782.58, 855.98, 804.13, 866.83, 784.75,
            746.49, 895.27, 923.45, 951.82, 1023.61,
            817.14, 958.84]
```

---

## 4. Frontend

### 4.1 Stack

| Herramienta | Version | Uso |
|---|---|---|
| React 18 | 18.3.x | UI components |
| Vite 5 | 5.4.x | Bundler, dev server, HMR |
| TypeScript | 5.5.x | Tipado estatico |
| Tailwind CSS 3 | 3.4.x | Estilos, modo oscuro |
| React Router DOM | 6.26.x | Ruteo SPA |
| React Leaflet | 4.2.x | Mapas interactivos |

### 4.2 Componentes

| Componente | Archivo | Funcion |
|---|---|---|
| `App.tsx` | Raiz | BrowserRouter, darkMode en localStorage, Navbar |
| `Navbar.tsx` | Componente | Navegacion con highlight de ruta activa + modo oscuro |
| `Inicio.tsx` | Pagina | Landing hero con gradiente y acceso rapido |
| `Mapa.tsx` | Pagina | Orquestador: 3 columnas, fetch inicial, click -> predict |
| `Acerca.tsx` | Pagina | Info del proyecto, fuentes, KPIs |
| `MapaCali.tsx` | Componente | Mapa Leaflet, estaciones, tiles CLIP, click handler, popup |
| `ControlPanel.tsx` | Componente | Selector contaminante/horizonte/fuente, checkboxes capas |
| `StatsPanel.tsx` | Componente | Promedios NO2/SO2/O3, cobertura anual |
| `EstacionMarker.tsx` | Componente | Circulo coloreado por contaminante + popup con valores |
| `Leyenda.tsx` | Componente | Colores Baja/Media/Alta |

### 4.3 Interaccion click -> prediccion

```
Usuario hace click en el mapa
  |
  v
MapaCali.tsx -> MapaClickHandler captura (lat, lon)
  |
  v
Mapa.tsx -> handleMapaClick(lat, lon)
  |-> fetch POST /api/predict
  |-> setPrediccion(data)
  v
MapaCali.tsx -> Popup en (lat, lon) con resultado
  |-> Clase + descripcion
  |-> NDVI
  |-> Tile ID usado
  |-> Latencia en ms
```

---

## 5. Datos locales

### 5.1 En `fuentes-proyecto-3/` (89 GB)

| Dataset | Contenido | Formato | Tamano |
|---|---|---|---|
| S2 SR Harmonized | 13 bandas, 1552 fechas, 3897x3897 | Zarr | 85.5 GB |
| S5P NO2 | 3 bandas, 25592 timesteps, 36x36 | Zarr | 19 MB |
| S5P SO2 | 2 bandas, 25829 timesteps, 36x36 | Zarr | 8 MB |
| S5P O3 | 2 bandas, 25716 timesteps, 36x36 | Zarr | 14 MB |
| ERA5 | 8 variables, 43824 timesteps, 2x2 | Zarr | 4.5 MB |
| MODIS MCD19A2 | 4 bandas, 1826 timesteps, 43x43 | Zarr | 16 MB |
| DAGMA | 10 estaciones, 107291 filas | Parquet | 0.83 MB |
| Tiles entrenamiento | 5000 tiles 13x64x64 | NPZ | 229 MB |
| Tiles metadata | 5000 filas x 22 columnas | Parquet | 297 KB |
| Checkpoint CLIP v2v | RemoteCLIP + fusion | PT | 611 MB |
| Checkpoint phase2 | RemoteCLIP + SAE + tab_encoder | PT | 622 MB |

### 5.2 En `dagma/` (local)

| Archivo | Contenido |
|---|---|
| `dagma_cvc_horario_raw.parquet` | 107291 mediciones, 10 estaciones, 2020-2024 |
| `estaciones_metadata.csv` | Coordenadas de las 10 estaciones |

### 5.3 En `backend/data/`

| Archivo | Contenido |
|---|---|
| `tiles_meta.parquet` | Copia de metadata de tiles (5000 registros) |
| `band_stats.json` | band_mean y band_std precalculados (cache) |

---

## 6. Como ejecutar

### Requisitos

```bash
# Python 3.12+
pip install fastapi uvicorn torch numpy pandas pyarrow

# Node 18+
cd pagina_web/frontend
npm install
```

### Iniciar backend

```bash
cd pagina_web
python run_api.py
# -> Uvicorn running on http://0.0.0.0:8000
```

### Iniciar frontend (otra terminal)

```bash
cd pagina_web/frontend
npm run dev
# -> Local: http://localhost:5173
```

### Probar predict

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"lat": 3.45, "lon": -76.53, "contaminante": "NO2", "horizonte": "T+1"}'
```

O desde el navegador:
- `http://localhost:5173` -> Frontend completo
- `http://localhost:8000` -> Pagina HTML informativa
- `http://localhost:8000/docs` -> Swagger UI

---

## 7. Estado de implementacion

| Componente | Estado | % |
|---|---|---|
| API estaciones DAGMA | Completo | 100% |
| API tiles CLIP | Completo | 100% |
| API predict (CLIP) | Completo | 100% |
| Frontend mapa | Completo | 100% |
| Frontend click -> predict | Completo | 100% |
| Landing page + Acerca | Completo | 100% |
| Documentacion Swagger mejorada | Completo | 100% |
| ConvLSTM + Kriging | Pendiente | 0% |
| Validacion LOO-CV | Pendiente | 0% |
| Grid de predicciones | Pendiente | 0% |
| Equidad por estratos | Pendiente | 0% |
| Slider temporal | Pendiente | 0% |
| Descarga GeoTIFF | Pendiente | 0% |

---

## 8. Limitaciones conocidas

1. **Latencia alta en CPU**: ~3-26 segundos por prediccion en CPU. Con GPU baja a ~200ms.
2. **No predice ug/m3**: CLIP solo clasifica visualmente el tile (urbano, vegetacion, contaminacion). No da concentraciones numericas.
3. **Sin validacion NO2**: Solo Yumbo mide NO2, no se puede hacer LOO-CV para ese contaminante.
4. **Tiles fijos**: Los 5000 tiles estan predefinidos. Si el usuario clickea muy lejos del tile mas cercano, la clasificacion puede no ser representativa.
5. **ConvLSTM no implementado**: El pipeline de prediccion temporal (T+1, T+3, T+7) no esta conectado.
