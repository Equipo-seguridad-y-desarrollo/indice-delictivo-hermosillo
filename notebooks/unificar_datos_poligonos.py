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
    
    # 2. Demografía (datos)
    print("\n[2/6] Cargando demografía...")
    demografia_path = project_root / 'data' / 'raw' / 'demografia_hermosillo.csv'
    demografia = pd.read_csv(demografia_path)
    print(f"   Colonias con demografía: {len(demografia):,}")
    
    # 3. Demografía con coordenadas (para spatial join)
    print("\n[3/6] Cargando coordenadas de demografía...")
    demografia_coords_path = project_root / 'data' / 'processed' / 'colonias_demografia_con_coordenadas.csv'
    demografia_coords = pd.read_csv(demografia_coords_path)
    print(f"   Demografía geocodificada: {len(demografia_coords):,}")
    
    # 4. Reportes procesados
    # 4. Reportes procesados
    print("\n[4/6] Cargando reportes 911 procesados...")
    reportes_path = project_root / 'data' / 'interim' / 'reportes_de_incidentes_procesados_2018_2025.csv'
    reportes = pd.read_csv(reportes_path)
    reportes['Timestamp'] = pd.to_datetime(reportes['Timestamp'])
    print(f"   Reportes cargados: {len(reportes):,}")
    print(f"   Periodo: {reportes['Timestamp'].min()} a {reportes['Timestamp'].max()}")
    
    # 5. Mapeo de colonias (normalización)
    print("\n[5/6] Cargando mapeo de colonias...")
    mapeo_path = project_root / 'data' / 'processed' / 'mapeo_colonias_reportes_911.csv'
    mapeo = pd.read_csv(mapeo_path)
    print(f"   Mapeos cargados: {len(mapeo):,}")
    
    # 6. Coordenadas de colonias de reportes
    print("\n[6/6] Cargando coordenadas de reportes...")
    coords_path = project_root / 'data' / 'processed' / 'colonias_reportes_911_con_coordenadas.csv'
    coords = pd.read_csv(coords_path)
    print(f"   Colonias geocodificadas: {len(coords):,}")
    
    return gdf_poligonos, demografia, demografia_coords, reportes, mapeo, coords


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
    
    print(f"\n✓ Spatial join completado:")
    print(f"   Incidentes dentro de polígonos: {con_poligono:,} ({con_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    print(f"   Incidentes sin polígono: {sin_poligono:,} ({sin_poligono/len(incidentes_en_poligonos)*100:.1f}%)")
    
    return incidentes_en_poligonos


def spatial_join_demografia_poligonos(demografia, demografia_coords, gdf_poligonos):
    """
    Asignar datos demográficos a polígonos mediante spatial join de coordenadas
    Usa buffer de 500m para capturar colonias cercanas que están justo fuera del polígono
    Y merge por nombre como fallback para coordenadas incorrectas
    """
    print("\n" + "="*70)
    print("SPATIAL JOIN: DEMOGRAFÍA → POLÍGONOS (3 pasos)")
    print("="*70)
    
    # Unir demografía con sus coordenadas
    print("\nUniendo demografía con coordenadas...")
    demografia_geo = demografia.merge(
        demografia_coords[['nom_col', 'LATITUD', 'LONGITUD']], 
        on='nom_col', 
        how='inner'
    )
    print(f"   Demografía con coordenadas: {len(demografia_geo):,}")
    
    # Crear GeoDataFrame con puntos
    print("Creando geometría de puntos...")
    gdf_demografia = gpd.GeoDataFrame(
        demografia_geo,
        geometry=gpd.points_from_xy(
            demografia_geo['LONGITUD'], 
            demografia_geo['LATITUD']
        ),
        crs='EPSG:4326'
    )
    
    # PASO 1: Spatial join sin buffer (dentro del polígono)
    print("\n[Paso 1/3] Spatial join SIN buffer (puntos dentro)...")
    demografia_en_poligonos = gpd.sjoin(
        gdf_demografia,
        gdf_poligonos[['CVE_COL', 'COLONIA', 'geometry']],
        how='left',
        predicate='within'
    )
    
    con_poligono_exacto = demografia_en_poligonos['CVE_COL'].notna().sum()
    sin_poligono = demografia_en_poligonos['CVE_COL'].isna().sum()
    
    print(f"   ✓ Dentro de polígonos: {con_poligono_exacto:,} ({con_poligono_exacto/len(demografia_en_poligonos)*100:.1f}%)")
    print(f"   ✗ Sin polígono: {sin_poligono:,} ({sin_poligono/len(demografia_en_poligonos)*100:.1f}%)")
    
    # PASO 2: Para los que no matchearon, usar buffer de 500m
    if sin_poligono > 0:
        print(f"\n[Paso 2/3] Aplicando buffer de 500m para {sin_poligono:,} colonias restantes...")
        
        # Convertir a proyección métrica (UTM 12N para Hermosillo)
        gdf_poligonos_utm = gdf_poligonos.to_crs('EPSG:32612')
        
        # Aplicar buffer de 500m
        gdf_poligonos_buffer = gdf_poligonos_utm.copy()
        gdf_poligonos_buffer.geometry = gdf_poligonos_utm.geometry.buffer(500)
        
        # Volver a WGS84
        gdf_poligonos_buffer = gdf_poligonos_buffer.to_crs('EPSG:4326')
        
        # Solo procesar los que no tienen match
        sin_match = gdf_demografia[gdf_demografia['nom_col'].isin(
            demografia_en_poligonos[demografia_en_poligonos['CVE_COL'].isna()]['nom_col']
        )].copy()
        
        # Spatial join con buffer
        match_buffer = gpd.sjoin(
            sin_match,
            gdf_poligonos_buffer[['CVE_COL', 'COLONIA', 'geometry']],
            how='left',
            predicate='within'
        )
        
        # Actualizar los que ahora sí matchearon
        nuevos_match = match_buffer[match_buffer['CVE_COL'].notna()]
        
        if len(nuevos_match) > 0:
            # Actualizar demografia_en_poligonos con los nuevos matches
            for idx, row in nuevos_match.iterrows():
                mask = demografia_en_poligonos['nom_col'] == row['nom_col']
                demografia_en_poligonos.loc[mask, 'CVE_COL'] = row['CVE_COL']
                demografia_en_poligonos.loc[mask, 'COLONIA'] = row['COLONIA']
        
        con_buffer = nuevos_match['CVE_COL'].notna().sum()
        print(f"   ✓ Capturadas con buffer: {con_buffer:,}")
    
    # PASO 3: Para los que aún no matchearon, intentar merge por NOMBRE
    sin_poligono_despues_buffer = demografia_en_poligonos['CVE_COL'].isna().sum()
    
    if sin_poligono_despues_buffer > 0:
        print(f"\n[Paso 3/3] Merge por NOMBRE para {sin_poligono_despues_buffer:,} colonias restantes...")
        print("   (Esto captura colonias con coordenadas incorrectas pero nombre correcto)")
        
        # Normalizar nombres para matching
        demografia_en_poligonos['nom_col_norm'] = (
            demografia_en_poligonos['nom_col']
            .str.upper()
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
        )
        
        gdf_poligonos_norm = gdf_poligonos.copy()
        gdf_poligonos_norm['COLONIA_norm'] = (
            gdf_poligonos_norm['COLONIA']
            .str.upper()
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
        )
        
        # Solo para los que no tienen CVE_COL
        sin_match_nombre = demografia_en_poligonos[
            demografia_en_poligonos['CVE_COL'].isna()
        ].copy()
        
        # Merge por nombre normalizado
        match_nombre = sin_match_nombre.merge(
            gdf_poligonos_norm[['CVE_COL', 'COLONIA', 'COLONIA_norm']],
            left_on='nom_col_norm',
            right_on='COLONIA_norm',
            how='left',
            suffixes=('_demo', '_poli')
        )
        
        # Actualizar los que matchearon por nombre
        nuevos_match_nombre = match_nombre[match_nombre['CVE_COL_poli'].notna()]
        
        if len(nuevos_match_nombre) > 0:
            for idx, row in nuevos_match_nombre.iterrows():
                mask = (demografia_en_poligonos['nom_col'] == row['nom_col']) & \
                       (demografia_en_poligonos['CVE_COL'].isna())
                demografia_en_poligonos.loc[mask, 'CVE_COL'] = row['CVE_COL_poli']
                demografia_en_poligonos.loc[mask, 'COLONIA'] = row['COLONIA_poli']
        
        con_nombre = len(nuevos_match_nombre)
        print(f"   ✓ Capturadas por nombre: {con_nombre:,}")
    
        con_nombre = len(nuevos_match_nombre)
        print(f"   ✓ Capturadas por nombre: {con_nombre:,}")
    
    # Estadísticas finales
    con_poligono_final = demografia_en_poligonos['CVE_COL'].notna().sum()
    sin_poligono_final = demografia_en_poligonos['CVE_COL'].isna().sum()
    
    print(f"\n📊 RESULTADO FINAL (3 pasos):")
    print(f"   ✓ Demografía con polígono: {con_poligono_final:,} ({con_poligono_final/len(demografia_en_poligonos)*100:.1f}%)")
    print(f"   ✗ Demografía sin polígono: {sin_poligono_final:,} ({sin_poligono_final/len(demografia_en_poligonos)*100:.1f}%)")
    print(f"\n   Desglose:")
    print(f"   • Paso 1 (spatial exacto): {con_poligono_exacto:,}")
    if sin_poligono > 0 and 'con_buffer' in locals():
        print(f"   • Paso 2 (buffer 500m): {con_buffer:,}")
    if sin_poligono_despues_buffer > 0 and 'con_nombre' in locals():
        print(f"   • Paso 3 (merge nombre): {con_nombre:,}")
    
    # Preparar para merge con polígonos
    demografia_por_poligono = demografia_en_poligonos.dropna(subset=['CVE_COL'])[[
        'CVE_COL', 'poblacion_total', 'viviendas_totales', 
        'escolaridad_años_prom', 'pctj_menores18', 'pctj_hombres', 'pctj_mujeres'
    ]].drop_duplicates(subset=['CVE_COL'])
    
    print(f"   Polígonos con demografía: {len(demografia_por_poligono):,}")
    
    return demografia_por_poligono


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
            
            print(f"   Índice de riesgo calculado para {completos.sum()} polígonos")
        except ImportError:
            print("   ⚠️  sklearn no disponible, índice de riesgo no calculado")
    
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
    gdf_poligonos, demografia, demografia_coords, reportes, mapeo, coords = cargar_datos_base()
    
    # 2. Spatial join: demografía → polígonos
    demografia_por_poligono = spatial_join_demografia_poligonos(demografia, demografia_coords, gdf_poligonos)
    
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
    print(f"\n✓ {output_csv.name}")
    
    # GeoJSON de polígonos
    output_geojson = output_dir / 'poligonos_unificados_completo.geojson'
    df_final.to_file(output_geojson, driver='GeoJSON')
    print(f"✓ {output_geojson.name}")
    
    # Incidentes individuales con CVE_COL (para mapa temporal)
    inc_validos = generar_resumen(df_final, incidentes_en_poligonos)
    
    # Guardar incidentes con CVE_COL para el dashboard
    cols_temporal = ['CVE_COL', 'COLONIA_POLIGONO', 'TIPO DE INCIDENTE', 'Timestamp', 
                    'ParteDelDia', 'DiaDeLaSemana', 'Categoria_Incidente', 
                    'Nivel_Severidad', 'LATITUD', 'LONGITUD']
    
    inc_temporal = inc_validos[cols_temporal].copy()
    output_temporal = output_dir / 'incidentes_con_poligono_temporal.csv'
    inc_temporal.to_csv(output_temporal, index=False, encoding='utf-8-sig')
    print(f"✓ {output_temporal.name}")
    
    print(f"\n📂 Archivos generados en: {output_dir}/")
    print("="*70)


if __name__ == "__main__":
    main()
