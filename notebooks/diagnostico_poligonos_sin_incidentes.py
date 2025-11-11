"""
Diagnóstico: ¿Por qué hay tantos polígonos sin incidentes?
Investigar la calidad del matching entre nombres de colonias
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely import wkt
import numpy as np

def cargar_datos():
    """Cargar todos los datasets"""
    project_root = Path(__file__).parent.parent
    
    # Polígonos
    print("Cargando polígonos...")
    poligonos = pd.read_csv(project_root / 'data' / 'raw' / 'poligonos_hermosillo.csv')
    print(f"  Polígonos: {len(poligonos):,}")
    print(f"  Colonias únicas: {poligonos['nom_col'].nunique():,}")
    
    # Reportes procesados
    print("\nCargando reportes 911...")
    reportes = pd.read_csv(project_root / 'data' / 'interim' / 'reportes_de_incidentes_procesados_2018_2025.csv')
    print(f"  Reportes: {len(reportes):,}")
    print(f"  Colonias únicas: {reportes['COLONIA'].nunique():,}")
    
    # Coordenadas de reportes
    print("\nCargando coordenadas...")
    coords = pd.read_csv(project_root / 'data' / 'processed' / 'colonias_reportes_911_con_coordenadas.csv')
    print(f"  Colonias geocodificadas: {len(coords):,}")
    
    # Mapeo de nombres
    print("\nCargando mapeo...")
    mapeo = pd.read_csv(project_root / 'data' / 'processed' / 'mapeo_colonias_reportes_911.csv')
    print(f"  Mapeos: {len(mapeo):,}")
    
    return poligonos, reportes, coords, mapeo


def comparar_nombres(poligonos, reportes, mapeo):
    """Comparar nombres de colonias entre polígonos y reportes"""
    print("\n" + "="*70)
    print("COMPARACIÓN DE NOMBRES")
    print("="*70)
    
    # Nombres normalizados de reportes
    reportes_norm = reportes.merge(mapeo, left_on='COLONIA', right_on='COLONIA_ORIGINAL', how='left')
    reportes_norm['COLONIA_NORMALIZADA'] = reportes_norm['COLONIA_NORMALIZADA'].fillna(reportes_norm['COLONIA'])
    
    colonias_reportes = set(reportes_norm['COLONIA_NORMALIZADA'].str.upper().str.strip())
    colonias_poligonos = set(poligonos['nom_col'].str.upper().str.strip())
    
    print(f"\nColonias en reportes: {len(colonias_reportes):,}")
    print(f"Colonias en polígonos: {len(colonias_poligonos):,}")
    
    # Intersección
    en_ambos = colonias_reportes & colonias_poligonos
    solo_reportes = colonias_reportes - colonias_poligonos
    solo_poligonos = colonias_poligonos - colonias_reportes
    
    print(f"\nEn ambos datasets: {len(en_ambos):,} ({len(en_ambos)/len(colonias_poligonos)*100:.1f}% de polígonos)")
    print(f"Solo en reportes: {len(solo_reportes):,}")
    print(f"Solo en polígonos: {len(solo_poligonos):,} ({len(solo_poligonos)/len(colonias_poligonos)*100:.1f}% sin match)")
    
    print(f"\n⚠️  PROBLEMA IDENTIFICADO: {len(solo_poligonos):,} polígonos no tienen match por nombre")
    
    return en_ambos, solo_reportes, solo_poligonos


def analizar_spatial_join(poligonos, reportes, coords, mapeo):
    """Verificar cuántos incidentes caen en polígonos mediante spatial join"""
    print("\n" + "="*70)
    print("ANÁLISIS SPATIAL JOIN")
    print("="*70)
    
    # Crear GeoDataFrame de polígonos
    print("\nCreando GeoDataFrame de polígonos...")
    if 'POLIGONO_WKT' in poligonos.columns:
        wkt_col = 'POLIGONO_WKT'
    elif 'geometry' in poligonos.columns:
        wkt_col = 'geometry'
    
    gdf_poligonos = gpd.GeoDataFrame(
        poligonos,
        geometry=poligonos[wkt_col].apply(wkt.loads),
        crs='EPSG:4326'
    )
    
    # Normalizar columnas
    if 'cve_col' in gdf_poligonos.columns:
        gdf_poligonos['CVE_COL'] = gdf_poligonos['cve_col']
    if 'nom_col' in gdf_poligonos.columns:
        gdf_poligonos['COLONIA'] = gdf_poligonos['nom_col']
    
    # Crear GeoDataFrame de reportes
    print("Creando GeoDataFrame de reportes...")
    reportes_norm = reportes.merge(mapeo, left_on='COLONIA', right_on='COLONIA_ORIGINAL', how='left')
    reportes_norm['COLONIA_NORMALIZADA'] = reportes_norm['COLONIA_NORMALIZADA'].fillna(reportes_norm['COLONIA'])
    
    reportes_geo = reportes_norm.merge(
        coords[['COLONIA', 'LATITUD', 'LONGITUD']], 
        left_on='COLONIA_NORMALIZADA', 
        right_on='COLONIA',
        how='left',
        suffixes=('', '_coord')
    )
    
    reportes_geo = reportes_geo.dropna(subset=['LATITUD', 'LONGITUD'])
    
    gdf_reportes = gpd.GeoDataFrame(
        reportes_geo,
        geometry=gpd.points_from_xy(reportes_geo['LONGITUD'], reportes_geo['LATITUD']),
        crs='EPSG:4326'
    )
    
    print(f"  Reportes con coordenadas: {len(gdf_reportes):,}")
    
    # Spatial join
    print("\nRealizando spatial join...")
    incidentes_en_poligonos = gpd.sjoin(
        gdf_reportes,
        gdf_poligonos[['CVE_COL', 'COLONIA', 'geometry']],
        how='left',
        predicate='within'
    )
    
    con_poligono = incidentes_en_poligonos['CVE_COL'].notna().sum()
    sin_poligono = incidentes_en_poligonos['CVE_COL'].isna().sum()
    
    print(f"\nResultado spatial join:")
    print(f"  Incidentes dentro de polígonos: {con_poligono:,} ({con_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    print(f"  Incidentes fuera de polígonos: {sin_poligono:,} ({sin_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    
    # Contar polígonos con incidentes
    poligonos_con_incidentes = incidentes_en_poligonos['CVE_COL'].dropna().nunique()
    total_poligonos = len(gdf_poligonos)
    poligonos_sin_incidentes = total_poligonos - poligonos_con_incidentes
    
    print(f"\nPolígonos con incidentes: {poligonos_con_incidentes:,} ({poligonos_con_incidentes/total_poligonos*100:.1f}%)")
    print(f"Polígonos sin incidentes: {poligonos_sin_incidentes:,} ({poligonos_sin_incidentes/total_poligonos*100:.1f}%)")
    
    return gdf_poligonos, gdf_reportes, incidentes_en_poligonos


def analizar_cobertura_geografica(gdf_poligonos, gdf_reportes):
    """Verificar si hay problemas de cobertura geográfica"""
    print("\n" + "="*70)
    print("ANÁLISIS DE COBERTURA GEOGRÁFICA")
    print("="*70)
    
    # Calcular bounds
    print("\nBounds de polígonos:")
    poli_bounds = gdf_poligonos.total_bounds
    print(f"  Lon: [{poli_bounds[0]:.4f}, {poli_bounds[2]:.4f}]")
    print(f"  Lat: [{poli_bounds[1]:.4f}, {poli_bounds[3]:.4f}]")
    
    print("\nBounds de reportes:")
    rep_bounds = gdf_reportes.total_bounds
    print(f"  Lon: [{rep_bounds[0]:.4f}, {rep_bounds[2]:.4f}]")
    print(f"  Lat: [{rep_bounds[1]:.4f}, {rep_bounds[3]:.4f}]")
    
    # Verificar reportes fuera de bounds de polígonos
    fuera_bounds = (
        (gdf_reportes.geometry.x < poli_bounds[0]) |
        (gdf_reportes.geometry.x > poli_bounds[2]) |
        (gdf_reportes.geometry.y < poli_bounds[1]) |
        (gdf_reportes.geometry.y > poli_bounds[3])
    )
    
    print(f"\nReportes fuera de bounds de polígonos: {fuera_bounds.sum():,} ({fuera_bounds.sum()/len(gdf_reportes)*100:.1f}%)")


def probar_fuzzy_matching(solo_reportes, solo_poligonos):
    """Probar fuzzy matching para mejorar el matching de nombres"""
    print("\n" + "="*70)
    print("FUZZY MATCHING")
    print("="*70)
    
    try:
        from rapidfuzz import process, fuzz
        
        print("\nBuscando matches similares...")
        matches = []
        
        for colonia_reporte in list(solo_reportes)[:50]:  # Primeras 50 para testing
            # Buscar el mejor match
            best_match = process.extractOne(
                colonia_reporte,
                solo_poligonos,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=80
            )
            
            if best_match:
                matches.append({
                    'reporte': colonia_reporte,
                    'poligono': best_match[0],
                    'score': best_match[1]
                })
        
        if matches:
            print(f"\nSe encontraron {len(matches)} posibles matches:")
            for m in matches[:10]:
                print(f"  {m['reporte']} → {m['poligono']} (score: {m['score']})")
        
        return matches
        
    except ImportError:
        print("\n⚠️  rapidfuzz no instalado (opcional para fuzzy matching)")
        print("   Puedes instalarlo con: pip install rapidfuzz")
        return []


def generar_resumen(en_ambos, solo_reportes, solo_poligonos, poligonos, reportes):
    """Generar resumen final del diagnóstico"""
    print("\n" + "="*70)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("="*70)
    
    print("\n🔍 PROBLEMA PRINCIPAL:")
    print(f"   - Hay {len(solo_poligonos):,} polígonos sin match por nombre")
    print(f"   - Esto representa el {len(solo_poligonos)/len(set(poligonos['nom_col'].str.upper()))*100:.1f}% de los polígonos")
    print(f"   - Los reportes usan {len(solo_reportes):,} nombres de colonias no presentes en polígonos")
    
    print("\n💡 CAUSAS POSIBLES:")
    print("   1. Diferencias en nomenclatura (abreviaturas, acentos, espacios)")
    print("   2. Colonias en reportes que no tienen polígono oficial (invasiones, nuevas colonias)")
    print("   3. Errores de captura en reportes 911")
    print("   4. Polígonos deshabitados o sin actividad delictiva")
    
    print("\n✅ SOLUCIONES RECOMENDADAS:")
    print("   1. SPATIAL JOIN (actual): Usa coordenadas, ignora nombres")
    print("      → Más preciso geográficamente")
    print("      → NO depende de nomenclatura")
    print("   2. Fuzzy matching: Mejorar normalización de nombres")
    print("      → Para análisis y validación")
    print("   3. Hybrid: Spatial join + validación por nombre")
    print("      → Detectar errores de geocodificación")


def main():
    print("="*70)
    print("DIAGNÓSTICO: POLÍGONOS SIN INCIDENTES")
    print("="*70)
    
    # 1. Cargar datos
    poligonos, reportes, coords, mapeo = cargar_datos()
    
    # 2. Comparar nombres
    en_ambos, solo_reportes, solo_poligonos = comparar_nombres(poligonos, reportes, mapeo)
    
    # 3. Analizar spatial join
    gdf_poligonos, gdf_reportes, incidentes_en_poligonos = analizar_spatial_join(
        poligonos, reportes, coords, mapeo
    )
    
    # 4. Cobertura geográfica
    analizar_cobertura_geografica(gdf_poligonos, gdf_reportes)
    
    # 5. Fuzzy matching
    matches = probar_fuzzy_matching(solo_reportes, solo_poligonos)
    
    # 6. Resumen
    generar_resumen(en_ambos, solo_reportes, solo_poligonos, poligonos, reportes)
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
