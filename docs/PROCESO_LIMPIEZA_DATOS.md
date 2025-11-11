# 📋 Documentación del Proceso de Limpieza de Datos
## Proyecto: Índice Delictivo Hermosillo

**Última actualización**: 10 de noviembre de 2025

---

## 📊 Resumen del Proyecto

Este documento describe el proceso completo de descarga, limpieza, normalización, estandarización y enriquecimiento de datos geográficos para el análisis del índice delictivo en Hermosillo, Sonora (2018-2025).

**Cambios importantes en v3.0**:
- ✅ Nueva Fase 0: Descarga y procesamiento de shapefile INE_Limpio
- ✅ Script colonias_poligonos.py para obtener polígonos desde fuente pública
- ✅ Trazabilidad completa de la fuente de datos geográficos
- ✅ Pipeline automatizado incluye descarga de shapefiles

**Cambios importantes en v2.0**:
- ✅ Migración de Google Drive a Hugging Face para descarga de datos
- ✅ Pipeline consolidado para procesamiento multi-año (2.3M registros)
- ✅ Estandarización de 475 tipos de incidentes a 198 categorías
- ✅ Feature engineering: 7 columnas derivadas (temporal, categórica, severidad)
- ✅ Geocodificación incremental para optimizar costos de API
- ✅ Optimización de esquema (10 columnas esenciales)

---

## 🗂️ Estructura de Datos

### Archivos de Entrada (Raw Data)
```
data/raw/
├── 213.xlsx                         # Datos de incidentes 911 (8 hojas: 2018-2025)
├── reportes_de_incidentes_2018_2025.csv  # Consolidado de Excel
├── delitos.csv                      # Catálogo de tipos de delitos
├── INE_Limpio.shp (+ .dbf, .shx, .prj)  # Shapefile de colonias (descargado)
├── demografia_hermosillo.csv        # Datos demográficos por colonia
└── poligonos_hermosillo.csv         # Polígonos geográficos (generado desde shapefile)
```

### Archivos Intermedios (Interim Data)
```
data/interim/
└── reportes_de_incidentes_procesados_2018_2025.csv  # 2.3M registros procesados (~310MB)
```

### Archivos Generados (Processed Data)
```
data/processed/
├── colonias_unicas_reportes_911.csv                # 2,047 colonias únicas
├── colonias_reportes_911_agrupadas_reporte.csv    # Reporte de 220 grupos con variantes
├── mapeo_colonias_reportes_911.csv                # Mapeo de 2,296 variantes → 2,047 únicas
├── colonias_reportes_911_con_coordenadas.csv      # Colonias con lat/lng (geocodificadas)
├── demografia_limpio.csv                          # Demografía con espacios normalizados
└── colonias_unicas_demografia.csv                 # 659 colonias únicas de demografía
```

---

## 🔄 Flujo del Proceso

### **Fase 0: Preparación de Polígonos Geográficos**

#### 0.1 Script: `colonias_poligonos.py`

**Objetivo**: Descargar y procesar el shapefile oficial de colonias de Sonora para extraer los polígonos de Hermosillo

