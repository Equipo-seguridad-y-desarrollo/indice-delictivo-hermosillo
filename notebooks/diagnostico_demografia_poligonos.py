"""
Diagnóstico: Analizar demografías que NO cayeron en polígonos
1. Identificar las 29 demografías sin polígono
2. Calcular distancia al polígono más cercano
3. Comparar spatial join vs merge por nombre
4. Determinar si podemos mejorar el match
"""

import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path
import numpy as np

def cargar_datos():
    """Cargar datos necesarios"""
    print("="*70)
    print("CARGANDO DATOS")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    
    # Polígonos
    print("\n[1/3] Polígonos...")
    poligonos = pd.read_csv(project_root / 'data' / 'raw' / 'poligonos_hermosillo.csv')
    gdf_poligonos = gpd.GeoDataFrame(
        poligonos,
        geometry=poligonos['POLIGONO_WKT'].apply(wkt.loads),
        crs='EPSG:4326'
    )
    print(f"   {len(gdf_poligonos):,} polígonos")
    
    # Demografía
    print("\n[2/3] Demografía...")
    demografia = pd.read_csv(project_root / 'data' / 'raw' / 'demografia_hermosillo.csv')
    print(f"   {len(demografia):,} colonias")
    
    # Demografía con coordenadas
    print("\n[3/3] Coordenadas...")
    demografia_coords = pd.read_csv(project_root / 'data' / 'processed' / 'colonias_demografia_con_coordenadas.csv')
    print(f"   {len(demografia_coords):,} geocodificadas")
    
    return gdf_poligonos, demografia, demografia_coords


def spatial_join_con_diagnostico(gdf_poligonos, demografia, demografia_coords):
    """Spatial join con información detallada"""
    print("\n" + "="*70)
    print("SPATIAL JOIN CON DIAGNÓSTICO")
    print("="*70)
    
    # Unir demografía con coordenadas
    demografia_geo = demografia.merge(
        demografia_coords[['nom_col', 'LATITUD', 'LONGITUD']], 
        on='nom_col', 
        how='inner'
    )
    
    # GeoDataFrame
    gdf_demografia = gpd.GeoDataFrame(
        demografia_geo,
        geometry=gpd.points_from_xy(demografia_geo['LONGITUD'], demografia_geo['LATITUD']),
        crs='EPSG:4326'
    )
    
    # Spatial join
    print("\nRealizando spatial join...")
    demo_en_poli = gpd.sjoin(
        gdf_demografia,
        gdf_poligonos[['CVE_COL', 'COLONIA', 'geometry']],
        how='left',
        predicate='within'
    )
    
    # Separar exitosos vs fallidos
    con_poligono = demo_en_poli[demo_en_poli['CVE_COL'].notna()].copy()
    sin_poligono = demo_en_poli[demo_en_poli['CVE_COL'].isna()].copy()
    
    print(f"\n✓ Con polígono: {len(con_poligono):,} ({len(con_poligono)/len(demo_en_poli)*100:.1f}%)")
    print(f"✗ Sin polígono: {len(sin_poligono):,} ({len(sin_poligono)/len(demo_en_poli)*100:.1f}%)")
    
    return con_poligono, sin_poligono, gdf_demografia


