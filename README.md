# 🚨 Índice Delictivo Hermosillo

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Análisis geoespacial de reportes a servicios de emergencia en Hermosillo, Sonora, por colonia.

---

## 📋 Descripción

Este proyecto analiza datos de incidentes policiales y características demográficas de las colonias de Hermosillo, Sonora, con el objetivo de generar un índice delictivo georreferenciado que permita:

- Identificar zonas de mayor incidencia delictiva
- Correlacionar factores demográficos con índices de criminalidad
- Proveer datos geoespaciales para análisis y visualización

---

## 🚀 Estado Actual

### ✅ Completado

- **Descarga de datos**: Migrado de Google Drive a Hugging Face para descarga directa
- **Procesamiento multi-año**: Pipeline consolidado para procesar datos 2018-2025 (2.3M registros)
- **Estandarización de incidentes**: 475 tipos de incidentes mapeados a 198 categorías únicas
- **Feature engineering**: 7 columnas derivadas (temporal, categórica, severidad)
- **Limpieza de colonias**: 2,047 colonias únicas identificadas (220 grupos con variantes)
- **Geocodificación incremental**: Coordenadas obtenidas vía Google Maps API con sistema anti-duplicados
- **Limpieza de datos demográficos**: 659 colonias con información poblacional
- **Documentación completa** del proceso de limpieza y normalización
- Validación cruzada entre datasets
- Análisis geoespacial de incidentes
- Visualización de datos en mapas interactivos

### 🔄 En Proceso


---

## 📊 Datasets

### Datos Crudos (`data/raw/`)

| Archivo | Registros | Descripción | Estatus |
|---------|-----------|-------------|-------------|
| `213.xlsx` | 2,297,081 | Incidentes reportados a servicios de emergencia 911 (2018-2025) | Por confirmar |
| `demografia_hermosillo.csv` | 660 | Datos demográficos por colonia (INEGI 2020) | Confirmado |
| `delitos.csv` | - | Catálogo de tipos de delitos | Por confirmar |
| `poligonos_hermosillo.csv` | - | Polígonos geográficos de colonias | Confirmado |
| `INE_Limpio.shx` | - | Polígonos geográficos de colonias, formato shapefile | Confirmado |
| `INE_Limpio.shp` | - | Polígonos geográficos de colonias, formato shapefile | Confirmado |
| `INE_Limpio.prj` | - | Polígonos geográficos de colonias, formato shapefile | Confirmado |
| `INE_Limpio.dbf` | - | Polígonos geográficos de colonias, formato shapefile | Confirmado |

### Datos Intermedios (`data/interim/`)

| Archivo | Descripción | Estatus |
|---------|-------------|-------------|
| `reportes_de_incidentes_procesados_2018_2025.csv` | Datos consolidados 2018-2025 con estandarización y feature engineering (~310MB, 2.3M registros) | Por confirmar |
| `colonias_sin_poblacion.csv` |  | Confirmado |
| `colonias_con_incidentes_sin_poligono.csv` |  | Confirmado |




### Datos Procesados (`data/processed/`)

| Archivo | Descripción |
|---------|-------------|
| `colonias_unicas_reportes_911.csv` | 2,047 colonias limpias del dataset policial |
| `colonias_reportes_911_con_coordenadas.csv` | Colonias con coordenadas geográficas (lat/lng) |
| `colonias_reportes_911_agrupadas_reporte.csv` | Reporte de 220 grupos con variantes ortográficas detectadas |
| `mapeo_colonias_reportes_911.csv` | Mapeo de colonias originales a normalizadas |
| `demografia_limpio.csv` | Datos demográficos normalizados |
| `colonias_unicas_demografia.csv` | Lista de colonias únicas de demografía |
| `colonias_demografia_con_coordenadas.csv` | - |

---

## 🛠️ Scripts Principales

### Pipeline Principal

```bash
# Pipeline completo: descarga y procesamiento de datos
python indice_delictivo_hermosillo_main.py
```

Este script orquesta:
1. **Descarga de datos** desde Hugging Face (`download_raw_data.py`)
2. **Procesamiento interim** con estandarización y feature engineering (`make_interim_data.py`)

### Procesamiento de Colonias

```bash
# 1. Extraer y normalizar colonias del dataset procesado
python notebooks/extraer_colonias_unicas_reportes_911.py

# 2. Geocodificación incremental (solo colonias nuevas)
python notebooks/geocodificar_colonias_reportes_911.py
```

### Limpieza de Demografía

