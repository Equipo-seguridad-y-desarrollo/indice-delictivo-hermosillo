import geopandas as gpd
from pathlib import Path
import pandas as pd

def explorar_shapefile(shp_path):
    """
    Explora el contenido de un shapefile y muestra información detallada
    """
    try:
        print(f"\n📁 Explorando: {Path(shp_path).name}")
        print("="*50)

        # Cargar shapefile
        gdf = gpd.read_file(shp_path)

        print(f"✅ Shapefile cargado exitosamente")
        print(f"📊 Número de registros: {len(gdf)}")
        print(f"🗺️  Tipo de geometría: {gdf.geometry.type.iloc[0] if len(gdf) > 0 else 'N/A'}")
        print(f"🌍 Sistema de coordenadas: {gdf.crs}")

        print(f"\n📋 Columnas disponibles ({len(gdf.columns)}):")
        for i, col in enumerate(gdf.columns, 1):
            print(f"   {i:2d}. {col}")

        print(f"\n🔍 Primeras filas:")
        print(gdf.head(3).to_string())

        # Estadísticas básicas
        print(f"\n📈 Estadísticas:")
        if 'nom_col' in gdf.columns:
            colonias_unicas = gdf['nom_col'].nunique()
            print(f"   • Colonias únicas: {colonias_unicas}")

        if 'nom_loc' in gdf.columns:
            localidades = gdf['nom_loc'].unique()
            print(f"   • Localidades: {list(localidades)}")

        # Verificar geometrías
        geometrias_validas = gdf.geometry.is_valid.sum()
        geometrias_vacias = gdf.geometry.is_empty.sum()
        print(f"   • Geometrías válidas: {geometrias_validas}/{len(gdf)}")
        print(f"   • Geometrías vacías: {geometrias_vacias}")

        return gdf

    except Exception as e:
        print(f"❌ Error al explorar {shp_path}: {e}")
        return None

def comparar_shapefiles():
    """
    Compara los diferentes shapefiles disponibles
    """
    print("\n" + "="*70)
    print("COMPARACIÓN DE SHAPEFILES DISPONIBLES")
    print("="*70)

    data_dir = Path(__file__).parent.parent / "data" / "raw"

    shapefiles_info = {}

    # INE_Limpio.shp
    ine_path = data_dir / "INE_Limpio.shp"
    if ine_path.exists():
        gdf_ine = explorar_shapefile(ine_path)
        shapefiles_info['INE_Limpio'] = gdf_ine

    # poligonos.shp
    pol_path = data_dir / "poligonos.shp"
    if pol_path.exists():
        gdf_pol = explorar_shapefile(pol_path)
        shapefiles_info['poligonos'] = gdf_pol

    # Comparar si ambos existen
    if len(shapefiles_info) == 2:
        print(f"\n🔄 COMPARACIÓN:")
        print("-"*30)

        ine_count = len(shapefiles_info['INE_Limpio'])
        pol_count = len(shapefiles_info['poligonos'])

        print(f"   INE_Limpio.shp: {ine_count} registros")
        print(f"   poligonos.shp:   {pol_count} registros")
        print(f"   Diferencia:      {abs(ine_count - pol_count)} registros")

        # Comparar colonias
        if 'nom_col' in shapefiles_info['INE_Limpio'].columns and 'nom_col' in shapefiles_info['poligonos'].columns:
            colonias_ine = set(shapefiles_info['INE_Limpio']['nom_col'].unique())
            colonias_pol = set(shapefiles_info['poligonos']['nom_col'].unique())

            comunes = colonias_ine.intersection(colonias_pol)
            solo_ine = colonias_ine - colonias_pol
            solo_pol = colonias_pol - colonias_ine

            print(f"\n🏘️  COLONIAS:")
            print(f"   • Comunes: {len(comunes)}")
            print(f"   • Solo en INE: {len(solo_ine)}")
            print(f"   • Solo en polígonos: {len(solo_pol)}")

def main():
    print("🔍 EXPLORADOR DE SHAPEFILES - ÍNDICE DELICTIVO HERMOSILLO")
    print("="*60)

    # Explorar shapefiles individuales
    data_dir = Path(__file__).parent.parent / "data" / "raw"

    # INE_Limpio.shp
    ine_path = data_dir / "INE_Limpio.shp"
    if ine_path.exists():
        explorar_shapefile(ine_path)

    # poligonos.shp
    pol_path = data_dir / "poligonos.shp"
    if pol_path.exists():
        explorar_shapefile(pol_path)

    # Comparar
    comparar_shapefiles()

    print(f"\n" + "="*60)
    print("💡 RECOMENDACIONES:")
    print("   • Usa 'INE_Limpio.shp' para datos oficiales de colonias")
    print("   • Los archivos HTML generados muestran mapas interactivos")
    print("   • Para análisis avanzado, usa los datos unificados en 'data/processed/'")
    print("="*60)

if __name__ == "__main__":
    main()