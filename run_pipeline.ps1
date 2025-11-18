# ============================================
# Pipeline Completo: Dashboard Hermosillo (V2.0: Con Setup de Entorno)
# ============================================
# Este script ejecuta todo el pipeline desde cero

Write-Host "`n" -NoNewline
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🚀 PIPELINE COMPLETO - DASHBOARD ÍNDICE DELICTIVO HERMOSILLO" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# ============================================
# PASO -1: Configuración del Entorno Virtual (SETUP)
# ============================================

Write-Host "[-1/7] " -NoNewline -ForegroundColor Yellow
Write-Host "Configurando entorno virtual y dependencias..." -ForegroundColor White
Write-Host "      Salida: Carpeta venv/ y dependencias instaladas" -ForegroundColor Gray

# 1. Crear el Entorno Virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "      Creando entorno virtual 'venv'..." -ForegroundColor Gray
    python -m venv venv

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al crear el entorno virtual. Saliendo." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      Entorno virtual 'venv' ya existe. Omitiendo creación." -ForegroundColor Green
}

# 2. Instalar dependencias usando la ruta completa al binario pip dentro del venv
Write-Host "      Instalando/Actualizando dependencias..." -ForegroundColor Gray

$pipPath = ".\venv\Scripts\pip.exe"
if (-not (Test-Path $pipPath)) {
    Write-Host "❌ No se encontró el ejecutable de pip dentro de venv/. Asegura que Python se instaló correctamente." -ForegroundColor Red
    exit 1
}

# Ejecutar pip install -r requirements.txt
& $pipPath install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al instalar dependencias desde requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso -1 completado (Entorno listo)`n" -ForegroundColor Green

# Establecer el Python a usar para el resto del script (dentro del venv)
$pythonPath = ".\venv\Scripts\python.exe"

# ============================================
# PASO 0: Descargar y procesar polígonos (MODIFICADO para omitir si existe)
# ============================================

$poligonosPath = "data/raw/poligonos_hermosillo.csv"

Write-Host "[0/7] " -NoNewline -ForegroundColor Yellow
Write-Host "Descargando y procesando shapefile INE_Limpio..." -ForegroundColor White
Write-Host "      Salida: data/raw/INE_Limpio.shp + $poligonosPath" -ForegroundColor Gray

if (Test-Path $poligonosPath) {
    Write-Host "✅ Archivo de polígonos ya existe ($poligonosPath). Omitiendo procesamiento." -ForegroundColor Green
} else {
    Write-Host "⬇️ Archivo de polígonos NO encontrado. Iniciando descarga y procesamiento..." -ForegroundColor Yellow
    
    # Usar el Python del entorno virtual
    & $pythonPath notebooks/colonias_poligonos.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error en paso 0: colonias_poligonos.py" -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path $poligonosPath)) {
    Write-Host "❌ Error en paso 0: colonias_poligonos.py (El archivo de salida final no fue generado)" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 0 completado`n" -ForegroundColor Green

# ============================================
# PASO 1: Descargar datos raw 
# ============================================

$rawDataPath = "data/raw/reportes_de_incidentes_2018_2025.csv"

Write-Host "[1/7] " -NoNewline -ForegroundColor Yellow
Write-Host "Descargando datos raw desde Hugging Face..." -ForegroundColor White
Write-Host "      Salida: $rawDataPath (~500MB)" -ForegroundColor Gray

if (Test-Path $rawDataPath) {
    Write-Host "✅ Archivo raw ya existe ($rawDataPath). Omitiendo descarga." -ForegroundColor Green
    # No ejecutar 'python notebooks/download_raw_data.py'
} else {
    Write-Host "⬇️ Archivo raw NO encontrado. Iniciando descarga..." -ForegroundColor Yellow
    
    # Usar el Python del entorno virtual
    & $pythonPath notebooks/download_raw_data.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error en paso 1: download_raw_data.py" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Descarga completada`n" -ForegroundColor Green
}

