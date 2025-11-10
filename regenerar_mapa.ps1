# ============================================
# Pipeline Rápido: Solo regenerar mapa
# ============================================
# Este script solo regenera el mapa con datos ya procesados
# Tiempo estimado: 2-3 minutos

Write-Host "`n" -NoNewline
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🗺️  REGENERAR MAPA INTERACTIVO" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# Verificar que existen los datos procesados
$geoJsonPath = "data\processed\unificado\poligonos_unificados_completo.geojson"
$incidentesPath = "data\processed\unificado\incidentes_con_poligono_temporal.csv"

if (-not (Test-Path $geoJsonPath)) {
    Write-Host "❌ Error: No se encontró $geoJsonPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Debes ejecutar primero el pipeline completo:" -ForegroundColor Yellow
    Write-Host "  .\run_pipeline.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "O al menos el paso de unificación:" -ForegroundColor Yellow
    Write-Host "  python notebooks\unificar_datos_poligonos.py" -ForegroundColor White
    Write-Host ""
    exit 1
}

if (-not (Test-Path $incidentesPath)) {
    Write-Host "❌ Error: No se encontró $incidentesPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Debes ejecutar primero:" -ForegroundColor Yellow
    Write-Host "  python notebooks\unificar_datos_poligonos.py" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✓ Datos procesados encontrados" -ForegroundColor Green
Write-Host ""

# Generar mapa
Write-Host "Generando mapa interactivo..." -ForegroundColor Yellow
Write-Host "  • Cargando 693 polígonos..." -ForegroundColor Gray
Write-Host "  • Cargando 2.2M incidentes..." -ForegroundColor Gray
Write-Host "  • Creando 5 capas de visualización..." -ForegroundColor Gray
Write-Host ""

python notebooks/mapa_interactivo_folium_avanzado.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Error al generar el mapa" -ForegroundColor Red
    exit 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "✅ MAPA GENERADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏱️  Tiempo: " -NoNewline -ForegroundColor White
Write-Host "$($duration.Minutes) minutos $($duration.Seconds) segundos" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 Archivo: " -NoNewline -ForegroundColor White
Write-Host "mapa_interactivo_hermosillo.html" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Características:" -ForegroundColor White
Write-Host "   • 5 capas seleccionables (incidentes, tasa, riesgo, severidad, población)" -ForegroundColor Gray
Write-Host "   • 693 polígonos con popups detallados" -ForegroundColor Gray
Write-Host "   • Panel de filtros (año, trimestre, categoría, severidad)" -ForegroundColor Gray
Write-Host "   • Herramientas de navegación (zoom, búsqueda, medición)" -ForegroundColor Gray
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Preguntar si desea abrir
$respuesta = Read-Host "¿Abrir mapa en navegador? (S/N)"

if ($respuesta -eq "S" -or $respuesta -eq "s") {
    Write-Host "`nAbriendo..." -ForegroundColor Cyan
    Invoke-Item mapa_interactivo_hermosillo.html
} else {
    Write-Host "`nMapa disponible en: mapa_interactivo_hermosillo.html" -ForegroundColor Yellow
}

Write-Host ""
