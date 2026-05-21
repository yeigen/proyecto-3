# Evidencias visuales

Esta carpeta guarda todas las imágenes del proyecto que se usan para documentación, informe, defensa o referencia visual. Las imágenes no deben quedar dispersas en `capturas/`, `imagenes-referencias/`, `entrenamiento/`, `arquitecturas/` ni dentro de carpetas de documentación específicas.

## Estructura

```text
docs/evidencias/
├── situacion-1/
│   ├── panel/
│   ├── eda/
│   └── fuentes/
├── situacion-2/
│   ├── muestreo/
│   ├── entrenamiento/
│   └── arquitectura/
└── situacion-3/
    ├── dagma/
    └── modelos/
```

## Regla principal

- Toda imagen final o de referencia vive bajo `docs/evidencias/`.
- Los notebooks pueden generar imágenes temporalmente en su entorno de ejecución, pero las imágenes que entren a documentación se copian o mueven aquí.
- No guardar capturas finales como `captura1.png`, `plot.png` o `imagen_final.png`.

## Nombres

Usar nombres completos y trazables:

```text
sit1_panel_kaggle_dataset.png
sit2_entrenamiento_curvas_aprendizaje.png
sit3_dagma_excel_parquet_correlacion_variables.png
```

## Criterio

Una imagen entra aquí si respalda una decisión, hallazgo, resultado o explicación del proyecto.