```bash
# Normalizar espacios en datos demográficos
python notebooks/normalizar_espacios_demografia.py
```

### Análisis

```bash
# Analizar calidad de datos demográficos
python notebooks/analizar_calidad_datos_demografia.py
```

---

## ⚙️ Configuración

### Requisitos

```bash
# Python 3.10+
pip install -r requirements.txt
```

**Dependencias principales**:
- `pandas>=2.0.0` - Manipulación de datos
- `googlemaps>=4.10.0` - Geocodificación
- `python-dotenv>=1.0.0` - Variables de entorno

### Google Maps API

Para usar el script de geocodificación:

1. Obtén una API key de [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita la **Geocoding API**
3. Crea un archivo `.env` en la raíz del proyecto:

```env
GOOGLE_MAPS_API_KEY=tu_api_key_aqui
```

⚠️ **IMPORTANTE**: Nunca subas tu API key al repositorio. El archivo `.env` está protegido por `.gitignore`.

Ver [`SECURITY.md`](SECURITY.md) para más detalles de seguridad.

---

## 📖 Documentación

- **[Proceso de Limpieza de Datos](docs/PROCESO_LIMPIEZA_DATOS.md)**: Documentación completa del flujo de trabajo
- **[Seguridad](SECURITY.md)**: Guía de manejo seguro de credenciales

---

## 📁 Organización del Proyecto

```
├── data/
│   ├── raw/                    # Datos originales (sin modificar)
│   └── processed/              # Datos limpios y procesados
│
├── notebooks/                  # Scripts de análisis y procesamiento
│   ├── 01_auto_eda_SweetViz.ipynb            # Análisis exploratorio automático usando SweetViz
│   ├── 01_auto_eda_ydata.ipynb               # Análisis exploratorio automático usando YDataProfiler
│   ├── 02_analisis_exploratorio.ipynb        # Análisis exploratorio manual
│   ├── 03_analisis_pca_y_generacion_indices.ipynb    # Análisis PCA
│   ├── extraer_colonias_unicas_reportes_911.py
│   ├── geocodificar_colonias_reportes_911.py
│   ├── normalizar_espacios_demografia.py
│   ├── mapa_interactivo_folium_avanzado.py    # Generador de mapa interactivo - mapa_interactivo_hermosillo.html
│   └── analizar_calidad_datos_demografia.py
│
├── references/                       # Documentación del proyecto
│   ├── Diccionario de Datos para Mapeo de Incidentes.md    # Diccionario de datos
│   └──  Análisis y Justificación del Sistema de Clasificación de Severidad de Incidentes para Servicios de Emergencia.md
|
├── docs/                       # Documentación del proyecto
│   ├── CAMBIO_FUENTE_POLIGONOS.md    # Diccionario de datos
│   ├── DICCIONARIO_DE_DATOS.md
│   ├── GIT_DATA_MANAGEMENT.md
│   ├── METODOLOGIA_PCA.md
│   ├── PROCESO_LIMPIEZA_DATOS.md
│   ├── README.md
│   └── RESUMEN_EJECUTIVO.md
|
├── reports/                       # Reportes de análisis
│   ├── figures/                      # Gráficas en PNG del análisis exploratorio manual
│   ├──1.0-EDA_YDataProfiler.html     # Primer reporte automatizado EDA
│   ├── 2.0-EDA_YDataProfiler.html    # Segundo reporte automatizado EDA
│   ├── Presentacion_delitoHMO.pptx   # Presentación de hallazgos de análisis exploratorio, PowerPoint
│   └── reporte_delitosHMO.html       # Reporte de hallazgos y análisis exploratorio
│
├── .env                        # Variables de entorno (NO SUBIR)
├── .gitignore                  # Archivos ignorados por Git
├── SECURITY.md                 # Guía de seguridad
├── requirements.txt            # Requisitos para environment (librerías, interpretes, etc.)
├── mapa_interactivo_hermosillo.html    #Mapa interactivo de Hermosillo con información demográfica y de delitos
└── README.md                   # Este archivo
```

---

## 🔬 Metodología de Limpieza

### Pipeline de Datos

**Flujo**: Hugging Face → Raw → Interim → Processed

1. **Descarga** (`download_raw_data.py`):
   - Fuente: Hugging Face dataset `Marcelinux/llamadas911_colonias_hermosillo_2018_2025`
   - Formato: Excel multi-hoja (8 hojas: 2018-2025)
   - Output: `data/raw/reportes_de_incidentes_2018_2025.csv`

2. **Procesamiento Interim** (`make_interim_data.py`):
   - **Estandarización**: 475 tipos de incidentes → 198 únicos (mapa de normalización)
   - **Categorización**: 12 categorías principales de incidentes
   - **Niveles de severidad**: BAJA, MEDIA, ALTA (200 reglas)
   - **Feature Engineering**:
     * `ParteDelDia`: Madrugada/Mañana/Tarde/Noche
     * `DiaDeLaSemana`: Lunes-Domingo
     * `EsFinDeSemana`: Boolean
     * `Mes`: 1-12
     * `EsQuincena`: Boolean (días 1, 14-16, 28-31)
   - **Optimización**: Columnas temporales redundantes eliminadas (FECHA, HORA, Año_Reporte)
   - Output: `data/interim/reportes_de_incidentes_procesados_2018_2025.csv` (~310MB)

### Normalización de Colonias

**Problema**: 2,296 nombres de colonias con múltiples errores ortográficos

**Solución**: Algoritmo de fuzzy matching que:
1. Normaliza texto (acentos, mayúsculas, espacios)
2. Calcula similitud entre nombres (90% umbral)
3. Valida que sean variantes reales (no colonias diferentes)
4. Selecciona el nombre más frecuente como representativo

**Resultado**: 2,047 colonias únicas consolidadas (220 grupos con variantes)

### Geocodificación Incremental

**Proceso**: Google Maps Geocoding API con sistema anti-duplicados
- Detección automática de colonias ya geocodificadas
- Solo procesa colonias nuevas (ahorro de costos)
- Formato: `"{colonia}, Hermosillo, Sonora, México"`
- Delay: 0.2s entre peticiones
- Tasa de éxito: ~100%

---

## � Análisis Exploratorio de Datos

El análisis exploratorio de datos (EDA) del proyecto se realiza a través de múltiples enfoques:

### 📁 Análisis Automatizados
Los análisis automatizados se encuentran en los siguientes notebooks:

- **`notebooks/01_auto_eda_SweetViz.ipynb`**: Análisis automático interactivo usando **SweetViz**, que genera reportes HTML con perfiles de datos, distribuciones, correlaciones y relaciones bivariadas
- **`notebooks/01_auto_eda_ydata.ipynb`**: Análisis automático usando **YData Profiling**, que proporciona un análisis profundo de calidad de datos, variables, interacciones y alertas

### 🔬 Análisis Exploratorio Manual
- **`notebooks/02_analisis_exploratorio.ipynb`**: Análisis exploratorio completo realizado manualmente que incluye:
  - ✅ Análisis detallado de datos faltantes
  - ✅ Detección de anomalías mediante múltiples técnicas (Z-Score, IQR, Isolation Forest)
  - ✅ Visualización de relaciones entre variables (pair plots, distribuciones, scatter plots)
  - ✅ Análisis de correlación y multicolinealidad
  - ✅ Reducción dimensional mediante PCA
  - ✅ Conclusiones estadísticas y recomendaciones accionables

---

## �📈 Métricas de Calidad

| Dataset | Registros | Colonias Únicas | Variantes Detectadas | Calidad |
|---------|-----------|-----------------|----------------------|---------|
| Datos Policiales (2018-2025) | 2,297,081 | 2,047 | 220 grupos (-9.8%) | ⭐⭐⭐⭐ |
| Datos Demográficos | 660 | 659 | 1 (-0.15%) | ⭐⭐⭐⭐⭐ |

### Estandarización de Incidentes

| Métrica | Valor |
|---------|-------|
| Tipos originales | 475 |
| Tipos estandarizados | 198 |
| Categorías principales | 12 |
| Niveles de severidad | 3 (BAJA, MEDIA, ALTA) |
| Periodo de datos | 2018-01-01 a 2025-09-30 |

---

## 👥 Equipo

**Organización**: Equipo-seguridad-y-desarrollo  
**Rama actual**: `colonias_geolocalizadas_unificadas`

---

## 📄 Licencia

Este proyecto está bajo licencia [LICENSE](LICENSE).

---

## 🤝 Contribuciones

Para contribuir al proyecto:
1. Revisa la documentación en [`docs/`](docs/)
2. Sigue las convenciones de nomenclatura establecidas
3. Documenta todos los cambios importantes
4. Nunca subas credenciales o API keys

---

*Última actualización: 18 de noviembre de 2025*

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         indice-delictivo-hermosillo and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── -reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── indice-delictivo-hermosillo   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes indice-delictivo-hermosillo a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