def analizar_sin_poligono(sin_poligono, gdf_poligonos):
    """Analizar colonias que no cayeron en polígonos"""
    print("\n" + "="*70)
    print("ANÁLISIS: DEMOGRAFÍAS SIN POLÍGONO")
    print("="*70)
    
    if len(sin_poligono) == 0:
        print("\n✓ Todas las demografías cayeron en polígonos!")
        return
    
    print(f"\nColonias sin polígono ({len(sin_poligono)}):")
    print("-"*70)
    
    # Calcular distancia al polígono más cercano
    resultados = []
    
    for idx, row in sin_poligono.iterrows():
        punto = row.geometry
        nombre = row['nom_col']
        
        # Calcular distancia a TODOS los polígonos
        distancias = gdf_poligonos.geometry.distance(punto)
        idx_cercano = distancias.idxmin()
        distancia_min = distancias.min()
        
        poligono_cercano = gdf_poligonos.loc[idx_cercano, 'COLONIA']
        cve_cercano = gdf_poligonos.loc[idx_cercano, 'CVE_COL']
        
        # Convertir distancia a metros (aprox)
        distancia_metros = distancia_min * 111000  # 1 grado ≈ 111 km
        
        resultados.append({
            'nom_col': nombre,
            'latitud': row['LATITUD'],
            'longitud': row['LONGITUD'],
            'poligono_cercano': poligono_cercano,
            'cve_cercano': cve_cercano,
            'distancia_grados': distancia_min,
            'distancia_metros': distancia_metros
        })
        
        print(f"\n{nombre}:")
        print(f"   Coordenadas: ({row['LATITUD']:.6f}, {row['LONGITUD']:.6f})")
        print(f"   Polígono más cercano: {poligono_cercano}")
        print(f"   Distancia: {distancia_metros:.1f} metros")
    
    df_sin_match = pd.DataFrame(resultados)
    
    # Estadísticas
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE DISTANCIAS")
    print("="*70)
    print(f"\nDistancia mínima: {df_sin_match['distancia_metros'].min():.1f} metros")
    print(f"Distancia máxima: {df_sin_match['distancia_metros'].max():.1f} metros")
    print(f"Distancia promedio: {df_sin_match['distancia_metros'].mean():.1f} metros")
    print(f"Distancia mediana: {df_sin_match['distancia_metros'].median():.1f} metros")
    
    # ¿Cuántas están a menos de X metros?
    umbrales = [10, 50, 100, 500, 1000]
    print(f"\nColonias por umbral de distancia:")
    for umbral in umbrales:
        count = (df_sin_match['distancia_metros'] < umbral).sum()
        print(f"   < {umbral:4d}m: {count:2d} colonias ({count/len(df_sin_match)*100:.1f}%)")
    
    return df_sin_match


def comparar_con_merge_por_nombre(gdf_poligonos, demografia, con_poligono):
    """Comparar spatial join vs merge por nombre"""
    print("\n" + "="*70)
    print("COMPARACIÓN: SPATIAL JOIN vs MERGE POR NOMBRE")
    print("="*70)
    
    # Merge por nombre (normalizado)
    print("\nRealizando merge por nombre...")
    demografia_norm = demografia.copy()
    demografia_norm['nom_col_upper'] = demografia_norm['nom_col'].str.upper().str.strip()
    
    poligonos_norm = gdf_poligonos.copy()
    poligonos_norm['COLONIA_upper'] = poligonos_norm['COLONIA'].str.upper().str.strip()
    
    merge_nombre = demografia_norm.merge(
        poligonos_norm[['CVE_COL', 'COLONIA', 'COLONIA_upper']],
        left_on='nom_col_upper',
        right_on='COLONIA_upper',
        how='left',
        indicator=True
    )
    
    # Estadísticas merge por nombre
    match_nombre = merge_nombre[merge_nombre['_merge'] == 'both']
    sin_match_nombre = merge_nombre[merge_nombre['_merge'] == 'left_only']
    
    print(f"\n📊 MERGE POR NOMBRE:")
    print(f"   ✓ Con match: {len(match_nombre):,} ({len(match_nombre)/len(demografia)*100:.1f}%)")
    print(f"   ✗ Sin match: {len(sin_match_nombre):,} ({len(sin_match_nombre)/len(demografia)*100:.1f}%)")
    
    # Estadísticas spatial join
    print(f"\n📍 SPATIAL JOIN (coordenadas):")
    print(f"   ✓ Con match: {len(con_poligono):,} ({len(con_poligono)/len(demografia)*100:.1f}%)")
    print(f"   ✗ Sin match: {len(demografia) - len(con_poligono):,}")
    
    # Diferencia
    diff = len(match_nombre) - len(con_poligono)
    print(f"\n📈 DIFERENCIA:")
    if diff > 0:
        print(f"   Merge por nombre encuentra {diff} más matches")
    elif diff < 0:
        print(f"   Spatial join encuentra {abs(diff)} más matches")
    else:
        print(f"   Ambos métodos encuentran el mismo número de matches")
    
    # ¿Hay colonias que matchean por nombre pero NO por coordenadas?
    nombres_match = set(match_nombre['nom_col'].values)
    nombres_spatial = set(con_poligono['nom_col'].values)
    
    solo_nombre = nombres_match - nombres_spatial
    solo_spatial = nombres_spatial - nombres_match
    
    if solo_nombre:
        print(f"\n⚠️  Colonias que matchean por NOMBRE pero NO por COORDENADAS ({len(solo_nombre)}):")
        for col in list(solo_nombre)[:10]:  # Mostrar primeras 10
            print(f"   - {col}")
        if len(solo_nombre) > 10:
            print(f"   ... y {len(solo_nombre)-10} más")
    
    if solo_spatial:
        print(f"\n✓ Colonias que matchean por COORDENADAS pero NO por NOMBRE ({len(solo_spatial)}):")
        for col in list(solo_spatial)[:10]:
            print(f"   - {col}")
        if len(solo_spatial) > 10:
            print(f"   ... y {len(solo_spatial)-10} más")
    
    return merge_nombre, match_nombre, sin_match_nombre


