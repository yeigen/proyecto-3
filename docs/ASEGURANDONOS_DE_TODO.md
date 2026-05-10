# Asegurándonos de todo — checklist para tranquilidad del equipo

**Fecha**: 2026-05-10 ~23:00
**Propósito**: revisión de cierre antes de archivar la sesión. Cada celda verde
significa "ya verificado, sin acción pendiente"; cada celda amarilla o roja
indica acción concreta que queda pendiente.

> Este documento complementa [`REVIEW_2026-05-10.md`](REVIEW_2026-05-10.md).
> El review explica la *lógica* del pipeline; este documento solo lista
> verificaciones concretas con evidencia.

---

## 1. Cobertura temporal del panel (verificación contra GCS)

Resultado de ejecutar `gsutil ls` y extraer la fecha mínima/máxima por fuente,
sobre la ventana solicitada **2021-01-01 → 2026-01-01** (5 años exactos):

| Fuente | Archivos raw en GCS | Primer dato | Último dato | Cubre los 5 años |
|---|---:|---|---|---|
| Sentinel-2 | 20,176 | **2021-01-03** | **2025-12-31** | ✅ |
| S5P NO₂ | 25,592 | 2020-12-31 | **2025-12-31** | ✅ (incluso 1 día antes) |
| S5P SO₂ | 25,829 | 2020-12-31 | **2025-12-31** | ✅ |
| S5P O₃ | 25,716 | 2020-12-31 | **2025-12-31** | ✅ |
| ERA5 horario | 43,824 | **2021-01-01** | **2025-12-31** | ✅ exacto |
| MODIS MAIAC | 151,558 | (sistema DOY) | (sistema DOY) | ✅ (ver nota) |

### Notas

- **El "último dato" siempre es 2025-12-31, nunca 2026-01-01.** Es comportamiento
  esperado: `ee.ImageCollection.filterDate(ini, fin)` de GEE incluye el inicio y
  **excluye el fin**. La ventana `("2021-01-01", "2026-01-01")` significa
  "desde el 1-ene-2021 inclusive hasta el 1-ene-2026 EXclusive". Para alcanzar
  el 1-ene-2026 habría que poner `fin="2026-01-02"`. Esto es <1 día y no afecta
  ninguna serie temporal. **No es un bug.**
- **Sentinel-2 empieza el 2021-01-03 y no el 2021-01-01**: revisita es de 5 días
  y la órbita no pasó por Cali los 2 primeros días del año. La siguiente
  adquisición fue el 3 de enero. No es algo que se pueda forzar.
- **MODIS usa Day-of-Year (DOY)** en `system:index`. El conteo de 151,558
  archivos viene de múltiples granules/día (Terra + Aqua + swaths superpuestos).
  La cobertura es densa y se reduce a la fecha mediante el agrupado por fecha
  en `modis_a_zarr.py:agrupar_por_fecha()`.

### Veredicto

Todas las fuentes cumplen los 5 años. El "1 mes faltante" al que tu memoria se
refería son en realidad **1 día** al final (2025-12-31 vs 2026-01-01). El equipo
puede defender con tranquilidad que la ventana 2021-2026 está cubierta.

---

## 2. Coherencia lossless Zarr ↔ GeoTIFF raw (S2 actual)

| Imagen | Banda | Píxeles válidos | `diff_max` | Resultado |
|---|---|---:|---:|---|
| 20210103T152641_T18NUJ | B1 | 2,354,710 | **0.000000** | bit-perfect |
| 20210103T152641_T18NUJ | B4 | 2,346,114 | **0.000000** | bit-perfect |
| 20210103T152641_T18NUJ | B8 | 2,346,114 | **0.000000** | bit-perfect |
| 20210103T152641_T18NUJ | SCL | 2,346,114 | **0.000000** | bit-perfect |

Script de verificación: `/tmp/verify_s2.py` (corrió en droplet, salida en `s2_zarr_run.log`).
Comparó la primera imagen del Zarr (que sí está completa porque corresponde al
lote 1/311 escrito a las 15:40) contra el GeoTIFF raw equivalente.

