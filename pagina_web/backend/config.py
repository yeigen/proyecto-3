import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

BBOX = [-76.65, 3.30, -76.30, 3.65]
CENTRO = [3.45, -76.53]

# Datos: variable de entorno GEOVISION_DATA (contenedor HF Spaces) o data/ local
DATA = Path(os.getenv("GEOVISION_DATA", str(RAIZ / "data")))

# Frontend estático (build de Vite) — servido por el backend en despliegue
FRONTEND_DIST = Path(os.getenv("GEOVISION_FRONTEND", str(Path(__file__).resolve().parent.parent / "frontend" / "dist")))

# Sit 3 — artefactos pre-computados (frontend-ready)
SIT3 = DATA / "sit3" / "frontend_data"
GRIDS_JSON = SIT3 / "grids_prediccion.json"
OVERLAYS_DIR = SIT3 / "overlays"
ESTACIONES_JSON = SIT3 / "estaciones.json"
LISA_JSON = SIT3 / "lisa.json"
VARIOGRAMAS_JSON = SIT3 / "variogramas.json"
PERFILES_JSON = SIT3 / "perfiles_kmeans.json"
LOOCV_JSON = SIT3 / "loocv.json"
KPIS_JSON = SIT3 / "kpis.json"

# DAGMA limpio (ground truth) + tiles Sit 2
RUTA_DAGMA = DATA / "dagma" / "df_dagma_unificado_coordenadas_limpias.parquet"
RUTA_ESTACIONES = DATA / "dagma" / "estaciones_metadata.csv"
TILES_META = DATA / "tiles" / "rescate-1500" / "tiles_meta.parquet"

CONTAMINANTES = ["NO2", "SO2", "O3"]
HORIZONTES = ["T+1", "T+3", "T+7"]
CLASES_CLIP = [
    "contaminacion_alta_NO2", "contaminacion_alta_SO2",
    "ozono_anomalo", "vegetacion_densa", "suelo_urbano",
]

# Gases con mapa de Kriging (NO2 excluido: solo 2 estaciones DAGMA)
GASES_CON_MAPA = ["SO2", "O3"]

ESCALAS_COLOR = {
    "NO2": ["#fef2f2", "#fee2e2", "#fecaca", "#fca5a5",
            "#f87171", "#ef4444", "#dc2626", "#b91c1c"],
    "SO2": ["#fffbeb", "#fef3c7", "#fde68a", "#fcd34d",
            "#fbbf24", "#f59e0b", "#d97706", "#b45309"],
    "O3": ["#faf5ff", "#f3e8ff", "#e9d5ff", "#d8b4fe",
           "#c084fc", "#a855f7", "#9333ea", "#7e22ce"],
}

CLASE_COLOR_MAPA = {
    "contaminacion_alta_NO2": "#ef4444",
    "contaminacion_alta_SO2": "#ef4444",
    "ozono_anomalo": "#ef4444",
    "vegetacion_densa": "#22c55e",
    "suelo_urbano": "#eab308",
}

CLASE_DESCRIPCION = {
    "contaminacion_alta_NO2": "Zona con posible contaminacion alta por NO2 (trafico vehicular)",
    "contaminacion_alta_SO2": "Zona con posible contaminacion alta por SO2 (industria)",
    "ozono_anomalo": "Zona con ozono troposferico elevado (temporada seca)",
    "vegetacion_densa": "Zona de vegetacion densa o cultivos",
    "suelo_urbano": "Zona urbana o suelo construido",
}

LATENCIA_MAXIMA_SEG = 8.0
SEMILLA = 42
