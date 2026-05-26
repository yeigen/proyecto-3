# Frontend — GeoVision-CLIP Cali

## 1. Requisitos del proyecto (qué hay que visualizar)

### 1.1 Funcionalidades obligatorias (PDF pág. 10)

El PDF del proyecto exige que el frontend permita al usuario:

| # | Funcionalidad | Descripción |
|---|---|---|
| (i) | **Click en cualquier punto del mapa** | El usuario hace clic en una ubicación de Cali y obtiene la predicción de contaminantes para ese punto |
| (ii) | **Selector de contaminante y horizonte** | Controles para elegir entre NO₂, SO₂, O₃ y horizontes T+1, T+3, T+7 |
| (iii) | **9 mapas de gradiente (3×3)** | Una grilla de 3 contaminantes × 3 horizontes, con slider animado que transiciona entre T+1 → T+3 → T+7 |
| (iv) | **Capa de incertidumbre** | Opacidad superpuesta al mapa de gradiente, inversamente proporcional a la desviación estándar σ |
| (v) | **Tooltips con valor predicho ± σ** | Al pasar el mouse sobre el mapa, muestra el valor estimado y su intervalo de confianza |
| (vi) | **Descarga de predicción** | Botón para exportar el mapa actual como GeoTIFF o CSV |
| (vii) | **10 estaciones DAGMA georreferenciadas** | Marcadores en el mapa con popups que muestran datos históricos de cada estación |

### 1.2 Stack tecnológico forzoso (PDF pág. 10)

| Capa | Tecnología | Obligatorio |
|---|---|---|
| Frontend | React + Vite (o Vue 3 / Next.js) | ✅ **Sí** |
| Mapas | Leaflet centrado en Cali | ✅ **Sí** |
| Backend API | FastAPI + Uvicorn | ✅ **Sí** |
| Contenedor | Docker multi-stage | ✅ **Sí** |
| Despliegue | DigitalOcean (App Platform o Droplet) | ✅ **Sí** |

### 1.3 Prohibiciones y penalizaciones

| Prohibición | Penalización | Impacto en nota |
|---|---|---|
| Usar Streamlit o Gradio como frontend principal | −30% del componente despliegue | ≈ −3% total |
| Pasar S5P como input directo del modelo (data leakage) | −25% del proyecto | −25% total |
| MD5 del checkpoint no coincide entre integrantes | −20% del componente modelo | −2% total |
| Validación LOO-CV no realizada o filtrada | −60% del componente Sit 3 | −6% total |
| Reportar KPIs sin evidencia computacional | −50% del componente afectado | Variable |

### 1.4 Bonificaciones — seleccionadas

| Bonus | Puntos | Estado |
|---|---|---|
| **Modo oscuro** implementado en frontend | **+2 puntos** | ✅ Incluido |
| **Análisis de equidad espacial por estrato socioeconómico** | **+4 puntos** | ✅ Incluido |
| Tercer modalidad de input (audio Whisper) | +3 puntos | ❌ No aplica |
| Comparación con OMI/AURA o GOME-2 | +3 puntos | ❌ No aplica |

### 1.5 KPIs de latencia (PDF pág. 9)

| KPI | Mínimo | Excelente |
|---|---|---|
| Latencia inferencia end-to-end | **< 8 segundos** | < 3 segundos |

### 1.6 Peso en la rúbrica

| Componente | Peso |
|---|---|
| Frontend y despliegue | **10%** |
| Informe técnico | **10%** |
| Pitch y defensa (demo en vivo) | **10%** |
| **Total frontend + informe + defensa** | **30%** |

---

## 2. Stack y justificación

| Capa | Tecnología | ¿Por qué? |
|---|---|---|
| Frontend | React + Vite + TypeScript | Exigido por el PDF. Alternativas válidas: Vue 3 o Next.js |
| Mapas | Leaflet + react-leaflet | Librería de mapas liviana, sin API key, sin costos. Se integra nativamente con React |
| Backend | FastAPI (Python) | El proyecto ya usa Python (torch, numpy, xarray, zarr). FastAPI permite cargar modelos directamente sin capa intermedia. Documentación Swagger automática en `/docs` |
| Despliegue | DigitalOcean (App Platform o Droplet VPS) | Escalable, soporta Docker, precio fijo mensual |

