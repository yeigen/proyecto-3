# Cómo trabajar con este proyecto (perfil del owner)

- **Usar skills siempre.** Antes de cualquier tarea técnica, cargar la skill relevante si existe.
- **No comentar código a menos que sea estrictamente necesario.** El código debe ser autoexplicativo.
- **Siempre preguntar y proponer opciones.** Jamás dar nada por sentado ni ejecutar sin consultar.
- **Usar los MCP disponibles** (filesystem, context7) para explorar archivos y documentación.
- **Corto, simple, sin sobre-ingeniería.** Una celda > tres celdas. Un archivo > tres archivos.
- **Usar GPU si está disponible** (T4 Kaggle). No proponer CPU-only si hay GPU.
- **Pegar código directo al notebook existente**, no crear notebooks paralelos para tareas chicas.
- **Notebook = memoria compartida**: no redefinir lo que ya está en celdas anteriores.
- **No mentir sobre lo que no se probó.** Si algo no se verificó, decirlo.
- **No hacer trabajo redundante.** Si el dato/script ya existe, reutilizar.
- **Español LATAM** en comentarios, logs y mensajes.

## Ubicación de datos y fuentes

**NO buscar en otros lugares.** Los datos están solo aquí:

### Locales (proyecto-3)
| Ruta | Contenido |
|---|---|
| `google-earth/config.py` | Config central (fuentes, bandas, BBox, escala) |
| `gcp/exportar_*.py` | Scripts de exportación GEE → GCS |
| `gcp/zarr/*.py` | Conversión GeoTIFF → Zarr |
| `hugging-face/` | Upload a HuggingFace Hub |
| `docs/` | Documentación técnica (conceptos, datasets, flujo) |
| `scripts/muestreo_sit2.ipynb` | Notebook de muestreo estratificado activo |
| `scripts/01_muestreo_kaggle.py` | Script de muestreo para Kaggle |
| `manifest/manifest.ipynb` | Generación del manifest.json |
| `dagma/` | Datos DAGMA ground truth (parquet + CSV + JSON) |
| `EDA.ipynb` | Análisis exploratorio completo |
| `imagenes-referencias/` | Diagramas de cada fuente satelital |

### Remotos (acceso público, sin credenciales)
| Ubicación | URL / Path |
|---|---|
| Kaggle Dataset | `juanjoseorozcolopez/geovision-fuentes` |
| Kaggle Notebook | `edwardsx/geovision-proyecto-3` |
| HF Bucket | `yeigen/fuentes-proyecto-3` |
| GCS | `gs://fuentes-proyecto-3` (proyecto `proyecto-analitica-3-495618`) |
| Droplet | `root@192.241.132.222` (SSH, GCS ADC + EE creds) |

## Stack y rutas relevantes

- Notebook activo Kaggle: [`edwardsx/geovision-proyecto-3`](https://www.kaggle.com/code/edwardsx/geovision-proyecto-3)
- Dataset Kaggle: [`juanjoseorozcolopez/geovision-fuentes`](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)
- Ruta del dataset en Kaggle: `/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes/`
- Output Kaggle: `/kaggle/working/`
- GCS bucket: `gs://fuentes-proyecto-3` (proyecto `proyecto-analitica-3-495618`)
- HF Bucket: `yeigen/fuentes-proyecto-3`
- Droplet: `root@192.241.132.222` (SSH preconfigurada, GCS ADC + EE creds disponibles)
- Acceso a todo es **público**, no preocuparse por credenciales en código.
