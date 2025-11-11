"""
Análisis Geoespacial de Colonias de Hermosillo

Script que procesa el shapefile INE_Limpio para:
- Descargar datos geoespaciales de colonias de Sonora
- Filtrar solo las colonias de Hermosillo (Polygon y MultiPolygon)
- Exportar datos procesados (CSV y Shapefile)
- Generar estadísticas y análisis de geometrías

Total esperado de colonias de Hermosillo: 700 (incluyendo MultiPolygons)
"""
import os
from pathlib import Path
import geopandas as gpd
import pandas as pd
import requests


def main():
    print("=" * 70)
    print("Análisis Geoespacial de Colonias de Hermosillo")
    print("=" * 70)
    
    # ========== 1. IMPORTAR LIBRERÍAS ==========
    print("\n✅ Librerías cargadas correctamente")
    
    # ========== 2. DESCARGAR Y CARGAR DATOS DEL SHAPEFILE ==========
    # Configuración de rutas (absoluta desde ubicación del script)
    script_dir = Path(__file__).resolve().parent
    datos_dir = script_dir.parent / 'data' / 'raw'
    datos_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de datos: {datos_dir}")
    
    # URLs del repositorio de Luis Moreno
    repo_url = "https://github.com/Sonora-en-Datos/ColoniasSonora/raw/main/shapes/INE_Limpio/"
    files = ["INE_Limpio.shp", "INE_Limpio.dbf", "INE_Limpio.shx", "INE_Limpio.prj"]
    
    print("\n📥 Descargando archivos del shapefile...")
    for fname in files:
        try:
            response = requests.get(repo_url + fname, timeout=10)
            if response.status_code == 200:
                filepath = datos_dir / fname
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"  ✓ {fname}")
        except Exception as e:
            print(f"  ❌ Error descargando {fname}: {e}")
    
    print("\n📂 Cargando datos geoespaciales...")
    shapefile_path = datos_dir / "INE_Limpio.shp"
    gdf_completo = gpd.read_file(shapefile_path)
    print(f"  Total de registros: {len(gdf_completo)}")
    print(f"  CRS: {gdf_completo.crs}")
    
    # ========== 3. FILTRAR GEOMETRÍAS VÁLIDAS ==========
    print("\n🔍 Filtrando geometrías válidas...\n")
    
    # Mostrar tipos de geometría disponibles
    print("Tipos de geometría en INE_Limpio.shp:")
    print(gdf_completo.geometry.type.value_counts())
    
    # Incluir Polygon Y MultiPolygon (los MultiPolygons son colonias con áreas discontinuas)
    gdf_poligonos = gdf_completo[gdf_completo.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    
    print(f"\n✅ Polígonos válidos extraídos: {len(gdf_poligonos)} de {len(gdf_completo)}")
    
    # ========== 4. FILTRAR COLONIAS DE HERMOSILLO ==========
    print("\n🏘️  Filtrando colonias de Hermosillo...\n")
    
    # Filtrar por localidad
    gdf_hermosillo = gdf_poligonos[gdf_poligonos['nom_loc'] == 'Hermosillo'].copy()
    
    print(f"Total de colonias de Hermosillo: {len(gdf_hermosillo)}")
    print(f"Colonias únicas: {gdf_hermosillo['nom_col'].nunique()}")
    print(f"\nColumnas disponibles: {list(gdf_hermosillo.columns)}")
    
    # ========== 5. ANÁLISIS DE TIPOS DE GEOMETRÍA ==========
    print("\n📊 Análisis de geometrías en Hermosillo:\n")
    
    # Contar tipos de geometría
    geometry_counts = gdf_hermosillo.geometry.type.value_counts()
    print("Tipos de geometría:")
    for geom_type, count in geometry_counts.items():
        print(f"  • {geom_type}: {count}")
    
    # Colonias con MultiPolygon (áreas discontinuas)
    multipolygons = gdf_hermosillo[gdf_hermosillo.geometry.type == 'MultiPolygon']
    if len(multipolygons) > 0:
        print(f"\n🔷 Colonias con áreas discontinuas (MultiPolygon): {len(multipolygons)}")
        print("\nEjemplos:")
        for idx, (_, row) in enumerate(multipolygons.head(10).iterrows()):
            print(f"  {idx+1}. {row['nom_col']} (CVE: {row['cve_col']})")
    
    # ========== 6. EXPORTAR DATOS PROCESADOS ==========
    print("\n💾 Exportando datos...\n")
    
    # Exportar a CSV solo las colonias de Hermosillo
    csv_path = datos_dir / 'poligonos_hermosillo.csv'
    gdf_hermosillo.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ CSV guardado: {csv_path.name}")
    
    print(f"\n📍 Total de registros exportados: {len(gdf_hermosillo)}")
    
    # ========== 7. TABLA DE RESUMEN DE COLONIAS ==========
    print("\n📋 Tabla de resumen de colonias\n")
    
    # Crear tabla de resumen
    df_resumen = gdf_hermosillo[['cve_col', 'nom_col', 'cp']].copy()
    df_resumen['geometry_type'] = gdf_hermosillo.geometry.type.values
    df_resumen = df_resumen.sort_values('nom_col')
    
    print(f"📋 Primeras 20 colonias de Hermosillo:\n")
    print(df_resumen.head(20).to_string(index=False))
    print(f"\n... (y {len(df_resumen) - 20} más)")
    
    # ========== RESUMEN FINAL ==========
    print("\n" + "=" * 70)
    print("📊 RESUMEN FINAL")
    print("=" * 70)
    print(f"Total de colonias de Hermosillo procesadas: {len(gdf_hermosillo)}")
    print(f"  • Polígonos regulares (Polygon): {len(gdf_hermosillo[gdf_hermosillo.geometry.type == 'Polygon'])}")
    print(f"  • Áreas discontinuas (MultiPolygon): {len(gdf_hermosillo[gdf_hermosillo.geometry.type == 'MultiPolygon'])}")
    print(f"\nArchivo generado:")
    print(f"  • {csv_path}")
    print(f"\nArchivos shapefile originales descargados en: {datos_dir}")
    print("\n✅ Proceso completado exitosamente")
    print("=" * 70)


if __name__ == "__main__":
    main()
