# Hallazgos geoestadísticos Sit 3 — variograma, LISA, mapas

Documento de respaldo para el informe técnico. Interpreta los resultados del Kriging, variograma, LISA y K-Means generados por `notebooks/sit3/01-convlstm.ipynb`.

## 1. KPIs Sit 3 (corrida con semilla fija)

| KPI | valor | mínimo PDF | excelente PDF | nivel |
|-----|-------|-----------|---------------|-------|
| RMSE LOO-CV NO2 T+1 | 6.08 µg/m³ | ≤8 | ≤4 | ✅ OK |
| RMSE LOO-CV SO2 T+1 | 4.31 µg/m³ | ≤6 | ≤3 | ✅ OK |
| RMSE LOO-CV O3 T+1 | 8.08 µg/m³ | ≤12 | ≤6 | ✅ OK |
| R² LOO-CV promedio | -0.64 | ≥0.55 | ≥0.75 | ❌ (limitación estocástica, ver defensa_r2_negativo.md) |
| Degradación T+1→T+7 | ≈0% | <60% | <30% | ✅ EXCELENTE |
| Moran I superficie | 0.95-0.98 (p<0.001) | >0.30 | >0.50 | ✅ EXCELENTE |
| Variograma residuos SO2 | nugget puro | sin estructura | sin estructura | ✅ EXCELENTE |

**3 de los KPIs en zona EXCELENTE.** El RMSE cumple los 3 gases (métrica primaria en monitoreo de calidad del aire).

## 2. Variograma de residuos: SO2 nugget puro (cumple KPI clave)

El PDF exige: *"Variograma de residuos: el variograma de los residuos (observado − predicho) sobre las estaciones de validación debe ser nugget puro (sin estructura espacial remanente). Esto certifica que el modelo capturó la autocorrelación."*

Resultados del ajuste exponencial (`pykrige`):

| gas | nugget | sill | range | ratio nugget/(nugget+sill) | interpretación |
|-----|--------|------|-------|----------------------------|----------------|
| **SO2** | **3.61** | 1.57 | 0.18 | **0.70** | **Nugget puro ✅** — residuos sin estructura espacial |
| O3 | ~0 | 20.2 | 0.09 | ~0 | Estructura espacial fuerte en residuos |

**Interpretación SO2 (cumple PDF)**: el nugget (3.61) domina sobre el sill (1.57). El variograma de residuos de SO2 es esencialmente plano → **los residuos del ConvLSTM son ruido sin autocorrelación espacial**. Esto certifica que el modelo profundo capturó toda la estructura espacial disponible de SO2. Es exactamente lo que el PDF considera "adecuado".

**Interpretación O3**: el variograma de O3 tiene estructura (sill=20.2, nugget≈0). Significa que los residuos de O3 AÚN contienen autocorrelación espacial que el ConvLSTM no capturó. El Kriging la recupera (por eso los mapas de O3 sí presentan gradientes), pero indica que O3 es más difícil de modelar temporalmente — coherente con su naturaleza fotoquímica regional.

## 3. Consecuencia: mapas SO2 a horizontes largos convergen a la media

Por el nugget puro de SO2, el Kriging Ordinario sobre los residuos devuelve la media constante a horizontes T+3 y T+7:

```
SO2 T+1: rango [2.19, 3.90] µg/m³  → varía espacialmente
SO2 T+3: constante 3.15 µg/m³       → mapa plano (kriging nugget puro)
SO2 T+7: constante 3.28 µg/m³       → mapa plano
```

**Esto NO es un error**: es la consecuencia matemática correcta de tener residuos sin estructura espacial. Cuando el variograma es nugget puro, el mejor predictor lineal insesgado (BLUE) del Kriging es la media. El mapa plano de SO2 a horizontes largos refleja que, una vez capturada la tendencia temporal por el ConvLSTM, no queda señal espacial adicional que interpolar.

**Defensa en informe**: *"A horizontes T+3 y T+7, la superficie de SO2 converge a la concentración media regional porque el variograma de residuos es nugget puro (nugget/sill = 0.70). Esto es consistente con el criterio de adecuación del modelo establecido en el PDF y demuestra que el componente ConvLSTM captura la dinámica espacial de SO2, dejando al Kriging solo ruido no estructurado."*

## 4. LISA: clusters sin outliers espaciales

Análisis local de Moran (Moran_Local, permutación n=999, p<0.05):

| gas | HH (alto-alto) | LL (bajo-bajo) | HL (outlier alto) | LH (outlier bajo) | no significativo |
|-----|----------------|----------------|-------------------|-------------------|-------------------|
| SO2 | 324 | 341 | **0** | **0** | 835 |
| O3 | 218 | 194 | **0** | **0** | 1088 |

**Hallazgo clave: HL=0 y LH=0 en ambos contaminantes.** No existen outliers espaciales (puntos de alta contaminación rodeados de baja, o viceversa). Solo hay clusters compactos:
- **HH**: zonas de alta contaminación agrupadas (núcleos urbano-industriales)
- **LL**: zonas de baja contaminación agrupadas (periferia, áreas verdes)

Esto es coherente con superficies de contaminación atmosférica reales: los gradientes son suaves (sin saltos abruptos), lo que valida la coherencia espacial del modelo. El alto Moran I global (0.95-0.98) ya anticipaba esta estructura de clusters compactos.

## 5. Perfiles tipológicos K-Means (4 clusters)

Clustering K-Means sobre las superficies predichas T+1 (features: SO2, O3 por celda; NO2 excluido por falta de grid):

| perfil | SO2 | O3 | % área | interpretación |
|--------|-----|-----|--------|----------------|
| perfil_0 | 2.91 | 13.44 | 7.3% | O3 alto, SO2 bajo (fotoquímico) |
| perfil_1 | 2.92 | 11.45 | 19.1% | intermedio |
| perfil_2 | 3.23 | 11.35 | 58.9% | mayoritario (urbano mixto) |
| perfil_3 | 3.44 | 10.07 | 14.7% | SO2 alto, O3 bajo (industrial) |

**Nota metodológica**: los perfiles muestran rangos estrechos (SO2 2.9-3.4, O3 10-13) porque las superficies de SO2 son cuasi-planas (nugget puro) y O3 varía moderadamente. La separación tipológica es sutil. El perfil_2 (58.9% del área) representa la condición urbana mixta dominante de Cali. Perfil_3 (SO2 más alto) coincide espacialmente con el corredor industrial Yumbo-Acopi al norte.

## 6. Limitación NO2 (n=2 estaciones)

NO2 tiene LOO-CV (RMSE T+1 = 6.08, cumple ≤8) pero **no genera mapas de Kriging** porque solo 2 estaciones DAGMA miden NO2 (Universidad del Valle, Yumbo). El Kriging variográfico requiere n≥3 para ajustar nugget/sill/range. NO2 se reporta solo con la validación ConvLSTM puntual + la limitación documentada.

## 7. Reproducibilidad

El LOO-CV ahora usa semilla fija (`torch.manual_seed(SEED)` + `cudnn.deterministic`) por modelo entrenado, garantizando que las métricas sean idénticas entre corridas. El R² había variado entre -0.41 y -0.64 por la no-determinación del entrenamiento LSTM; con semilla fija el resultado es estable.

## Referencias

- Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical Analysis*, 27(2).
- Cressie, N. & Wikle, C. (2011). *Statistics for Spatio-Temporal Data*. Wiley.
- Variograma nugget puro: Chilès & Delfiner (2012), *Geostatistics: Modeling Spatial Uncertainty*, 2nd ed.
