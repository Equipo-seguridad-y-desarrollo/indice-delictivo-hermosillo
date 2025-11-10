# 🚀 Pipeline Completo: Dashboard Interactivo

## Pipeline de Ejecución para generar el Mapa/Dashboard

### 📊 OPCIÓN 1: Pipeline Completo (desde cero)

```bash
# ============================================
# PASO 1: Descargar datos raw desde Hugging Face
# ============================================
python notebooks/download_raw_data.py

# Entrada:  Ninguna (descarga desde HuggingFace)
# Salida:   data/raw/reportes_de_incidentes_2018_2025.csv (500MB)
# Tiempo:   ~2-5 minutos
# Descripción: Descarga 2.3M registros desde HuggingFace


# ============================================
# PASO 2: Procesar datos interim (limpieza + feature engineering)
# ============================================
python notebooks/make_interim_data.py

# Entrada:  data/raw/reportes_de_incidentes_2018_2025.csv
# Salida:   data/interim/reportes_de_incidentes_procesados_2018_2025.csv
# Tiempo:   ~3-5 minutos
# Descripción: 
#   - Estandarización de nombres de incidentes
#   - Asignación de severidad (ALTA/MEDIA/BAJA)
#   - Creación de 10 nuevas columnas (año, mes, trimestre, etc.)
#   - Normalización de nombres de colonias


# ============================================
# PASO 3: Geocodificar colonias de reportes 911
# ============================================
python notebooks/geocodificar_colonias_reportes_911.py

# Entrada:  data/interim/reportes_de_incidentes_procesados_2018_2025.csv
# Salida:   data/processed/colonias_reportes_911_con_coordenadas.csv
# Tiempo:   ~5-10 minutos (con caché incremental)
# Descripción: 
#   - Extrae colonias únicas de los reportes
#   - Geocodifica usando Google Maps API (con caché)
#   - ~2,117 colonias únicas


# ============================================
# PASO 4: Geocodificar colonias de demografía
# ============================================
python notebooks/geocodificar_colonias_demografia.py

# Entrada:  data/raw/demografia_hermosillo.csv
# Salida:   data/processed/colonias_demografia_con_coordenadas.csv
# Tiempo:   ~2-3 minutos (con caché incremental)
# Descripción: 
#   - Geocodifica 659 colonias de datos demográficos
#   - Usa Google Maps API con caché incremental


# ============================================
# PASO 5: Unificar datos (CORE DEL ANÁLISIS)
# ============================================
python notebooks/unificar_datos_poligonos.py

# Entrada:  
#   - data/raw/poligonos_hermosillo.csv (693 polígonos)
#   - data/raw/demografia_hermosillo.csv (660 colonias)
#   - data/processed/colonias_demografia_con_coordenadas.csv
#   - data/interim/reportes_de_incidentes_procesados_2018_2025.csv
#   - data/processed/colonias_reportes_911_con_coordenadas.csv
#
# Salida:   
#   - data/processed/unificado/poligonos_unificados_completo.csv (93MB)
#   - data/processed/unificado/poligonos_unificados_completo.geojson (127MB)
#   - data/processed/unificado/incidentes_con_poligono_temporal.csv (512MB)
#
# Tiempo:   ~5-8 minutos
# Descripción: 
#   - Spatial join de 3 pasos:
#     * Paso 1: Exacto (629 colonias)
#     * Paso 2: Buffer 500m (19 colonias)
#     * Paso 3: Merge por nombre (10 colonias)
#   - Agrega 2.2M incidentes por polígono
#   - Calcula índices: tasa per 1k, severidad, riesgo
#   - 658/658 (100%) colonias demográficas asignadas


# ============================================
# PASO 6: Generar mapa interactivo (DASHBOARD)
# ============================================
python notebooks/mapa_interactivo_folium_avanzado.py

# Entrada:  
#   - data/processed/unificado/poligonos_unificados_completo.geojson
#   - data/processed/unificado/incidentes_con_poligono_temporal.csv
#
# Salida:   
#   - mapa_interactivo_hermosillo.html (11.7 MB)
#
# Tiempo:   ~2-3 minutos
# Descripción: 
#   - 5 capas de visualización:
#     1. 🚨 Total Incidentes
#     2. 📊 Tasa per 1k habitantes
#     3. ⚠️ Índice de Riesgo (0-100)
#     4. 🔥 Score Severidad (1-3)
#     5. 👥 Población
#   - Popups con demografía e incidentes
#   - Panel de filtros (año/trimestre/categoría)
#   - 693 polígonos con métricas


# ============================================
# PASO 7: Abrir en navegador
# ============================================
# PowerShell:
Invoke-Item mapa_interactivo_hermosillo.html

# O directamente doble clic en el archivo HTML
```

