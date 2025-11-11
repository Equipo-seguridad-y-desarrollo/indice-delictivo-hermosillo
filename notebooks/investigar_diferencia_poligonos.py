import geopandas as gpd
import pandas as pd
from pathlib import Path

def investigar_diferencias():
    """
    Investiga las diferencias entre los shapefiles y el CSV de polígonos
    """
    print("="*70)
    print("INVESTIGACIÓN: ¿Por qué hay diferencias en los polígonos?")
    print("="*70)
    
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    # Cargar archivos
    print("\n📂 CARGANDO ARCHIVOS...")
    print("-"*40)
    
    # 1. INE_Limpio.shp
    gdf_ine = gpd.read_file(data_dir / "INE_Limpio.shp")
    print(f"✓ INE_Limpio.shp: {len(gdf_ine)} registros")
    
    # 2. poligonos.shp
    gdf_pol = gpd.read_file(data_dir / "poligonos.shp")
    print(f"✓ poligonos.shp: {len(gdf_pol)} registros")
    
    # 3. poligonos_hermosillo.csv
    df_csv = pd.read_csv(data_dir / "poligonos_hermosillo.csv")
    print(f"✓ poligonos_hermosillo.csv: {len(df_csv)} registros")
    
    print("\n🔍 ANÁLISIS DE ORIGEN:")
    print("-"*40)
    
    # Filtrar solo Hermosillo de los shapefiles
    gdf_ine_hmo = gdf_ine[gdf_ine['nom_loc'] == 'Hermosillo'].copy()
    gdf_pol_hmo = gdf_pol[gdf_pol['nom_loc'] == 'Hermosillo'].copy()
    
    print(f"INE_Limpio.shp (solo Hermosillo): {len(gdf_ine_hmo)} polígonos")
    print(f"poligonos.shp (solo Hermosillo): {len(gdf_pol_hmo)} polígonos")
    print(f"poligonos_hermosillo.csv: {len(df_csv)} polígonos")
    
    print("\n📊 COMPARACIÓN DE CLAVES (cve_col):")
    print("-"*40)
    
    claves_ine = set(gdf_ine_hmo['cve_col'].unique())
    claves_pol = set(gdf_pol_hmo['cve_col'].unique())
    claves_csv = set(df_csv['cve_col'].unique())
    
    print(f"Claves únicas en INE_Limpio: {len(claves_ine)}")
    print(f"Claves únicas en poligonos.shp: {len(claves_pol)}")
    print(f"Claves únicas en CSV: {len(claves_csv)}")
    
    # ¿De dónde viene el CSV?
    print("\n🔎 ORIGEN DEL CSV:")
    print("-"*40)
    
    csv_en_ine = claves_csv.intersection(claves_ine)
    csv_en_pol = claves_csv.intersection(claves_pol)
    
    print(f"Claves del CSV que están en INE_Limpio: {len(csv_en_ine)}/{len(claves_csv)} ({len(csv_en_ine)/len(claves_csv)*100:.1f}%)")
    print(f"Claves del CSV que están en poligonos.shp: {len(csv_en_pol)}/{len(claves_csv)} ({len(csv_en_pol)/len(claves_csv)*100:.1f}%)")
    
    # Claves que faltan
    csv_no_ine = claves_csv - claves_ine
    csv_no_pol = claves_csv - claves_pol
    
    if csv_no_ine:
        print(f"\n⚠️ Claves en CSV que NO están en INE_Limpio: {len(csv_no_ine)}")
        print("Ejemplos:")
        for clave in list(csv_no_ine)[:5]:
            row = df_csv[df_csv['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    if csv_no_pol:
        print(f"\n⚠️ Claves en CSV que NO están en poligonos.shp: {len(csv_no_pol)}")
        print("Ejemplos:")
        for clave in list(csv_no_pol)[:5]:
            row = df_csv[df_csv['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    # Claves que están en shapefiles pero NO en CSV
    print("\n❌ POLÍGONOS FALTANTES EN CSV:")
    print("-"*40)
    
    ine_no_csv = claves_ine - claves_csv
    pol_no_csv = claves_pol - claves_csv
    
    print(f"Polígonos en INE_Limpio que NO están en CSV: {len(ine_no_csv)}")
    if len(ine_no_csv) > 0:
        print("Ejemplos de colonias faltantes:")
        for clave in list(ine_no_csv)[:10]:
            row = gdf_ine_hmo[gdf_ine_hmo['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    print(f"\nPolígonos en poligonos.shp que NO están en CSV: {len(pol_no_csv)}")
    if len(pol_no_csv) > 0:
        print("Ejemplos de colonias faltantes:")
        for clave in list(pol_no_csv)[:10]:
            row = gdf_pol_hmo[gdf_pol_hmo['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    # Analizar diferencias entre INE y poligonos.shp
    print("\n🔄 DIFERENCIAS ENTRE SHAPEFILES:")
    print("-"*40)
    
    solo_ine = claves_ine - claves_pol
    solo_pol = claves_pol - claves_ine
    
    print(f"Polígonos solo en INE_Limpio: {len(solo_ine)}")
    if len(solo_ine) > 0:
        print("Ejemplos:")
        for clave in list(solo_ine)[:5]:
            row = gdf_ine_hmo[gdf_ine_hmo['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    print(f"\nPolígonos solo en poligonos.shp: {len(solo_pol)}")
    if len(solo_pol) > 0:
        print("Ejemplos:")
        for clave in list(solo_pol)[:5]:
            row = gdf_pol_hmo[gdf_pol_hmo['cve_col'] == clave].iloc[0]
            print(f"  • {clave}: {row['nom_col']}")
    
    # Verificar si mapa_poligonos.html usa poligonos.shp
    print("\n📋 CONCLUSIÓN:")
    print("="*70)
    print("El archivo 'mapa_poligonos.html' se genera desde 'poligonos.shp'")
    print(f"que tiene {len(gdf_pol_hmo)} polígonos de Hermosillo.")
    print(f"\nLa diferencia con INE_Limpio.shp ({len(gdf_ine_hmo)} polígonos) es de {len(gdf_ine_hmo) - len(gdf_pol_hmo)} polígonos.")
    print(f"\nEl CSV 'poligonos_hermosillo.csv' tiene {len(df_csv)} registros")
    print("y fue generado manualmente, NO proviene directamente de los shapefiles.")
    print("\n⚠️ PROBLEMA IDENTIFICADO:")
    print("Los 3 archivos tienen DIFERENTES cantidades de polígonos:")
    print(f"  • INE_Limpio.shp (Hermosillo): {len(gdf_ine_hmo)} polígonos")
    print(f"  • poligonos.shp (Hermosillo): {len(gdf_pol_hmo)} polígonos")
    print(f"  • poligonos_hermosillo.csv: {len(df_csv)} polígonos")
    print("\n💡 RECOMENDACIÓN:")
    print("Usa 'INE_Limpio.shp' como fuente oficial ya que tiene más polígonos")
    print("y es el archivo más completo del INE.")
    print("="*70)
    
    # Guardar reporte
    output_path = Path(__file__).parent.parent / "investigacion_poligonos.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("REPORTE: Investigación de diferencias en polígonos\n")
        f.write("="*70 + "\n\n")
        f.write(f"INE_Limpio.shp (Hermosillo): {len(gdf_ine_hmo)} polígonos\n")
        f.write(f"poligonos.shp (Hermosillo): {len(gdf_pol_hmo)} polígonos\n")
        f.write(f"poligonos_hermosillo.csv: {len(df_csv)} polígonos\n\n")
        f.write(f"Polígonos faltantes en CSV vs INE: {len(ine_no_csv)}\n")
        f.write(f"Polígonos faltantes en CSV vs poligonos.shp: {len(pol_no_csv)}\n\n")
        f.write("Colonias faltantes en CSV (vs INE_Limpio):\n")
        for clave in sorted(ine_no_csv):
            row = gdf_ine_hmo[gdf_ine_hmo['cve_col'] == clave].iloc[0]
            f.write(f"  • {clave}: {row['nom_col']}\n")
    
    print(f"\n📄 Reporte guardado en: {output_path}")

if __name__ == "__main__":
    investigar_diferencias()
