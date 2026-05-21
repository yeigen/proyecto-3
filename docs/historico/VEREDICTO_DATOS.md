# Veredicto honesto de la calidad de datos vs requisitos del PDF

Documento de balance brutal, sin justificaciones cómodas, antes de avanzar al bloque 8 y al entrenamiento. Todos los números vienen del EDA propio (`scripts/eda/eda_completo.py`) y los requisitos vienen del PDF `proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf`.

> Corte: **2026-05-17**.

---

## TL;DR

**Lo bueno:** Sit 1 cumple, Sit 2 cumple, ERA5 y S5P están sanos. El muestreo Sit 2 es de calidad técnica alta.

**Lo MALO real:** DAGMA es heterogéneo y NO₂ solo existe en 1 estación (Yumbo CVC). Esto **rompe el LOO-CV de Sit 3 para NO₂** tal como lo pide el PDF. Penalización máxima si no se mitiga: **-60% del componente Sit 3 = -18 puntos del proyecto total**.

**Lo mal entendido:** "DAGMA solo sirven 2 años" es una simplificación. La realidad es:
- 2020-2022: múltiples estaciones DAGMA activas (gaps grandes pero datos)
- 2023-2024: solo Yumbo (CVC) tiene cobertura densa
- 2025: vacío (manifest DAGMA llega a 2024-12-31)

**Lo defendible:** sí, con honestidad y mitigaciones documentadas. No tenemos que inventar datos — tenemos que ser explícitos sobre las limitaciones, anteponernos a la crítica y mostrar que el modelo funciona dentro del subconjunto válido.

---

## 1. Mapeo brutal por fuente: qué pide el PDF vs qué tenemos

### Sentinel-2 L2A

