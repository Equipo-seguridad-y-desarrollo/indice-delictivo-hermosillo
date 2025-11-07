# Datos del Proyecto

Este directorio contiene los datos utilizados en el análisis del índice delictivo de Hermosillo.

## ⚠️ Importante

**Los archivos de datos NO están incluidos en el repositorio Git** debido a su gran tamaño (>500MB).

## 📥 Cómo obtener los datos

### Opción 1: Descarga automática (Recomendado)
```bash
# Desde la raíz del proyecto
python notebooks/download_raw_data.py
```

Este script descarga automáticamente los datos desde Hugging Face.

### Opción 2: Descarga manual
1. Visita: https://huggingface.co/datasets/Equipo-seguridad-y-desarrollo/hermosillo-incidentes
2. Descarga el dataset
3. Coloca el archivo CSV en `data/raw/reportes_de_incidentes_2018_2025.csv`

## 📁 Estructura de directorios

```
data/
├── raw/                    # Datos originales sin procesar
│   ├── reportes_de_incidentes_2018_2025.csv    (500MB, 2.3M registros)
│   ├── demografia_hermosillo.csv               (50KB, 660 colonias)
│   ├── poligonos_hermosillo.csv                (5MB, 693 polígonos)
│   └── colonias_imc2020.shp                    (Shapefile INEGI)
│
├── interim/                # Datos intermedios del proceso
│   └── reportes_de_incidentes_procesados_2018_2025.csv
│
├── processed/              # Datos finales procesados
│   ├── colonias_demografia_con_coordenadas.csv
│   ├── colonias_reportes_911_con_coordenadas.csv
│   ├── mapeo_colonias_reportes_911.csv
│   └── unificado/
│       ├── poligonos_unificados_completo.csv      (93MB)
│       ├── poligonos_unificados_completo.geojson  (127MB)
│       └── incidentes_con_poligono_temporal.csv   (512MB)
│
└── external/               # Datos de fuentes externas
```

## 📊 Descripción de datasets

### Raw (Originales)

#### `reportes_de_incidentes_2018_2025.csv`
- **Fuente**: Hugging Face
- **Registros**: 2,297,081
- **Periodo**: Enero 2018 - Septiembre 2025
- **Columnas**: 
  - Timestamp, Latitud, Longitud
  - Colonia, Categoría, Severidad
  - Detalles del incidente
- **Tamaño**: ~500MB

#### `demografia_hermosillo.csv`
- **Fuente**: INEGI Censo 2020
- **Registros**: 660 colonias
- **Columnas**:
  - nom_col, poblacion_total, viviendas_totales
  - escolaridad_años_prom, pctj_menores18
  - pctj_hombres, pctj_mujeres
- **Tamaño**: ~50KB

#### `poligonos_hermosillo.csv`
- **Fuente**: INEGI Marco Geoestadístico 2020
- **Registros**: 693 polígonos
- **Columnas**:
  - CVE_COL, COLONIA, CP
  - POLIGONO_WKT (geometría)
  - CLASIF (clasificación INEGI)
  - POBTOT (población total)
- **Tamaño**: ~5MB

### Processed (Finales)

#### `poligonos_unificados_completo.csv`
- **Descripción**: Dataset maestro con todas las métricas
- **Registros**: 693 polígonos
- **Columnas clave**:
  - Demografía: población, viviendas, escolaridad
  - Incidentes: total, por severidad, por categoría
  - Índices: tasa per 1k, score severidad, índice riesgo
  - Temporal: incidentes por año/trimestre
- **Tamaño**: ~93MB

#### `poligonos_unificados_completo.geojson`
- **Descripción**: Geometrías para visualización
- **Formato**: GeoJSON
- **CRS**: EPSG:4326 (WGS84)
- **Tamaño**: ~127MB

## 🔄 Pipeline de procesamiento

```
download_raw_data.py
    ↓
    raw/reportes_de_incidentes_2018_2025.csv
    ↓
[Geocodificación + Feature Engineering]
    ↓
    interim/reportes_de_incidentes_procesados_2018_2025.csv
    ↓
[Unificación con demografía y polígonos]
    ↓
    processed/unificado/poligonos_unificados_completo.csv
    ↓
[Visualización]
    ↓
    mapa_interactivo_hermosillo.html
```

## 📈 Estadísticas

### Cobertura de datos
- **Incidentes georreferenciados**: 97.0% (2,227,287 / 2,297,081)
- **Demografía asignada**: 100% (658 / 658 colonias)
- **Polígonos con demografía**: 64.1% (444 / 693)
- **Polígonos con índice de riesgo**: 62.8% (435 / 693)

### Período de análisis
- **Inicio**: 1 de enero de 2018
- **Fin**: 30 de septiembre de 2025
- **Duración**: 7 años 9 meses
- **Actualizaciones**: Trimestrales

## 🔐 Política de privacidad

Los datos de incidentes delictivos son **agregados y anonimizados**:
- No contienen información personal identificable
- Coordenadas redondeadas a nivel de colonia
- Sin nombres, direcciones, o detalles de víctimas

## 📝 Citación

Si utilizas estos datos en investigación o publicaciones:

```
Equipo de Seguridad y Desarrollo (2025). 
"Dataset de Incidentes Delictivos de Hermosillo 2018-2025". 
Hugging Face Datasets.
https://huggingface.co/datasets/Equipo-seguridad-y-desarrollo/hermosillo-incidentes
```

## 🔗 Enlaces útiles

- **Dataset en Hugging Face**: https://huggingface.co/datasets/Equipo-seguridad-y-desarrollo/hermosillo-incidentes
- **Documentación completa**: Ver `/docs/DICCIONARIO_DE_DATOS.md`
- **Proceso de limpieza**: Ver `/docs/PROCESO_LIMPIEZA_DATOS.md`

## 📞 Contacto

Para preguntas sobre los datos:
- Repositorio: https://github.com/Equipo-seguridad-y-desarrollo/indice-delictivo-hermosillo
- Issues: Reportar problemas en GitHub Issues

---

**Última actualización**: 7 de noviembre de 2025  
**Versión**: v4.0