---

### 📊 OPCIÓN 2: Pipeline Rápido (si ya tienes datos procesados)

Si ya ejecutaste los pasos 1-5 anteriormente y solo quieres actualizar el mapa:

```bash
# Solo regenerar el mapa con datos existentes
python notebooks/mapa_interactivo_folium_avanzado.py

# Abrir
Invoke-Item mapa_interactivo_hermosillo.html
```

---

### 📊 OPCIÓN 3: Pipeline de Desarrollo (con diagnóstico)

Si quieres analizar la calidad de los datos antes de generar el mapa:

```bash
# Pasos 1-5 (igual que OPCIÓN 1)
python notebooks/download_raw_data.py
python notebooks/make_interim_data.py
python notebooks/geocodificar_colonias_reportes_911.py
python notebooks/geocodificar_colonias_demografia.py
python notebooks/unificar_datos_poligonos.py

# DIAGNÓSTICO: Analizar polígonos sin demografía
python notebooks/diagnostico_poligonos_sin_demografia.py

# Genera:
#   - data/processed/diagnostico/poligonos_sin_demografia.csv
#   - data/processed/diagnostico/poligonos_no_residenciales.csv

# Luego generar mapa
python notebooks/mapa_interactivo_folium_avanzado.py
```

---

## 🔄 Dependencias entre Scripts

```
download_raw_data.py
    ↓
reportes_de_incidentes_2018_2025.csv
    ↓
make_interim_data.py
    ↓
reportes_de_incidentes_procesados_2018_2025.csv
    ↓
    ├─→ geocodificar_colonias_reportes_911.py
    │       ↓
    │   colonias_reportes_911_con_coordenadas.csv
    │
    └─→ [demografía] + geocodificar_colonias_demografia.py
            ↓
        colonias_demografia_con_coordenadas.csv
            ↓
            ↓ (ambos feeds)
            ↓
    unificar_datos_poligonos.py ←─── [polígonos_hermosillo.csv]
            ↓
    poligonos_unificados_completo.geojson
            ↓
    mapa_interactivo_folium_avanzado.py
            ↓
    mapa_interactivo_hermosillo.html (DASHBOARD)
```

---

## 📁 Archivos Generados por Paso

### Paso 1: Download Raw Data
```
data/raw/
└── reportes_de_incidentes_2018_2025.csv    (500 MB, 2.3M registros)
```

### Paso 2: Make Interim Data
```
data/interim/
└── reportes_de_incidentes_procesados_2018_2025.csv    (500 MB)
```

### Paso 3 & 4: Geocodificación
```
data/processed/
├── colonias_reportes_911_con_coordenadas.csv           (50 KB)
├── colonias_demografia_con_coordenadas.csv             (15 KB)
└── _geocache/
    ├── geocache_reportes_911.json                      (caché)
    └── geocache_demografia.json                        (caché)
```

### Paso 5: Unificación
```
data/processed/unificado/
├── poligonos_unificados_completo.csv         (93 MB)
├── poligonos_unificados_completo.geojson     (127 MB)
└── incidentes_con_poligono_temporal.csv      (512 MB)
```

### Paso 6: Dashboard
```
mapa_interactivo_hermosillo.html              (11.7 MB)
```

---

## ⏱️ Tiempo Total de Ejecución

| Escenario | Tiempo |
|-----------|--------|
| **Primera vez (sin datos)** | ~20-30 minutos |
| **Con datos raw descargados** | ~15-20 minutos |
| **Con datos procesados** | ~2-3 minutos (solo mapa) |
| **Solo actualizar mapa** | ~2 minutos |

---

## 🔑 Requisitos Previos

### Dependencias de Python
```bash
pip install -r requirements.txt

# Principales:
# - pandas
# - geopandas
# - shapely
# - folium >= 0.15.0
# - branca >= 0.6.0
# - requests
# - datasets (Hugging Face)
```

### API Keys (para geocodificación)
Si necesitas re-geocodificar (pasos 3-4):
```python
# Configurar en notebooks/geocodificar_*.py
GOOGLE_MAPS_API_KEY = "tu-api-key-aqui"
```

**Nota**: Los datos geocodificados ya están disponibles en el repo, no necesitas API key a menos que quieras actualizar coordenadas.