**Nueva fuente de datos**:
- **Repositorio**: [ColoniasSonora](https://github.com/Sonora-en-Datos/ColoniasSonora) de Luis Moreno
- **Archivo**: `INE_Limpio.shp` (Marco Geoestadístico Nacional del INE)
- **Alcance**: Todo el estado de Sonora
- **Calidad**: Datos oficiales verificados por el INE

**Proceso**:
```python
# 1. Descarga automática de archivos del shapefile
repo_url = "https://github.com/Sonora-en-Datos/ColoniasSonora/raw/main/shapes/INE_Limpio/"
files = ["INE_Limpio.shp", "INE_Limpio.dbf", "INE_Limpio.shx", "INE_Limpio.prj"]

# 2. Cargar shapefile completo
gdf_completo = gpd.read_file("INE_Limpio.shp")

# 3. Filtrar geometrías válidas (Polygon + MultiPolygon)
gdf_poligonos = gdf_completo[gdf_completo.geometry.type.isin(['Polygon', 'MultiPolygon'])]

# 4. Filtrar solo Hermosillo
gdf_hermosillo = gdf_poligonos[gdf_poligonos['nom_loc'] == 'Hermosillo']

# 5. Exportar a CSV
gdf_hermosillo.to_csv('data/raw/poligonos_hermosillo.csv', index=False)
```

**Resultados**:
- **Registros totales del shapefile**: Varios miles (todo Sonora)
- **Colonias de Hermosillo extraídas**: ~700
- **Tipos de geometría incluidos**: 
  - Polygon: Colonias con área continua
  - MultiPolygon: Colonias con áreas discontinuas (no son errores)
- **Archivo generado**: `data/raw/poligonos_hermosillo.csv`

**Por qué MultiPolygon no es un error**:
Algunas colonias tienen áreas geográficas separadas por infraestructura (avenidas, vías de tren, etc.) pero mantienen el mismo nombre administrativo. Ejemplos comunes:
- Colonias divididas por avenidas principales
- Fraccionamientos con secciones separadas
- Colonias con parques o áreas públicas intermedias

**Información obtenida**:
- Geometrías (polígonos en formato WKT)
- Claves geográficas (CVE_COL, CVE_ENT, CVE_MUN)
- Nombres oficiales de colonias
- Códigos postales
- Datos del Índice de Marginación 2020 (CONAPO)
- Indicadores de carencias sociales

---

### **Fase 1: Descarga y Consolidación de Datos**

#### 1.1 Script: `download_raw_data.py`

**Objetivo**: Descargar datos desde Hugging Face y consolidar Excel multi-hoja en CSV único

**Migración realizada**:
- **Antes**: Google Drive API con autenticación OAuth2
- **Después**: Descarga directa HTTP desde Hugging Face
- **Beneficio**: Sin autenticación, más simple, más confiable

**Proceso**:
```python
# 1. Descarga desde Hugging Face
url = "https://huggingface.co/datasets/Marcelinux/llamadas911_colonias_hermosillo_2018_2025/resolve/main/213.xlsx"
response = requests.get(url, stream=True)

# 2. Lectura multi-hoja
all_sheets = pd.read_excel(BytesIO(response.content), sheet_name=None)

# 3. Extracción de año desde nombre de hoja
for sheet_name, df_sheet in all_sheets.items():
    year = int(sheet_name)  # "2018" → 2018
    df_sheet['Año_Reporte'] = year

# 4. Consolidación
df_consolidated = pd.concat(list_dfs, ignore_index=True)
```

**Resultados**:
- **Hojas procesadas**: 8 (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
- **Registros totales**: 2,297,081
- **Columnas originales**: COLONIA, TIPO DE INCIDENTE, FECHA, HORA
- **Columna añadida**: Año_Reporte
- **Archivo generado**: `data/raw/reportes_de_incidentes_2018_2025.csv`

---

### **Fase 2: Procesamiento Interim - Estandarización y Feature Engineering**

#### 2.1 Script: `make_interim_data.py`

**Objetivo**: Estandarizar tipos de incidentes, categorizar, generar features temporales y optimizar esquema

**Componentes del procesamiento**:

##### A. Estandarización de Tipos de Incidentes
```python
MAPA_DE_INCIDENTES = {
    # 475 reglas de mapeo
    "PORTACION DE ARMAS O CARTUCHOS": "PORTACIÓN DE ARMAS O CARTUCHOS",
    "PERSONA AGRESIVA": "PERSONA AGRESIVA",
    "APOYO A LA CIUDADANIA": "APOYO A LA CIUDADANÍA",
    # ... 472 reglas más
}

# Aplicar normalización
df['TIPO DE INCIDENTE'] = df['TIPO DE INCIDENTE'].map(MAPA_DE_INCIDENTES)
```

**Resultados estandarización**:
- **Tipos originales**: 475 variantes
- **Tipos únicos post-mapeo**: 198
- **Registros sin mapeo**: 7 (mantienen valor original)
- **Reducción**: 58% en variabilidad

##### B. Categorización de Incidentes
```python
CATEGORIAS_INCIDENTES = {
    # 216 reglas de categorización en 12 grupos
    "PORTACIÓN DE ARMAS O CARTUCHOS": "Armas y Objetos Peligrosos",
    "PERSONA AGRESIVA": "Violencia y Agresión",
    "APOYO A LA CIUDADANÍA": "Apoyo Ciudadano",
    # ... 213 reglas más
}

df['Categoria_Incidente'] = df['TIPO DE INCIDENTE'].map(CATEGORIAS_INCIDENTES).fillna('Otros')
```

**12 Categorías principales**:
1. Violencia y Agresión
2. Tránsito y Vehículos
3. Apoyo Ciudadano
4. Delitos Patrimoniales
5. Alteración del Orden
6. Sospechosos y Vigilancia
7. Menores y Familia
8. Armas y Objetos Peligrosos
9. Emergencias Médicas
10. Fenómenos Naturales
11. Espacios Públicos
12. Otros

##### C. Clasificación de Severidad
```python
NIVEL_SEVERIDAD = {
    # 200 reglas de clasificación
    "PORTACIÓN DE ARMAS O CARTUCHOS": "ALTA",
    "PERSONA AGRESIVA": "MEDIA",
    "APOYO A LA CIUDADANÍA": "BAJA",
    # ... 197 reglas más
}

df['Nivel_Severidad'] = df['TIPO DE INCIDENTE'].map(NIVEL_SEVERIDAD).fillna('MEDIA')
```

**3 Niveles de severidad**:
- **ALTA**: Incidentes graves (armas, agresión violenta, allanamiento)
- **MEDIA**: Incidentes moderados (persona agresiva, vehículo sospechoso)
- **BAJA**: Incidentes leves (apoyo ciudadano, animales en vía pública)

##### D. Feature Engineering Temporal
```python
# 1. Timestamp consolidado
df['Timestamp'] = pd.to_datetime(df['FECHA'] + ' ' + df['HORA'].astype(str) + ':00:00')

# 2. Parte del día (binning de horas)
df['ParteDelDia'] = pd.cut(
    df['Timestamp'].dt.hour, 
    bins=[-1, 5, 11, 17, 23], 
    labels=['Madrugada', 'Mañana', 'Tarde', 'Noche']
)

# 3. Día de la semana
dias_map = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 
            4:'Viernes', 5:'Sábado', 6:'Domingo'}
df['DiaDeLaSemana'] = df['Timestamp'].dt.dayofweek.map(dias_map)

# 4. Fin de semana
df['EsFinDeSemana'] = df['Timestamp'].dt.dayofweek.isin([5, 6]).map({True: 'Sí', False: 'No'})

# 5. Mes
df['Mes'] = df['Timestamp'].dt.month

# 6. Quincena (días de pago típicos)
dias_quincena = [1, 14, 15, 16, 28, 29, 30, 31]
df['EsQuincena'] = df['Timestamp'].dt.day.isin(dias_quincena).map({True: 'Sí', False: 'No'})
```

##### E. Optimización de Esquema
```python
# Columnas redundantes eliminadas: FECHA, HORA, Año_Reporte
# Solo se mantiene Timestamp como referencia temporal única

final_cols = [
    'COLONIA',
    'TIPO DE INCIDENTE',
    'Timestamp',
    'ParteDelDia',
    'DiaDeLaSemana',
    'EsFinDeSemana',
    'Mes',
    'EsQuincena',
    'Categoria_Incidente',
    'Nivel_Severidad'
]

df_final = df[final_cols]
```

**Optimización lograda**:
- **Antes**: 13 columnas (COLONIA, TIPO, FECHA, HORA, Año, Timestamp, + 7 derivadas)
- **Después**: 10 columnas (eliminadas FECHA, HORA, Año_Reporte redundantes)
- **Beneficio**: -23% tamaño, menos confusión temporal

**Archivo generado**:
- **Ruta**: `data/interim/reportes_de_incidentes_procesados_2018_2025.csv`
- **Tamaño**: ~310 MB
- **Registros**: 2,297,081
- **Periodo**: 2018-01-01 00:00:00 a 2025-09-30 23:00:00
- **Encoding**: UTF-8 con BOM (utf-8-sig)

---

### **Fase 3: Limpieza de Datos Policiales - Extracción de Colonias**

#### 3.1 Migración del Script

**Cambio importante**: `extraer_colonias_unicas_reportes_911.py` migrado para usar datos procesados del interim

- **Antes**: Usaba `data/raw/213.csv` (obsoleto)
- **Después**: Usa `data/interim/reportes_de_incidentes_procesados_2018_2025.csv`
- **Beneficio**: Opera sobre datos ya estandarizados y enriquecidos

#### 3.2 Análisis Inicial
- **Archivo**: `reportes_de_incidentes_procesados_2018_2025.csv`
- **Registros totales**: 2,297,081
- **Colonias originales**: 2,296
- **Problema identificado**: Múltiples errores ortográficos y variantes del mismo nombre

#### 3.3 Algoritmo de Normalización

**Objetivo**: Identificar y agrupar colonias con errores ortográficos usando fuzzy matching

**Algoritmo implementado**:

```python
# 1. Normalización de texto
def normalizar_texto(texto):
    - Convertir a MAYÚSCULAS
    - Remover acentos
    - Normalizar espacios múltiples
    
# 2. Cálculo de similitud
- Usar SequenceMatcher de difflib
- Umbral: 90% de similitud

# 3. Validación de variantes
def son_variantes_validas():
    ✓ Detectar números romanos diferentes (VI ≠ VIII)
    ✓ Detectar números arábigos diferentes (1 ≠ 2)
    ✓ Detectar sectores/etapas diferentes
    ✓ Detectar nombres distintivos diferentes
    ✓ Solo agrupar errores ortográficos reales
```

**Reglas de agrupación**:
1. **SÍ agrupar**:
   - Diferencias solo en acentos: `JESÚS` ↔ `JESUS`
   - Errores tipográficos: `PUERTA` ↔ `PUERAT`
   - Espacios inconsistentes: `LOS OLIVOS` ↔ `LO OLIVOS`

2. **NO agrupar**:
   - Números diferentes: `LAS PEREDAS` ≠ `LAS PEREDAS 2`
   - Números romanos: `PUERTA REAL VI` ≠ `PUERTA REAL VIII`
   - Sectores diferentes: `SOLIDARIDAD IV` ≠ `SOLIDARIDAD V`
   - Nombres distintivos: `PINOS` ≠ `ENCINOS`

**Resultados**:
- **Colonias únicas finales**: 2,047
- **Grupos con variantes**: 220
- **Registros mapeados**: 2,296
- **Variante representativa**: La más frecuente (asume que la mayoría escribe correctamente)

**Ejemplo de agrupación exitosa**:
```
'QUINTA ESMERALDA' (1,511 registros)
  - QUINTA ESMELRALDA (1)    ← Error tipográfico
  - QUINTA ESMERAL (1)       ← Nombre incompleto
  - QUINTA ESMERALDA (1,508) ← ✓ Forma correcta (más frecuente)
  - QUINTA ESMERALDA| (1)    ← Carácter extra
```

**Archivos generados**:
- `colonias_unicas_reportes_911.csv`: Lista de 2,047 colonias limpias
- `colonias_reportes_911_agrupadas_reporte.csv`: Reporte detallado de 220 grupos con variantes
- `mapeo_colonias_reportes_911.csv`: Mapeo de cada una de las 2,296 colonias originales a su versión normalizada

---

###**Fase 4: Geocodificación con Google Maps API**

#### 4.1 Script: `geocodificar_colonias_reportes_911.py`

**Objetivo**: Obtener coordenadas geográficas (latitud/longitud) para cada colonia con sistema incremental

**Mejora implementada**: **Geocodificación Incremental**

**Antes (v1.0)**:
- Geocodificaba todas las colonias en cada ejecución
- Costo: ~$6 USD por ejecución completa
- Tiempo: ~8-10 minutos
- Problema: Re-procesar colonias ya geocodificadas desperdicia tiempo y dinero

**Después (v2.0)**:
- Detecta automáticamente colonias ya geocodificadas
- Solo procesa colonias nuevas
- **1era ejecución**: Geocodifica 2,047 colonias (~8-10 min, ~$6 USD)
- **Ejecuciones posteriores**: Solo colonias nuevas (segundos, $0.00)
- Combina geocodificaciones previas con nuevas en archivo único

**Lógica incremental**:
```python
# 1. Verificar si existe archivo de salida
if os.path.exists(archivo_salida):
    df_previas = pd.read_csv(archivo_salida)
    colonias_ya_geocodificadas = set(df_previas['COLONIA'].unique())
    
    # 2. Filtrar solo colonias nuevas
    df_colonias = df_colonias[~df_colonias['COLONIA'].isin(colonias_ya_geocodificadas)]
    
    if len(df_colonias) == 0:
        print("[OK] Todas las colonias ya están geocodificadas")
        return df_previas

# 3. Geocodificar solo las nuevas
# ... proceso de geocodificación ...

# 4. Combinar previas + nuevas
df_resultados = pd.concat([df_previas, df_nuevas], ignore_index=True)
```

**Configuración de seguridad**:
```python
# ✓ API Key en variable de entorno (.env)
GOOGLE_MAPS_API_KEY=tu_api_key_aqui

# ✓ Protección con .gitignore
.env  # Nunca subir al repositorio
```

**Parámetros de geocodificación**:
```python
direccion = f"{colonia}, Hermosillo, Sonora, México"
delay = 0.2  # segundos entre peticiones (evitar límites de API)
```

**Resultados**:
- **Colonias procesadas**: 2,047
- **Tiempo aproximado**: 8-10 minutos (primera ejecución)
- **Tasa de éxito**: ~100% (todas encontradas)
- **Costo estimado inicial**: ~$6.34 USD (incluido en crédito gratuito de $200/mes)
- **Ejecuciones posteriores**: Solo colonias nuevas (ahorro significativo)

**Información obtenida por colonia**:
```csv
COLONIA, LATITUD, LONGITUD, DIRECCION_FORMATEADA, TIPO_UBICACION, PLACE_ID, TIPOS, TIMESTAMP
```

**Ejemplo**:
```csv
QUINTA ESMERALDA,29.075595,-110.957462,"Quinta Esmeralda, 83000 Hermosillo, Son., Mexico",APPROXIMATE,ChIJ...,political|sublocality,2025-11-06T15:30:45
```

**Archivo generado**:
- `colonias_reportes_911_con_coordenadas.csv`: 2,047 colonias con coordenadas y metadata

---

### **Fase 5: Limpieza de Datos Demográficos**

#### 5.1 Análisis: `analizar_calidad_datos_demografia.py`

**Objetivo**: Verificar calidad de datos demográficos

**Resultados del análisis**:
- **Registros totales**: 660
- **Colonias únicas**: 660
- **Calidad de datos**: ✓ Excelente (casi sin errores)

**Variantes detectadas inicialmente**: 11 grupos
- Mayoría eran colonias genuinamente diferentes
- Solo 1 error real detectado: `PRIMERO  HERMOSILLO` (doble espacio)

#### 5.2 Script: `normalizar_espacios_demografia.py`

**Objetivo**: Normalizar solo errores obvios (espacios dobles)

**Proceso**:
```python
def normalizar_espacios(texto):
    return ' '.join(texto.split())
```

**Resultados**:
- **Correcciones aplicadas**: 2 registros
  - `PRIMERO  HERMOSILLO` → `PRIMERO HERMOSILLO`
  - `LA CORUÑA SECCION  PRIVADA ALMAR` → `LA CORUÑA SECCION PRIVADA ALMAR`
- **Colonias finales**: 659 (consolidó 1 duplicado)

**Archivos generados**:
- `demografia_limpio.csv`: Dataset limpio
- `colonias_unicas_demografia.csv`: 659 colonias únicas

---

## 📈 Métricas del Proceso

### Pipeline Completo

| Fase | Input | Output | Tiempo | Costo |
|------|-------|--------|--------|-------|
| 0. Polígonos | GitHub shapefile | 700 polígonos CSV | ~1 min | $0 |
| 1. Descarga | Hugging Face | 2.3M registros CSV | ~2 min | $0 |
| 2. Procesamiento Interim | Raw CSV | Procesado con 10 cols | ~5 min | $0 |
| 3. Extracción Colonias | Procesado | 2,047 colonias únicas | ~30 seg | $0 |
| 4. Geocodificación (1era) | Colonias únicas | Con coordenadas | ~8-10 min | ~$6 |
| 4. Geocodificación (subsec.) | Solo nuevas | Incremental | segundos | ~$0 |

### Datos Policiales (2018-2025)
| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Registros totales | 2,297,081 | 2,297,081 | - |
| Colonias únicas | 2,296 | 2,047 | -249 (-10.8%) |
| Tipos de incidentes | 475 | 198 | -277 (-58.3%) |
| Columnas | 4→13 | 10 | Optimizado |
| Errores detectados | 220 grupos | 0 | 100% normalizado |
| Variantes por grupo | Hasta 4 | - | Consolidadas |

### Estandarización y Enriquecimiento
| Métrica | Valor |
|---------|-------|
| Tipos estandarizados | 475 → 198 |
| Categorías creadas | 12 |
| Niveles de severidad | 3 (BAJA, MEDIA, ALTA) |
| Features temporales añadidas | 5 |
| Features categóricas añadidas | 2 |
| Periodo de datos | 2018-01-01 a 2025-09-30 |

### Datos Demográficos
| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Colonias únicas | 660 | 659 | -1 (1 duplicado) |
| Errores detectados | 1 | 0 | 100% limpio |

### Geocodificación
| Métrica | Valor |
|---------|-------|
| Colonias geocodificadas | 2,047 |
| Tasa de éxito | ~100% |
| Tiempo (1era ejecución) | ~8-10 min |
| Costo (1era ejecución) | ~$6.34 USD |
| Tiempo (ejecuciones posteriores) | segundos |
| Costo (ejecuciones posteriores) | $0.00 USD |

---

## 🔧 Scripts Desarrollados

### Scripts de Pipeline Principal

0. **`colonias_poligonos.py`**
   - Descarga automática del shapefile INE_Limpio desde GitHub
   - Filtrado de geometrías válidas (Polygon + MultiPolygon)
   - Extracción de colonias de Hermosillo (~700 registros)
   - Exportación a CSV para integración con pipeline

1. **`indice_delictivo_hermosillo_main.py`**
   - Orquestador del pipeline completo
   - Ejecuta descarga → procesamiento interim
   - Manejo de errores y logging

2. **`download_raw_data.py`**
   - Descarga desde Hugging Face
   - Consolidación de Excel multi-hoja
   - Extracción de años desde nombres de hojas

3. **`make_interim_data.py`**
   - Estandarización de 475 tipos de incidentes
   - Categorización en 12 grupos principales
   - Clasificación de severidad (3 niveles)
   - Feature engineering temporal (5 features)
   - Optimización de esquema (10 columnas)

### Scripts de Procesamiento de Colonias

5. **`extraer_colonias_unicas_reportes_911.py`**
   - Limpieza y normalización de nombres de colonias
   - Algoritmo de fuzzy matching (90% umbral)
   - Validación inteligente de variantes
   - Migrado para usar datos del interim

5. **`geocodificar_colonias_reportes_911.py`**
   - Geocodificación con Google Maps API
   - **Sistema incremental anti-duplicados** (v2.0)
   - Manejo seguro de credenciales
   - Delay entre peticiones (0.2s)

### Scripts de Análisis

6. **`normalizar_espacios_demografia.py`**
   - Normalización de espacios en datos demográficos
   - Proceso minimalista (solo errores obvios)

7. **`analizar_calidad_datos_demografia.py`**
   - Análisis de calidad de datos demográficos
   - Detección de posibles duplicados

---

## 🛡️ Seguridad

### Protección de Credenciales
```bash
# Archivo .env (NO SUBIR A GIT)
GOOGLE_MAPS_API_KEY=tu_api_key_aqui

# .gitignore
.env
.venv/
```

### Buenas Prácticas Implementadas
✓ API keys en variables de entorno  
✓ Validación de existencia de variables  
✓ Delay entre peticiones de API  
✓ Manejo de errores robusto  
✓ Documentación de seguridad (SECURITY.md)

---

## 📝 Nomenclatura y Convenciones

### Nombres de Variables
```python
# ✓ Descriptivos y en español
colonias_unicas        # Lista de colonias sin duplicados
frecuencias           # Diccionario {colonia: conteo}
umbral_similitud      # Float: 0.90

# ✓ Funciones verbos en infinitivo
normalizar_texto()
obtener_coordenadas()
son_variantes_validas()
```

### Nombres de Archivos
```
# Scripts - Patrón: {acción}_{objeto}_{fuente}.py
extraer_colonias_unicas_reportes_911.py
geocodificar_colonias_reportes_911.py
normalizar_espacios_demografia.py
analizar_calidad_datos_demografia.py

# Datos procesados - Patrón: {objeto}_{fuente}_{detalle}.csv
colonias_unicas_reportes_911.csv
colonias_reportes_911_con_coordenadas.csv
mapeo_colonias_reportes_911.csv
colonias_unicas_demografia.csv
demografia_limpio.csv
```

---

## 🎯 Próximos Pasos Sugeridos

1. **Validación Cruzada**
   - Comparar colonias entre reportes procesados y demografía
   - Identificar colonias faltantes en cada dataset
   - Análisis de cobertura geográfica

2. **Enriquecimiento de Datos**
   - Crear dataset maestro unificado con:
     * Reportes procesados (2.3M registros)
     * Coordenadas geográficas (2,047 colonias)
     * Datos demográficos (659 colonias)
     * Polígonos geográficos
   - Calcular métricas agregadas por colonia

3. **Análisis Temporal**
   - Explotar features temporales (ParteDelDia, DiaDeLaSemana, EsQuincena)
   - Identificar patrones estacionales
   - Análisis de tendencias 2018-2025

4. **Análisis por Categoría y Severidad**
   - Mapas de calor por nivel de severidad
   - Distribución de categorías por colonia
   - Identificación de zonas críticas

5. **Análisis Geoespacial**
   - Mapear incidentes delictivos por colonia
   - Análisis de densidad delictiva
   - Clusters espaciales (hotspots)
   - Correlación espacial con índice de marginación

6. **Visualización**
   - Crear mapas interactivos (Folium, Plotly)
   - Dashboards con métricas por colonia
   - Timeline de incidentes
   - Heatmaps por categoría y hora del día

---

## 📚 Dependencias

```bash
# Python packages
pandas>=2.0.0          # Manipulación de datos
googlemaps>=4.10.0     # Geocodificación
python-dotenv>=1.0.0   # Variables de entorno
requests>=2.31.0       # Descarga HTTP
openpyxl>=3.1.0        # Lectura de Excel

# API Services
Google Maps Geocoding API
Hugging Face Datasets
```

---

## 👥 Equipo

**Equipo-seguridad-y-desarrollo**  
**Proyecto**: indice-delictivo-hermosillo  
**Rama actual**: colonias_geolocalizadas_unificadas

---

*Última actualización: 10 de noviembre de 2025*