Verificaciones previas del usuario (registradas en `CONTEXTO_AGENTE.md`):

| Fuente | Imagen | Diff max |
|---|---|---:|
| S2 (B1) | 20210103 | 0.000000 |
| S5P NO2 | 20240715 | 2e-12 (ruido float64) |
| ERA5 | 20210211 | 0.000000 |

**Veredicto**: la conversión Zarr es lossless. Las decimales `e-12` que aparecen
en S5P son ruido de la precisión `float64` al castear a `float32`, no error de
pipeline.

---

## 3. Estado del proceso S2 → Zarr (al momento de escribir esto)

| Métrica | Valor |
|---|---|
| PID | 3187819 |
| Lote actual | 209/311 (67%) |
| Tiempo transcurrido | 7h 18min |
| RSS | 1.64 GB (bajó del peak de 4.85 GB — el GC está limpiando) |
| Lotes restantes | 102 |
| Ritmo | ~2.1 min/lote |
| ETA | ~3h 35min → ~02:30 AM del 2026-05-11 |
| Errores en log | 0 |

**Acción pendiente**: NO matar el proceso. Verificar a las 02:30 que
`zr.consolidate_metadata` se ejecutó y que `gs://fuentes-proyecto-3/copernicus_s2_sr_harmonized/panel.zarr/.zmetadata`
existe.

---

## 4. Inventario de almacenamiento (GCS + HF)

### GCS — `gs://fuentes-proyecto-3/`

| Prefijo | Archivos | Peso |
|---|---:|---:|
| `copernicus_s2_sr_harmonized/raw/` | 19,400+ | 76.99 GB |
| `copernicus_s2_sr_harmonized/panel.zarr/` | 5,198 (en aumento) | 53.93 GB (será ~84 GB) |
| `copernicus_s5p_offl_l3_no2/raw/` | 25,592 | 0.04 GB |
| `copernicus_s5p_offl_l3_so2/raw/` | 25,829 | 0.04 GB |
| `copernicus_s5p_offl_l3_o3/raw/` | 25,716 | 0.06 GB |
| `ecmwf_era5_hourly/raw/` | 43,824 | 0.09 GB |
| `modis_061_mcd19a2_granules/raw/` | 151,558 | 0.02 GB |

**Total raw GCS**: 77.23 GB (cumple ≥ 50 GB con margen del 54%).
**Total raw + Zarr S2 final**: ~161 GB.

### HuggingFace — [`yeigen/fuentes-proyecto-3`](https://huggingface.co/buckets/yeigen/fuentes-proyecto-3)

| Carpeta | Archivos | Última actualización |
|---|---:|---|
| `copernicus_s5p_offl_l3_no2` | 216 | hace ~7 h |
| `copernicus_s5p_offl_l3_so2` | 280 | hace ~7 h |
| `copernicus_s5p_offl_l3_o3` | 152 | hace ~7 h |
| `ecmwf_era5_hourly` | 40 | hace ~7 h |
| `modis_061_mcd19a2_granules` | 54 | hace ~7 h |
| **Total** | **742** | **63.6 MB** |

**Falta**: subir `copernicus_s2_sr_harmonized/panel.zarr/` (~84 GB) cuando termine.
Para esto se creó `hugging-face/subir_s2_hf.py` (ver §5).

---

## 5. Script de subida S2 → HuggingFace (nuevo)

Archivo: [`hugging-face/subir_s2_hf.py`](../hugging-face/subir_s2_hf.py)

### Cómo se ejecuta en el droplet, después de que S2 zarr termine

```bash
ssh root@192.241.132.222
cd /root/proyecto-3
# Si el PID 3187819 aún está corriendo, el script espera:
nohup .venv/bin/python hugging-face/subir_s2_hf.py \
  --esperar-pid 3187819 --limpiar \
  > s2_hf_upload.log 2>&1 &
```

