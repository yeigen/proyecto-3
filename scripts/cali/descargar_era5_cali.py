import os, sys, urllib.request
import ee

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'google-earth'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from config import PROJECT_ID
from logger import get_logger

log = get_logger('era5_cali')
ee.Initialize(project=PROJECT_ID)

OUT = os.path.join(HERE, '..', '..', 'docs', 'situacion-1', 'evidencias',
                   'fuentes', 'google-earth', 'cali', 'era5')
os.makedirs(OUT, exist_ok=True)

cali = ee.Geometry.Rectangle([-76.65, 3.30, -76.30, 3.65])

COMBOS = [
    ('2024-01-15', '06', 'madrugada'),
    ('2024-01-15', '11', 'amanecer'),
    ('2024-01-15', '18', 'mediodia'),
    ('2024-01-15', '00', 'atardecer'),
    ('2024-07-15', '18', 'julio_mediodia'),
]

VIZ = {'bands': ['temperature_2m'],
       'min': 280, 'max': 310,
       'palette': ['blue', 'cyan', 'green', 'yellow', 'red']}

for dia, hora, etiq in COMBOS:
    h_fin = str(int(hora) + 1).zfill(2)
    try:
        img = (ee.ImageCollection('ECMWF/ERA5/HOURLY')
               .filterDate(f'{dia}T{hora}:00', f'{dia}T{h_fin}:00')
               .first()
               .select('temperature_2m')
               .unmask(280)
               .clip(cali))
        url = img.getThumbURL({**VIZ, 'dimensions': 512, 'region': cali, 'format': 'png'})
        fname = f'{dia.replace("-","")}_T{hora}.png'
        urllib.request.urlretrieve(url, os.path.join(OUT, fname))
        log.info(f'OK  {fname}')
    except Exception as e:
        log.warning(f'ERR {etiq}: {e}')
