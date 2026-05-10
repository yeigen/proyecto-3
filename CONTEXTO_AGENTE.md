# Contexto completo — GeoVision-CLIP Cali

**Fecha**: 2026-05-10 ~22:30
**Objetivo del agente**: Conectarse al droplet, revisar el pipeline S2→Zarr, verificar bucket GCS, y determinar si hay que arreglar algo o está todo correcto.

---

## 1. Acceso al droplet

```bash
ssh root@192.241.132.222
```

El droplet es un DigitalOcean de 4 vCPU, 8 GB RAM, 160 GB disco. Ubuntu 24.04.

## 2. Proyecto local vs droplet

El proyecto está en dos ubicaciones:

| Ubicación | Ruta | Sincronizado |
|-----------|------|-------------|
| **Local** | `/home/yeigen/Documents/proyecto-3` | Git (main) |
| **Droplet** | `/root/proyecto-3` | Copia manual, NO sincronizada con git |

La versión canónica del código está en local. El droplet solo ejecuta el pipeline.

### Estructura del proyecto (local)

```
proyecto-3/
├── google-earth/
│   ├── config.py              ← CALI bbox, PROJECT_ID, FUENTES, BANDAS_UTILES
│   ├── autenticacion/
│   ├── imagenes-cali/         ← scripts EDA + visualizaciones
│   │   ├── imagenes-reales/   ← PNG generados por fuente
│   │   ├── visualizar_imagenes.py
│   │   ├── calcular_peso_cali.py
│   │   └── ver_archivos_cali.py
│   └── imagenes-globales/
├── gcp/
│   ├── exportar_s2.py         ← descarga S2 de GEE a GCS
│   ├── exportar_s5p_no2.py    ← descarga S5P NO2
│   ├── exportar_s5p_so2.py
│   ├── exportar_s5p_o3.py
│   ├── exportar_era5.py
│   ├── exportar_modis.py
│   └── zarr/
│       ├── s2_a_zarr.py       ← S2 GeoTIFF → Zarr (EJECUTANDOSE AHORA)
│       ├── s5p_no2_a_zarr.py
│       ├── s5p_so2_a_zarr.py
│       ├── s5p_o3_a_zarr.py
│       ├── era5_a_zarr.py
│       └── modis_a_zarr.py
├── hugging-face/
│   └── staging/               ← metadata stubs de HF (NO datos reales)
├── docs/
│   ├── conceptos/
│   │   └── geotiff-vs-zarr.md ← comparativa técnica con referencias verificadas
│   ├── DATASETS.md            ← documentación de las 6 fuentes
│   ├── PESOS_PIPELINE.md      ← pesos reales por etapa
│   ├── EDA_VISUALIZACION.md   ← guía EDA + verificación coherencia
│   ├── JUSTIFICACION_FORMATO.md
│   ├── REFERENCIAS.md
│   ├── CRUCE_FUENTES_PDF.txt  ← comparación PDF vs implementación
│   └── plans/
├── proyecto/
│   └── ProyectoFinal_GeoVisionCLIP_Cali.pdf  ← PDF asignatura
├── pyproject.toml
└── .env                       ← HF_TOKEN
```

## 3. Configuración clave (`google-earth/config.py`)