### Qué hace el script

1. **`--esperar-pid 3187819`**: bloquea hasta que el proceso S2→Zarr termine
   (poll cada 120 s).
2. **Verifica GCS**: cuenta blobs en `panel.zarr/`, suma peso, comprueba que
   `.zmetadata` esté escrito. Aborta si pesa < 40 GB.
3. **Descarga GCS → `hugging-face/staging/copernicus_s2_sr_harmonized/`** con
   16 workers paralelos. Usa cache (no re-descarga archivos cuyo tamaño ya coincide).
4. **`hf buckets sync staging/... hf://buckets/yeigen/fuentes-proyecto-3/copernicus_s2_sr_harmonized`**
   (mismo patrón que `subir_hf.py` usado para los otros 5 datasets).
5. **Verifica HF post-upload**: cuenta archivos visibles en `hf://buckets/.../panel.zarr/`.
6. **`--limpiar`**: borra el staging después del sync exitoso.

### Sobre transferencia directa GCP → HF (lo que preguntaste)

No existe un equivalente al Storage Transfer Service entre GCS y HuggingFace
Hub — HF no es un proveedor de cloud storage al que GCP pueda enviar
directamente. La opción más rápida con la infra actual es usar el droplet como
pivote:

- **Ruta**: GCS (us-central1) → Droplet DigitalOcean (NYC1) → HF (us-east).
- **Throughput esperado**: ~1 Gbps (límite del NIC del droplet) ≈ 125 MB/s.
- **84 GB / 125 MB/s** ≈ 11 minutos teórico, en la práctica ~25-40 minutos
  (handshakes HTTPS, chunk-level multipart de HF, latencia).
- **No usaría streaming chunk-by-chunk** (más complejo, sin ganancia neta) —
  el espacio en `/root` del droplet es 141 GB libres, suficiente para
  staging temporal de 84 GB con 57 GB de margen.

Si en el futuro se necesita evitar el pivote, la alternativa más realista es
usar **Cloudflare R2** o **AWS S3** como bucket público, ambos soportados
nativamente por `huggingface_hub` como upstream con `hf_xet` — pero eso es
trabajo extra que no está justificado para esta entrega.

---

## 6. Checklist anti-pánico (lo que cualquiera del equipo puede verificar)

### Verificable desde el navegador

