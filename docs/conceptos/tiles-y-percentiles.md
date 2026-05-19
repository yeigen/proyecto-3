# Tiles y percentiles — Situación 2

Dos conceptos que sostienen toda la decisión de muestreo de Sit 2: **qué es un "tile"** (la unidad mínima que el modelo CLIP ingiere) y **qué es un percentil** (el umbral que usamos para etiquetar tiles de contaminación). Sin tener claros estos dos, las decisiones #9 y #11 de `JUSTIFICACIONES.md` no se entienden.

---

## 1. ¿Qué es un tile?

Un **tile** (o *patch*) es un recorte rectangular pequeño de una imagen satelital grande, con tamaño fijo en píxeles. En lugar de pasarle al modelo la escena completa (decenas de miles de píxeles de lado), se la corta en cuadrados del mismo tamaño que el modelo sabe procesar.

### Por qué se trabaja con tiles y no con la escena completa

1. **Las CNN/transformers tienen entrada fija.** Una ViT-B/32 (la base de CLIP) espera entradas de tamaño constante; no acepta "una imagen entera de Sentinel-2 de 10,980×10,980 px".
2. **Memoria GPU.** Una escena S2 completa en 13 bandas float32 pesa ~6 GiB. Una T4 tiene 16 GiB de VRAM total. No cabe ni un batch de 1.
3. **Localidad espacial.** Un tile de 64×64 px a 10 m/px cubre **640 m × 640 m = 0.41 km²**. Es la unidad mínima coherente para "una zona urbana" o "una pluma de contaminación localizada".
4. **Balance de clases.** Una escena completa tiene mezcla de vegetación, urbano, agua, nubes. Cortarla en tiles permite **etiquetar cada tile con una clase pura** y balancear el dataset.

### Por qué 64×64×13 es correcto para este proyecto

| Decisión | Valor | Justificación |
|---|---|---|
| Lado del tile | 64 px | Estándar de la literatura para Sentinel-2 (EuroSAT). Cubre 640 m a 10 m/px — suficiente para una manzana urbana grande o una pluma industrial local. |
| Bandas (canales) | 13 | Las 13 bandas espectrales completas de Sentinel-2 L2A (B1, B2-B12, SCL), resampleadas a 10 m. RemoteCLIP también espera multibanda. |
| `dtype` | float32 | Compatible con torch sin casting adicional. |
| Shape final | `(N, 13, 64, 64)` | Convención PyTorch `(batch, channels, H, W)`. |

**El paper EuroSAT** ([Helber et al., 2017]) usa exactamente esta configuración para la clasificación de uso de suelo con Sentinel-2 y reporta accuracy 98.57% con CNN profundas. Cito textual de la sección III-B "Dataset Creation" del paper (verificado en `ar5iv.labs.arxiv.org/html/1709.00029`):

> "The patches measure 64x64 pixels."

**RemoteCLIP** ([Liu et al., 2023]) — el modelo que vamos a fine-tunear — está diseñado precisamente para ingerir tiles satelitales de este tipo y realizar transferencia a tareas downstream con fine-tuning (el paper menciona explícitamente "require annotated data for fine-tuning" como el escenario que cubre). 5,000 tiles balanceados es un volumen estándar para fine-tuning de CLIP en dominios específicos.

### Por qué N=1000 por clase (5K total) es defendible

