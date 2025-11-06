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

- **Limpieza de datos policiales**: 1,267 colonias únicas identificadas
- **Geocodificación**: Coordenadas obtenidas para todas las colonias vía Google Maps API
- **Limpieza de datos demográficos**: 659 colonias con información poblacional
- **Documentación completa** del proceso de limpieza y normalización

### 🔄 En Proceso

- Validación cruzada entre datasets
- Análisis geoespacial de incidentes
- Visualización de datos en mapas interactivos

---

## 📊 Datasets

### Datos Crudos (`data/raw/`)

| Archivo | Registros | Descripción |
|---------|-----------|-------------|
| `213.csv` | 349,131 | Incidentes reportados a servicios de emergencia |
| `demografia_hermosillo.csv` | 660 | Datos demográficos por colonia (INEGI 2020) |
| `delitos.csv` | - | Catálogo de tipos de delitos |
| `poligonos_hermosillo.csv` | - | Polígonos geográficos de colonias |

### Datos Procesados (`data/processed/`)

| Archivo | Descripción |
|---------|-------------|
| `colonias_unicas_reportes_911.csv` | 1,267 colonias limpias del dataset policial |
| `colonias_reportes_911_con_coordenadas.csv` | Colonias con coordenadas geográficas (lat/lng) |
| `colonias_reportes_911_agrupadas_reporte.csv` | Reporte de variantes ortográficas detectadas |
| `mapeo_colonias_reportes_911.csv` | Mapeo de colonias originales a normalizadas |
| `demografia_limpio.csv` | Datos demográficos normalizados |
| `colonias_unicas_demografia.csv` | Lista de colonias únicas de demografía |

---

## 🛠️ Scripts Principales

### Limpieza de Datos

```bash
# 1. Extraer y normalizar colonias del dataset policial (reportes 911)
python notebooks/extraer_colonias_unicas_reportes_911.py

# 2. Obtener coordenadas geográficas (requiere API key)
python notebooks/geocodificar_colonias_reportes_911.py

# 3. Normalizar espacios en datos demográficos
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
│   ├── extraer_colonias_unicas_reportes_911.py
│   ├── geocodificar_colonias_reportes_911.py
│   ├── normalizar_espacios_demografia.py
│   └── analizar_calidad_datos_demografia.py
│
├── docs/                       # Documentación del proyecto
│   └── PROCESO_LIMPIEZA_DATOS.md
│
├── .env                        # Variables de entorno (NO SUBIR)
├── .gitignore                  # Archivos ignorados por Git
├── SECURITY.md                 # Guía de seguridad
└── README.md                   # Este archivo
```

---

## 🔬 Metodología de Limpieza

### Normalización de Colonias

**Problema**: 1,407 nombres de colonias con múltiples errores ortográficos

**Solución**: Algoritmo de fuzzy matching que:
1. Normaliza texto (acentos, mayúsculas, espacios)
2. Calcula similitud entre nombres (90% umbral)
3. Valida que sean variantes reales (no colonias diferentes)
4. Selecciona el nombre más frecuente como representativo

**Resultado**: 1,267 colonias únicas consolidadas

### Geocodificación

**Proceso**: Google Maps Geocoding API
- Formato: `"{colonia}, Hermosillo, Sonora, México"`
- Delay: 0.2s entre peticiones
- Tasa de éxito: 100%

---

## 📈 Métricas de Calidad

| Dataset | Registros | Colonias Únicas | Duplicados Eliminados | Calidad |
|---------|-----------|-----------------|----------------------|---------|
| Datos Policiales | 349,131 | 1,267 | 140 (-10%) | ⭐⭐⭐ |
| Datos Demográficos | 660 | 659 | 1 (-0.15%) | ⭐⭐⭐⭐⭐ |

---

## 👥 Equipo

**Organización**: Equipo-seguridad-y-desarrollo  
**Rama actual**: `correccionColoniasPoblacion`

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

*Última actualización: 5 de noviembre de 2025*

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
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
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

