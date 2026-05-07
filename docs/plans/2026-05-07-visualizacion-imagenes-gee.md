# Visualización de Imágenes GEE para Cali

> **Para NEXUS:** Delegar la implementación a @general. El agente debe crear el script, no recibir la solución.

**Goal:** Crear un script que genere thumbnails PNG de las 6 fuentes GEE recortados a la zona de Cali, permitiendo al usuario ver visualmente cómo se ve cada dataset.

**Architecture:** Un script Python que usa `ee.Image.getThumbURL()` para generar thumbnails PNG desde el servidor de GEE, los descarga vía `urllib` (stdlib), y los guarda en un directorio de salida. Opcionalmente genera un HTML simple para verlos lado a lado. No requiere dependencias adicionales más allá de las ya instaladas (earthengine-api + stdlib).

**Tech Stack:** Python 3.12+, `earthengine-api`, `urllib` (stdlib), `json` (stdlib). Usar `uv` para ejecutar. El proyecto ya tiene `uv` como gestor.

---

### Task 1: Script de visualización de imágenes

**Files:**
- Create: `google-earth/imagenes-cali/visualizar_imagenes.py`

**Descripción del problema (sin pre-solver):**

El proyecto tiene 6 fuentes de datos GEE configuradas en `config.py` con sus bandas útiles definidas en `BANDAS_UTILES`. Los scripts existentes (`ver_archivos_cali.py`, `explorar_metadata_cali.py`) solo muestran metadatos. El usuario necesita ver visualmente cómo se ven los rasters reales de cada fuente para la zona de Cali.

**Lo que el agente debe resolver:**

1. Cómo obtener una imagen reciente representativa de cada fuente para el bounding box de Cali
2. Cómo generar thumbnails/visualizaciones que se puedan guardar como PNG y abrir localmente
3. Qué bandas seleccionar y qué parámetros de visualización usar para que cada fuente se vea bien (las bandas útiles están en `BANDAS_UTILES` en `config.py`)
4. Cómo manejar las diferencias entre fuentes: S5P son bandas únicas atmosféricas, Sentinel-2 es multi-espectral (RGB posible), ERA5 es meteorológico grillado, MODIS MAIAC es AOD
5. El script debe seguir el patrón de los scripts existentes: importar config, usar el logger del proyecto, inicializar GEE con el PROJECT_ID

**Datos disponibles:**
- `config.py`: PROJECT_ID, FUENTES, CALI (bbox [-76.60, 3.30, -76.40, 3.55]), BANDAS_UTILES, DISPONIBILIDAD, ESCALA_OVERRIDE
- `logger/`: get_logger() para logging
- `autenticacion/autenticacion.py`: ee.Authenticate()
- Dependencias en pyproject.toml: earthengine-api, xarray, xee, rioxarray, zarr, tqdm, huggingface-hub, python-dotenv
- NO hay matplotlib, geemap, ni folium instalados (el script no debe requerirlos)

**Output esperado:**
- Un script Python ejecutable con `uv run python google-earth/imagenes-cali/visualizar_imagenes.py`
- El script genera archivos PNG (uno por fuente) y los guarda en un subdirectorio (ej. `google-earth/imagenes-cali/thumbnails/`)
- Opcional: un HTML simple para visualizarlos juntos
- Las imágenes deben estar recortadas al bounding box de Cali
- Cada imagen debe tener un título o superposición indicando la fuente y fecha

**Constraints:**
- NO agregar dependencias nuevas (no matplotlib, no geemap, no folium, no pillow)
- Usar `uv run` para ejecutar
- El script debe funcionar standalone siguiendo el mismo patrón de path-hack que los otros scripts (`sys.path.insert`)
- Las imágenes deben ser ligeras (thumbnails, no descargas completas)

**Dependencies:**
- Depende de `config.py`, `logger/`, y autenticación GEE ya funcional
