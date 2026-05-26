# GeoVision-CLIP — Arquitectura y guía técnica

> Documento de referencia para la implementación del frontend y backend.
> Versión: 1.0 — 2026-05-22

---

## 1. Diagrama de arquitectura general

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          USUARIO (Navegador)                             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ HTTPS / HTTP
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  pagina_web/frontend/ — React + Vite + Tailwind + Leaflet               │
│                                                                          │
│  ┌──────────┐  ┌──────────────────────┐  ┌──────────┐                    │
│  │ Inicio   │  │ Mapa (3 columnas)     │  │ Acerca   │                    │
│  │ (landing)│  │ ┌────┬────────┬────┐ │  │ (info)   │                    │
│  └──────────┘  │ │Ctrl│ Mapa   │Stats│ │  └──────────┘                    │
│                │ │Panel│Leaflet │Panel│ │                                  │
│                │ └────┴────────┴────┘ │                                  │
│                └──────────────────────┘                                  │
│                                                                          │
│  Proxy Vite: /api → http://localhost:8000                               │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ JSON / HTTP
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  pagina_web/backend/ — FastAPI + Uvicorn + Python                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  main.py — FastAPI app                                           │   │
│  │  • CORS middleware                                               │   │
│  │  • Routers: predict, validate, grids, estaciones, tiles          │   │
│  │  • Static files: /static/grids/*.tiff                            │   │
│  └──┬──────────┬──────────┬──────────┬──────────┬──────────────────┘   │
│     │          │          │          │          │                        │
│  ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼──────┐               │
│  │ predict│ │validate│ │ grids  │ │tiles   │ │estac.  │               │
│  │  .py   │ │  .py   │ │  .py   │ │  .py   │ │  .py   │               │
│  └──┬─────┘ └────────┘ └────────┘ └────────┘ └─────────┘               │
│     │                                                                   │
│  ┌──▼──────────────────────────────────────────────────────────────┐   │
│  │  modelo/                                                        │   │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐   │   │
│  │  │ clip_sae.py      │  │ convlstm.py    │  │ kriging.py     │   │   │
│  │  │ • CLIP + SAE     │  │ • ConvLSTM 2cap │  │ • ST-Kriging  │   │   │
│  │  │ • Checkpoint     │  │ • Hidden 128   │  │ • Moran/LISA  │   │   │
│  │  │   640 MB         │  │ • Head 1×1→9   │  │ • PyKrige +   │   │   │
│  │  └─────────────────┘  └────────────────┘  │   PySAL       │   │   │
│  │                                            └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  data/                                                          │   │
│  │  ┌─────────────────────────┐  ┌──────────────────────────┐      │   │
│  │  │ loader.py               │  │ estaciones.py             │      │   │
│  │  │ • Kaggle → Zarr local   │  │ • DAGMA parquet (107K)   │      │   │
│  │  │ • Fallback HF bucket    │  │ • GeoJSON estaciones     │      │   │
│  │  │ • tiles S2, series S5P  │  │ • Promedios x estación   │      │   │
│  │  └─────────────────────────┘  └──────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Datos locales:                                                         │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────────────────┐      │
│  │ dagma/      │  │ checkpoint-    │  │ backend/data/          │      │
│  │ • parquet   │  │ kaggle/        │  │ tiles_meta.parquet     │      │
│  │ • CSV       │  │ • .pt (640MB)  │  │ (5000 tiles reales)   │      │
│  └─────────────┘  └────────────────┘  └────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend — Stack y componentes

### 2.1 Stack tecnológico

| Herramienta | Versión | Propósito |
|---|---|---|
| **React 18** | 18.3.x | UI components, estado, efectos |
| **Vite 5** | 5.4.x | Bundler, dev server, HMR |
| **TypeScript** | 5.5.x | Tipado estático |
| **Tailwind CSS 3** | 3.4.x | Estilos utilitarios, modo oscuro |
| **React Router DOM** | 6.26.x | Ruteo SPA (/, /mapa, /acerca) |
| **React Leaflet** | 4.2.x | Mapas interactivos (wrapper React de Leaflet) |
| **Leaflet** | 1.9.x | Motor de mapas (OpenStreetMap) |

### 2.2 Estructura de archivos

```
frontend/
├── index.html              # Entry point HTML (Leaflet CSS via CDN)
├── package.json            # Dependencias y scripts
├── vite.config.ts          # Proxy /api → backend
├── tsconfig.json           # TypeScript config
├── tailwind.config.js      # Colores personalizados (no2, so2, o3, clip)
├── postcss.config.js       # Tailwind + autoprefixer
├── nginx.conf              # Config para deploy producción
├── Dockerfile              # Build multi-stage
└── src/
    ├── main.tsx            # ReactDOM.createRoot
    ├── App.tsx             # Router + darkMode + Navbar
    ├── index.css           # Tailwind directives + Leaflet fixes
    ├── vite-env.d.ts       # Tipos Vite
    ├── types/
    │   └── index.ts        # Interfaces: Estacion, TileClip, Stats, etc.
    ├── data/
    │   └── mock.ts         # Constantes reales (fuentes, contaminantes)
    ├── components/
    │   ├── Navbar.tsx      # Barra de navegación + dark mode
    │   ├── MapaCali.tsx    # Mapa Leaflet con overlays
    │   ├── EstacionMarker.tsx  # Marcador circular con popup
    │   ├── ControlPanel.tsx    # Panel lateral izquierdo
    │   ├── StatsPanel.tsx      # Panel lateral derecho
    │   └── Leyenda.tsx     # Leyenda de clases CLIP
    └── pages/
        ├── Inicio.tsx      # Landing page
        ├── Mapa.tsx        # Página principal del mapa
        └── Acerca.tsx      # Información del proyecto
```

### 2.3 Componentes en detalle

#### `App.tsx` — Raíz de la aplicación

```tsx
// BrowserRouter con 3 rutas
// Estado darkMode persistido en localStorage
// Renderiza Navbar + Routes
<BrowserRouter>
  <Navbar darkMode toggleDarkMode />
  <Routes>
    <Route path="/" element={<Inicio />} />
    <Route path="/mapa" element={<Mapa />} />
    <Route path="/acerca" element={<Acerca />} />
  </Routes>
</BrowserRouter>
```

#### `MapaCali.tsx` — Mapa Leaflet

```tsx
// react-leaflet: MapContainer + TileLayer + Rectangle
// Centrado en Cali: [3.45, -76.53], zoom 11
// Renderiza:
//   - Estaciones DAGMA como CircleMarker (react-leaflet)
//   - Tiles CLIP como Rectangle coloreados por clase
//   - Leyenda como control Leaflet personalizado
<MapContainer center={[3.45, -76.53]} zoom={11}>
  <TileLayer url="https://{s}.tile.openstreetmap.org/..." />
  <EstacionMarker estacion={e} contaminante={c} />
  <Rectangle bounds={[[lat-d, lon-d], [lat+d, lon+d]]} pathOptions={{color, fillOpacity}} />
  <Leyenda />
</MapContainer>
```

#### `EstacionMarker.tsx` — Marcador de estación

```tsx
// CircleMarker de react-leaflet
// Radio: 8px, borde blanco, relleno según contaminante
// Popup con: nombre, lat/lon, altitud, tabla NO₂/SO₂/O₃
// getColor() usa umbrales fijos por contaminante
getColor(contaminante, valor) {
  // NO₂: <10=verde, <20=amarillo, <40=naranja, >=40=rojo
  // SO₂: <5=verde, <10=amarillo, <20=naranja, >=20=rojo
  // O₃: <30=verde, <50=amarillo, <80=naranja, >=80=rojo
}
```

#### `ControlPanel.tsx` — Panel de control

```tsx
// Botones de contaminante (NO₂/SO₂/O₃)
// Botones de horizonte (T+1/T+3/T+7)
// Selector de fuente satelital (6 fuentes)
// Checkboxes de capas (estaciones, tiles)
// Estado futuro: gradiente, incertidumbre, estratos, descarga GeoTIFF
```

#### `StatsPanel.tsx` — Panel de estadísticas

```tsx
// Promedios NO₂/SO₂/O₃ (datos reales del backend)
// Cobertura anual con barras de progreso
// Futuro: máximos, estratos, métricas de validación
```

#### `Mapa.tsx` — Orquestador

```tsx
// Layout 3 columnas: ControlPanel (256px) | Mapa (flex) | StatsPanel (256px)
// useEffect: fetch a /api/estaciones, /api/estaciones/promedios,
//            /api/estaciones/cobertura, /api/tiles-clip
// Offset superior 3.5rem por el Navbar fijo
```

### 2.4 Flujo de datos del frontend

```
Al cargar Mapa.tsx:
  1. fetch /api/estaciones          → GeoJSON → setEstaciones()
  2. fetch /api/estaciones/promedios → JSON   → setEstaciones(con promedios)
  3. fetch /api/estaciones/cobertura → JSON   → setStats(cobertura)
  4. fetch /api/tiles-clip?limite=2000 → GeoJSON → setTilesClip()

Cada fetch tiene .catch() que deja el estado anterior
(sin datos si el backend no está disponible)
```

---

## 3. Backend — Stack y módulos

### 3.1 Stack tecnológico

| Herramienta | Versión | Propósito |
|---|---|---|
| **FastAPI** | 0.136.x | Framework REST, validación Pydantic |
| **Uvicorn** | 0.47.x | Servidor ASGI |
| **Python** | 3.12 | Lenguaje base |
| **PyTorch** | 2.7.x | Modelos deep learning (CLIP, ConvLSTM) |
| **PyKrige** | 1.7.x | Kriging Ordinario 3D |
| **PySAL / libpysal** | 26.x / 4.x | Moran Global, LISA, pesos espaciales |
| **esda** | 2.8.x | Estadística espacial exploratoria |
| **xarray** | 2026.4.x | Arrays N-dimensionales, carga Zarr |
| **zarr** | 3.2.x | Almacenamiento chunked de arrays |
| **pandas** | 3.0.x | DataFrames, DAGMA parquet |
| **rasterio** | 1.5.x | Generación de GeoTIFFs |
| **kagglehub** | 1.0.x | Descarga de datasets Kaggle |
| **huggingface-hub** | 0.31.x | Acceso a HF bucket (fallback) |
| **scikit-learn** | 1.6.x | Métricas RMSE/MAE/R² |
| **Pydantic** | 2.12.x | Validación de request/response |

### 3.2 Estructura de archivos

```
backend/
├── __init__.py
├── main.py                 # FastAPI app, routers, endpoints directos
├── config.py               # Constantes, rutas, hiperparámetros
├── data/
│   ├── __init__.py
│   ├── loader.py           # Carga Zarrs (Kaggle → local, fallback HF)
│   ├── estaciones.py       # DAGMA ground truth
│   └── tiles.py            # Tiles CLIP metadata
├── modelo/
│   ├── __init__.py
│   ├── clip_sae.py         # CLIP + Sparse Autoencoder
│   ├── convlstm.py         # ConvLSTM espacio-temporal
│   └── kriging.py          # ST-Kriging + Moran/LISA
├── api/
│   ├── __init__.py
│   ├── predict.py          # POST /api/predict (placeholder)
│   ├── validate.py         # GET /api/validate (placeholder)
│   └── grids.py            # GET /api/grids (placeholder)
└── static/
    └── grids/              # GeoTIFFs generados (futuro)
```

### 3.3 Endpoints actuales

#### `GET /api/estaciones` — GeoJSON de estaciones

```python
# backend/data/estaciones.py → estaciones_geojson()
# Lee: dagma/estaciones_metadata.csv
# Retorna: FeatureCollection con 10 estaciones
# Cada feature: {type, geometry: {coordinates}, properties: {id, nombre, altitud}}
```

#### `GET /api/estaciones/promedios` — Promedios por estación

```python
# backend/data/estaciones.py → promedios_contaminantes()
# Lee: dagma/dagma_cvc_horario_raw.parquet (107.291 filas)
# Agrupa por estacion_id y msfl_code (NO₂/SO₂/O₃)
# Calcula mean() de med_concentracion_estandar
# Retorna: {"estacion_id": {"no2": x, "so2": y, "o3": z}}
```

#### `GET /api/estaciones/cobertura` — Conteo por año

```python
# backend/data/estaciones.py → coverage_por_anio()
# Lee: dagma/dagma_cvc_horario_raw.parquet
# Agrupa por año de med_fecha_inicio
# Retorna: {"2020": 52192, "2021": 11514, ...}
```

#### `GET /api/tiles-clip?limite=N` — Tiles CLIP en GeoJSON

```python
# backend/data/tiles.py → tiles_clip_geojson(limite)
# Lee: backend/data/tiles_meta.parquet (5.000 tiles reales)
# Mapea clase_str → clase_int:
#   vegetacion_densa → 0 (verde)
#   suelo_urbano → 1 (amarillo)
#   contaminacion_alta_NO₂/SO₂, ozono_anomalo → 2 (rojo)
# Calcula score = 0.5 + abs(ndvi) * 0.5
# Retorna: FeatureCollection con tile_id, clase, score, ndvi
```

#### `GET /api/health` — Health check

```python
# Retorna: {"status": "ok", "version": "1.0.0"}
```

### 3.4 Módulos del modelo (futuro)

#### `clip_sae.py` — CLIP + Sparse Autoencoder

```python
class SparseAutoencoder(nn.Module):
    # Linear(768 → 512) + ReLU + Linear(512 → 768)
    # Pérdida: MSE reconstrucción + λ·L1 (sparsity)
    # forward(x) → x_recon, z_latent, loss_recon, loss_l1, sparsity

class GeoVisionCLIPSAE(nn.Module):
    # SAE visual (768→512) + projection (512→256)
    # SAE textual (768→512) + projection (512→256)
    # Temperatura aprendible (init 0.07)
    # forward_visual(x) → emb_256d, loss_recon, loss_l1, sparsity
    # loss_contrastiva(emb_img, emb_txt) → InfoNCE

# Checkpoint: 640 MB en checkpoint-kaggle/clip_finetuned_best.pt
# Recall@1: 0.483, Recall@5: 1.000 (del metrics.json)
```

#### `convlstm.py` — ConvLSTM

```python
class ConvLSTMCell(nn.Module):
    # Conv2d(input_dim+hidden_dim → 4*hidden_dim, kernel=3)
    # Compuertas: input, forget, output, cell → sigmoid/tanh

class ConvLSTM(nn.Module):
    # 2 capas, hidden_dim=128, kernel=3
    # Input: (B, seq, C, H, W) → Output: (B, seq, hidden, H, W)

class GeoConvLSTM(nn.Module):
    # ConvLSTM + head Conv2d(hidden→64→9)
    # Output: (B, 3 horizontes, 3 contaminantes, H, W)
    # Sin checkpoint aún (entrenar con notebook Sit3)
```

#### `kriging.py` — ST-Kriging + Moran

```python
def st_kriging(lats, lons, times, values, q_lats, q_lons, q_t):
    # Normaliza coordenadas (evita anisotropía espuria)
    # PyKrige.OrdinaryKriging3D → variograma exponencial
    # Retorna: (valores_predichos, varianza)

def moran_global(predicciones, lats, lons):
    # libpysal.weights.DistanceBand (threshold=0.02)
    # esda.Moran → I, p_value (permutation test n=999)
    # Retorna: {I, p_value, significativo}

def moran_lisa(predicciones, lats, lons):
    # esda.Moran_Local → quadrant, p_value por punto
    # Retorna: {clusters: [{quadrant, p_value, significativo}]}
```

### 3.5 Pipeline de inferencia (futuro)

```
POST /api/predict {lat, lon, contaminante, horizonte}
  ↓
loader.obtener_tile_s2(lat, lon)          → tile 64×64 desde Zarr S2
loader.obtener_serie_s5p(lat, lon, cont)   → 8 fechas S5P desde Zarr
  ↓
clip_sae.cargar_checkpoint() → embedding 256-d
  ↓
convlstm.cargar_checkpoint() → predicción (horizonte, contaminante)
  ↓
kriging.st_kriging() → valor ± varianza
  ↓
Response {valor, varianza, latencia_ms}
```

---

## 4. Docker — Despliegue

### 4.1 Frontend Dockerfile

```dockerfile
# Etapa 1: Build de React
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Etapa 2: Nginx para servir estáticos
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# nginx.conf proxy /api/ → backend:8000
```

### 4.2 Backend Dockerfile

```dockerfile
# Etapa 1: Build de dependencias Python
FROM python:3.12-slim AS builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Etapa 2: Runtime
FROM python:3.12-slim
COPY --from=builder /app/.venv .venv/
COPY backend/ backend/
COPY dagma/ dagma/
COPY checkpoint-kaggle/ checkpoint-kaggle/
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 docker-compose.yml

```yaml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes:
      - ./checkpoint-kaggle:/app/checkpoint-kaggle
    networks: [geovision]

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]
    networks: [geovision]

networks:
  geovision: { driver: bridge }
```

---

## 5. Datos — Fuentes y formatos

| Dataset | Contenido | Formato | Tamaño | Obtención |
|---|---|---|---|---|
| DAGMA | 10 estaciones, NO₂/SO₂/O₃ horario | Parquet + CSV | ~10 MB | Local (`dagma/`) |
| Tiles CLIP | 5.000 tiles con lat/lon, clase, NDVI | Parquet | 297 KB | Kaggle (`geovision-tiles-sit2`) |
| Checkpoint CLIP | Modelo fine-tuned | .pt | 640 MB | Kaggle (`geovision-clip-modelo-v2`) |
| S5P NO₂ | Columnas troposféricas 2020-2024 | Zarr | 20.4 GB | Kaggle / HF bucket |
| S5P SO₂ | Columnas verticales 2020-2024 | Zarr | 8.1 GB | Kaggle / HF bucket |
| S5P O₃ | Columna total 2020-2024 | Zarr | 14.8 GB | Kaggle / HF bucket |
| Sentinel-2 | 13 bandas ópticas 10/20/60m | Zarr | 89.67 GB | Kaggle / HF bucket |
| ERA5 | T2m, viento, BLH, RH horario | Zarr | 4.7 GB | Kaggle / HF bucket |
| MODIS | AOD corregido (v2) | Panel | — | Kaggle (`modis-v2-panel`) |

---

## 6. Estado de implementación

| Componente | Estado | Dependencias |
|---|---|---|
| API estaciones | ✅ Completo | DAGMA parquet local |
| API tiles CLIP | ✅ Completo | tiles_meta.parquet local |
| Frontend mapa | ✅ Completo | API funcionando |
| Frontend estaciones | ✅ Completo | API + DAGMA real |
| Frontend tiles | ✅ Completo | API + tiles reales |
| API predict | 🟡 Placeholder (501) | Zarrs (83 GB) + checkpoint ConvLSTM |
| API validate | 🟡 Placeholder (501) | predict funcionando |
| API grids | 🟡 Placeholder (501) | predict/grid funcionando |
| Modelo CLIP+SAE | 🟡 Código listo, sin integrar | Checkpoint existe |
| Modelo ConvLSTM | 🟡 Código listo, sin checkpoint | Entrenar o descargar |
| Modelo Kriging | 🟡 Código listo, probado | Datos del pipeline |
| Gradiente en mapa | 🔴 No implementado | predict funcionando |
| Incertidumbre overlay | 🔴 No implementado | predict funcionando |
| Estratos | 🔴 No implementado | Datos de estratos reales |
| Descarga GeoTIFF | 🔴 No implementado | grids funcionando |
| Slider temporal | 🔴 No implementado | predict con múltiples horizontes |
| Input voz Whisper | 🔴 No implementado | — |
