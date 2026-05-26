# Diagnóstico SO2 tiles v2

Total muestras: 1150

## Balance
```text
clase
contaminacion_alta_NO2    230
contaminacion_alta_SO2    230
ozono_anomalo             230
suelo_urbano              230
vegetacion_densa          230
```

## Variables ópticas medias
```text
                          ndvi    ndbi  scl_pct
clase                                          
contaminacion_alta_NO2  0.4942 -0.1304   0.8527
contaminacion_alta_SO2  0.6124 -0.2010   0.8994
ozono_anomalo           0.5268 -0.1547   0.8388
suelo_urbano            0.1777  0.1062   0.8986
vegetacion_densa        0.6943 -0.2674   0.8846
```

## Distancias centroides no-leak desde SO2
```text
vegetacion_densa          0.8594
contaminacion_alta_NO2    0.9758
ozono_anomalo             1.1268
suelo_urbano              2.9310
```

## KS SO2 vs vegetación densa
```text
     variable  ks_stat  p_value   so2_mean  other_mean  delta_mean
     modis_WV 0.082609 0.413254   2.939411    2.840181    0.099230
   era5_RH850 0.104348 0.163520  85.890311   86.925384   -1.035073
     era5_BLH 0.130435 0.039855 679.035325  655.982307   23.053018
     era5_v10 0.130435 0.039855  -0.814155   -0.819452    0.005297
      scl_pct 0.152174 0.009638   0.899394    0.884639    0.014755
modis_AOD_047 0.183745 0.001080   0.269237    0.323867   -0.054629
modis_AOD_055 0.186730 0.000845   0.194791    0.234652   -0.039861
     era5_u10 0.191304 0.000427   0.226397    0.374083   -0.147686
          no2 0.214545 0.000513   0.000015    0.000012    0.000003
         ndbi 0.269565 0.000000  -0.200974   -0.267449    0.066475
         ndvi 0.382609 0.000000   0.612356    0.694295   -0.081938
           o3 0.426087 0.000000   0.118294    0.113687    0.004607
          so2 1.000000 0.000000   0.000390   -0.000003    0.000393
```

## Lectura rápida
- SO2 queda ópticamente cerca de vegetación si NDVI/NDBI/SCL son similares.
- Si SO2 solo se separa por la columna so2, Sentinel-2 no contiene suficiente señal visual directa para esa clase.
- Si SO2 se separa mejor con ERA5/MODIS que con NDVI/NDBI, conviene usar late fusion tabular o corregir pseudo-labels.