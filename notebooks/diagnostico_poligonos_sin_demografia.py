"""
Diagnóstico: Polígonos sin demografía dentro de la ciudad
Investigar por qué 255 polígonos (36.8%) no tienen datos demográficos
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
    
    # Polígonos unificados
    print("\n[1/4] Polígonos unificados...")
    gdf_unificado = gpd.read_file(
        project_root / 'data' / 'processed' / 'unificado' / 'poligonos_unificados_completo.geojson'
    )
    print(f"   {len(gdf_unificado):,} polígonos")
    
    # Polígonos originales
    print("\n[2/4] Polígonos originales...")
    poligonos = pd.read_csv(project_root / 'data' / 'raw' / 'poligonos_hermosillo.csv')
    gdf_poligonos = gpd.GeoDataFrame(
        poligonos,
        geometry=poligonos['POLIGONO_WKT'].apply(wkt.loads),
        crs='EPSG:4326'
    )
    print(f"   {len(gdf_poligonos):,} polígonos")
    
    # Demografía
    print("\n[3/4] Demografía...")
    demografia = pd.read_csv(project_root / 'data' / 'raw' / 'demografia_hermosillo.csv')
    print(f"   {len(demografia):,} colonias")
    
    # Demografía con coordenadas
    print("\n[4/4] Demografía geocodificada...")
    demografia_coords = pd.read_csv(
        project_root / 'data' / 'processed' / 'colonias_demografia_con_coordenadas.csv'
    )
    print(f"   {len(demografia_coords):,} colonias")
    
    return gdf_unificado, gdf_poligonos, demografia, demografia_coords


def analizar_sin_demografia(gdf_unificado):
    """Analizar polígonos sin demografía"""
    print("\n" + "="*70)
    print("ANÁLISIS: POLÍGONOS SIN DEMOGRAFÍA")
    print("="*70)
    
    # Separar con y sin demografía
    con_demo = gdf_unificado[gdf_unificado['poblacion_total'].notna()]
    sin_demo = gdf_unificado[gdf_unificado['poblacion_total'].isna()]
    
    print(f"\n✓ Con demografía: {len(con_demo):,} ({len(con_demo)/len(gdf_unificado)*100:.1f}%)")
    print(f"✗ Sin demografía: {len(sin_demo):,} ({len(sin_demo)/len(gdf_unificado)*100:.1f}%)")
    
    # Verificar si tienen incidentes
    sin_demo_con_inc = sin_demo[sin_demo['total_incidentes'] > 0]
    sin_demo_sin_inc = sin_demo[sin_demo['total_incidentes'] == 0]
    
    print(f"\nPolígonos SIN demografía:")
    print(f"   • Con incidentes: {len(sin_demo_con_inc):,}")
    print(f"   • Sin incidentes: {len(sin_demo_sin_inc):,}")
    
    return con_demo, sin_demo, sin_demo_con_inc


def comparar_nombres_colonias(sin_demo, demografia):
    """Comparar nombres de colonias para encontrar matches potenciales"""
    print("\n" + "="*70)
    print("COMPARACIÓN DE NOMBRES")
    print("="*70)
    
    # Nombres de polígonos sin demografía
    nombres_sin_demo = set(sin_demo['COLONIA'].str.upper().str.strip())
    
    # Nombres en demografía
    nombres_demo = set(demografia['nom_col'].str.upper().str.strip())
    
    print(f"\nNombres en polígonos sin demo: {len(nombres_sin_demo):,}")
    print(f"Nombres en demografía: {len(nombres_demo):,}")
    
    # ¿Hay matches exactos que no se capturaron?
    matches_exactos = nombres_sin_demo & nombres_demo
    
    print(f"\n🔍 Matches EXACTOS por nombre: {len(matches_exactos)}")
    
    if len(matches_exactos) > 0:
        print("\nColonias que SÍ existen en demografía pero NO se asignaron:")
        for idx, nombre in enumerate(sorted(matches_exactos)[:20], 1):
            print(f"   {idx}. {nombre}")
        if len(matches_exactos) > 20:
            print(f"   ... y {len(matches_exactos)-20} más")
    
    # Matches parciales (similares)
    from difflib import get_close_matches
    
    print("\n" + "="*70)
    print("MATCHES PARCIALES (similitud)")
    print("="*70)
    
    matches_parciales = []
    nombres_demo_list = list(nombres_demo)
    
    for nombre_sin in list(nombres_sin_demo)[:50]:  # Primeros 50 para no tardar mucho
        similares = get_close_matches(nombre_sin, nombres_demo_list, n=3, cutoff=0.8)
        if similares:
            matches_parciales.append({
                'poligono': nombre_sin,
                'similares_en_demo': similares
            })
    
    if matches_parciales:
        print(f"\nEncontrados {len(matches_parciales)} polígonos con nombres similares:")
        for item in matches_parciales[:15]:
            print(f"\n   Polígono: {item['poligono']}")
            print(f"   Similar a: {', '.join(item['similares_en_demo'])}")
        if len(matches_parciales) > 15:
            print(f"\n   ... y {len(matches_parciales)-15} más")
    
    return matches_exactos, matches_parciales


def analizar_tipos_poligonos(sin_demo, gdf_poligonos):
    """Analizar qué tipo de polígonos son los que no tienen demografía"""
    print("\n" + "="*70)
    print("ANÁLISIS DE TIPOS DE POLÍGONOS")
    print("="*70)
    
    # Unir con datos originales para ver clasificación
    sin_demo_completo = sin_demo.merge(
        gdf_poligonos[['CVE_COL', 'CLASIF', 'NOM_SUN', 'POBTOT']],
        on='CVE_COL',
        how='left'
    )
    
    # Clasificación
    if 'CLASIF' in sin_demo_completo.columns:
        print("\n📊 Por clasificación INEGI:")
        clasif_counts = sin_demo_completo['CLASIF'].value_counts()
        for clasif, count in clasif_counts.items():
            print(f"   {clasif}: {count:,} polígonos")
    
    # Población en polígonos originales
    if 'POBTOT' in sin_demo_completo.columns:
        print("\n👥 Población en polígonos originales:")
        con_pob_orig = sin_demo_completo['POBTOT'].notna().sum()
        sin_pob_orig = sin_demo_completo['POBTOT'].isna().sum()
        pob_cero = (sin_demo_completo['POBTOT'] == 0).sum()
        
        print(f"   Con población > 0: {(sin_demo_completo['POBTOT'] > 0).sum():,}")
        print(f"   Población = 0: {pob_cero:,}")
        print(f"   Sin dato: {sin_pob_orig:,}")
        
        if (sin_demo_completo['POBTOT'] > 0).sum() > 0:
            print("\n⚠️  PROBLEMA DETECTADO:")
            print(f"   Hay {(sin_demo_completo['POBTOT'] > 0).sum()} polígonos con población")
            print(f"   en los datos originales pero SIN demografía detallada!")
    
    # Nombres que sugieren tipo no residencial
    palabras_clave_no_residencial = [
        'PARQUE', 'INDUSTRIAL', 'AEROPUERTO', 'UNIVERSIDAD', 'CEMENTERIO',
        'PANTEÓN', 'PANTEON', 'CAMPO', 'EJIDO', 'HOSPITAL', 'CLINIC',
        'ESTADIO', 'DEPORTIVO', 'PLAZA', 'MERCADO', 'CENTRAL'
    ]
    
    print("\n🏭 Polígonos probablemente NO RESIDENCIALES:")
    no_residenciales = []
    
    for idx, row in sin_demo.iterrows():
        nombre = row['COLONIA'].upper()
        for palabra in palabras_clave_no_residencial:
            if palabra in nombre:
                no_residenciales.append({
                    'nombre': row['COLONIA'],
                    'tipo': palabra,
                    'incidentes': int(row['total_incidentes'])
                })
                break
    
    df_no_res = pd.DataFrame(no_residenciales)
    if len(df_no_res) > 0:
        print(f"\n   Encontrados: {len(df_no_res)} polígonos no residenciales")
        tipo_counts = df_no_res['tipo'].value_counts()
        for tipo, count in tipo_counts.items():
            print(f"   • {tipo}: {count} polígonos")
        
        # Mostrar algunos ejemplos
        print("\n   Ejemplos:")
        for idx, row in df_no_res.head(10).iterrows():
            print(f"   - {row['nombre']} ({row['incidentes']:,} incidentes)")
    
    return sin_demo_completo, df_no_res


def analizar_area_geografica(sin_demo, con_demo):
    """Analizar distribución geográfica"""
    print("\n" + "="*70)
    print("ANÁLISIS GEOGRÁFICO")
    print("="*70)
    
    # Calcular área
    sin_demo_utm = sin_demo.to_crs('EPSG:32612')
    con_demo_utm = con_demo.to_crs('EPSG:32612')
    
    area_sin_demo = sin_demo_utm.geometry.area.sum() / 1e6  # km²
    area_con_demo = con_demo_utm.geometry.area.sum() / 1e6
    
    print(f"\n📏 Área total:")
    print(f"   Con demografía: {area_con_demo:.2f} km²")
    print(f"   Sin demografía: {area_sin_demo:.2f} km²")
    print(f"   Total: {area_con_demo + area_sin_demo:.2f} km²")
    print(f"   % sin demo: {area_sin_demo/(area_con_demo + area_sin_demo)*100:.1f}%")
    
    # Calcular centroide de Hermosillo
    centro_hermosillo = [29.0892, -110.9615]
    
    # Distancia promedio al centro
    from shapely.geometry import Point
    centro_point = Point(centro_hermosillo[1], centro_hermosillo[0])
    
    sin_demo['dist_centro'] = sin_demo.geometry.centroid.distance(centro_point) * 111  # km aprox
    con_demo['dist_centro'] = con_demo.geometry.centroid.distance(centro_point) * 111
    
    print(f"\n📍 Distancia al centro de Hermosillo:")
    print(f"   Con demografía: {con_demo['dist_centro'].mean():.2f} km promedio")
    print(f"   Sin demografía: {sin_demo['dist_centro'].mean():.2f} km promedio")
    
    # ¿Los sin demografía están en la periferia?
    sin_demo_centro = sin_demo[sin_demo['dist_centro'] < 5]  # < 5km del centro
    
    print(f"\n🎯 Polígonos SIN demografía a < 5km del centro: {len(sin_demo_centro):,}")
    
    if len(sin_demo_centro) > 0:
        print("\n⚠️  POLÍGONOS CÉNTRICOS SIN DEMOGRAFÍA:")
        for idx, row in sin_demo_centro.head(15).iterrows():
            print(f"   • {row['COLONIA']} - {row['dist_centro']:.2f} km - {int(row['total_incidentes']):,} incidentes")


def proponer_soluciones(matches_exactos, sin_demo_completo):
    """Proponer soluciones al problema"""
    print("\n" + "="*70)
    print("💡 SOLUCIONES PROPUESTAS")
    print("="*70)
    
    print("\n1️⃣ AUMENTAR BUFFER (PRIORIDAD ALTA)")
    print("   Problema: Buffer de 500m puede ser insuficiente")
    print("   Solución: Probar buffer de 1km o 2km")
    print("   Beneficio: Capturar más colonias cercanas")
    
    if len(matches_exactos) > 0:
        print("\n2️⃣ MERGE POR NOMBRE COMPLEMENTARIO (PRIORIDAD ALTA)")
        print(f"   Problema: {len(matches_exactos)} colonias con nombre exacto NO se asignaron")
        print("   Solución: Hacer merge por nombre para las que no matchearon espacialmente")
        print("   Beneficio: Capturar colonias con coordenadas ligeramente incorrectas")
    
    print("\n3️⃣ USAR POBLACIÓN DE POLÍGONOS ORIGINALES (PRIORIDAD MEDIA)")
    print("   Problema: Polígonos tienen POBTOT pero no demografía detallada")
    print("   Solución: Usar POBTOT como fallback para cálculos básicos")
    print("   Limitación: No tendremos edad, escolaridad, etc.")
    
    print("\n4️⃣ NEAREST NEIGHBOR PARA CERCANOS (PRIORIDAD BAJA)")
    print("   Problema: Algunas colonias están muy cerca pero no matchean")
    print("   Solución: Asignar demografía del polígono más cercano")
    print("   Riesgo: Puede ser inexacto")
    
    print("\n5️⃣ IDENTIFICAR Y MARCAR NO RESIDENCIALES (PRIORIDAD ALTA)")
    print("   Problema: Mezclar zonas residenciales con industriales distorsiona métricas")
    print("   Solución: Clasificar polígonos (residencial, industrial, comercial, etc.)")
    print("   Beneficio: Análisis más preciso, no esperar demografía donde no hay población")


def guardar_diagnostico(sin_demo, df_no_res):
    """Guardar resultados"""
    print("\n" + "="*70)
    print("GUARDANDO DIAGNÓSTICO")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'data' / 'processed' / 'diagnostico'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Polígonos sin demografía
    output_sin = output_dir / 'poligonos_sin_demografia.csv'
    sin_demo[['CVE_COL', 'COLONIA', 'total_incidentes', 'incidentes_alta', 
              'incidentes_media', 'incidentes_baja']].to_csv(
        output_sin, index=False, encoding='utf-8-sig'
    )
    print(f"\n✓ {output_sin.name}")
    
    # No residenciales
    if len(df_no_res) > 0:
        output_no_res = output_dir / 'poligonos_no_residenciales.csv'
        df_no_res.to_csv(output_no_res, index=False, encoding='utf-8-sig')
        print(f"✓ {output_no_res.name}")
    
    print(f"\n📂 Archivos en: {output_dir}/")


def main():
    """Pipeline de diagnóstico"""
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO: POLÍGONOS SIN DEMOGRAFÍA")
    print("="*70)
    
    # 1. Cargar datos
    gdf_unificado, gdf_poligonos, demografia, demografia_coords = cargar_datos()
    
    # 2. Analizar polígonos sin demografía
    con_demo, sin_demo, sin_demo_con_inc = analizar_sin_demografia(gdf_unificado)
    
    # 3. Comparar nombres
    matches_exactos, matches_parciales = comparar_nombres_colonias(sin_demo, demografia)
    
    # 4. Analizar tipos de polígonos
    sin_demo_completo, df_no_res = analizar_tipos_poligonos(sin_demo, gdf_poligonos)
    
    # 5. Análisis geográfico
    analizar_area_geografica(sin_demo, con_demo)
    
    # 6. Proponer soluciones
    proponer_soluciones(matches_exactos, sin_demo_completo)
    
    # 7. Guardar
    guardar_diagnostico(sin_demo, df_no_res)
    
    print("\n" + "="*70)
    print("✓ DIAGNÓSTICO COMPLETADO")
    print("="*70)


if __name__ == "__main__":
    main()