| Requisito PDF | Lo que tenemos | Veredicto |
|---|---|:---:|
| 13 bandas (B2-B12) + SCL | 13 bandas presentes | ✅ |
| Resolución 10/20/60 m, resampleadas | 10 m con 3,897×3,897 px | ✅ |
| 5 días revisita | S2A+S2B+S2C, 1,552 escenas en 5 años | ✅ |
| BBox Cali + Yumbo + Acopi | BBox ampliado 0.35° × 0.35° (decisión #1) | ✅ |
| **Filtro nubosidad < 60%** (PDF p. 4) | Filtramos SCL > 30% → **136 escenas (8.8%)** | ✅ con caveat |

**Caveat:** el PDF estimaba "≈164 adquisiciones útiles/tile" con filtro < 60%. Con SCL > 30% real obtuvimos 136 escenas totales (sobre 2 tiles). Está dentro de lo razonable considerando que Cali es trópico húmedo.

### Sentinel-5P L2 OFFL

| Requisito PDF | Lo que tenemos | Veredicto |
|---|---|:---:|
| NO₂ troposférico | 25,592 escenas, banda `tropospheric_NO2_column_number_density` | ✅ |
| SO₂ vertical column | 25,829 escenas | ✅ |
| O₃ total column | 25,716 escenas | ✅ |
| Diaria 1-2 órbitas | ~430 escenas/mes | ✅ |
| Resolución 3.5 × 5.5 km | Producto L3 a 1.1 km (re-grillado) | ✅ |
| Recorte HARP a BBox | Saltado (decisión #5: GEE L3 ya viene re-grillado) | ⚠ documentado |
| **No usar S5P como input directo** (penalización -25%) | Sit 2 usa S5P solo como pseudo-label en texto | ✅ |

**Penalización evitada:** -25% si pasáramos S5P como input visual al CLIP. El muestreo lo evita correctamente (decisión declarada en `MUESTREO_SIT2.md` técnica 1).

### MODIS MCD19A2 AOD

| Requisito PDF | Lo que tenemos | Veredicto |
|---|---|:---:|
| AOD (proxy PM) | Bandas `Optical_Depth_047/055`, `Column_WV`, `AOD_QA` | ⚠ con bug |
| Resolución 1 km | 0.92 km observada | ✅ |
| Diaria | 1,826 días continuos | ✅ |
| **Valores físicamente válidos** | **Mediana escalada -1.237, rango [-4.2, 0.05]. 99.6% fuera del valid_range MAIAC [-0.1, 5.0]** | 🔴 **BUG** |

**Implicación:** MODIS en estado actual **no es usable** para Sit 3 (Kriging requiere valores físicos). Opciones reales:
- **Reprocesar el panel** desde GEE (`MODIS/061/MCD19A2_GRANULES`, fuente declarada en `google-earth/config.py`). ~4 h de trabajo.
- **Excluir MODIS** del modelo: **NO viable**, el PDF lo lista como fuente obligatoria.

**Decisión necesaria antes de Sit 3:** reprocesar. Sin alternativa.

### ERA5-Land (PDF) vs ERA5-Hourly (proyecto)

| Requisito PDF | Lo que tenemos | Veredicto |
|---|---|:---:|
| ERA5-Land 9 km, T2m, viento, BLH, RH | ERA5 horario 28 km, 8 variables (incluye BLH y RH₈₅₀) | ⚠ desvío justificado |
| Horaria | 43,824 timestamps continuos, **sin gaps** | ✅ |

**Desvío del PDF:** se cambió ERA5-Land por ERA5-Hourly porque ERA5-Land **no incluye BLH ni RH₈₅₀** (decisión #4, documentada). El bloque 4 del EDA confirmó **BLH varía × 9 entre día y noche** — sin esta variable no modelamos la mezcla atmosférica. Defensa: necesidad física, no comodidad.

### DAGMA + SISAIRE — el problema

| Requisito PDF | Lo que tenemos | Veredicto |
|---|---|:---:|
| 9 estaciones DAGMA | **10 estaciones** (9 DAGMA + 1 CVC Yumbo) | ✅ (+ extra) |
| **NO₂, SO₂, O₃ in situ** en cada estación | NO₂: **1/10** (Yumbo CVC). SO₂: 6/10. O₃: 8/10 | 🔴 **PROBLEMA SEVERO** |
| Datos horarios | Sí, 107,291 mediciones | ✅ |
| 5 años | DAGMA cubre **2020-2024**, panel cubre 2021-2025. **Overlap: 4 años (2021-2024)** | ⚠ |
| **LOO-CV obligatorio** sobre las 9 estaciones (PDF p. 9) | **Imposible para NO₂** con 1 estación. Posible para SO₂ (n=6) y O₃ (n=8) | 🔴 |

**Cobertura real por estación (sobre 59 meses esperados, panel 2020-2024):**

| Estación | Meses activos | % cobertura | Contaminantes que mide |
|---|---:|---:|---|
| **8777 Yumbo CVC** | **46/59** | **80.9%** | NO₂, SO₂, O₃ |
| 8285 Base Aérea (DAGMA) | 25/59 | 35.5% | SO₂, O₃ |
| 8986 La Flora | 17/59 | 23.7% | SO₂, O₃ |
| 30111 La Ermita | 22/59 | 20.3% | SO₂, O₃ |
| 30110 Compartir | 24/59 | 17.7% | O₃ |
| 26190 Transitoria-Navarro | 12/59 | 17.5% | SO₂, O₃ |
| 30004 Era Obrero | 20/59 | 16.3% | O₃ |
| 8291 UniValle | 25/59 | 14.9% | O₃ |
| 8288 Pance | 21/59 | 13.8% | O₃ |
| 30109 Cañaveralejo | 16/59 | 11.9% | SO₂ |

**Lectura honesta:**
- **Yumbo es 4× más cubierta que la mediana** del resto. Es la única estación verdaderamente "buena".
- **5 estaciones DAGMA tienen menos del 18% cobertura**. Si reportamos LOO-CV ponderado uniforme por estación, esos 5 puntos arrastran la métrica.
- **NO₂ es un agujero estructural**: solo Yumbo (que es CVC, no DAGMA pura). El PDF dice "validar contra 9 estaciones DAGMA" → **el dataset no permite cumplirlo para NO₂**.

---

## 2. Veredicto por situación

### Situación 1 — Construcción del panel (20% del proyecto)

| Criterio rúbrica | Cumplido | Riesgo |
|---|:---:|---|
| ≥ 50 GB verificado | ✅ ~83 GB | ninguno |
| Manifest con MD5 | ⏳ pendiente generar | sin riesgo (script trivial) |
| EDA completo (≥ 8 viz) | ✅ ya tenemos > 30 figuras | ninguno |
| ETL distribuido (Dask/Spark) | ⚠ usamos GEE serverless + threading | revisar si cuenta |
| Diagrama arquitectura cloud | ⏳ pendiente | sin riesgo |

**Veredicto:** ✅ **Sit 1 está sólida.** El "ETL distribuido" puede ser pregunta de defensa — argumentar que GEE + GCS + HF es arquitectura distribuida por diseño, aunque no usemos Dask/Spark explícitamente.

### Situación 2 — CLIP + SAE (20% del proyecto)

| Criterio | Cumplido | Riesgo |
|---|:---:|---|
| 5,000 tiles balanceados (1000/clase × 5) | ✅ confirmado por EDA bloque 7 | ninguno |
| Pseudo-labels S5P por percentil | ✅ p90 NO₂/SO₂, p95 O₃ con defensa empírica | ninguno |
| NO pasar S5P como input directo | ✅ S5P solo en texto | ninguno |
| Checkpoint MD5 reproducible | ⏳ pendiente (requiere seed fijo) | -20% si difiere |
| KPIs: Recall@1 ≥ 0.45, Recall@5 ≥ 0.70, sparsity ≥ 0.70 | ⏳ entrenamiento pendiente | dependiente |
| AFE + AFC con CFI > 0.90, RMSEA < 0.08 | ⏳ pendiente | dependiente |

**Veredicto:** ✅ **Sit 2 es viable**. El muestreo está bien construido, falta solo entrenar. El sesgo de año del ozono (2022+2024 = 86% del muestreo O₃) **se mitiga con split estratificado por año**.

### Situación 3 — DL + Geoestadística (30% del proyecto) 🔴 CRÍTICA

| Criterio rúbrica | Cumplido | Riesgo |
|---|:---:|---|
| ConvLSTM bidir, 8 frames | ⏳ pendiente | dependiente |
| Variograma + ST-Kriging | ⏳ pendiente | dependiente |
| **LOO-CV obligatorio sobre 9 estaciones DAGMA** | 🔴 **imposible para NO₂** (1 estación) | **-60% Sit 3** |
| RMSE LOO-CV NO₂ ≤ 8 µg/m³ | 🔴 sin LOO-CV no hay métrica | parte del -60% |
| RMSE LOO-CV SO₂ ≤ 6 µg/m³ | ⚠ posible con n=6 estaciones, cobertura desigual | medio |
| RMSE LOO-CV O₃ ≤ 12 µg/m³ | ⚠ posible con n=8 estaciones | medio |
| R² LOO-CV ≥ 0.55 (promedio) | ⏳ pendiente, agregación crítica | dependiente |
| Moran I > 0.30 (p<0.05) | ⏳ pendiente | bajo |
| Variograma residuos nugget puro | ⏳ pendiente | bajo |
| Cobertura cinturón 95% σ Kriging ≥ 92% | ⏳ pendiente | bajo |

**Penalización máxima si no se mitiga:** -60% del componente Sit 3 = **-18 puntos del proyecto total**.

---

## 3. Mitigaciones defendibles (estrategia recomendada)

### Mitigación A — NO₂: validación alternativa documentada

**Problema:** LOO-CV no aplica con 1 estación.

**Estrategia:** reportar **3 métricas alternativas** y documentarlas como justificación:

1. **In-sample agreement Yumbo CVC**: predecir sobre Yumbo con modelo entrenado sin Yumbo en pseudo-label. Métrica RMSE/MAE/R².
2. **Concordancia espacial S5P↔predicción**: correlación entre el mapa S5P NO₂ promedio y el mapa predicho por ConvLSTM+Kriging. Métricas: Pearson r, Moran I.
3. **Distribución global**: comparar histograma de predicciones vs histograma DAGMA NO₂ (Yumbo). Métrica: KS test, Wasserstein distance.

**Argumento de defensa:** la red oficial de Cali tiene solo una estación NO₂ históricamente activa. Reportamos las métricas posibles con honestidad. La rúbrica exige LOO-CV "sobre 9 estaciones", pero el dataset solo permite LOO-CV sobre las que efectivamente miden el contaminante. Esto es **transparencia, no incumplimiento**.

### Mitigación B — Cobertura heterogénea: LOO-CV ponderado + restringido

**Problema:** 5 estaciones < 18% cobertura → arrastran la métrica si peso uniforme.

**Estrategia:** reportar **3 versiones de LOO-CV** por contaminante:

1. **LOO-CV completo (peso uniforme por estación)** — cumple literalmente el PDF.
2. **LOO-CV ponderado por número de mediciones** — refleja la métrica "real".
3. **LOO-CV restringido a estaciones con ≥ 20% cobertura** — métrica conservadora sobre datos de calidad.

Reportar las 3 en el informe permite que el evaluador elija cuál considerar.

### Mitigación C — MODIS: reprocesar el panel antes de Sit 3

**Acción concreta:** abrir notebook nuevo `scripts/reprocesar_modis.py` que:
1. Descarga gránulos MAIAC desde GEE con `getDownloadURL(scale=1000)`.
2. Aplica `(raw - add_offset) × scale_factor + mask(_FillValue=-28672)` correctamente.
3. Promedia por día y construye Zarr nuevo.
4. Sube como nuevo dataset Kaggle o sobre-escribe el panel base.

Tiempo estimado: 4-6 h. Es la única opción viable porque el PDF lo lista como fuente obligatoria.

### Mitigación D — Sesgo de año en muestreo O₃

**Problema:** 86% de tiles ozono_anomalo en 2022+2024.

**Estrategia:**
1. **Split train/val/test estratificado por año** (no aleatorio) en Sit 2.
2. **Para ConvLSTM Sit 3**: usar todas las clases (no solo O₃) y reportar métricas por año en el análisis de ablación (sección 6 del informe).
3. **Documentar honestamente** en el informe como "limitación del régimen temporal del panel S2 disponible".

---

## 4. Calendario propuesto (priorizado por penalización evitable)

| # | Acción | Esfuerzo | Penalización evitada |
|---:|---|---|---|
| 1 | **Reprocesar MODIS** (Mitigación C) | 4-6 h | Cumplimiento fuente obligatoria |
| 2 | **Decidir y documentar formato de validación NO₂** (Mitigación A) | 1 h documentación | -60% Sit 3 → defensa fuerte |
| 3 | **Generar manifest MD5** Sit 1 | 30 min script | -3% proyecto |
| 4 | **Diagrama arquitectura cloud** | 1 h (con imagen real, no inventada) | rúbrica |
| 5 | **Reporte costos cloud** | 30 min | rúbrica |
| 6 | Entrenar CLIP+SAE Sit 2 | 4-6 h GPU | dependiente |
| 7 | Implementar ConvLSTM + Kriging | 6-8 h | dependiente |
| 8 | Frontend React + Vite + Leaflet | 1.5 días | -30% despliegue |
| 9 | Informe + defensa | 1 día | -10% informe |

**Acción inmediata (esta semana):** ítems 1 + 2 + 3. Sin ellos, Sit 3 está condenada.

---

## 5. Responder al miedo: "los datos son una mierda"

**No, no son una mierda. Son lo que existe.** Punto.

| Fuente | Realidad |
|---|---|
| S2 panel | Cali es trópico húmedo. 91% nubes es **realidad geográfica**, no falla del dataset. |
| S5P | 16% cobertura NO₂ es **filtro qa_value de KNMI**, decisión upstream estándar. |
| ERA5 | **Perfecto.** 43,824 horas continuas. |
| MODIS | **Bug del panel local**, fuente original sí funciona. Reparable. |
| DAGMA | **Realidad operativa de la red oficial.** Cali tiene 1 estación NO₂ activa, no más. |

**La defensa NO es "los datos son malos". Es:**

1. **Identificamos exactamente qué tenemos y qué falta** (este documento + `EDA_HALLAZGOS.md`).
2. **Justificamos cada desvío técnico** con datos del propio EDA (decisión #4, #1, #11, etc.).
3. **Documentamos las limitaciones del dataset** como parte del problema científico, no como excusa.
4. **Proponemos mitigaciones concretas y medibles** (Mitigación A, B, C, D arriba).
5. **Reportamos métricas que sí son medibles** (LOO-CV sobre estaciones con cobertura suficiente, validación alternativa NO₂).

**Esto NO es "los datos son una mierda" — esto es ingeniería de datos seria.** La rúbrica del PDF castiga incumplimientos sin justificación, no realismo documentado.

---

## 6. Preguntas que esperar en defensa

1. *"¿Por qué solo 1 estación NO₂?"* → Cobertura operativa real DAGMA + CVC. Documentamos en EDA.
2. *"¿Cómo validan NO₂ sin LOO-CV?"* → Mitigación A — 3 métricas alternativas.
3. *"¿Por qué el MODIS tiene valores negativos en su panel?"* → Bug de construcción del Zarr local. Mostramos que la fuente oficial sí funciona y la reprocesamos.
4. *"¿Por qué cambiaron ERA5-Land por ERA5-Hourly?"* → Decisión #4. BLH varía × 9 día/noche, ERA5-Land no la tiene.
5. *"¿Por qué solo 8.8% de las escenas S2 son usables?"* → Filtro SCL > 30% sobre 1,552 escenas. Cali tropical húmedo. Solución: pre-filtrado por escena, 10× speed-up en muestreo (decisión #10).
6. *"¿2025 es entrenable si DAGMA no llega?"* → Sit 2 sí (usa pseudo-labels S5P, no DAGMA). Sit 3 LOO-CV solo 2021-2024.

---

## 7. Conclusión

**Es defendible si:**

1. Reprocesamos MODIS (no opcional).
2. Documentamos la estrategia de validación NO₂ alternativa (Mitigación A).
3. Reportamos LOO-CV ponderado + restringido (Mitigación B).
4. Mantenemos split estratificado por año en Sit 2 (Mitigación D).
5. Generamos los entregables documentales pendientes de Sit 1.

**Si todo lo anterior se hace**, el proyecto cumple ~85-90% de la rúbrica con limitaciones documentadas. Sin las mitigaciones, expectativa razonable cae a 50-60%.

**Las limitaciones del dataset no son nuestra culpa.** El cómo las manejamos sí lo es. Este documento es la base de esa defensa.
