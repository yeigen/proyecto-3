# Cómo trabajar con este proyecto (perfil del owner)

- **Corto, simple, sin sobre-ingeniería.** Una celda > tres celdas. Un archivo > tres archivos.
- **Documentado, pero no demasiado.** Comentarios donde aporten, no en cada línea. Sin docstrings largos.
- **Usar GPU si está disponible** (T4 Kaggle). No proponer CPU-only si hay GPU.
- **Siempre dar opciones** cuando hay decisiones técnicas. No imponer una sola ruta.
- **Pegar código directo al notebook existente**, no crear notebooks paralelos para tareas chicas.
- **Notebook = memoria compartida**: no redefinir lo que ya está en celdas anteriores.
- **No mentir sobre lo que no se probó.** Si algo no se verificó, decirlo.
- **No hacer trabajo redundante.** Si el dato/script ya existe, reutilizar.
- **Español LATAM** en comentarios, logs y mensajes.

## Stack y rutas relevantes

- Notebook activo Kaggle: [`edwardsx/geovision-proyecto-3`](https://www.kaggle.com/code/edwardsx/geovision-proyecto-3)
- Dataset Kaggle: [`juanjoseorozcolopez/geovision-fuentes`](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)
- Ruta del dataset en Kaggle: `/kaggle/input/datasets/juanjoseorozcolopez/geovision-fuentes/`
- Output Kaggle: `/kaggle/working/`
- GCS bucket: `gs://fuentes-proyecto-3` (proyecto `proyecto-analitica-3-495618`)
- HF Bucket: `yeigen/fuentes-proyecto-3`
- Droplet: `root@192.241.132.222` (SSH preconfigurada, GCS ADC + EE creds disponibles)
- Acceso a todo es **público**, no preocuparse por credenciales en código.
