"""
Script para unificar datos de incidentes, demografía y polígonos
Usa spatial join para asignar incidentes a polígonos y calcula índices delictivos
"""

import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path
import numpy as np
from datetime import datetime

def cargar_datos_base():
    """Cargar todos los datasets necesarios"""
    print("="*70)
    print("CARGANDO DATOS BASE")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    
    # 1. Polígonos (BASE MAESTRA)
    print("\n[1/6] Cargando polígonos (base maestra)...")
    poligonos_path = project_root / 'data' / 'raw' / 'poligonos_hermosillo.csv'
    poligonos = pd.read_csv(poligonos_path)
    
    # Detectar columna WKT y convertir a geometría (acepta 'POLIGONO_WKT' o 'geometry')
    if 'POLIGONO_WKT' in poligonos.columns:
        wkt_col = 'POLIGONO_WKT'
    elif 'geometry' in poligonos.columns:
        wkt_col = 'geometry'
    else:
        raise KeyError("No WKT column found in poligonos_hermosillo.csv (expected 'POLIGONO_WKT' or 'geometry')")

    # Convertir WKT a geometría
    gdf_poligonos = gpd.GeoDataFrame(
        poligonos,
        geometry=poligonos[wkt_col].apply(wkt.loads),
        crs='EPSG:4326'
    )
    print(f"   Polígonos cargados: {len(gdf_poligonos):,}")

    # Normalizar nombres de columnas para compatibilidad con el resto del script
    # Algunas fuentes usan minúsculas ('cve_col', 'nom_col', 'cp')
    col_map = {}
    if 'cve_col' in gdf_poligonos.columns and 'CVE_COL' not in gdf_poligonos.columns:
        col_map['cve_col'] = 'CVE_COL'
    if 'nom_col' in gdf_poligonos.columns and 'COLONIA' not in gdf_poligonos.columns:
        col_map['nom_col'] = 'COLONIA'
    if 'cp' in gdf_poligonos.columns and 'CP' not in gdf_poligonos.columns:
        col_map['cp'] = 'CP'

    if col_map:
        gdf_poligonos = gdf_poligonos.rename(columns=col_map)
    
    # 2. Demografía (preferir versión normalizada si existe)
    print("\n[2/5] Cargando demografía...")
    demo_clean_path = project_root / 'data' / 'processed' / 'demografia_limpio.csv'
    demo_raw_path = project_root / 'data' / 'raw' / 'demografia_hermosillo.csv'
    if demo_clean_path.exists():
        demografia = pd.read_csv(demo_clean_path)
        print(f"   Usando demografía limpia: {demo_clean_path.name} ({len(demografia):,} registros)")
    else:
        demografia = pd.read_csv(demo_raw_path)
        print(f"   Usando demografía RAW: {demo_raw_path.name} ({len(demografia):,} registros)")
    
    # 3. Reportes procesados
    print("\n[3/5] Cargando reportes 911 procesados...")
    reportes_path = project_root / 'data' / 'interim' / 'reportes_de_incidentes_procesados_2018_2025.csv'
    reportes = pd.read_csv(reportes_path)
    reportes['Timestamp'] = pd.to_datetime(reportes['Timestamp'])
    print(f"   Reportes cargados: {len(reportes):,}")
    print(f"   Periodo: {reportes['Timestamp'].min()} a {reportes['Timestamp'].max()}")
    
    # 4. Mapeo de colonias (normalización)
    print("\n[4/5] Cargando mapeo de colonias...")
    mapeo_path = project_root / 'data' / 'processed' / 'mapeo_colonias_reportes_911.csv'
    mapeo = pd.read_csv(mapeo_path)
    print(f"   Mapeos cargados: {len(mapeo):,}")
    
    # 5. Coordenadas de colonias de reportes
    print("\n[5/5] Cargando coordenadas de reportes...")
    coords_path = project_root / 'data' / 'processed' / 'colonias_reportes_911_con_coordenadas.csv'
    coords = pd.read_csv(coords_path)
    print(f"   Colonias geocodificadas: {len(coords):,}")
    
    return gdf_poligonos, demografia, reportes, mapeo, coords


