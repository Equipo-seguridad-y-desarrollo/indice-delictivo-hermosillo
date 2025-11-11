"""
Diagnóstico: ¿Por qué hay tantos incidentes sin coordenadas?
Investigar qué colonias no tienen geocodificación
"""

import pandas as pd
from pathlib import Path

def main():
    print("="*70)
    print("DIAGNÓSTICO: INCIDENTES SIN COORDENADAS")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    
    # Cargar datos
    print("\nCargando datos...")
    reportes = pd.read_csv(project_root / 'data' / 'interim' / 'reportes_de_incidentes_procesados_2018_2025.csv')
    coords = pd.read_csv(project_root / 'data' / 'processed' / 'colonias_reportes_911_con_coordenadas.csv')
    mapeo = pd.read_csv(project_root / 'data' / 'processed' / 'mapeo_colonias_reportes_911.csv')
    
    print(f"  Reportes totales: {len(reportes):,}")
    print(f"  Colonias únicas en reportes: {reportes['COLONIA'].nunique():,}")
    print(f"  Colonias geocodificadas: {len(coords):,}")
    
    # Normalizar nombres
    print("\n" + "="*70)
    print("ANÁLISIS DE COBERTURA")
    print("="*70)
    
    reportes_norm = reportes.merge(
        mapeo, 
        left_on='COLONIA', 
        right_on='COLONIA_ORIGINAL',
        how='left'
    )
    reportes_norm['COLONIA_NORMALIZADA'] = reportes_norm['COLONIA_NORMALIZADA'].fillna(reportes_norm['COLONIA'])
    
    # Agregar coordenadas
    reportes_con_coords = reportes_norm.merge(
        coords[['COLONIA', 'LATITUD', 'LONGITUD']], 
        left_on='COLONIA_NORMALIZADA', 
        right_on='COLONIA',
        how='left',
        suffixes=('', '_coord')
    )
    
    con_coords = reportes_con_coords['LATITUD'].notna()
    sin_coords = ~con_coords
    
    print(f"\nReportes con coordenadas: {con_coords.sum():,} ({con_coords.sum()/len(reportes)*100:.1f}%)")
    print(f"Reportes sin coordenadas: {sin_coords.sum():,} ({sin_coords.sum()/len(reportes)*100:.1f}%)")
    
    # Analizar colonias sin coordenadas
    print("\n" + "="*70)
    print("COLONIAS SIN GEOCODIFICACIÓN")
    print("="*70)
    
    reportes_sin_coords = reportes_con_coords[sin_coords]
    
    # Top 20 colonias sin coordenadas
    top_sin_coords = reportes_sin_coords['COLONIA'].value_counts().head(20)
    
    print(f"\nTop 20 colonias sin coordenadas (total: {sin_coords.sum():,} incidentes):")
    print(f"{'Colonia':<50} {'Incidentes':>10}")
    print("-"*70)
    for colonia, count in top_sin_coords.items():
        print(f"{colonia:<50} {count:>10,}")
    
    # Porcentaje que representan
    top_20_total = top_sin_coords.sum()
    print(f"\nTop 20 representan: {top_20_total:,} incidentes ({top_20_total/sin_coords.sum()*100:.1f}% del total sin coords)")
    
    # Analizar tipos de colonias sin coordenadas
    print("\n" + "="*70)
    print("ANÁLISIS DE PATRONES")
    print("="*70)
    
    colonias_sin_coords = reportes_sin_coords['COLONIA'].unique()
    print(f"\nColonias únicas sin coordenadas: {len(colonias_sin_coords):,}")
    
    # Detectar patrones
    patrones = {
        'SIN CLASIFICAR': 0,
        'SIN NOMBRE': 0,
        'SIN COLONIA': 0,
        'Vacías o NULL': 0,
        'Otras': 0
    }
    
    for col in colonias_sin_coords:
        col_upper = str(col).upper().strip()
        if 'SIN CLASIFICAR' in col_upper:
            patrones['SIN CLASIFICAR'] += 1
        elif 'SIN NOMBRE' in col_upper:
            patrones['SIN NOMBRE'] += 1
        elif 'SIN COLONIA' in col_upper:
            patrones['SIN COLONIA'] += 1
        elif col_upper in ['', 'NAN', 'NONE', 'NULL']:
            patrones['Vacías o NULL'] += 1
        else:
            patrones['Otras'] += 1
    
    print("\nPatrones detectados en nombres de colonias:")
    for patron, count in patrones.items():
        print(f"  {patron}: {count} colonias")
    
    # Contar incidentes por patrón
    print("\nIncidentes por patrón:")
    for patron in ['SIN CLASIFICAR', 'SIN NOMBRE', 'SIN COLONIA']:
        incidentes = reportes_sin_coords[reportes_sin_coords['COLONIA'].str.contains(patron, case=False, na=False)]
        if len(incidentes) > 0:
            print(f"  {patron}: {len(incidentes):,} incidentes ({len(incidentes)/sin_coords.sum()*100:.1f}%)")
    
    # Verificar si están en el mapeo pero no geocodificadas
    print("\n" + "="*70)
    print("ANÁLISIS DE MAPEO")
    print("="*70)
    
    colonias_normalizadas = set(reportes_norm['COLONIA_NORMALIZADA'].unique())
    colonias_geocodificadas = set(coords['COLONIA'].unique())
    
    en_mapeo_sin_coords = colonias_normalizadas - colonias_geocodificadas
    
    print(f"\nColonias normalizadas: {len(colonias_normalizadas):,}")
    print(f"Colonias geocodificadas: {len(colonias_geocodificadas):,}")
    print(f"En mapeo pero SIN geocodificar: {len(en_mapeo_sin_coords):,}")
    
    if len(en_mapeo_sin_coords) > 0:
        # Contar incidentes afectados
        reportes_afectados = reportes_norm[reportes_norm['COLONIA_NORMALIZADA'].isin(en_mapeo_sin_coords)]
        print(f"Incidentes afectados: {len(reportes_afectados):,} ({len(reportes_afectados)/len(reportes)*100:.1f}%)")
        
        # Top 20 de estas colonias
        print(f"\nTop 20 colonias normalizadas sin geocodificar:")
        top_sin_geo = reportes_afectados['COLONIA_NORMALIZADA'].value_counts().head(20)
        for colonia, count in top_sin_geo.items():
            print(f"  {colonia}: {count:,} incidentes")
    
    # Resumen y recomendaciones
    print("\n" + "="*70)
    print("RESUMEN Y RECOMENDACIONES")
    print("="*70)
    
    print("\n🔍 CAUSAS PRINCIPALES:")
    print(f"   1. Colonias sin clasificar: ~{reportes_sin_coords['COLONIA'].str.contains('SIN CLASIFICAR', case=False, na=False).sum():,} incidentes")
    print(f"   2. Colonias sin nombre válido: ~{reportes_sin_coords['COLONIA'].str.contains('SIN NOMBRE|SIN COLONIA', case=False, na=False).sum():,} incidentes")
    print(f"   3. Colonias normalizadas pero no geocodificadas: ~{len(reportes_afectados):,} incidentes")
    
    print("\n✅ SOLUCIONES:")
    print("   1. Geocodificar las colonias faltantes (usar script de geocodificación)")
    print("   2. Filtrar incidentes 'SIN CLASIFICAR' antes del análisis")
    print("   3. Validar datos en origen (sistema 911)")
    
    print("\n💡 IMPACTO:")
    porcentaje_sin_coords = sin_coords.sum() / len(reportes) * 100
    print(f"   - {porcentaje_sin_coords:.1f}% de incidentes sin coordenadas")
    print(f"   - Mejorando geocodificación podríamos recuperar ~{len(reportes_afectados):,} incidentes")
    print(f"   - Esto aumentaría cobertura de {con_coords.sum()/len(reportes)*100:.1f}% a ~{(con_coords.sum()+len(reportes_afectados))/len(reportes)*100:.1f}%")


if __name__ == "__main__":
    main()