if (-not (Test-Path $rawDataPath)) {
    Write-Host "❌ Error en paso 1: download_raw_data.py" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 1 completado`n" -ForegroundColor Green

# ============================================
# PASO 2: Procesar datos interim
# ============================================
Write-Host "[2/7] " -NoNewline -ForegroundColor Yellow
Write-Host "Procesando datos (limpieza + feature engineering)..." -ForegroundColor White
Write-Host "      Salida: data/interim/reportes_de_incidentes_procesados_2018_2025.csv" -ForegroundColor Gray

# Usar el Python del entorno virtual
& $pythonPath notebooks/make_interim_data.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en paso 2: make_interim_data.py" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 2 completado`n" -ForegroundColor Green

# ============================================
# PASO 3: Geocodificar reportes 911
# ============================================
Write-Host "[3/6] " -NoNewline -ForegroundColor Yellow
Write-Host "Geocodificando colonias de reportes 911..." -ForegroundColor White
Write-Host "      Salida: data/processed/colonias_reportes_911_con_coordenadas.csv" -ForegroundColor Gray

# Usar el Python del entorno virtual
& $pythonPath notebooks/geocodificar_colonias_reportes_911.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en paso 3: geocodificar_colonias_reportes_911.py" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 3 completado`n" -ForegroundColor Green

# ============================================
# PASO 4: Unificar datos (CORE)
# ============================================
Write-Host "[4/6] " -NoNewline -ForegroundColor Yellow
Write-Host "Unificando datos (merge directo demografía + spatial join reportes)..." -ForegroundColor White
Write-Host "      Salida: data/processed/unificado/poligonos_unificados_completo.*" -ForegroundColor Gray
Write-Host "      OPTIMIZACIÓN: Demografía usa cve_col (sin geocodificación)" -ForegroundColor Magenta

# Usar el Python del entorno virtual
& $pythonPath notebooks/unificar_datos_poligonos.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en paso 4: unificar_datos_poligonos.py" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 4 completado`n" -ForegroundColor Green

# ============================================
# PASO 5: Generar dashboard
# ============================================
Write-Host "[5/6] " -NoNewline -ForegroundColor Yellow
Write-Host "Generando mapa interactivo (5 capas)..." -ForegroundColor White
Write-Host "      Salida: mapa_interactivo_hermosillo.html (~12MB)" -ForegroundColor Gray

# Usar el Python del entorno virtual
& $pythonPath notebooks/mapa_interactivo_folium_avanzado.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en paso 5: mapa_interactivo_folium_avanzado.py" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Paso 5 completado`n" -ForegroundColor Green

# ============================================
# RESUMEN
# ============================================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "✅ PIPELINE COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏱️  Tiempo total: " -NoNewline -ForegroundColor White
Write-Host "$($duration.Minutes) minutos $($duration.Seconds) segundos" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 Archivos generados:" -ForegroundColor White
Write-Host "   • data/raw/INE_Limpio.shp (shapefile con geometrías)" -ForegroundColor Gray
Write-Host "   • data/raw/poligonos_hermosillo.csv (700 colonias)" -ForegroundColor Gray
Write-Host "   • data/raw/reportes_de_incidentes_2018_2025.csv (500 MB)" -ForegroundColor Gray
Write-Host "   • data/interim/reportes_de_incidentes_procesados_2018_2025.csv" -ForegroundColor Gray
Write-Host "   • data/processed/unificado/poligonos_unificados_completo.csv (93 MB)" -ForegroundColor Gray
Write-Host "   • data/processed/unificado/poligonos_unificados_completo.geojson (127 MB)" -ForegroundColor Gray
Write-Host "   • mapa_interactivo_hermosillo.html (12 MB)" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Dashboard listo:" -ForegroundColor White
Write-Host "   6 pasos completados (OPTIMIZADO: sin geocodificar demografía)" -ForegroundColor Gray
Write-Host "   5 capas de visualización" -ForegroundColor Gray
Write-Host "   700 polígonos con métricas" -ForegroundColor Gray
Write-Host "   2.2M incidentes agregados" -ForegroundColor Gray
Write-Host "   659 colonias con demografía (99.8% cobertura por cve_col)" -ForegroundColor Gray
Write-Host ""
Write-Host "💰 Ahorro: 50% de costos API (sin geocodificar demografía)" -ForegroundColor Magenta
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Preguntar si desea abrir el mapa
$respuesta = Read-Host "¿Desea abrir el mapa en el navegador? (S/N)"

if ($respuesta -eq "S" -or $respuesta -eq "s") {
    Write-Host "`nAbriendo mapa..." -ForegroundColor Cyan
    Invoke-Item mapa_interactivo_hermosillo.html
} else {
    Write-Host "`nPuede abrir el mapa manualmente: mapa_interactivo_hermosillo.html" -ForegroundColor Yellow
}

Write-Host ""