import os
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import ee
from config import PROJECT_ID, FUENTES, CALI  # type: ignore[reportMissingImports]
from logger import get_logger                  # type: ignore[reportMissingImports]

log = get_logger('visualizar_imagenes')
ee.Initialize(project=PROJECT_ID)

# ── Directorios de salida ────────────────────────────────────────────────
BASE_DIR = os.path.join(HERE, 'imagenes-reales')

SUBDIR = {
    'COPERNICUS/S5P/OFFL/L3_NO2':  's5p_no2',
    'COPERNICUS/S5P/OFFL/L3_SO2':  's5p_so2',
    'COPERNICUS/S5P/OFFL/L3_O3':   's5p_o3',
    'COPERNICUS/S2_SR_HARMONIZED': 'sentinel2',
    'ECMWF/ERA5/HOURLY':           'era5',
    'MODIS/061/MCD19A2_GRANULES':  'modis_maiact',
}

for d in SUBDIR.values():
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

# ── Geometria de Cali ────────────────────────────────────────────────────
region = ee.Geometry.Rectangle(CALI)

# ── Parametros de visualizacion por fuente ───────────────────────────────
VIZ_BASE = {
    'COPERNICUS/S5P/OFFL/L3_NO2': {
        'bands': ['tropospheric_NO2_column_number_density'],
        'min': 0,
        'max': 0.00008,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S5P/OFFL/L3_SO2': {
        'bands': ['SO2_column_number_density'],
        'min': 0,
        'max': 0.0002,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S5P/OFFL/L3_O3': {
        'bands': ['O3_column_number_density'],
        'min': 0.107,
        'max': 0.109,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'red'],
    },
    'COPERNICUS/S2_SR_HARMONIZED': {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 0.3,
    },
    'ECMWF/ERA5/HOURLY': {
        'bands': ['temperature_2m'],
        'min': 280,
        'max': 310,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'red'],
    },
    'MODIS/061/MCD19A2_GRANULES': {
        'bands': ['Optical_Depth_047'],
        'min': 0,
        'max': 1100,
        'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red'],
    },
}


def descargar_thumbnail(imagen, viz, out_path, dims=512):
    """Genera y descarga un thumbnail PNG."""
    params = {**viz, 'dimensions': dims, 'region': region, 'format': 'png'}
    url = imagen.getThumbURL(params)
    urllib.request.urlretrieve(url, out_path)


def preprocesar_s2(raw):
    """S2: enmascara nubes + cirrus, divide por 10000."""
    qa = raw.select('QA60')
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0)
    cirrus_mask = qa.bitwiseAnd(1 << 11).eq(0)
    return raw.updateMask(cloud_mask.And(cirrus_mask)).divide(10000)


# ═══════════════════════════════════════════════════════════════════════════
# S5P (NO2, SO2, O3): composites trimestrales + primer dia de cada mes
# ═══════════════════════════════════════════════════════════════════════════
TRIMESTRES = [
    ('2024-01-01', '2024-03-31', 'q1_2024'),
    ('2024-04-01', '2024-06-30', 'q2_2024'),
    ('2024-07-01', '2024-09-30', 'q3_2024'),
    ('2024-10-01', '2024-12-31', 'q4_2024'),
]

for fuente_id in ('COPERNICUS/S5P/OFFL/L3_NO2',
                  'COPERNICUS/S5P/OFFL/L3_SO2',
                  'COPERNICUS/S5P/OFFL/L3_O3'):
    log.info(f"S5P: {fuente_id}")
    sub = SUBDIR[fuente_id]
    viz = VIZ_BASE[fuente_id]
    try:
        for ini, fin, etiqueta in TRIMESTRES:
            composite = (ee.ImageCollection(fuente_id)
                         .filterBounds(region)
                         .filterDate(ini, fin)
                         .mean()
                         .select(viz['bands'])
                         .unmask(viz.get('min', 0))
                         .clip(region))
            fname = os.path.join(BASE_DIR, sub, f'{etiqueta}.png')
            descargar_thumbnail(composite, viz, fname)
            log.info(f"  ✓ {sub}/{etiqueta}.png")
    except Exception as exc:
        log.warning(f"  ✗ {fuente_id}: {exc}")

