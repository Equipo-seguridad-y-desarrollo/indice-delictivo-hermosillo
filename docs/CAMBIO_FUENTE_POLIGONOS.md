# 📍 Actualización: Nueva Fuente de Datos de Polígonos

**Fecha**: 10 de noviembre de 2025  
**Versión**: 5.0  
**Cambio Principal**: Migración a shapefile INE_Limpio como fuente primaria de polígonos

---

## 🎯 Resumen del Cambio

Este proyecto ha migrado la fuente de datos de **polígonos geográficos** de un archivo CSV estático a un proceso automatizado que descarga y procesa el shapefile oficial **INE_Limpio.shp** desde el repositorio público de datos abiertos de Sonora.

### ¿Qué cambió?

**Antes (v4.0 y anteriores)**:
- Archivo `poligonos_hermosillo.csv` existía en `data/raw/` sin documentación de origen
- No había proceso claro de cómo se generaba
- No se podía actualizar fácilmente con datos nuevos
- Falta de trazabilidad de la fuente

**Ahora (v5.0)**:
- Script `colonias_poligonos.py` descarga shapefile oficial automáticamente
- Proceso completamente documentado y reproducible
- Fuente trazable: Repositorio público de Luis Moreno (Sonora-en-Datos)
- Integrado al pipeline automatizado
- Datos oficiales del INE con alta calidad

---

## 📦 Fuente de Datos