---

## 🐛 Troubleshooting

### Error: "No module named 'folium'"
```bash
pip install folium branca
```

### Error: "File not found: data/raw/..."
```bash
# Ejecutar paso 1
python notebooks/download_raw_data.py
```

### Error: "File not found: data/processed/unificado/..."
```bash
# Ejecutar paso 5
python notebooks/unificar_datos_poligonos.py
```

### El mapa se ve vacío o sin datos
- Verificar que `poligonos_unificados_completo.geojson` existe y no está corrupto
- Verificar tamaño: debe ser ~127 MB
- Re-ejecutar paso 5 si es necesario

### Geocodificación muy lenta
- Caché incremental está activado, segunda ejecución será rápida
- Primera vez puede tomar 10-15 minutos (2,117 + 659 colonias)

---

## 🎯 Script de Ejecución Completa

Puedes crear un script PowerShell para automatizar todo:

```powershell
# run_pipeline.ps1

Write-Host "🚀 Iniciando pipeline completo..." -ForegroundColor Cyan

# Paso 1
Write-Host "`n[1/6] Descargando datos raw..." -ForegroundColor Yellow
python notebooks/download_raw_data.py

# Paso 2
Write-Host "`n[2/6] Procesando datos interim..." -ForegroundColor Yellow
python notebooks/make_interim_data.py

# Paso 3
Write-Host "`n[3/6] Geocodificando reportes 911..." -ForegroundColor Yellow
python notebooks/geocodificar_colonias_reportes_911.py

# Paso 4
Write-Host "`n[4/6] Geocodificando demografía..." -ForegroundColor Yellow
python notebooks/geocodificar_colonias_demografia.py

# Paso 5
Write-Host "`n[5/6] Unificando datos..." -ForegroundColor Yellow
python notebooks/unificar_datos_poligonos.py

# Paso 6
Write-Host "`n[6/6] Generando mapa interactivo..." -ForegroundColor Yellow
python notebooks/mapa_interactivo_folium_avanzado.py

Write-Host "`n✅ Pipeline completado!" -ForegroundColor Green
Write-Host "Abriendo mapa..." -ForegroundColor Cyan
Invoke-Item mapa_interactivo_hermosillo.html
```

Para ejecutarlo:
```powershell
.\run_pipeline.ps1
```

---

## 📊 Versiones de Dashboard Disponibles

### 1. `mapa_interactivo_folium_avanzado.py` ⭐ (RECOMENDADO)
- **Tipo**: Mapa estático HTML con 5 capas
- **Características**:
  - 5 capas de visualización seleccionables
  - Popups ricos con demografía e incidentes
  - Panel de filtros (UI presente, backend pendiente)
  - 693 polígonos con métricas
- **Output**: `mapa_interactivo_hermosillo.html` (11.7 MB)
- **Ventaja**: Auto-contenido, compartible, sin servidor

### 2. `dashboard_mapa_interactivo.py` ❌ (DEPRECADO)
- **Tipo**: Plotly Dash (requiere servidor)
- **Estado**: Tiene errores de callbacks
- **No recomendado**: Usar opción 1 en su lugar

### 3. Otros mapas experimentales:
- `mapa_folium_interactivo.py` - Versión simplificada
- `mapa_dinamico_folium.py` - Con filtros básicos
- `mapa_dinamico_filtros.py` - Con sliders temporales

**Recomendación**: Usa `mapa_interactivo_folium_avanzado.py` para producción.

---

## 🎨 Personalización del Dashboard

### Cambiar colores de capas
Editar en `mapa_interactivo_folium_avanzado.py`:
```python
# Línea ~150-200
colormap_incidentes = branca.colormap.LinearColormap(
    colors=['#FFF5B7', '#FFDE59', '#FF9D00', '#FF4500', '#8B0000'],
    vmin=0, vmax=max_incidentes
)
```

### Agregar nueva capa
```python
# Crear nueva FeatureGroup
fg_nueva = folium.FeatureGroup(name='🆕 Nueva Métrica')

# Agregar polígonos con tu métrica
for idx, row in gdf_poligonos.iterrows():
    # ... tu lógica aquí
    
fg_nueva.add_to(m)
```

### Modificar popup
Editar función `crear_popup_html()` en línea ~50-150.

---

**Versión**: 4.0  
**Última actualización**: 7 de noviembre de 2025  
**Dashboard actual**: `mapa_interactivo_folium_avanzado.py`
