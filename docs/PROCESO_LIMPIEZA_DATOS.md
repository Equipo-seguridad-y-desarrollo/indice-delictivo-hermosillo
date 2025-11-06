# 📋 Documentación del Proceso de Limpieza de Datos
## Proyecto: Índice Delictivo Hermosillo

---

## 📊 Resumen del Proyecto

Este documento describe el proceso completo de limpieza, normalización y enriquecimiento de datos geográficos para el análisis del índice delictivo en Hermosillo, Sonora.

---

## 🗂️ Estructura de Datos

### Archivos de Entrada (Raw Data)
```
data/raw/
├── 213.csv                      # Datos de incidentes policiales
├── delitos.csv                  # Catálogo de tipos de delitos
├── demografia_hermosillo.csv    # Datos demográficos por colonia
├── diccionario_colonias.csv     # Diccionario de colonias
└── poligonos_hermosillo.csv     # Polígonos geográficos
```

### Archivos Generados (Processed Data)
```
data/processed/
├── colonias_unicas_reportes_911.csv                # Colonias únicas del archivo policial
├── colonias_reportes_911_agrupadas_reporte.csv    # Reporte de variantes detectadas
├── mapeo_colonias_reportes_911.csv                # Mapeo original → normalizada
├── colonias_reportes_911_con_coordenadas.csv      # Colonias con lat/lng de Google Maps
├── demografia_limpio.csv                          # Demografía con espacios normalizados
└── colonias_unicas_demografia.csv                 # Colonias únicas de demografía
```

---

## 🔄 Flujo del Proceso

### **Fase 1: Limpieza de Datos Policiales (213.csv)**

#### 1.1 Análisis Inicial
- **Archivo**: `213.csv`
- **Registros totales**: 349,131
- **Colonias originales**: 1,407
- **Problema identificado**: Múltiples errores ortográficos y variantes del mismo nombre

#### 1.2 Script: `extraer_colonias_unicas_reportes_911.py`

**Objetivo**: Identificar y agrupar colonias con errores ortográficos

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
- **Colonias únicas finales**: 1,267
- **Grupos con variantes**: 124
- **Variante representativa**: La más frecuente (asume que la mayoría escribe correctamente)

**Ejemplo de agrupación exitosa**:
```
'QUINTA ESMERALDA' (32 registros)
  - QUINTA ESMELRALDA (1)    ← Error tipográfico
  - QUINTA ESMERAL (1)       ← Nombre incompleto
  - QUINTA ESMERALDA (29)    ← ✓ Forma correcta (más frecuente)
  - QUINTA ESMERALDA| (1)    ← Carácter extra
```

**Archivos generados**:
- `colonias_unicas_reportes_911.csv`: Lista de 1,267 colonias limpias
- `colonias_reportes_911_agrupadas_reporte.csv`: Reporte detallado de variantes
- `mapeo_colonias_reportes_911.csv`: Mapeo de cada colonia original a su versión normalizada

---

### **Fase 2: Geocodificación con Google Maps API**

#### 2.1 Script: `geocodificar_colonias_reportes_911.py`

**Objetivo**: Obtener coordenadas geográficas (latitud/longitud) para cada colonia

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
- **Colonias procesadas**: 1,267
- **Tiempo aproximado**: 8-10 minutos
- **Tasa de éxito**: ~100% (todas encontradas)
- **Costo estimado**: ~$6.34 USD (incluido en crédito gratuito de $200/mes)

**Información obtenida por colonia**:
```csv
COLONIA, LATITUD, LONGITUD, DIRECCION_FORMATEADA, TIPO_UBICACION, PLACE_ID, TIPOS
```

**Ejemplo**:
```csv
QUINTA ESMERALDA,29.075595,-110.957462,"Quinta Esmeralda, 83000 Hermosillo, Son., Mexico",APPROXIMATE,ChIJ...,political|sublocality
```

**Archivo generado**:
- `colonias_reportes_911_con_coordenadas.csv`: 1,267 colonias con coordenadas

---

### **Fase 3: Limpieza de Datos Demográficos**

#### 3.1 Análisis: `analizar_calidad_datos_demografia.py`

**Objetivo**: Verificar calidad de datos demográficos

**Resultados del análisis**:
- **Registros totales**: 660
- **Colonias únicas**: 660
- **Calidad de datos**: ✓ Excelente (casi sin errores)

**Variantes detectadas inicialmente**: 11 grupos
- Mayoría eran colonias genuinamente diferentes
- Solo 1 error real detectado: `PRIMERO  HERMOSILLO` (doble espacio)

#### 3.2 Script: `normalizar_espacios_demografia.py`

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

### Datos Policiales (213.csv)
| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Colonias únicas | 1,407 | 1,267 | -10% (140 duplicados eliminados) |
| Errores detectados | 225 grupos | 124 grupos | Agrupación más precisa |
| Variantes por grupo | Hasta 6 | Hasta 4 | Mejor calidad |

### Datos Demográficos
| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Colonias únicas | 660 | 659 | -1 (1 duplicado) |
| Errores detectados | 1 | 0 | 100% limpio |

### Geocodificación
| Métrica | Valor |
|---------|-------|
| Colonias geocodificadas | 1,267 |
| Tasa de éxito | 100% |
| Tiempo total | ~8-10 min |
| Costo | ~$6.34 USD |

---

## 🔧 Scripts Desarrollados

### Scripts de Análisis
1. **`extraer_colonias_unicas.py`**
   - Análisis y agrupación de colonias con errores ortográficos
   - Algoritmo de fuzzy matching con validaciones

2. **`analizar_colonias_demografia.py`**
   - Análisis de calidad de datos demográficos
   - Detección de variantes

### Scripts de Procesamiento

1. **`extraer_colonias_unicas_reportes_911.py`**
   - Limpieza y normalización de nombres de colonias
   - Algoritmo de fuzzy matching (90% umbral)
   - Validación inteligente de variantes

2. **`geocodificar_colonias_reportes_911.py`**
   - Geocodificación con Google Maps API
   - Manejo seguro de credenciales

3. **`normalizar_espacios_demografia.py`**
   - Normalización de espacios en datos demográficos
   - Proceso minimalista (solo errores obvios)

4. **`analizar_calidad_datos_demografia.py`**
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
   - Comparar colonias entre `213.csv` y `demografia_hermosillo.csv`
   - Identificar colonias faltantes en cada dataset

2. **Enriquecimiento de Datos**
   - Unir coordenadas geográficas con datos demográficos
   - Crear dataset maestro de colonias

3. **Análisis Geoespacial**
   - Mapear incidentes delictivos por colonia
   - Análisis de densidad delictiva

4. **Visualización**
   - Crear mapas interactivos
   - Dashboards con métricas por colonia

---

## 📚 Dependencias

```bash
# Python packages
pandas>=2.0.0
googlemaps>=4.10.0
python-dotenv>=1.0.0

# API Services
Google Maps Geocoding API
```

---

## 👥 Equipo

**Equipo-seguridad-y-desarrollo**  
**Proyecto**: indice-delictivo-hermosillo  
**Rama actual**: correccionColoniasPoblacion

---

*Última actualización: 5 de noviembre de 2025*