```python
CALI = [-76.65, 3.30, -76.30, 3.65]  # ~39×39 km, 1515 km²
PROJECT_ID = 'proyecto-analitica-3-495618'

FUENTES = [
    'COPERNICUS/S5P/OFFL/L3_NO2',
    'COPERNICUS/S5P/OFFL/L3_SO2',
    'COPERNICUS/S5P/OFFL/L3_O3',
    'COPERNICUS/S2_SR_HARMONIZED',
    'ECMWF/ERA5/HOURLY',           # Atmosférico, NO ERA5-Land (tiene BLH y RH)
    'MODIS/061/MCD19A2_GRANULES'
]

BANDAS_UTILES = {
    'COPERNICUS/S2_SR_HARMONIZED': ['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B11','B12','SCL'],
    'COPERNICUS/S5P/OFFL/L3_NO2': ['tropospheric_NO2_column_number_density', 'NO2_column_number_density', 'cloud_fraction'],
    'COPERNICUS/S5P/OFFL/L3_SO2': ['SO2_column_number_density', 'cloud_fraction'],
    'COPERNICUS/S5P/OFFL/L3_O3':  ['O3_column_number_density', 'cloud_fraction'],
    'ECMWF/ERA5/HOURLY': ['temperature_2m','dewpoint_temperature_2m','u_component_of_wind_10m','v_component_of_wind_10m','boundary_layer_height','relative_humidity_850hPa','surface_pressure','total_precipitation'],
    'MODIS/061/MCD19A2_GRANULES': ['Optical_Depth_047','Optical_Depth_055','Column_WV','AOD_QA'],
}
```

**ERA5 vs ERA5-Land**: El PDF pide ERA5-Land pero ese dataset no tiene `boundary_layer_height` ni `relative_humidity`. Usamos ERA5 atmosférico (28 km en vez de 9 km) para tener BLH, que es la variable meteorológica más importante para modelado de dispersión.

## 4. Bucket GCS

```
Bucket: gs://fuentes-proyecto-3
Proyecto GCP: proyecto-analitica-3-495618
```

### Estructura

```
gs://fuentes-proyecto-3/
├── copernicus_s2_sr_harmonized/
│   ├── raw/                    ← 19,400 GeoTIFFs (1 por imagen×banda), 76.99 GB total
│   └── panel.zarr/             ← Zarr 4D (time,band,y,x), escribiendo ahora
│       ├── .zgroup, .zattrs
│       ├── data/               ← chunks 0.0.0.0 a ~31.0.4.4 (21.2 GB hasta ahora)
│       ├── band/
│       ├── time/
│       ├── y/
│       └── x/
├── copernicus_s5p_offl_l3_no2/
│   └── raw/                    ← 25,592 GeoTIFFs, ~0.04 GB
├── copernicus_s5p_offl_l3_so2/
│   └── raw/                    ← 25,830 GeoTIFFs, ~0.04 GB
├── copernicus_s5p_offl_l3_o3/
│   └── raw/                    ← 25,717 GeoTIFFs, ~0.06 GB
├── ecmwf_era5_hourly/
│   └── raw/                    ← 34,499 GeoTIFFs, ~0.09 GB
└── modis_061_mcd19a2_granules/
    └── raw/                    ← ~28,450 GeoTIFFs, ~0.02 GB
```

**Peso total GeoTIFF: 77.23 GB** (umbral PDF: ≥50 GB ✅)

### Zarrs listos (en staging del droplet, NO en GCS)

Los Zarr de S5P NO2, SO2, O3, ERA5 y MODIS están construidos en el droplet:

```
/root/proyecto-3/hugging-face/staging/
├── S5P_NO2/panel.zarr/         ← 25,808 archivos, 145 MB
├── S5P_SO2/panel.zarr/
├── S5P_O3/panel.zarr/          ← 134 MB
└── ERA5/panel.zarr/            ← 54,066 archivos, 218 MB
```

Falta subirlos al bucket HF con `hf buckets sync`.

## 5. Pipeline S2 → Zarr (en ejecución)

### Comando

```bash
cd /root/proyecto-3
nohup /root/proyecto-3/.venv/bin/python gcp/zarr/s2_a_zarr.py --batch-size 5 \
  > s2_zarr_run.log 2>&1 &
```

**PID actual**: 3187819

### Parámetros