### ¿Por qué React + Vite y no HTML vanilla?

El PDF exige explícitamente React + Vite + Leaflet. Usar Streamlit o HTML vanilla penaliza -30% del componente despliegue.

Además:
- React permite componentes reutilizables (Mapa, Slider, Tooltip, PanelControl)
- El estado global es necesario para coordinar slider temporal + capas + tooltips
- react-leaflet da wrappers declarativos para el mapa
- Vite es el build tool estándar, ultra-rápido, reemplaza a Webpack

### ¿Por qué FastAPI y no Flask?

- Async nativo: no bloquea mientras consulta modelos o datasets
- Validación automática con Pydantic (tipado fuerte en requests/responses)
- Swagger en `/docs` gratis para probar endpoints
- Rendimiento muy superior a Flask (cercano a Node.js/Go)
- Todo el stack del proyecto ya es Python

---

## 3. Sitemap y navegación

```
┌────────────────────────────────────────────────────┐
│                    NAVBAR                          │
│  [🌍 GeoVision-CLIP]  [Inicio]  [Mapa]  [Acerca]  │ ☀️/🌙
└────────────────────────────────────────────────────┘

INICIO (/)                    → Landing page
  ├── Hero: imagen satelital Cali + título + "Ir al mapa"
  ├── 3 cards de acceso rápido:
  │   ├── 🗺️  Mapa interactivo   → /mapa
  │   ├── 📊  Datos y fuentes    → /acerca#datos
  │   └── 🔬  Metodología        → /acerca#metodologia
  └── Footer con créditos

MAPA (/mapa)                  → Página principal
  ├── Leaflet (ocupa ~70% del ancho)
  │   ├── Marcadores estaciones DAGMA
  │   ├── Capa tiles CLIP coloreados por clase
  │   ├── Capa gradiente con isolíneas (Fase 2)
  │   └── Capa incertidumbre con opacidad (Fase 2)
  ├── ControlPanel (sidebar izquierdo)
  │   ├── Selector contaminante: [NO₂] [SO₂] [O₃]
  │   ├── Selector horizonte: [T+1] [T+3] [T+7]
  │   ├── Selector fuente satelital (dropdown)
  │   └── Checkbox de capas
  ├── Slider temporal animado (abajo del mapa)
  └── StatsPanel (sidebar derecho)
      ├── Promedios por contaminante y año
      ├── Valores máximos
      └── Cobertura de datos (%)

ACERCA (/acerca)              → Página informativa
  ├── El problema (contaminación en Cali)
  ├── Datos y fuentes (S2, S5P, ERA5, MODIS, DAGMA)
  ├── Metodología (CLIP + SAE + ConvLSTM + Kriging)
  └── Resultados y KPIs
```

---

## 4. Paleta de colores y diseño visual

### Paleta base

