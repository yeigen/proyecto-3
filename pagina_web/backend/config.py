from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

BBOX = [-76.65, 3.30, -76.30, 3.65]
CENTRO = [3.45, -76.53]

BASE_DATOS = RAIZ / "fuentes-proyecto-3"

BASE_TILES = BASE_DATOS / "GeoVision Tiles Sit 2"

TILES_NPZ = BASE_TILES / "tiles_train.npz"
TILES_META = BASE_TILES / "tiles_meta.parquet"

CHECKPOINT_CLIP = BASE_DATOS / "geovision-clip-modelo-v2v" / "clip_finetuned_best.pt"
METRICS_CLIP = BASE_DATOS / "geovision-clip-modelo-v2v" / "metrics.json"
BAND_STATS = Path(__file__).resolve().parent / "data" / "band_stats.json"

RUTA_DAGMA = RAIZ / "dagma" / "dagma_cvc_horario_raw.parquet"
RUTA_ESTACIONES = RAIZ / "dagma" / "estaciones_metadata.csv"

KAGGLE_MODIS = "edwardsx/modis-v2-panel"

CONTAMINANTES = ["NO2", "SO2", "O3"]
HORIZONTES = ["T+1", "T+3", "T+7"]
CLASES_CLIP = [
    "contaminacion_alta_NO2", "contaminacion_alta_SO2",
    "ozono_anomalo", "vegetacion_densa", "suelo_urbano",
]

INDICES_BANDAS_S2 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

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