| Parámetro | Valor | Nota |
|-----------|-------|------|
| batch_size | 5 | = TIME_CHUNK |
| TIME_CHUNK | 5 | |
| Y_CHUNK | 974 | |
| X_CHUNK | 974 | |
| BAND_CHUNK | 13 (todas) | |
| Compresor | blosc/zstd/c5/bitshuffle | |
| Workers | 2 (ThreadPoolExecutor) | |
| Origen | `gs://fuentes-proyecto-3/copernicus_s2_sr_harmonized/raw/*.tif` | |
| Destino | `gs://fuentes-proyecto-3/copernicus_s2_sr_harmonized/panel.zarr/` | |

### Progreso (último check ~22:25)

```
Batches completados: 193 de 311 (62.1%)
Tiempo transcurrido: 6h 48min
Ritmo:              ~2.1 min/batch
ETA:                ~4 horas → ~2:30 AM
Peso en GCS:        21.18 GB (1,998 data chunks)
RAM proceso (RSS):  4.92 GB
RAM libre sistema:  2.6 GB
CPU:                70.8%
Errores:            0
OOM kills:          0 (en este intento)
```

### Historial de OOM kills

Hubo 3 intentos anteriores que murieron por OOM (consumían 7+ GB RSS sobre 7.8 GB total):
- PID 3167171: RSS 7.68 GB, matado
- PID 3169172: RSS 7.74 GB, matado
- PID 3173905: RSS 7.17 GB, matado

El intento actual (4º) usa `batch_size=5` y tiene `gc.collect()` entre batches. Está estable.

### Log

```bash
# Ultimas lineas (desde droplet)
tail -20 /root/proyecto-3/s2_zarr_run.log

# Progreso completo (desde droplet)
grep 'escrito' /root/proyecto-3/s2_zarr_run.log | wc -l
```

### Cómo verificar estado (comandos útiles en el droplet)

```bash
# Proceso vivo?
ps -p 3187819 -o pid,pcpu,rss,etime,args

# Memoria
free -h

# Ultimo batch escrito
grep 'escrito' /root/proyecto-3/s2_zarr_run.log | tail -1

# Total batches completados
grep 'Lote.*escrito' /root/proyecto-3/s2_zarr_run.log | wc -l

# Chunks en GCS (requiere Python en droplet)
cd /root/proyecto-3 && .venv/bin/python -c "
import sys; sys.path.insert(0,'google-earth')
from config import PROJECT_ID
from google.cloud import storage
c = storage.Client(project=PROJECT_ID)
b = c.bucket('fuentes-proyecto-3')
data = [x for x in b.list_blobs(prefix='copernicus_s2_sr_harmonized/panel.zarr/data/', max_results=5000) if not x.name.endswith(('.zarray','.zattrs'))]
print(f'Chunks: {len(data)} | Peso: {sum(x.size for x in data)/1024**3:.2f} GB')
"
```

## 6. Coherencia GeoTIFF ↔ Zarr (VERIFICADA)

Probada píxel a píxel en 3 fuentes el 2026-05-10:

| Fuente | Pixeles comparados | Diff max | Veredicto |
|--------|-------------------|----------|-----------|
| S2 (B1, img 20210103) | 2,354,710 | 0.000000 | Idéntico |
| S5P NO2 (img 20240715) | 1,203 | 2e-12 | Idéntico (ruido float64) |
| ERA5 (img 20210211) | 32 | 0.000000 | Idéntico |

La conversión es lossless. No hay que arreglar nada.

## 7. PDF de la asignatura — Situación 1

El PDF (`proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf`) pide para Situación 1:

1. ✅ Credenciales GEE + CDSE
2. ✅ Pipeline descarga distribuido (Dask/Spark — GEE batch export paralelo)
3. ✅ Recorte HARP sobre S5P (BBox Cali en export_*.py)
4. 🔄 Conversión a Zarr (S2 en progreso, resto listo en staging)
5. ✅ Persistencia en GCS (6 fuentes, 77 GB GeoTIFFs)
6. ⏳ Manifest JSON con MD5 (post-conversión)
7. ✅ EDA con 8+ visualizaciones (PNGs generados, Zarr EDA documentado)

