import logging
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, 'logger', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(nombre: str) -> logging.Logger:
    log = logging.getLogger(nombre)
    if log.handlers:
        return log

    log.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    archivo = os.path.join(LOG_DIR, f"{nombre}_{datetime.now():%Y%m%d_%H%M%S}.log")
    fh = logging.FileHandler(archivo)
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    log.addHandler(fh)
    log.addHandler(sh)
    log.propagate = False
    log.info(f"Log file: {archivo}")
    return log