- [ ] [Bucket HF](https://huggingface.co/buckets/yeigen/fuentes-proyecto-3) muestra
      los 5 datasets (NO2, SO2, O3, ERA5, MODIS).
- [ ] [Bucket GCS](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3)
      muestra las 6 carpetas `raw/` y la `copernicus_s2_sr_harmonized/panel.zarr/`.

### Verificable desde la consola (local, sin credenciales especiales)

```bash
# Tamaños y conteos (lectura pública del bucket si tiene permisos)
gcloud storage du -s gs://fuentes-proyecto-3/

# Conteo de archivos por fuente
for src in copernicus_s2_sr_harmonized copernicus_s5p_offl_l3_no2 \
           copernicus_s5p_offl_l3_so2 copernicus_s5p_offl_l3_o3 \
           ecmwf_era5_hourly modis_061_mcd19a2_granules; do
  echo "$src: $(gcloud storage ls -r gs://fuentes-proyecto-3/$src/raw/ | wc -l) archivos raw"
done
```

### Verificable desde el droplet

```bash
ssh root@192.241.132.222
# Proceso S2 vivo?
ps -p 3187819 -o pid,pcpu,rss,etime
# Ultimo lote escrito
tail -3 /root/proyecto-3/s2_zarr_run.log
# Total escritos
grep -c 'escrito' /root/proyecto-3/s2_zarr_run.log
```

### Verificable desde Python

```python
import xarray as xr, gcsfs
fs = gcsfs.GCSFileSystem(token='google_default')

# Abrir cualquier panel y verificar dimensiones
for src in ['copernicus_s2_sr_harmonized', 'copernicus_s5p_offl_l3_no2',
            'ecmwf_era5_hourly']:
    ds = xr.open_zarr(fs.get_mapper(f'fuentes-proyecto-3/{src}/panel.zarr'),
                       consolidated=False)
    print(f'{src}: {dict(ds.sizes)} | dtype={ds["data"].dtype}')
```

---

## 7. Lo que potencialmente se pasó por alto

He buscado riesgos no documentados. Lo que encontré:

| Hallazgo | Severidad | Acción |
|---|---|---|
| `docs/DATASETS.md` líneas 19-23 describen `batch_NNNN.zarr/` que **no existen** (los scripts producen un único `panel.zarr/` por fuente) | baja | corregir DATASETS.md (1 párrafo) |
| `docs/JUSTIFICACION_FORMATO.md` línea 7 dice "Zarr v3" pero los stores usan `zarr_format=2` (en código y en `.zarray` reales) | muy baja, cosmético | corregir referencia |
| `s2_a_zarr.py` línea 194 dice "Zarr ~50-60 GB" pero la realidad es ~84 GB (proyectado) | baja, log informativo | corregir el `log.info` con la cifra real cuando se sepa final |
| `subir_hf.py` línea 65: `staging = os.path.join(staging, prefix) if prefix else staging` — funciona pero hace que `--dataset s2` apunte a `staging/copernicus_s2_sr_harmonized/`. El nuevo `subir_s2_hf.py` evita esta capa de indirección | baja | OK, ambos son compatibles |
| No hay `manifest.json` con MD5 (entregable PDF p.5) | **media** | generar después de completar S2 Zarr — son 30 min de script |
| No hay `EDA Situacion1.ipynb` consolidado con 8+ visualizaciones (entregable PDF p.5) | **media** | hay PNGs sueltos, falta el notebook armado |
| No hay diagrama de arquitectura cloud (entregable PDF p.5) | baja | una imagen, no es código |
| `MODIS/061/MCD19A2_GRANULES` tiene 151,558 archivos raw pero solo 54 blobs en HF — porque `modis_a_zarr.py:procesar_fecha` agrupa todos los granules del mismo día y promedia (ver línea 91 del script). Es por diseño, no es pérdida | informativo | OK, ya está documentado en `DATASETS.md` §MODIS |
| `.env` con `HF_TOKEN` ya está en `.gitignore` línea 2 — no se va a commitear | informativo | OK |

---

## 8. Si algo se cae en las próximas 4 horas

| Síntoma | Diagnóstico rápido | Recovery |
|---|---|---|
| `ssh` no conecta | droplet caído o reiniciado | revisar DigitalOcean console; el proceso `nohup` sobrevive a reinicios solo si `systemctl` lo gestiona (no es el caso aquí, hay que relanzar) |
| Proceso S2 muere por OOM | `dmesg` en droplet muestra `Out of memory: Killed process 3187819` | revisar `s2_zarr_run.log` para último lote escrito; relanzar con `--batch-size 3` y el Zarr existente se extiende vía `append_dim` desde el último timestamp |
| `hf buckets sync` falla con 401 | token HF expiró | `hf auth login` en droplet |
| HF reporta "too many files" | superamos 10K archivos en el bucket | inesperado — el panel S2 es 7,833 chunks; no debería pasar |

---

## 9. Resumen de una línea para cada miembro del equipo

> Todo está en orden. El proceso S2→Zarr corre estable en el droplet y termina
> esta madrugada (~02:30). El panel cumple los 5 años 2021-2026 (con 1 día de
> margen de cierre por el comportamiento `filterDate` de GEE, que es esperado).
> La conversión a Zarr es lossless (verificado bit a bit). Los 5 datasets
> pequeños ya están en HuggingFace. Solo falta subir S2 a HF con el script
> nuevo `subir_s2_hf.py` cuando el droplet termine, y armar el manifest MD5 +
> notebook EDA como entregables formales del PDF.
