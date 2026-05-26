"""Descarga datasets satelitales desde HuggingFace Hub al cache local.

Uso:
    uv run python scripts/descargar_hf.py [--solo nombre1,nombre2]

Variables de entorno requeridas:
    HF_TOKEN  — token de HuggingFace (en .env)

Targets por defecto (4 datasets):
    copernicus_s5p_offl_l3_no2   — NO2 troposférico
    copernicus_s5p_offl_l3_o3    — O3 columnar
    copernicus_s5p_offl_l3_so2   — SO2 vertical
    ecmwf_era5_hourly            — meteorología horaria

Sentinel-2 NO se descarga (97 GB, vive solo en GCS y Kaggle).
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import snapshot_download

REPO_ID = "yeigen/fuentes-proyecto-3"
REPO_TYPE = "dataset"
TARGETS_DEFAULT = [
    "copernicus_s5p_offl_l3_no2",
    "copernicus_s5p_offl_l3_o3",
    "copernicus_s5p_offl_l3_so2",
    "ecmwf_era5_hourly",
]
DESTINO = Path("data/hf-cache")


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    log = logging.getLogger("descargar_hf")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo", type=str, default=None,
                        help="Lista coma-separada de datasets a descargar (default: los 4)")
    args = parser.parse_args()

    targets = args.solo.split(",") if args.solo else TARGETS_DEFAULT
    targets = [t.strip() for t in targets]

    token = os.getenv("HF_TOKEN")
    if not token:
        log.error("HF_TOKEN no encontrado en .env")
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    log.info(f"Destino: {DESTINO.resolve()}")
    log.info(f"Datasets a descargar: {targets}")

    for nombre in targets:
        log.info(f"--- {nombre} ---")
        try:
            snapshot_download(
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                allow_patterns=f"{nombre}/*",
                local_dir=str(DESTINO),
                token=token,
            )
            destino_dataset = DESTINO / nombre
            n_files = sum(1 for _ in destino_dataset.rglob("*") if _.is_file())
            size_mb = sum(f.stat().st_size for f in destino_dataset.rglob("*") if f.is_file()) / 1024**2
            log.info(f"OK {nombre}: {n_files} archivos, {size_mb:.1f} MB en {destino_dataset}")
        except Exception as e:
            log.error(f"FAIL {nombre}: {e}")
            return 2

    log.info("Descarga completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