### Repositorio Público
- **Proyecto**: [ColoniasSonora](https://github.com/Sonora-en-Datos/ColoniasSonora)
- **Autor**: Luis Moreno (Sonora en Datos)
- **Archivo**: `INE_Limpio.shp` (Marco Geoestadístico Nacional)
- **Alcance**: Todo el estado de Sonora
- **Formato**: Shapefile (formato estándar SIG)

### Archivos del Shapefile
```
data/raw/
├── INE_Limpio.shp    # Geometrías
├── INE_Limpio.dbf    # Atributos (nombres, códigos)
├── INE_Limpio.shx    # Índice espacial
└── INE_Limpio.prj    # Sistema de coordenadas
```

---

## 🔄 Nuevo Script: `colonias_poligonos.py`

### Ubicación en el Pipeline

Este script representa la **Fase 0** del pipeline - el primer paso antes de cualquier procesamiento:

```
Fase 0: colonias_poligonos.py
   ↓
Fase 1: download_raw_data.py
   ↓
Fase 2: make_interim_data.py
   ↓
... (resto del pipeline)
```

### Funcionalidad

El script realiza 7 operaciones:

1. **Descarga automática**: Obtiene los 4 archivos del shapefile desde GitHub
2. **Carga geoespacial**: Lee el shapefile con GeoPandas
3. **Filtrado de geometrías**: Extrae solo Polygon y MultiPolygon válidos
4. **Filtrado geográfico**: Selecciona únicamente colonias de Hermosillo
5. **Análisis de tipos**: Identifica colonias con áreas discontinuas (MultiPolygon)
6. **Exportación a CSV**: Genera `poligonos_hermosillo.csv` para integración
7. **Reporte detallado**: Muestra estadísticas y primeras 20 colonias

### Salidas Generadas

```
data/raw/
├── INE_Limpio.shp (+ .dbf, .shx, .prj)  # Shapefile completo descargado
└── poligonos_hermosillo.csv              # ~700 colonias de Hermosillo
```

---

## 📊 Datos Obtenidos

### Información Geográfica

El shapefile INE_Limpio proporciona:

- **Geometrías precisas**: Polígonos con coordenadas exactas
- **Claves geográficas**: CVE_ENT, CVE_MUN, CVE_LOC, CVE_COL
- **Nombres oficiales**: Nombres estandarizados por el INE
- **Códigos postales**: CP de cada colonia
- **Clasificación**: Tipo de asentamiento (colonia, fraccionamiento, etc.)

### Datos del CONAPO (Índice de Marginación 2020)

Cada polígono incluye:

- **Indicadores demográficos**: Población total
- **Carencias sociales**: 11 indicadores (educación, servicios, vivienda)
- **Índice de Marginación**: IM_2020 (score numérico)
- **Grado de Marginación**: GM_2020 (categoría: Muy bajo, Bajo, Medio, Alto, Muy alto)
- **Índice Normalizado**: IMN_2020 (escala 0-1)

---

## 🔍 Sobre los MultiPolygon

### ¿Qué son?

Algunas colonias tienen geometrías tipo **MultiPolygon** (áreas discontinuas). **Esto NO es un error** sino una característica real del territorio.

### ¿Por qué existen?

Colonias pueden tener áreas separadas por:
- Avenidas principales o autopistas
- Vías de tren
- Parques o áreas públicas
- Ríos o canales
- Infraestructura urbana

### Ejemplo Real

```
COLONIA X (MultiPolygon)
   ├── Área 1: Norte de la Av. Principal
   └── Área 2: Sur de la Av. Principal
   
Ambas áreas pertenecen administrativamente a la misma colonia
```

### Estadísticas

El script reporta:
- Total de colonias Polygon (áreas continuas)
- Total de colonias MultiPolygon (áreas discontinuas)
- Ejemplos de colonias con MultiPolygon

---

## 🔗 Integración al Pipeline

### Pipeline Automatizado (PowerShell)

El script `run_pipeline.ps1` ahora incluye:

```powershell
# PASO 0: Descargar y procesar polígonos (NUEVO)
python notebooks/colonias_poligonos.py

# PASO 1: Descargar datos raw
python notebooks/download_raw_data.py

# ... (resto de pasos)
```

**Tiempo total del pipeline**: Aumentó ~1 minuto (de 20-30 min a 21-31 min)

### Makefile (comandos Make)

Nuevos comandos disponibles:

```bash
# Ejecutar solo descarga de polígonos
make poligonos

# Descargar datos raw
make download

# Procesar datos interim
make process

# Pipeline completo (incluye poligonos)
make pipeline
```

### Ejecución Manual

```bash
# Opción 1: PowerShell (Windows)
.\run_pipeline.ps1

# Opción 2: Make (cross-platform)
make pipeline

# Opción 3: Script individual
python notebooks/colonias_poligonos.py
```

---

## 📚 Documentación Actualizada

Se actualizaron los siguientes documentos:

### 1. `docs/DICCIONARIO_DE_DATOS.md`
- ✅ Sección de polígonos con origen del shapefile
- ✅ Explicación de MultiPolygon
- ✅ Proceso de generación documentado
- ✅ Total de registros actualizado (~700)

### 2. `README.md`
- ✅ Fase 0 agregada al pipeline manual
- ✅ Tabla de datasets actualizada con shapefile
- ✅ Sección de ejecución con nuevo paso

### 3. `docs/PROCESO_LIMPIEZA_DATOS.md`
- ✅ Nueva Fase 0 completa con explicación detallada
- ✅ Renumeración de fases (0-5 en lugar de 0-4)
- ✅ Tabla de tiempos actualizada
- ✅ Lista de scripts con colonias_poligonos.py

### 4. `run_pipeline.ps1`
- ✅ Paso 0 agregado al inicio
- ✅ Numeración actualizada (0/7, 1/7, ..., 6/7)
- ✅ Mensajes de progreso ajustados
- ✅ Resumen final con archivos generados

### 5. `Makefile`
- ✅ Nuevo comando `make poligonos`
- ✅ Comandos `download` y `process` separados
- ✅ Comando `pipeline` con dependencias ordenadas

---

## ✅ Beneficios del Cambio

### 1. **Trazabilidad**
- Fuente de datos claramente identificada
- Proceso completamente documentado
- Fácil verificación de datos originales

### 2. **Reproducibilidad**
- Pipeline 100% automatizado desde la fuente
- Cualquier persona puede ejecutar el proceso completo
- No depende de archivos "mágicos" sin origen conocido

### 3. **Actualización**
- Fácil actualización cuando haya nuevos datos del INE
- Solo ejecutar `python notebooks/colonias_poligonos.py`
- Proceso idempotente (se puede ejecutar múltiples veces)

### 4. **Calidad de Datos**
- Datos oficiales del Instituto Nacional Electoral
- Geometrías validadas y precisas
- Incluye índices de marginación (CONAPO 2020)

### 5. **Transparencia**
- Código abierto (repositorio público)
- Proceso auditable
- Contribución a datos abiertos en México

---

## 🚀 Migración para Usuarios Existentes

Si ya tenías el proyecto corriendo, estos son los pasos:

### Opción 1: Pipeline Completo (Recomendado)

```powershell
# Ejecuta todo el pipeline incluyendo polígonos nuevos
.\run_pipeline.ps1
```

### Opción 2: Solo Polígonos

```bash
# Si solo quieres actualizar los polígonos
python notebooks/colonias_poligonos.py
```

### Opción 3: Makefile

```bash
# Descarga solo polígonos
make poligonos

# O ejecuta pipeline completo
make pipeline
```

---

## 🔍 Validación de Resultados

Después de ejecutar el script, verifica:

### 1. Archivos Generados

```bash
# Verificar que existen los archivos
ls data/raw/INE_Limpio.*       # 4 archivos (.shp, .dbf, .shx, .prj)
ls data/raw/poligonos_hermosillo.csv
```

### 2. Número de Registros

```python
import pandas as pd

# Cargar CSV generado
poligonos = pd.read_csv('data/raw/poligonos_hermosillo.csv')
print(f"Total colonias: {len(poligonos)}")  # Debe ser ~700

# Verificar columnas clave
print(poligonos[['COLONIA', 'CP', 'POBTOT', 'GM_2020']].head())
```

### 3. Geometrías Válidas

```python
import geopandas as gpd
from shapely import wkt

# Cargar y validar geometrías
gdf = gpd.GeoDataFrame(
    poligonos,
    geometry=poligonos['POLIGONO_WKT'].apply(wkt.loads),
    crs='EPSG:4326'
)

# Validar tipos de geometría
print(gdf.geometry.type.value_counts())
# Debe mostrar: Polygon y MultiPolygon
```

---

## 📞 Soporte

Si tienes problemas con el nuevo script:

1. **Verifica dependencias**:
   ```bash
   pip install geopandas requests
   ```

2. **Revisa conectividad**:
   - El script necesita acceso a GitHub
   - URL: `https://github.com/Sonora-en-Datos/ColoniasSonora`

3. **Consulta logs**:
   - El script imprime información detallada del proceso
   - Errores se muestran claramente en consola

4. **Alternativa manual**:
   - Puedes descargar manualmente desde [el repositorio](https://github.com/Sonora-en-Datos/ColoniasSonora/tree/main/shapes/INE_Limpio)
   - Colocar archivos en `data/raw/`

---

## 🙏 Créditos

- **Shapefile INE_Limpio**: [Luis Moreno](https://github.com/Sonora-en-Datos) - Sonora en Datos
- **Fuente primaria**: Instituto Nacional Electoral (INE)
- **Índice de Marginación**: CONAPO 2020
- **Integración al proyecto**: Equipo-seguridad-y-desarrollo

---

## 📝 Changelog

### v5.0 (10 nov 2025)
- ✅ Script `colonias_poligonos.py` creado
- ✅ Integración a pipeline automatizado
- ✅ Documentación completa actualizada
- ✅ Comandos Makefile agregados
- ✅ Fuente de datos trazable y documentada

### v4.0 (6 nov 2025)
- Unificación de datos completa (100% demografía)
- Pipeline consolidado con 6 pasos

### v3.0 y anteriores
- Pipeline sin descarga automática de polígonos
- Fuente de `poligonos_hermosillo.csv` no documentada

---

**Última actualización**: 10 de noviembre de 2025  
**Equipo**: Equipo-seguridad-y-desarrollo  
**Proyecto**: indice-delictivo-hermosillo
