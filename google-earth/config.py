CALI = [-76.60, 3.30, -76.40, 3.55]
PROJECT_ID = 'proyecto-analitica-3-495618'

FUENTES = [
    ('COPERNICUS/S5P/OFFL/L3_NO2'),  # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2?hl=es-419
    ('COPERNICUS/S5P/OFFL/L3_SO2'),  # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2?hl=es-419
    ('COPERNICUS/S5P/OFFL/L3_O3'),   # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3?hl=es-419
    ('COPERNICUS/S2_SR_HARMONIZED'), # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
    ('ECMWF/ERA5/HOURLY'),           # https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY (atmospheric, tiene BLH y RH)
    ('MODIS/061/MCD19A2_GRANULES')]  # https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES?hl=es-419

# Rangos de disponibilidad reales (ver docs/DISPONIBLIDAD_DATOS.txt)

DISPONIBILIDAD = {
    'COPERNICUS/S5P/OFFL/L3_NO2':   ('2021-01-01', '2026-01-01'),
    'COPERNICUS/S5P/OFFL/L3_SO2':   ('2021-01-01', '2026-01-01'),
    'COPERNICUS/S5P/OFFL/L3_O3':    ('2021-01-01', '2026-01-01'),
    'COPERNICUS/S2_SR_HARMONIZED':  ('2021-01-01', '2026-01-01'),
    'ECMWF/ERA5/HOURLY':            ('2021-01-01', '2026-01-01'),
    'MODIS/061/MCD19A2_GRANULES':   ('2021-01-01', '2026-01-01'),
}

BANDAS_UTILES = {
    'COPERNICUS/S5P/OFFL/L3_NO2': [
        'tropospheric_NO2_column_number_density',
        'NO2_column_number_density',
        'cloud_fraction',
    ],
    'COPERNICUS/S5P/OFFL/L3_SO2': [
        'SO2_column_number_density',
        'cloud_fraction',
    ],
    'COPERNICUS/S5P/OFFL/L3_O3': [
        'O3_column_number_density',
        'cloud_fraction',
    ],
    'COPERNICUS/S2_SR_HARMONIZED': [
        'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
        'B8', 'B8A', 'B9', 'B11', 'B12', 'SCL',
    ],
    'ECMWF/ERA5/HOURLY': [
        'temperature_2m',
        'dewpoint_temperature_2m',
        'u_component_of_wind_10m',
        'v_component_of_wind_10m',
        'boundary_layer_height',
        'relative_humidity_850hPa',
        'surface_pressure',
        'total_precipitation',
    ],
    'MODIS/061/MCD19A2_GRANULES': [
        'Optical_Depth_047',
        'Optical_Depth_055',
        'Column_WV',
        'AOD_QA',
    ],
}

# Override de escala (m/px) cuando nominalScale() no refleja la nativa real.
# S2 reporta 60m pero las bandas RGB/NIR estan a 10m -> 36x mas pixeles.
ESCALA_OVERRIDE = {
    'COPERNICUS/S2_SR_HARMONIZED': 10.0,
}