def preparar_incidentes_con_geometria(reportes, mapeo, coords):
    """
    Crear GeoDataFrame de incidentes con coordenadas
    Cada incidente hereda las coordenadas de su colonia
    """
    print("\n" + "="*70)
    print("PREPARANDO INCIDENTES CON GEOMETRÍA")
    print("="*70)
    
    # Normalizar nombres de colonias
    print("\nNormalizando nombres de colonias...")
    reportes_norm = reportes.merge(
        mapeo, 
        left_on='COLONIA', 
        right_on='COLONIA_ORIGINAL',
        how='left'
    )
    
    # Llenar NaN en COLONIA_NORMALIZADA (colonias que no necesitaron normalización)
    reportes_norm['COLONIA_NORMALIZADA'] = reportes_norm['COLONIA_NORMALIZADA'].fillna(reportes_norm['COLONIA'])
    
    # Agregar coordenadas
    print("Agregando coordenadas...")
    reportes_geo = reportes_norm.merge(
        coords[['COLONIA', 'LATITUD', 'LONGITUD']], 
        left_on='COLONIA_NORMALIZADA', 
        right_on='COLONIA',
        how='left',
        suffixes=('', '_coord')
    )
    
    # Filtrar solo los que tienen coordenadas
    antes = len(reportes_geo)
    reportes_geo = reportes_geo.dropna(subset=['LATITUD', 'LONGITUD'])
    despues = len(reportes_geo)
    
    print(f"   Incidentes con coordenadas: {despues:,} ({despues/antes*100:.1f}%)")
    print(f"   Incidentes sin coordenadas: {antes - despues:,} ({(antes-despues)/antes*100:.1f}%)")
    
    # Crear geometría de puntos
    print("Creando geometría de puntos...")
    gdf_reportes = gpd.GeoDataFrame(
        reportes_geo,
        geometry=gpd.points_from_xy(
            reportes_geo['LONGITUD'], 
            reportes_geo['LATITUD']
        ),
        crs='EPSG:4326'
    )
    
    return gdf_reportes