Tres referencias cruzadas (ver `JUSTIFICACIONES.md` decisión #9):

- **AFC (Análisis Factorial Confirmatorio)**: regla de Kline — mínimo 10 observaciones por parámetro estimado. Con ~32 parámetros, mínimo 320. Tenemos 5,000 → holgura **15×**.
- **Recall@5 en retrieval**: por clase mínimo 500 tiles para estabilizar la métrica. Tenemos 1,000/clase → holgura **2×**.
- **Fine-tuning CLIP**: la literatura reporta convergencia razonable desde ~5K pares imagen-texto cuando se parte de un checkpoint pre-entrenado fuerte (RemoteCLIP).

### Limitación conocida (caveat para defensa)

Un tile de 64×64 no permite segmentación a nivel pixel — solo clasificación por tile. Si dentro de los 640×640 m hay mezcla (mitad vegetación, mitad urbano), el modelo solo recibe una etiqueta. **Mitigación**: el pre-filtrado SCL descarta tiles con > 30% nubes/sombras, y el filtrado por NDVI/NDBI fuerza pureza de clase (NDVI > 0.6 para vegetación, < 0.3 para urbano).

---

## 2. ¿Qué es un percentil?

Un **percentil P_k** (escrito p90, p95, p99…) es el valor por debajo del cual cae el **k%** de los datos de una distribución. Es una medida de **posición relativa**, no de valor absoluto.

### Ejemplo numérico simple

Para los valores de NO₂ de Cali en 2024 (1,000 mediciones diarias), si:

- p90 = 0.00018 mol/m² → 90% de los días tuvieron NO₂ ≤ 0.00018; los 100 días más contaminados están **por encima** de ese valor.
- p95 = 0.00021 mol/m² → 95% de los días por debajo; los 50 más contaminados arriba.
- p99 = 0.00027 mol/m² → 99% por debajo; solo los 10 días más extremos arriba.

A mayor k, **más estricto** el umbral y **menos eventos** califican.

### Cómo se calcula (sin entrar en formalismos)

1. Ordenar los datos de menor a mayor.
2. Encontrar el índice que corresponde al k% de la longitud total.
3. Reportar el valor en esa posición (con interpolación lineal si cae entre dos valores).

En código del proyecto:

```python
import numpy as np
p95 = np.percentile(no2_values, 95)
```

### Por qué se usan percentiles como umbrales (y no medias)

1. **Robustos a outliers.** La media puede dispararse con un solo valor extremo; el percentil no.
2. **Definen "extremo" sin elegir un valor mágico.** En lugar de "NO₂ > 0.0002" (¿por qué ese y no 0.0003?), se dice "el 5% más alto", lo que se traslada entre regiones/años.
3. **Estándar en monitoreo ambiental.** EPA y WHO los usan oficialmente:

| Norma | Contaminante | Percentil |
|---|---|---|
| EPA NAAQS — NO₂ horario | 1-h daily max | **p98** anual, promedio 3 años |
| EPA NAAQS — SO₂ horario | 1-h daily max | **p99** anual, promedio 3 años |
| WHO Air Quality Guidelines 2021 — PM₂.₅ 24 h | exposición diaria | **p99** (≈ 3-4 días de excedencia por año) |

Citas textuales verificadas:

- EPA NAAQS: *"Annual 98th percentile of 1-hour daily maximum concentrations, averaged over 3 years"* (NO₂); *"Annual 99th percentile of 1-hour daily maximum concentrations, averaged over 3 years"* (SO₂). Fuente: [EPA NAAQS Table](https://www.epa.gov/criteria-air-pollutants/naaqs-table).
- WHO 2021: *"99th percentile (i.e. 3–4 exceedance days per year)"* aplicado a PM₂.₅ 24 h. Fuente: [WHO Air Quality Guidelines](https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines).

### Por qué nuestro proyecto bajó de p99 a p95 para O₃

Decisión #11 de `JUSTIFICACIONES.md`. La regla EPA/WHO usa p99 sobre **series anuales largas de estaciones in situ**. Nosotros tenemos imágenes satelitales **filtradas por SCL (sin nubes)**, lo que reduce drásticamente la cantidad de fechas únicas disponibles:

| Umbral combinado | Fechas únicas O₃ | Top-5 fechas concentran |
|---|---:|---:|
| p99 NO₂/SO₂/O₃ + SCL > 0.5 | 11 | **81%** del muestreo |
| p95 NO₂/SO₂/O₃ + SCL > 0.3 | **31** | < 40% del muestreo |

Con p99 + SCL > 0.5, el dataset colapsaba temporalmente a 5 fechas (cualquier estacionalidad o evento puntual contamina el 80% de las muestras). Con p95 + SCL > 0.3, se mantiene diversidad temporal sin sacrificar la condición "evento extremo" (sigue siendo el 5% superior). **El umbral relajado no es laxitud; es adaptación al dominio satelital**, donde la cobertura nubosa truncó la serie efectiva.

---

## 3. Resumen para la defensa oral

1. Un tile es un recorte cuadrado de tamaño fijo (64×64 px) que el modelo CLIP puede ingerir. Elegimos 64×64 porque es el estándar de EuroSAT para Sentinel-2 y cubre 640×640 m, suficiente para resolver una pluma local sin promediar tipos de cobertura.
2. 5,000 tiles balanceados (1,000 por clase × 5 clases) supera por holgura los mínimos de AFC (Kline 10:1) y de Recall@5 (500/clase).
3. Un percentil es el valor por debajo del cual cae un % dado de los datos. Lo usan EPA (p98 NO₂, p99 SO₂) y WHO (p99 PM₂.₅) como umbral estándar de "evento extremo".
4. Nosotros bajamos a p95 + SCL > 0.3 porque el filtrado por nubes redujo las fechas únicas; p99 + SCL > 0.5 colapsaba a 11 fechas con 81% de concentración en top-5.

---

## Referencias (URLs verificadas, status 200 al 2026-05-17)

- **EuroSAT — patches 64×64 Sentinel-2** — Helber, P., Bischke, B., Dengel, A., Borth, D. (2017). *EuroSAT: A Novel Dataset and Deep Learning Benchmark for Land Use and Land Cover Classification*. arXiv:1709.00029. [arxiv.org/abs/1709.00029](https://arxiv.org/abs/1709.00029) — HTML legible: [ar5iv.labs.arxiv.org/html/1709.00029](https://ar5iv.labs.arxiv.org/html/1709.00029) — Repo: [github.com/phelber/EuroSAT](https://github.com/phelber/EuroSAT).
- **RemoteCLIP — fine-tuning CLIP en remote sensing** — Liu, F., Chen, D., Guan, Z., Zhou, X., Zhu, J., Ye, Q., Fu, L., Zhou, J. (2023). *RemoteCLIP: A Vision Language Foundation Model for Remote Sensing*. arXiv:2306.11029. [arxiv.org/abs/2306.11029](https://arxiv.org/abs/2306.11029) — Repo oficial: [github.com/ChenDelong1999/RemoteCLIP](https://github.com/ChenDelong1999/RemoteCLIP).
- **EPA NAAQS — percentiles p98/p99 como umbrales regulatorios** — U.S. Environmental Protection Agency. *NAAQS Table*. [epa.gov/criteria-air-pollutants/naaqs-table](https://www.epa.gov/criteria-air-pollutants/naaqs-table).
- **WHO Air Quality Guidelines 2021 — p99 para PM₂.₅** — World Health Organization. *What are the WHO Air Quality Guidelines?*. [who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines](https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines).
