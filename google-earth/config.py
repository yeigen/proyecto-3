CALI = [-76.60, 3.30, -76.40, 3.55]
PROJECT_ID = 'charming-mile-436804-q2'

FUENTES = [
    ('COPERNICUS/S5P/OFFL/L3_NO2'),  # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2?hl=es-419
    ('COPERNICUS/S5P/OFFL/L3_SO2'),  # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2?hl=es-419
    ('COPERNICUS/S5P/OFFL/L3_O3'),   # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3?hl=es-419
    ('COPERNICUS/S2_SR_HARMONIZED'), # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
    ('ECMWF/ERA5_LAND/HOURLY'),      # https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY?hl=es-419
    ('MODIS/061/MCD19A2_GRANULES')]  # https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES?hl=es-419

# Rangos de disponibilidad reales (ver docs/DISPONIBLIDAD_DATOS.txt)

DISPONIBILIDAD = {
    'COPERNICUS/S5P/OFFL/L3_NO2':   ('2018-06-28', '2026-04-26'),
    'COPERNICUS/S5P/OFFL/L3_SO2':   ('2018-12-05', '2026-05-01'),
    'COPERNICUS/S5P/OFFL/L3_O3':    ('2018-09-08', '2026-05-01'),
    'COPERNICUS/S2_SR_HARMONIZED':  ('2017-03-28', '2026-05-06'),
    'ECMWF/ERA5_LAND/HOURLY':       ('1950-01-01', '2026-04-30'),
    'MODIS/061/MCD19A2_GRANULES':   ('2000-02-24', '2026-05-04'),
}

# Override de escala (m/px) cuando nominalScale() no refleja la nativa real.
# S2 reporta 60m pero las bandas RGB/NIR estan a 10m -> 36x mas pixeles.
ESCALA_OVERRIDE = {
    'COPERNICUS/S2_SR_HARMONIZED': 10.0,
}