def spatial_join_incidentes_poligonos(gdf_reportes, gdf_poligonos):
    """
    Asignar cada incidente al polígono que lo contiene mediante spatial join
    """
    print("\n" + "="*70)
    print("SPATIAL JOIN: INCIDENTES → POLÍGONOS")
    print("="*70)
    
    print("\nRealizando spatial join (esto puede tomar unos minutos)...")
    
    # Spatial join: cada punto cae en UN polígono
    incidentes_en_poligonos = gpd.sjoin(
        gdf_reportes,
        gdf_poligonos[['CVE_COL', 'COLONIA', 'CP', 'geometry']],
        how='left',
        predicate='within'
    )
    
    # Renombrar para evitar confusión
    incidentes_en_poligonos.rename(columns={
        'COLONIA_right': 'COLONIA_POLIGONO',
        'COLONIA_left': 'COLONIA_REPORTE'
    }, inplace=True)
    
    # Estadísticas de cobertura
    con_poligono = incidentes_en_poligonos['CVE_COL'].notna().sum()
    sin_poligono = incidentes_en_poligonos['CVE_COL'].isna().sum()
    
    print(f"\nSpatial join completado:")
    print(f"   Incidentes dentro de polígonos: {con_poligono:,} ({con_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    print(f"   Incidentes sin polígono: {sin_poligono:,} ({sin_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    
    return incidentes_en_poligonos


def merge_demografia_poligonos_por_clave(demografia, gdf_poligonos):
    """
    Asignar datos demográficos a polígonos mediante merge directo por cve_col (clave oficial INEGI)
    Este método es mucho más rápido y preciso que spatial join, ya que usa identificadores únicos oficiales.
    NO requiere geocodificación ni coordenadas.
    """
    print("\n" + "="*70)
    print("MERGE DIRECTO: DEMOGRAFIA -> POLIGONOS (por cve_col)")
    print("="*70)
    
    print("\nRealizando merge directo por cve_col (clave oficial INEGI)...")
    print("   Ventajas: Sin costos de API, sin spatial join, 100% preciso")
    
    # Preparar demografía con CVE_COL normalizado
    demografia_prep = demografia.copy()
    
    # Asegurar que ambas claves están en el mismo formato
    if 'cve_col' in demografia_prep.columns:
        demografia_prep['CVE_COL'] = demografia_prep['cve_col'].astype(str)
    
    # Merge directo por CVE_COL
    demografia_por_poligono = gdf_poligonos[['CVE_COL', 'COLONIA']].merge(
        demografia_prep[['cve_col', 'poblacion_total', 'viviendas_totales', 
                        'escolaridad_años_prom', 'pctj_menores18', 'pctj_hombres', 'pctj_mujeres']],
        left_on='CVE_COL',
        right_on='cve_col',
        how='left'
    )
    
    # Limpiar columna duplicada
    demografia_por_poligono = demografia_por_poligono.drop(columns=['cve_col'])
    
    # Estadísticas
    con_demografia = demografia_por_poligono['poblacion_total'].notna().sum()
    sin_demografia = demografia_por_poligono['poblacion_total'].isna().sum()
    
    print(f"\nRESULTADO:")
    print(f"   Poligonos con demografia: {con_demografia:,} ({con_demografia/len(gdf_poligonos)*100:.1f}%)")
    print(f"   Poligonos sin demografia: {sin_demografia:,} ({sin_demografia/len(gdf_poligonos)*100:.1f}%)")
    
    # Verificar si hay colonias en demografía que no están en polígonos
    if 'cve_col' in demografia.columns:
        cve_demo = set(demografia['cve_col'].dropna().astype(str))
        cve_poli = set(gdf_poligonos['CVE_COL'].astype(str))
        sin_poligono = cve_demo - cve_poli
        if len(sin_poligono) > 0:
            print(f"\n   ADVERTENCIA: {len(sin_poligono)} colonias demograficas sin poligono")
            print(f"   (Estas se ignoran en el analisis espacial)")
    
    # Preparar para merge con polígonos
    demografia_final = demografia_por_poligono.dropna(subset=['poblacion_total'])[[
        'CVE_COL', 'poblacion_total', 'viviendas_totales', 
        'escolaridad_años_prom', 'pctj_menores18', 'pctj_hombres', 'pctj_mujeres'
    ]].drop_duplicates(subset=['CVE_COL'])
    
    print(f"\n   Poligonos listos para analisis: {len(demografia_final):,}")
    
    return demografia_final


def agregar_por_poligono(incidentes_en_poligonos, gdf_poligonos, demografia_por_poligono):
    """
    Agregar todos los incidentes por polígono y unir con demografía
    """
    print("\n" + "="*70)
    print("AGREGACIÓN POR POLÍGONO")
    print("="*70)
    
    # Filtrar solo incidentes que cayeron en algún polígono
    inc_validos = incidentes_en_poligonos.dropna(subset=['CVE_COL'])
    print(f"\nIncidentes válidos para agregación: {len(inc_validos):,}")
    
    # AGREGACIONES
    print("Calculando agregaciones...")
    
    # Agregaciones simples
    agg_dict = {
        'total_incidentes': ('TIPO DE INCIDENTE', 'count'),
        'incidentes_alta': ('Nivel_Severidad', lambda x: (x == 'ALTA').sum()),
        'incidentes_media': ('Nivel_Severidad', lambda x: (x == 'MEDIA').sum()),
        'incidentes_baja': ('Nivel_Severidad', lambda x: (x == 'BAJA').sum()),
        'categorias_dict': ('Categoria_Incidente', lambda x: x.value_counts().to_dict()),
        'partes_dia_dict': ('ParteDelDia', lambda x: x.value_counts().to_dict()),
        'incidentes_fin_semana': ('EsFinDeSemana', lambda x: (x == 'Sí').sum()),
        'incidentes_quincena': ('EsQuincena', lambda x: (x == 'Sí').sum()),
        'dias_semana_dict': ('DiaDeLaSemana', lambda x: x.value_counts().to_dict()),
        'fecha_inicio': ('Timestamp', 'min'),
        'fecha_fin': ('Timestamp', 'max')
    }
    
    agg_incidentes = inc_validos.groupby('CVE_COL').agg(**agg_dict).reset_index()
    
    print(f"   Polígonos con incidentes: {len(agg_incidentes):,}")
    
    # UNIR CON POLÍGONOS (geometría + info base)
    print("Uniendo con polígonos...")
    resultado = gdf_poligonos.merge(agg_incidentes, on='CVE_COL', how='left')
    
    # Rellenar polígonos sin incidentes con 0
    resultado['total_incidentes'] = resultado['total_incidentes'].fillna(0).astype(int)
    resultado['incidentes_alta'] = resultado['incidentes_alta'].fillna(0).astype(int)
    resultado['incidentes_media'] = resultado['incidentes_media'].fillna(0).astype(int)
    resultado['incidentes_baja'] = resultado['incidentes_baja'].fillna(0).astype(int)
    resultado['incidentes_fin_semana'] = resultado['incidentes_fin_semana'].fillna(0).astype(int)
    resultado['incidentes_quincena'] = resultado['incidentes_quincena'].fillna(0).astype(int)
    
    # UNIR CON DEMOGRAFÍA (ya mapeada por spatial join)
    print("Uniendo con demografía...")
    resultado = resultado.merge(
        demografia_por_poligono,
        on='CVE_COL',
        how='left'
    )
    
    con_demografia = resultado['poblacion_total'].notna().sum()
    print(f"   Polígonos con demografía: {con_demografia:,}")
    
    return resultado


def calcular_indices(df_poligonos_completo):
    """
    Calcular índices per cápita y métricas derivadas
    """
    print("\n" + "="*70)
    print("CALCULANDO ÍNDICES DELICTIVOS")
    print("="*70)
    
    # Filtrar solo polígonos con datos demográficos
    con_poblacion = df_poligonos_completo['poblacion_total'].notna() & (df_poligonos_completo['poblacion_total'] > 0)
    
    print(f"\nPolígonos con población: {con_poblacion.sum()}")
    print(f"Polígonos sin población: {(~con_poblacion).sum()}")
    
    # TASAS POR 1000 HABITANTES
    print("\nCalculando tasas per cápita...")
    df_poligonos_completo.loc[con_poblacion, 'tasa_incidentes_per_1k'] = (
        df_poligonos_completo.loc[con_poblacion, 'total_incidentes'] / 
        df_poligonos_completo.loc[con_poblacion, 'poblacion_total'] * 1000
    )
    
    df_poligonos_completo.loc[con_poblacion, 'tasa_alta_severidad_per_1k'] = (
        df_poligonos_completo.loc[con_poblacion, 'incidentes_alta'] / 
        df_poligonos_completo.loc[con_poblacion, 'poblacion_total'] * 1000
    )
    
    # SCORE DE SEVERIDAD (0-3, ponderado)
    print("Calculando score de severidad...")
    df_poligonos_completo['score_severidad'] = (
        (df_poligonos_completo['incidentes_alta'] * 3 + 
         df_poligonos_completo['incidentes_media'] * 2 + 
         df_poligonos_completo['incidentes_baja'] * 1) / 
        df_poligonos_completo['total_incidentes'].replace(0, 1)
    )
    
    # DENSIDAD POBLACIONAL
    print("Calculando densidad poblacional...")
    df_poligonos_completo['area_km2'] = df_poligonos_completo.geometry.to_crs('EPSG:32612').area / 1e6
    df_poligonos_completo.loc[con_poblacion, 'densidad_poblacional'] = (
        df_poligonos_completo.loc[con_poblacion, 'poblacion_total'] / 
        df_poligonos_completo.loc[con_poblacion, 'area_km2']
    )
    
    # ÍNDICE DE RIESGO COMPUESTO (0-100)
    print("Calculando índice de riesgo compuesto...")
    # Algunos datasets pueden no tener la columna 'IM_2020' (índice de marginación).
    if 'IM_2020' in df_poligonos_completo.columns:
        completos = con_poblacion & df_poligonos_completo['IM_2020'].notna()
    else:
        completos = pd.Series(False, index=df_poligonos_completo.index)

    if completos.sum() > 0:
        try:
            from sklearn.preprocessing import MinMaxScaler
            
            componentes = df_poligonos_completo.loc[completos, [
                'tasa_incidentes_per_1k',
                'score_severidad',
                'IM_2020',
                'densidad_poblacional'
            ]].copy()
            
            # Normalizar 0-1
            scaler = MinMaxScaler()
            componentes_norm = pd.DataFrame(
                scaler.fit_transform(componentes),
                index=componentes.index,
                columns=componentes.columns
            )
            
            # Índice ponderado
            df_poligonos_completo.loc[completos, 'indice_riesgo'] = (
                componentes_norm['tasa_incidentes_per_1k'] * 0.4 +
                componentes_norm['score_severidad'] * 0.3 +
                componentes_norm['IM_2020'] * 0.2 +
                componentes_norm['densidad_poblacional'] * 0.1
            ) * 100
            
            print(f"   Indice de riesgo calculado para {completos.sum()} poligonos")
        except ImportError:
            print("   ADVERTENCIA: sklearn no disponible, indice de riesgo no calculado")
    
    return df_poligonos_completo


def generar_resumen(df_final, inc_en_poligonos):
    """Generar resumen estadístico"""
    print("\n" + "="*70)
    print("RESUMEN ESTADÍSTICO - DATASET UNIFICADO")
    print("="*70)
    
    print(f"\nPOLÍGONOS:")
    print(f"   Total: {len(df_final):,}")
    print(f"   Con incidentes: {(df_final['total_incidentes'] > 0).sum():,}")
    print(f"   Con demografía: {df_final['poblacion_total'].notna().sum():,}")
    if 'indice_riesgo' in df_final.columns:
        print(f"   Con índice de riesgo: {df_final['indice_riesgo'].notna().sum():,}")
    
    print(f"\nINCIDENTES:")
    print(f"   Total: {df_final['total_incidentes'].sum():,}")
    print(f"   Alta severidad: {df_final['incidentes_alta'].sum():,}")
    print(f"   Media severidad: {df_final['incidentes_media'].sum():,}")
    print(f"   Baja severidad: {df_final['incidentes_baja'].sum():,}")
    
    # TOP 10
    print(f"\nTOP 10 POLÍGONOS POR TASA DE INCIDENCIA:")
    if 'tasa_incidentes_per_1k' in df_final.columns:
        top10 = df_final[df_final['tasa_incidentes_per_1k'].notna()].nlargest(10, 'tasa_incidentes_per_1k')
        if len(top10) > 0:
            for idx, row in top10.iterrows():
                print(f"   {row['COLONIA']}: {row['tasa_incidentes_per_1k']:.2f} por 1k hab ({int(row['total_incidentes'])} incidentes)")
        else:
            print("   No hay polígonos con tasa calculada (requiere datos demográficos)")
    else:
        print("   Tasa no calculada")
    
    # Guardar también los incidentes con CVE_COL para el mapa interactivo
    return inc_en_poligonos.dropna(subset=['CVE_COL'])


def main():
    """Pipeline principal"""
    print("\n" + "="*70)
    print("UNIFICACIÓN DE DATOS POR POLÍGONOS")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Cargar datos
    gdf_poligonos, demografia, reportes, mapeo, coords = cargar_datos_base()
    
    # 2. Merge directo: demografía → polígonos (por cve_col)
    demografia_por_poligono = merge_demografia_poligonos_por_clave(demografia, gdf_poligonos)
    
    # 3. Preparar incidentes con geometría
    gdf_reportes = preparar_incidentes_con_geometria(reportes, mapeo, coords)
    
    # 4. Spatial join: incidentes → polígonos
    incidentes_en_poligonos = spatial_join_incidentes_poligonos(gdf_reportes, gdf_poligonos)
    
    # 5. Agregar por polígono
    df_poligonos_completo = agregar_por_poligono(incidentes_en_poligonos, gdf_poligonos, demografia_por_poligono)
    
    # 6. Calcular índices
    df_final = calcular_indices(df_poligonos_completo)
    
    # 6. Guardar resultados
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'data' / 'processed' / 'unificado'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "="*70)
    print("GUARDANDO RESULTADOS")
    print("="*70)
    
    # CSV de polígonos agregados
    df_final_csv = df_final.drop(columns=['geometry'])
    output_csv = output_dir / 'poligonos_unificados_completo.csv'
    df_final_csv.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\nGuardado: {output_csv.name}")
    
    # GeoJSON de polígonos
    output_geojson = output_dir / 'poligonos_unificados_completo.geojson'
    df_final.to_file(output_geojson, driver='GeoJSON')
    print(f"Guardado: {output_geojson.name}")
    
    # Incidentes individuales con CVE_COL (para mapa temporal)
    inc_validos = generar_resumen(df_final, incidentes_en_poligonos)
    
    # Guardar incidentes con CVE_COL para el dashboard
    cols_temporal = ['CVE_COL', 'COLONIA_POLIGONO', 'TIPO DE INCIDENTE', 'Timestamp', 
                    'ParteDelDia', 'DiaDeLaSemana', 'Categoria_Incidente', 
                    'Nivel_Severidad', 'LATITUD', 'LONGITUD']
    
    inc_temporal = inc_validos[cols_temporal].copy()
    output_temporal = output_dir / 'incidentes_con_poligono_temporal.csv'
    inc_temporal.to_csv(output_temporal, index=False, encoding='utf-8-sig')
    print(f"Guardado: {output_temporal.name}")
    
    print(f"\nArchivos generados en: {output_dir}/")
    print("="*70)


if __name__ == "__main__":
    main()