# ═══════════════════════════════════════════════════════════════════════════
# Sentinel-2: 4 fechas con poca nubosidad en Cali (estacion seca dic-ago)
# RGB natural (B4/B3/B2) + falso color infrarrojo (B8/B4/B3)
# ═══════════════════════════════════════════════════════════════════════════
FECHAS_S2 = ['2024-01-01', '2024-07-01', '2024-12-01', '2025-03-01']
VIZ_S2_RGB = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}
VIZ_S2_FCC = {'bands': ['B8', 'B4', 'B3'], 'min': 0, 'max': 0.5}

log.info("Sentinel-2")
sub = SUBDIR['COPERNICUS/S2_SR_HARMONIZED']
for fecha in FECHAS_S2:
    try:
        raw = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterBounds(region)
               .filterDate(fecha, f'{fecha[:7]}-31')
               .first())
        imagen = preprocesar_s2(raw).clip(region)

        # RGB natural
        descargar_thumbnail(imagen, VIZ_S2_RGB,
                            os.path.join(BASE_DIR, sub, f'{fecha}_rgb.png'))
        log.info(f"  ✓ {sub}/{fecha}_rgb.png")

        # Falso color infrarrojo (B8 NIR → R, B4 Red → G, B3 Green → B)
        descargar_thumbnail(imagen, VIZ_S2_FCC,
                            os.path.join(BASE_DIR, sub, f'{fecha}_fcc.png'))
        log.info(f"  ✓ {sub}/{fecha}_fcc.png")
    except Exception as exc:
        log.warning(f"  ✗ Sentinel-2 {fecha}: {exc}")

# ═══════════════════════════════════════════════════════════════════════════
# ERA5: 3 horas del mismo dia (06, 12, 18 UTC) + otro dia para contraste
# ═══════════════════════════════════════════════════════════════════════════
log.info("ERA5")
sub = SUBDIR['ECMWF/ERA5/HOURLY']
viz = VIZ_BASE['ECMWF/ERA5/HOURLY']

for dia, hora, h_fin in [('2024-01-15', '06', '07'),
                           ('2024-01-15', '12', '13'),
                           ('2024-01-15', '18', '19'),
                           ('2024-07-15', '12', '13')]:
    try:
        imagen = (ee.ImageCollection('ECMWF/ERA5/HOURLY')
                  .filterDate(f'{dia}T{hora}:00', f'{dia}T{h_fin}:00')
                  .first()
                  .select(viz['bands'])
                  .unmask(viz.get('min', 0))
                  .clip(region))
        fname = os.path.join(BASE_DIR, sub, f'{dia}T{hora}.png')
        descargar_thumbnail(imagen, viz, fname)
        log.info(f"  ✓ {sub}/{dia}T{hora}.png")
    except Exception as exc:
        log.warning(f"  ✗ ERA5 {dia}T{hora}: {exc}")

# ═══════════════════════════════════════════════════════════════════════════
# MODIS MAIAC: 4 fechas distintas (estacion seca vs humeda)
# ═══════════════════════════════════════════════════════════════════════════
log.info("MODIS MAIAC")
sub = SUBDIR['MODIS/061/MCD19A2_GRANULES']
viz = VIZ_BASE['MODIS/061/MCD19A2_GRANULES']

for fecha in ['2024-02-01', '2024-06-01', '2024-10-01', '2025-01-01']:
    try:
        imagen = (ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
                  .filterBounds(region)
                  .filterDate(fecha, f'{fecha[:7]}-28')
                  .first()
                  .select(viz['bands'])
                  .unmask(viz.get('min', 0))
                  .clip(region))
        fname = os.path.join(BASE_DIR, sub, f'{fecha}.png')
        descargar_thumbnail(imagen, viz, fname)
        log.info(f"  ✓ {sub}/{fecha}.png")
    except Exception as exc:
        log.warning(f"  ✗ MODIS {fecha}: {exc}")

log.info(f"Directorio base: {BASE_DIR}")