def sugerir_mejoras(df_sin_match):
    """Sugerir estrategias para mejorar el match"""
    print("\n" + "="*70)
    print("💡 SUGERENCIAS PARA MEJORAR EL MATCH")
    print("="*70)
    
    if df_sin_match is None or len(df_sin_match) == 0:
        print("\n✓ No hay demografías sin match - ¡Excelente cobertura!")
        return
    
    # Colonias muy cercanas (< 100m)
    muy_cercanas = df_sin_match[df_sin_match['distancia_metros'] < 100]
    
    if len(muy_cercanas) > 0:
        print(f"\n1️⃣ BUFFER DE TOLERANCIA:")
        print(f"   {len(muy_cercanas)} colonias están a < 100m del polígono más cercano")
        print(f"   Sugerencia: Aplicar buffer de 100m a los polígonos antes del spatial join")
        print(f"   Esto capturaría estas colonias que están 'casi dentro'")
    
    # Colonias lejanas (> 1km)
    lejanas = df_sin_match[df_sin_match['distancia_metros'] > 1000]
    
    if len(lejanas) > 0:
        print(f"\n2️⃣ COLONIAS LEJANAS:")
        print(f"   {len(lejanas)} colonias están a > 1km del polígono más cercano")
        print(f"   Sugerencia: Revisar si las coordenadas son correctas")
        print(f"   Posibles causas:")
        print(f"   - Geocodificación incorrecta")
        print(f"   - Colonias fuera del área de estudio")
        print(f"   - Polígonos incompletos")
    
    # Match alternativo: asignar al polígono más cercano
    print(f"\n3️⃣ ASIGNACIÓN AL MÁS CERCANO:")
    print(f"   Podríamos asignar las {len(df_sin_match)} demografías sin match")
    print(f"   al polígono más cercano (nearest neighbor)")
    print(f"   Pros: 100% de cobertura")
    print(f"   Contras: Puede ser inexacto para colonias lejanas")


def guardar_diagnostico(df_sin_match, merge_nombre):
    """Guardar resultados del diagnóstico"""
    print("\n" + "="*70)
    print("GUARDANDO DIAGNÓSTICO")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'data' / 'processed' / 'diagnostico'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if df_sin_match is not None and len(df_sin_match) > 0:
        # Demografías sin match espacial
        output_path = output_dir / 'demografias_sin_poligono.csv'
        df_sin_match.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ {output_path.name}")
    
    # Comparación de métodos
    output_comp = output_dir / 'comparacion_metodos_match.csv'
    merge_nombre.to_csv(output_comp, index=False, encoding='utf-8-sig')
    print(f"✓ {output_comp.name}")
    
    print(f"\n📂 Archivos en: {output_dir}/")


def main():
    """Pipeline de diagnóstico"""
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO: DEMOGRAFÍA → POLÍGONOS")
    print("="*70)
    print("Objetivo: Entender por qué 29 demografías no cayeron en polígonos\n")
    
    # 1. Cargar datos
    gdf_poligonos, demografia, demografia_coords = cargar_datos()
    
    # 2. Spatial join con diagnóstico
    con_poligono, sin_poligono, gdf_demografia = spatial_join_con_diagnostico(
        gdf_poligonos, demografia, demografia_coords
    )
    
    # 3. Analizar colonias sin polígono
    df_sin_match = analizar_sin_poligono(sin_poligono, gdf_poligonos) if len(sin_poligono) > 0 else None
    
    # 4. Comparar con merge por nombre
    merge_nombre, match_nombre, sin_match_nombre = comparar_con_merge_por_nombre(
        gdf_poligonos, demografia, con_poligono
    )
    
    # 5. Sugerir mejoras
    sugerir_mejoras(df_sin_match)
    
    # 6. Guardar resultados
    guardar_diagnostico(df_sin_match, merge_nombre)
    
    print("\n" + "="*70)
    print("✓ DIAGNÓSTICO COMPLETADO")
    print("="*70)


if __name__ == "__main__":
    main()