| Rol | Modo claro | Modo oscuro |
|---|---|---|
| Fondo página | `slate-50` (#f8fafc) | `slate-950` (#020617) |
| Superficie (cards, sidebar) | `white` (#ffffff) | `slate-900` (#0f172a) |
| Texto principal | `slate-900` (#0f172a) | `slate-100` (#f1f5f9) |
| Bordes y separadores | `slate-200` (#e2e8f0) | `slate-700` (#334155) |
| Primario (branding) | `emerald-600` (#059669) | `emerald-500` (#10b981) |
| Secundario (enlaces) | `sky-600` (#0284c7) | `sky-400` (#38bdf8) |

### Colores por contaminante

| Contaminante | Color |
|---|---|
| NO₂ | `rose-500` (#f43f5e) |
| SO₂ | `amber-500` (#f59e0b) |
| O₃ | `violet-500` (#8b5cf6) |

### Colores de clases CLIP (tiles)

| Clase | Color | Significado |
|---|---|---|
| Baja contaminación | `emerald-500` (#10b981) | Verde |
| Media contaminación | `amber-400` (#fbbf24) | Amarillo |
| Alta contaminación | `red-500` (#ef4444) | Rojo |

### Layout visual

```
┌─────────────────── NAVBAR ──────────────────────┐
│  🌍 GeoVision-CLIP  [Inicio] [Mapa] [Acerca]   │ ☀️/🌙
└─────────────────────────────────────────────────┘

┌─ Sidebar ─┬─────────── MAPA ───────────┬─ Panel ─┐
│           │                            │         │
│ Contami-  │   ┌─── Leaflet ────┐      │ Prom.   │
│ nante:    │   │               │      │ NO₂: X │
│  [NO₂]    │   │  🟢  🟡  🔴    │      │ SO₂: Y │
│  [SO₂]    │   │  📍 estaciones │      │ O₃:  Z │
│  [O₃]     │   │               │      │         │
│           │   └───────────────┘      │ Cobert. │
│ Horizonte │   ◀─── Slider ────▶      │ 2021:XX%│
│  [T+1]    │   T+1 ──●─── T+7        │ 2022:XX%│
│  [T+3]    │                          │         │
│  [T+7]    │                          │         │
│           │                          │         │
│ Capas:    │                          │         │
│ ☑ CLIP    │                          │         │
│ ☑ Estac.  │                          │         │
│ ☑ Grad.   │                          │         │
└───────────┴──────────────────────────┴─────────┘
```

---

## 5. Arquitectura general

```
                    DigitalOcean
┌───────────────────────────────────────────────────────┐
│                                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │         Droplet / App Platform                │     │
│  │                                               │     │
│  │  ┌─────────────────────────────────────────┐  │     │
│  │  │         Frontend React + Vite            │  │     │
│  │  │  ┌──────────┐  ┌──────────┐  ┌───────┐  │  │     │
│  │  │  │ MapaCali │  │Control-  │  │ Stats │  │  │     │
│  │  │  │ (Leaflet)│  │Panel     │  │ Panel │  │  │     │
│  │  │  └────┬─────┘  └────┬─────┘  └───┬───┘  │  │     │
│  │  │       │             │            │       │  │     │
│  │  │       └─────────────┼────────────┘       │  │     │
│  │  │                     │ fetch / axios       │  │     │
│  │  └─────────────────────┼───────────────────┘  │     │
│  │                        │ HTTP (puerto 8000)   │     │
│  │  ┌─────────────────────┼───────────────────┐  │     │
│  │  │         FastAPI Backend                  │  │     │
│  │  │                                          │  │     │
│  │  │  GET /api/estaciones  ─── estaciones.csv │  │     │
│  │  │  GET /api/tiles-clip  ─── tiles + CLIP   │  │     │
│  │  │  GET /api/stats       ─── resumen.csv    │  │     │
│  │  │  GET /api/panel-info  ─── manifest.json  │  │     │
│  │  │  POST /api/predict    ─── ConvLSTM (S3)  │  │     │
│  │  │  POST /api/validate   ─── Kriging (S3)   │  │     │
│  │  │                                          │  │     │
│  │  │  ┌────────────────────┐                  │  │     │
│  │  │  │ clip_finetuned_best│  ← checkpoint    │  │     │
│  │  │  │ .pt (611 MB en    │      cargado en   │  │     │
│  │  │  │  RAM)             │      memoria      │  │     │
│  │  │  └────────────────────┘                  │  │     │
│  │  └──────────────────────────────────────────┘  │     │
│  │                                               │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 6. Endpoints del backend

### Fase 1 — Con datos actuales (construible hoy)

| Endpoint | Método | Respuesta | ¿Qué hace el frontend con esto? |
|---|---|---|---|
| `GET /api/estaciones` | JSON | `[{id, nombre, lat, lon, altitud, contaminantes}]` | Dibuja marcadores en el mapa. Al hacer click, muestra tooltip con valores históricos |
| `GET /api/tiles-clip` | JSON | `[{tile_id, lat, lon, clase, score, fecha}]` | Pinta polígonos 64×64px en el mapa. Color según clase: verde=baja, amarillo=media, rojo=alta |
| `GET /api/stats` | JSON | `{promedios, maximos, cobertura}` | Panel lateral derecho con resumen rápido de contaminación por año |
| `GET /api/panel-info` | JSON | `{fuentes, rango_temporal, pesos}` | Selector de fuente satelital. El usuario elige qué capa ver (S2, S5P, ERA5, MODIS) |
| `GET /api/imagenes` | JSON | `[{url, titulo, fuente}]` | Galería de PNGs pre-renderizados de evidencias |

### Fase 2 — Cuando Sit 3 esté listo

| Endpoint | Método | Entrada | Respuesta | ¿Qué hace el frontend? |
|---|---|---|---|---|
| `POST /api/predict` | JSON | `{lat, lon, fecha, contaminante}` | `{valor, confianza, intervalo}` | Genera mapa de gradiente (isolineas) sobre el área de Cali. El slider temporal cambia la fecha y vuelve a consultar |
| `POST /api/validate` | JSON | `{lat, lon, fecha, valor_real}` | `{error, r², observaciones}` | Tooltip extendido que compara predicción vs valor real de estación |

---

## 7. Flujo de datos completo

```
Kaggle Dataset (juanjoseorozcolopez/geovision-fuentes)
 └── Zarr (S2, S5P, ERA5, MODIS) → 89 GB, no se sirve directo
     └── metadata extraída → CSVs locales → backend → API → frontend

Kaggle Dataset (edwardsx/geovision-clip-modelo-v2)
 └── clip_finetuned_best.pt → backend lo carga en RAM → clasifica tiles → API

CSVs locales (repositorio)
 ├── estaciones_metadata.csv    → 10 estaciones DAGMA
 ├── resumen_contaminantes.csv  → estadísticas por contaminante
 └── tiles_meta.parquet         → metadatos de 5,000 tiles

Frontend React
 ├── fetch("/api/estaciones")   → pinta marcadores
 ├── fetch("/api/tiles-clip")   → pinta capa CLIP
 ├── fetch("/api/stats")        → llena panel lateral
 └── fetch("/api/panel-info")   → llena selector de fuentes
```

---

## 8. Estructura de carpetas

```
proyecto-3/
├── frontend/                          ← App React + Vite
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapaCali.tsx           → Mapa Leaflet centrado en [3.45, -76.53]
│   │   │   │                            Usa MapContainer, TileLayer de react-leaflet
│   │   │   │                            Renderiza EstacionMarker y TileLayerClip
│   │   │   │
│   │   │   ├── ControlPanel.tsx       → Selectores: fuente satelital, fecha, capa
│   │   │   │                            Cada cambio dispara fetch al backend
│   │   │   │
│   │   │   ├── EstacionMarker.tsx     → Marcador circular coloreado por nivel
│   │   │   │                            Popup con nombre, contaminantes, valores
│   │   │   │
│   │   │   ├── TileLayerClip.tsx      → Capa de rectángulos 64×64px
│   │   │   │                            Color = clase CLIP (verde/amarillo/rojo)
│   │   │   │                            Opacidad = score de confianza
│   │   │   │
│   │   │   ├── GradientMap.tsx        → Capa de isolíneas de gradiente (Fase 2)
│   │   │   │                            Se superpone al mapa base
│   │   │   │
│   │   │   ├── UncertaintyOverlay.tsx → Capa de opacidad = 1/σ (Fase 2)
│   │   │   │                            Se renderiza sobre GradientMap
│   │   │   │
│   │   │   ├── Leyenda.tsx            → Rectángulo explicativo: colores = clases
│   │   │   │                            Se renderiza sobre el mapa en esquina
│   │   │   │
│   │   │   ├── SliderTemporal.tsx     → Input range animado T+1 / T+3 / T+7 (Fase 2)
│   │   │   │                            Al soltar, llama POST /api/predict
│   │   │   │
│   │   │   └── StatsPanel.tsx         → Panel fijo lado derecho
│   │   │                                Promedios, máximos, cobertura por año
│   │   │
│   │   ├── pages/
│   │   │   ├── Inicio.tsx            → Landing page: hero + 3 cards de acceso
│   │   │   ├── Mapa.tsx              → Página principal con el dashboard completo
│   │   │   └── Acerca.tsx            → Página informativa del proyecto
│   │   │
│   │   ├── api/
│   │   │   └── client.ts             → Funciones fetch tipadas
│   │   │                                getEstaciones(), getTilesClip(), getStats()
│   │   │                                postPredict(lat, lon, fecha)
│   │   │
│   │   ├── types/
│   │   │   └── index.ts              → Interfaces TypeScript
│   │   │                                Estacion, TileClip, Stats, Prediccion
│   │   │
│   │   ├── App.tsx                    → Layout: Navbar + Router + Footer
│   │   └── main.tsx                   → Entry point, renderiza <App />
│   │
│   ├── package.json                   → react, react-leaflet, leaflet, axios, recharts
│   ├── vite.config.ts                 → proxy /api → http://localhost:8000
│   ├── tailwind.config.js             → Paleta de colores, modo oscuro
│   ├── tsconfig.json
│   └── Dockerfile.frontend
│
├── backend/                           ← API FastAPI
│   ├── main.py                        → Crea app FastAPI, monta routers
│   │                                    Carga clip_finetuned_best.pt al iniciar
│   │                                    CORS activado para frontend
│   │
│   ├── routers/
│   │   ├── estaciones.py              → GET /api/estaciones
│   │   │                                Lee estaciones_metadata.csv, devuelve JSON
│   │   ├── tiles.py                   → GET /api/tiles-clip
│   │   │                                Lee tiles_meta.parquet, ejecuta CLIP, devuelve clase + score
│   │   ├── stats.py                   → GET /api/stats
│   │   │                                Lee resumen_contaminantes.csv, agrega por año
│   │   ├── predict.py                 → POST /api/predict (placeholder)
│   │   │                                Fase 1: devuelve {"status": "pendiente"}
│   │   │                                Fase 2: carga ConvLSTM + Kriging
│   │   └── validate.py                → POST /api/validate (placeholder)
│   │                                   Fase 1: devuelve {"status": "pendiente"}
│   │                                   Fase 2: ejecuta Kriging LOO-CV
│   │
│   ├── models/
│   │   └── clip_model.py             → Carga clip_finetuned_best.pt
│   │                                    Wrapper: preprocesa tile, devuelve embedding + clase
│   │
│   ├── data/                          → CSVs y metadatos locales
│   │   ├── estaciones_metadata.csv
│   │   ├── tiles_meta.parquet
│   │   └── resumen_contaminantes.csv
│   │
│   ├── requirements.txt              → fastapi, uvicorn, torch, pandas, pyarrow, zarr, gcsfs
│   └── Dockerfile.backend
│
├── docker-compose.yml                → Orquesta backend + frontend
└── docs/
    └── FRONTEND.md                    ← Este documento
```

---

## 9. Componentes React explicados

### Inicio.tsx (página)

Landing page del proyecto. Contiene:
- **Hero section**: imagen de fondo satelital de Cali, título "GeoVision-CLIP Cali", subtítulo explicativo, botón "Ir al mapa"
- **3 cards** con íconos que enlazan a:
  - Mapa interactivo (`/mapa`)
  - Datos y fuentes (`/acerca#datos`)
  - Metodología (`/acerca#metodologia`)
- **Footer** con créditos del equipo

### Mapa.tsx (página)

Página principal del dashboard. Layout de 3 columnas: sidebar izquierdo (controles) + mapa central + sidebar derecho (stats).

### Acerca.tsx (página)

Página informativa con secciones apiladas verticalmente. Cada sección es un card expandible.

### MapaCali.tsx

- Contenedor principal del mapa usando `<MapContainer>` de react-leaflet
- Centro: `[3.45, -76.53]`, zoom 11
- Capa base: OpenStreetMap (TileLayer gratuito)
- Renderiza hijos: `EstacionMarker[]`, `TileLayerClip`, `GradientMap`, `UncertaintyOverlay`, `Leyenda`
- Escucha cambios en `ControlPanel` para actualizar capas

### EstacionMarker.tsx

- Recibe prop `estacion: Estacion`
- Renderiza `<CircleMarker>` con radio fijo, color según contaminante seleccionado
- Escala de colores: verde (bajo), amarillo (medio), naranja (alto), rojo (crítico)
- `<Popup>` con nombre de estación, coordenadas, tabla de valores históricos
- Al hacer click, opcionalmente dispara `POST /api/predict` con esas coordenadas

### TileLayerClip.tsx

- Recibe prop `tiles: TileClip[]`
- Renderiza `<Rectangle>` por cada tile (64×64 px en coordenadas reales)
- Color de relleno según `tile.clase`: 0=verde (baja contaminación), 1=amarillo (media), 2=rojo (alta)
- Opacidad según `tile.score` (confianza del modelo CLIP)
- Al hacer click, muestra popup con fecha, clase, score

### GradientMap.tsx (Fase 2)

- Recibe prop `grid: number[][]` del endpoint `/api/predict`
- Renderiza isolíneas de gradiente sobre el mapa usando canvas de Leaflet
- Colores interpolados según la escala del contaminante activo

### UncertaintyOverlay.tsx (Fase 2)

- Recibe prop `sigma: number[][]` del endpoint `/api/predict`
- Renderiza una capa semitransparente donde opacidad = 1 − σ/σ_max
- A mayor incertidumbre, más transparente (menos opacidad) → zonas confiables se ven más sólidas

### ControlPanel.tsx

- Selector de contaminante: 3 botones tipo pill [NO₂] [SO₂] [O₃]
- Selector de horizonte: 3 botones tipo pill [T+1] [T+3] [T+7]
- Dropdown de fuentes satelitales: "S2", "S5P NO₂", "S5P SO₂", "S5P O₃", "ERA5", "MODIS"
- Checkbox para mostrar/ocultar: CLIP, Estaciones, Gradiente, Incertidumbre
- Botón "Descargar" que dispara GET /api/geotiff
- Cada cambio actualiza el estado global y los componentes hijos se re-renderizan

### SliderTemporal.tsx (Fase 2)

- Input range con 3 posiciones: T+1, T+3, T+7
- Botón de reproducción ▶ que anima automáticamente entre los 3 horizontes
- Al soltar o al cambiar, llama `POST /api/predict` con el horizonte seleccionado
- Mientras carga, muestra spinner sobre el mapa

### StatsPanel.tsx

- Panel fijo en lado derecho del viewport
- Muestra: promedios anuales por contaminante, valores máximos, cobertura de datos (%)
- Datos de `/api/stats` se cargan al montar el componente
- Diseño responsivo: en móvil se oculta y se muestra como drawer

---

## 10. Análisis de equidad espacial por estrato socioeconómico (bonus +4 pts)

### ¿Qué es?

El análisis de equidad espacial evalúa si la contaminación del aire en Cali afecta desproporcionadamente a los estratos socioeconómicos más bajos. Se cruzan las predicciones del modelo (o datos observados DAGMA) con los polígonos de estratificación oficial de Cali (estratos 1 al 6) para determinar:

- ¿Respiran peor los estratos bajos que los altos?
- ¿Hay clustering espacial de contaminación sobre zonas vulnerables?
- ¿Las estaciones de monitoreo cubren equitativamente todos los estratos?

### Datos necesarios

| Dato | Formato | Origen |
|---|---|---|
| Polígonos de estratificación de Cali | GeoJSON | DANE / Planeación Municipal (público) |
| Predicciones del modelo | Grid GeoTIFF | `POST /api/predict` o datos pre-computados |
| Observaciones DAGMA | CSV/Parquet | `dagma/dagma_cvc_horario_raw.parquet` |

### Endpoint nuevo

| Endpoint | Método | Respuesta | ¿Qué hace? |
|---|---|---|---|
| `GET /api/estratos` | JSON | GeoJSON con polígonos de estratos + estadísticas de contaminación por estrato | El frontend pinta cada polígono con color según nivel de contaminación promedio |

### Cómo funciona el análisis

```
Capa de estratos (GeoJSON)
       │
       ▼
Superponer grid de predicciones o datos de estaciones DAGMA
       │
       ▼
Para cada polígono de estrato:
  ├── Calcular promedio de contaminante (NO₂, SO₂, O₃)
  ├── Calcular percentiles (p25, p50, p75, p95)
  └── Contar estaciones DAGMA dentro del polígono
       │
       ▼
Comparar entre estratos 1-2-3 vs 4-5-6
       │
       ▼
Visualizar en mapa + tabla comparativa + indicador de inequidad
```

### Componente nuevo: EstratosLayer.tsx

- Recibe prop `estratos: GeoJSON` del endpoint `/api/estratos`
- Renderiza cada polígono de estrato con color interpolado:
  - Más rojo = mayor contaminación promedio
  - Más verde = menor contaminación promedio
- Opacidad fija 0.5 para ver el mapa base debajo
- Al hacer click en un polígono, popup con:
  - Número de estrato (1-6)
  - Contaminante promedio (NO₂, SO₂, O₃)
  - Comparación con el promedio de Cali
- Toggle en ControlPanel: checkbox "Estratos" para mostrar/ocultar

### Componente nuevo: EquityPanel.tsx

Panel lateral adicional (o integrado en StatsPanel) que muestra:

| Indicador | Descripción |
|---|---|
| Promedio NO₂ por estrato | Gráfico de barras, estratos 1-6 en eje X |
| Promedio SO₂ por estrato | Ídem |
| Promedio O₃ por estrato | Ídem |
| Diferencia estrato 1 vs 6 | "En estrato 1 se respira X% más NO₂ que en estrato 6" |
| Índice de inequidad | (promedio estrato 1) / (promedio estrato 6) |
| Cobertura de estaciones | Cuántas estaciones DAGMA hay en cada estrato |

### Cómo se integra en la navegación

- Desde el **ControlPanel** se agrega checkbox `☐ Estratos`
- Al activarlo, se superpone la capa de polígonos de estratos en el mapa
- El **StatsPanel** se expande con una pestaña "Equidad" que muestra EquityPanel
- En la página **Acerca** se agrega sección "Equidad espacial" explicando la metodología

### Endpoint nuevo en backend

```python
# backend/routers/estratos.py
GET /api/estratos
  → Lee GeoJSON de estratos de Cali (archivo local o URL pública)
  → Cruza con datos de contaminación (desde CSVs o modelo)
  → Devuelve GeoJSON con propiedades enriquecidas:
      {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "geometry": { ... },
            "properties": {
              "estrato": 3,
              "no2_promedio": 12.5,
              "so2_promedio": 3.1,
              "o3_promedio": 45.2,
              "estaciones_cerca": 1,
              "diferencia_vs_media": -0.15
            }
          }
        ]
      }
  → Se registra en main.py como router adicional
```

## 11. Datos que consume cada componente

| Componente | Datos | Formato | Origen |
|---|---|---|---|
| MapaCali | Mapa base | Tile URL | OpenStreetMap (CDN gratis, sin API key) |
| EstacionMarker[] | Lat, lon, nombre, contaminantes | JSON | `GET /api/estaciones` ← `estaciones_metadata.csv` |
| TileLayerClip | Centroide, clase (0/1/2), score | JSON | `GET /api/tiles-clip` ← `tiles_meta.parquet` + CLIP |
| GradienteMap | Grid de valores predichos | JSON | `POST /api/predict` ← ConvLSTM + Kriging |
| UncertaintyOverlay | Grid de desviación σ | JSON | `POST /api/predict` ← ConvLSTM + Kriging |
| StatsPanel | Promedios, máximos, cobertura | JSON | `GET /api/stats` ← `resumen_contaminantes.csv` |
| ControlPanel | Fuentes disponibles, rango temporal | JSON | `GET /api/panel-info` ← `manifest.json` |
| SliderTemporal (F2) | Horizontes disponibles | - | Fijo: T+1, T+3, T+7 |
| EstratosLayer | GeoJSON con estadísticas por estrato | JSON | `GET /api/estratos` ← GeoJSON + cruce con datos |
| EquityPanel | Indicadores de inequidad por estrato | JSON | `GET /api/estratos` (properties) |

---

## 12. Estado del proyecto: ¿qué se puede construir hoy?

### Listo para construir ahora (Fase 1)

| Componente | Estado | Dependencias |
|---|---|---|
| `GET /api/estaciones` | ✅ Datos locales en `dagma/estaciones_metadata.csv` | Ninguna |
| `GET /api/stats` | ✅ Datos locales en `csv/dagma/resumen_contaminantes.csv` | Ninguna |
| `GET /api/panel-info` | ✅ Datos locales en `manifest/manifest_output/manifest.json` | Ninguna |
| `GET /api/tiles-clip` | ⚠️ Datos en Kaggle (`edwardsx/geovision-tiles-sit2`). Hay que descargarlos al backend | Descargar ~229 MB |
| Mapa Leaflet con estaciones | ✅ Solo depende de `/api/estaciones` | Ninguna |
| Marcadores con tooltips | ✅ Solo depende de `/api/estaciones` | Ninguna |
| Capa de tiles CLIP | ✅ Depende de `/api/tiles-clip` (con datos descargados) | Descargar tiles de Kaggle |
| Panel lateral stats | ✅ Solo depende de `/api/stats` | Ninguna |
| Selector de fuente | ✅ Solo depende de `/api/panel-info` | Ninguna |
| Landing page (Inicio) | ✅ Solo HTML + CSS | Ninguna |
| Página Acerca | ✅ Solo HTML + CSS | Ninguna |
| Navbar con modo oscuro | ✅ Solo CSS + estado React | Ninguna |
| Capa de estratos en mapa | ⚠️ Pendiente de conseguir GeoJSON de estratos de Cali (fuente: DANE/Planeación Municipal) | Buscar o descargar datos públicos |
| EquityPanel con indicadores | ⚠️ Depende de capa de estratos + datos de contaminación | Tener GeoJSON + CSVs |

### Pendiente de Sit 3 (ConvLSTM + Kriging)

| Componente | Bloqueado por | Alternativa mientras tanto |
|---|---|---|
| `POST /api/predict` | ConvLSTM entrenado y funcionando | Placeholder que devuelve `{"status": "pendiente"}` |
| `POST /api/validate` | Kriging con LOO-CV funcionando | Placeholder que devuelve `{"status": "pendiente"}` |
| GradientMap | POST /api/predict devolviendo grid | No mostrar o mostrar datos DAGMA interpolados simple |
| UncertaintyOverlay | POST /api/predict devolviendo σ | No mostrar |
| SliderTemporal animado | POST /api/predict por horizonte | Dropdown de fechas con datos observados (no predichos) |
| Descarga GeoTIFF/CSV | POST /api/predict generando archivos | Botón deshabilitado con tooltip "Próximamente" |

---

## 13. Despliegue

### Desarrollo local

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# Abre http://localhost:5173
```

### Producción (DigitalOcean)

**Opción A — Droplet VPS (recomendado, más control)**
- Un servidor Ubuntu con Docker y docker-compose
- Frontend React (puerto 5173) + Backend FastAPI (puerto 8000)
- Nginx como proxy reverso (puerto 80/443)
- Certbot para HTTPS gratis

```bash
# 1. Crear Droplet Ubuntu 22.04 (plan básico $4/mes)
# 2. Conectar por SSH e instalar Docker
ssh root@<droplet-ip>
apt update && apt install -y docker.io docker-compose certbot nginx

# 3. Clonar el repo
git clone <repo-url>
cd proyecto-3

# 4. Construir y levantar
docker-compose up --build -d

# 5. Configurar Nginx como proxy reverso
#    /etc/nginx/sites-available/geovision
#    → frontend.react:5173, backend.api:8000

# 6. Certbot para HTTPS
certbot --nginx -d geovision-cali.com
```

**Opción B — DigitalOcean App Platform (serverless)**
- Backend: componente de servicio Docker, arranca con `uvicorn main:app`
- Frontend: componente estático, `npm run build` → carpeta `dist/`
- Conectar repositorio GitHub, despliegue automático en cada push
- HTTPS incluido, dominio personalizable


---

## 14. Dependencias

### Backend (`requirements.txt`)
```
fastapi
uvicorn[standard]
torch
pandas
pyarrow
zarr
gcsfs
kagglehub
python-multipart
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18",
    "react-leaflet": "^4",
    "leaflet": "^1.9",
    "axios": "^1",
    "react-router-dom": "^6"
  },
  "devDependencies": {
    "@types/leaflet": "^1",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "postcss": "^8",
    "typescript": "^5",
    "vite": "^5"
  }
}
```

---

## 15. Resumen

| Aspecto | Estado |
|---|---|
| Stack definido | ✅ React + Vite + Tailwind + Leaflet + FastAPI |
| Paleta de colores | ✅ Definida: slate/emerald/sky, colores por contaminante |
| Navegación | ✅ 3 páginas: Inicio, Mapa, Acerca |
| Modo oscuro | ✅ Incluido (+2 pts bonus) |
| Equidad espacial por estrato | ✅ Incluido (+4 pts bonus) |
| Datos de estaciones | ✅ Listos |
| Datos de tiles | ✅ Listos (descargar de Kaggle) |
| Estadísticas | ✅ Listas |
| Checkpoint CLIP | ✅ `clip_finetuned_best.pt` en Kaggle (611 MB) |
| Endpoints predict/validate | ❌ Pendiente de Sit 3 |
| Gradiente + incertidumbre | ❌ Pendiente de Sit 3 |
| Slider temporal animado | ❌ Pendiente de Sit 3 |
| **% construible hoy** | **~70% del frontend funcional** |
