# Frontend — GeoVision-CLIP

> Documentación de referencia de la estructura actual del frontend.
> **Nota:** Esto es un inventario preliminar. Se reemplazará cuando la implementación sea definitiva.

---

## Stack

| Herramienta | Versión |
|---|---|
| Vite | 5.x |
| React | 18.x |
| TypeScript | 5.5 |
| Tailwind CSS | 3.4 |
| React Router DOM | — |
| React Leaflet | — |
| Leaflet | — |

---

## Archivos raíz (`frontend/`)

### `package.json`
Manifiesto del proyecto. Define scripts (`dev`, `build`, `preview`), dependencias (React, Leaflet, React Router) y devDeps (Vite, TypeScript, Tailwind, PostCSS).

### `vite.config.ts`
Configuración de Vite: plugin React + proxy de `/api` a `http://localhost:8000` (para conectar con backend).

### `tsconfig.json`
Configuración de TypeScript: target ES2020, `jsx: react-jsx`, strict mode, `noEmit`, incluye solo `src/`.

### `tailwind.config.js`
Configuración de Tailwind. `darkMode: 'class'`. Colores personalizados para `no2` (rose), `so2` (amber), `o3` (purple) y `clip` (baja, media, alta).

### `postcss.config.js`
Pipeline PostCSS: `tailwindcss` + `autoprefixer`.

### `index.html`
Entry point HTML. Idioma español, importa CSS de Leaflet desde CDN, monta `<div id="root">` y carga `src/main.tsx`.

### `README.md`
Instrucciones rápidas de instalación y desarrollo.

---

## `src/`

### `src/main.tsx`
Punto de entrada de la app. Renderiza `<App />` en `#root` con `React.StrictMode`.

### `src/App.tsx`
Componente raíz. Configura:
- `BrowserRouter` con rutas `/` (Inicio), `/mapa` (Mapa), `/acerca` (Acerca).
- Estado de `darkMode` persistido en `localStorage`, togglea clase `.dark` en `<html>`.
- Renderiza `Navbar` + `Routes`.

### `src/index.css`
Estilos globales. Directivas Tailwind (`@tailwind base/components/utilities`) + regla para `.leaflet-container` (100% height/width).

### `src/vite-env.d.ts`
Declaración de tipos ambiente de Vite.

---

## `src/types/`

### `src/types/index.ts`
**Tipos centrales compartidos:**

| Tipo | Campos clave |
|---|---|
| `Estacion` | `id`, `nombre`, `lat`, `lon`, `altitud`, `contaminantes[]`, `no2_avg?`, `so2_avg?`, `o3_avg?` |
| `TileClip` | `tile_id`, `lat`, `lon`, `clase` (0\|1\|2), `score`, `fecha` |
| `Stats` | `promedios`, `maximos` (NO₂/SO₂/O₃), `cobertura` (Record<string, number>) |
| `FuenteInfo` | `id`, `nombre`, `periodo`, `peso_gb` |
| `EstratoInfo` | `estrato`, `no2_promedio`, `so2_promedio`, `o3_promedio`, `estaciones_cerca`, `diferencia_vs_media` |

---

## `src/data/`

### `src/data/mock.ts`
**Datos simulados para desarrollo.** Exporta:
- `estaciones: Estacion[]` — 10 estaciones DAGMA con coordenadas y promedios.
- `tilesClip: TileClip[]` — 30 tiles CLIP aleatorios con clase y score.
- `stats: Stats` — promedios, máximos y cobertura por año.
- `fuentes: FuenteInfo[]` — 6 fuentes satelitales (Sentinel-2, S5P, ERA5, MODIS).
- `estratos: EstratoInfo[]` — 6 estratos socioeconómicos con valores decrecientes de contaminación.

---

## `src/components/`

### `Navbar.tsx`
Barra de navegación fija superior. Props: `{ darkMode, toggleDarkMode }`.
- Links a Inicio, Mapa, Acerca con highlight de ruta activa (`useLocation`).
- Botón de modo oscuro/claro.
- Fondo semi-transparente con backdrop blur.

### `MapaCali.tsx`
Mapa Leaflet centrado en Cali (3.45, -76.53, zoom 11). Props: `{ estaciones, tilesClip, contaminanteActivo, mostrarEstaciones, mostrarTiles }`.
- Renderiza `TileLayer` (OpenStreetMap).
- Renderiza `EstacionMarker` por cada estación (si `mostrarEstaciones`).
- Renderiza `Rectangle` por cada tile CLIP (si `mostrarTiles`), coloreado por clase (0=verde, 1=amarillo, 2=rojo), opacidad según score.
- Renderiza `Leyenda`.

### `EstacionMarker.tsx`
Marcador circular para una estación. Props: `{ estacion, contaminanteActivo }`.
- `getValor()` extrae el valor del contaminante activo.
- `getColor()` retorna color según umbrales del contaminante.
- Popup con nombre, coordenadas, altitud, tabla de contaminantes.

### `ControlPanel.tsx`
Panel lateral izquierdo de control. Props: todas las variables de control.
- Selector de contaminante (NO₂, SO₂, O₃) en botones.
- Selector de fuente satelital (`<select>`).
- Checkboxes para capas: estaciones, tiles CLIP, estratos.
- Sección de equidad (si `mostrarEstratos`): bar chart horizontal NO₂ por estrato + ratio de inequidad.

### `StatsPanel.tsx`
Panel lateral derecho de estadísticas. Props: `{ stats, estratos, contaminanteActivo }`.
- Promedios y máximos de NO₂/SO₂/O₃.
- Cobertura anual con barras horizontales.
- Gráfico del contaminante activo por estrato (barras rojas si > promedio, verdes si <).

### `Leyenda.tsx`
Leyenda del mapa (esquina inferior izquierda). Sin props.
- Tres colores: verde (Baja), amarillo (Media), rojo (Alta).

---

## `src/pages/`

### `Inicio.tsx`
Página de aterrizaje / hero.
- Fondo gradient slate→emerald con patrón de grilla y orbes.
- Título "GeoVision-CLIP", botón CTA "Ir al mapa interactivo".
- Tres tarjetas de acceso rápido: Mapa, Datos y fuentes, Metodología.
- Footer simple.

### `Mapa.tsx`
Página principal del mapa. Orquesta `MapaCali`, `ControlPanel` y `StatsPanel`.
- Estado local: `contaminanteActivo`, `fuenteActiva`, `mostrarEstaciones`, `mostrarTiles`, `mostrarEstratos`.
- Layout 3 columnas: ControlPanel (256px) | MapaCali (flex) | StatsPanel (256px).
- Offset superior de 3.5rem por el navbar.

### `Acerca.tsx`
Página informativa. Tres secciones:
1. **Datos y fuentes** — 6 fuentes satelitales + 10 estaciones DAGMA.
2. **Metodología** — Situación 1 (panel), Situación 2 (CLIP+LoRA+SAE), Situación 3 (ConvLSTM+Kriging), Equidad espacial.
3. **Indicadores de rendimiento** — R@1 (0.483), R@5 (1.000), 89 GB panel, 10 estaciones.