**Umbral ≥50 GB**: cumplido con 77 GB solo en GeoTIFFs (54% margen).

## 8. Decisiones técnicas documentadas

| Decisión | Justificación | Documento |
|----------|--------------|-----------|
| ERA5 atmosférico, no ERA5-Land | BLH y RH no existen en ERA5-Land | CRUCE_FUENTES_PDF.txt |
| 13 bandas S2 (B1+SCL extra) | PDF pide B2-B12 (11), completamos a 13 | BANDAS_JUSTIFICACION.md |
| BBox CALI expandido vs PDF | Cubre Yumbo+Acopi+caña, no solo municipio | DATASETS.md |
| Formato dual GeoTIFF+Zarr | GeoTIFF=source-of-truth, Zarr=vista analítica | JUSTIFICACION_FORMATO.md |
| Chunks (5,13,974,974) | Optimizado para LSTM y Kriging | conceptos/geotiff-vs-zarr.md |
| Resampleo S2 a 10m | Todas las bandas alineadas para ViT-CLIP | DATASETS.md |

## 9. Lo que NO hay que tocar

- **El proceso S2→Zarr en el droplet** (PID 3187819). NO matarlo. Se lanzó con `nohup`, no con `screen`. Si se cae la sesión SSH, sigue corriendo.
- **El bucket GCS**. Los datos están correctos y verificados.
- **Los Zarrs en staging**. Están listos, solo falta upload a HF.
- **Los .env y credenciales**. HF_TOKEN, ADC de GCP — configurados y funcionando.

## 10. Si el agente necesita arreglar algo

Escenarios posibles y qué hacer:

### Si el pipeline S2 falló (OOM u otro error)
```bash
# Verificar último batch exitoso
grep 'escrito' /root/proyecto-3/s2_zarr_run.log | tail -1
# Ej: "Lote 193 escrito" → resume desde 194

# Relanzar desde donde quedó (NO desde cero)
cd /root/proyecto-3
nohup .venv/bin/python gcp/zarr/s2_a_zarr.py --batch-size 3 \
  > s2_zarr_run_v2.log 2>&1 &
# batch-size=3 para menos presión de RAM
```

### Si hay que subir los Zarr a HF
```bash
cd /root/proyecto-3
hf buckets sync hugging-face/staging/S5P_NO2/ hf://buckets/yeigen/fuentes-proyecto-3/copernicus_s5p_offl_l3_no2/
hf buckets sync hugging-face/staging/ERA5/ hf://buckets/yeigen/fuentes-proyecto-3/ecmwf_era5_hourly/
# ... etc para SO2, O3, MODIS
```

### Si hay que verificar coherencia de nuevo
```bash
cd /root/proyecto-3
.venv/bin/python -c "
import xarray as xr, rioxarray, numpy as np, gcsfs
# Leer Zarr
fs = gcsfs.GCSFileSystem(token='google_default')
m = fs.get_mapper('fuentes-proyecto-3/copernicus_s2_sr_harmonized/panel.zarr')
ds = xr.open_zarr(m, consolidated=False)
# Leer GeoTIFF equivalente
from google.cloud import storage
import sys; sys.path.insert(0,'google-earth')
from config import PROJECT_ID
c = storage.Client(project=PROJECT_ID)
b = c.bucket('fuentes-proyecto-3')
blob = b.blob('copernicus_s2_sr_harmonized/raw/20210103T152641_20210103T153117_T18NUJ__B1.tif')
import io; buf = io.BytesIO(blob.download_as_bytes())
tif = rioxarray.open_rasterio(buf).values
if tif.ndim == 3: tif = tif[0]
zarr = ds['data'].isel(time=0, band=0).values
mask = (tif > 0) & (~np.isnan(zarr))
diff = np.abs(tif[mask].astype('float32') - zarr[mask])
print(f'Pixeles: {mask.sum()}, Diff max: {diff.max():.6f}, Cero: {(diff==0).sum()}')
"
```
