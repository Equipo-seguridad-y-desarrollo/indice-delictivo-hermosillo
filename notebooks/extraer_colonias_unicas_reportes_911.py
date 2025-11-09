"""
Script para extraer colonias únicas del archivo procesado de reportes 911
Detecta y agrupa colonias con errores ortográficos usando fuzzy matching

Archivo de entrada:
    data/interim/reportes_de_incidentes_procesados_2018_2025.csv
    
Archivos de salida:
    - data/processed/colonias_unicas_reportes_911.csv (lista simple)
    - data/processed/mapeo_colonias_reportes_911.csv (mapeo original → normalizada)
    - data/processed/colonias_reportes_911_agrupadas_reporte.csv (reporte de variantes)
"""

import pandas as pd
from difflib import SequenceMatcher
import unicodedata
from pathlib import Path


def normalizar_texto(texto):
    """
    Normaliza el texto removiendo acentos, convirtiendo a mayúsculas
    y eliminando espacios extra
    """
    if pd.isna(texto):
        return ""
    
    # Convertir a string y a mayúsculas
    texto = str(texto).upper().strip()
    
    # Remover acentos
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Normalizar espacios múltiples a uno solo
    texto = ' '.join(texto.split())
    
    return texto


def similitud(texto1, texto2):
    """
    Calcula la similitud entre dos textos usando SequenceMatcher
    Retorna un valor entre 0 y 1
    """
    return SequenceMatcher(None, texto1, texto2).ratio()


def son_variantes_validas(texto1, texto2, texto1_norm, texto2_norm):
    """
    Verifica si dos colonias son realmente variantes ortográficas válidas
    y no colonias completamente diferentes
    
    Args:
        texto1, texto2: Textos originales
        texto1_norm, texto2_norm: Textos normalizados
    
    Returns:
        bool: True si son variantes válidas
    """
    import re
    
    # Regla 1: Si solo difieren en acentos/mayúsculas, son variantes válidas
    if texto1_norm == texto2_norm:
        return True
    
    # Regla 2a: Detectar números romanos (indican colonias diferentes)
    nums_romanos1 = re.findall(r'\b([IVX]+)\s*$', texto1.upper())
    nums_romanos2 = re.findall(r'\b([IVX]+)\s*$', texto2.upper())
    
    if nums_romanos1 and nums_romanos2 and nums_romanos1 != nums_romanos2:
        return False
    
    if bool(nums_romanos1) != bool(nums_romanos2):
        return False
    
    # Regla 2b: Detectar números arábigos al final del nombre
    nums_final1 = re.findall(r'\s+(\d+)\s*$', texto1.upper())
    nums_final2 = re.findall(r'\s+(\d+)\s*$', texto2.upper())
    
    if nums_final1 and nums_final2 and nums_final1 != nums_final2:
        return False
    
    if bool(nums_final1) != bool(nums_final2):
        return False
    
    # Regla 3: Detectar sectores/etapas diferentes
    palabras_sector = ['SECTOR', 'ETAPA', 'SECCION', 'SECC.', 'SECC']
    tiene_sector1 = any(p in texto1.upper() for p in palabras_sector)
    tiene_sector2 = any(p in texto2.upper() for p in palabras_sector)
    
    if tiene_sector1 or tiene_sector2:
        nums1 = set(re.findall(r'(?:SECTOR|ETAPA|SECCION|SECC\.?)\s*([A-Z0-9]+)', texto1.upper()))
        nums2 = set(re.findall(r'(?:SECTOR|ETAPA|SECCION|SECC\.?)\s*([A-Z0-9]+)', texto2.upper()))
        
        if nums1 and nums2 and nums1 != nums2:
            return False
    
    # Regla 4: Detectar nombres completamente diferentes
    stop_words = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL'}
    
    palabras1 = set(texto1_norm.split()) - stop_words
    palabras2 = set(texto2_norm.split()) - stop_words
    
    if palabras1 and palabras2 and not palabras1.intersection(palabras2):
        return False
    
    # Regla 5: Detectar palabras clave que indican colonias diferentes
    palabras_distintivas = {
        'PINO', 'PINOS', 'ENCINO', 'ENCINOS', 'SAUCE', 'SAUCES', 'PALMA', 'PALMAS',
        'ROBLE', 'ROBLES', 'OLIVO', 'OLIVOS', 'CEDRO', 'CEDROS', 'FRESNO', 'FRESNOS',
        'ALTARIA', 'ANTARA', 'CANTABRIA', 'CATALINAS', 'CATAVINA',
        'ALONDRA', 'ALONDRAS', 'CANTERA', 'CANTERAS', 'MALLORCA',
        'ACACIA', 'CIMA', 'CORSICA', 'CORCITA',
        'BOSQUE', 'PALMAR', 'PRADO', 'PRADERA'
    }
    
    palabras_dist1 = palabras1.intersection(palabras_distintivas)
    palabras_dist2 = palabras2.intersection(palabras_distintivas)
    
    if palabras_dist1 and palabras_dist2 and palabras_dist1 != palabras_dist2:
        return False
    
    return True


def agrupar_colonias_similares(colonias, umbral_similitud=0.90):
    """
    Agrupa colonias que son muy similares (posibles errores ortográficos)
    """
    colonias_normalizadas = {col: normalizar_texto(col) for col in colonias}
    colonias_ordenadas = sorted(colonias, key=lambda x: len(x))
    
    grupos = {}
    procesadas = set()
    
    for colonia in colonias_ordenadas:
        if colonia in procesadas:
            continue
        
        grupo = [colonia]
        procesadas.add(colonia)
        
        for otra_colonia in colonias:
            if otra_colonia in procesadas:
                continue
            
            col_norm = colonias_normalizadas[colonia]
            otra_norm = colonias_normalizadas[otra_colonia]
            
            sim = similitud(col_norm, otra_norm)
            
            if sim >= umbral_similitud and son_variantes_validas(
                colonia, otra_colonia, col_norm, otra_norm
            ):
                grupo.append(otra_colonia)
                procesadas.add(otra_colonia)
        
        grupos[colonia] = grupo
    
    return grupos


def main():
    """
    Función principal que procesa el archivo de incidentes procesados,
    extrae colonias únicas y genera archivos de salida.
    """
    # Rutas de entrada y salida (desde la raíz del proyecto)
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'data' / 'interim' / 'reportes_de_incidentes_procesados_2018_2025.csv'
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("EXTRACCION DE COLONIAS UNICAS - REPORTES 911")
    print("="*70)
    print(f"\nArchivo de entrada: {input_path}")
    
    if not input_path.exists():
        print(f"\nError: No se encuentra el archivo {input_path}")
        print("   Ejecuta primero el pipeline principal (indice_delictivo_hermosillo_main.py)")
        return
    
    print("\nCargando datos procesados...")
    df = pd.read_csv(input_path)
    
    print(f"Total de registros: {len(df):,}")
    
    # Convertir Timestamp si es necesario
    try:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        print(f"Periodo: {df['Timestamp'].min()} a {df['Timestamp'].max()}")
    except Exception:
        print("(Timestamp no disponible o en formato no estandar)")
    
    # Obtener colonias únicas (sin normalizar)
    colonias_originales = df['COLONIA'].dropna().unique()
    print(f"\nColonias unicas (sin procesar): {len(colonias_originales):,}")
    
    # Obtener frecuencia de cada colonia
    frecuencias = df['COLONIA'].value_counts()
    
    print("\nAgrupando colonias similares...")
    grupos_temp = agrupar_colonias_similares(colonias_originales, umbral_similitud=0.93)
    
    # Elegir la variante más frecuente como representativa de cada grupo
    grupos = {}
    for _, variantes in grupos_temp.items():
        variantes_con_freq = [(var, frecuencias.get(var, 0)) for var in variantes]
        variantes_con_freq.sort(key=lambda x: -x[1])
        representativa = variantes_con_freq[0][0]
        grupos[representativa] = variantes

    print(f"\nColonias unicas (despues de agrupar similares): {len(grupos):,}")

    # Crear lista de colonias únicas finales, filtrando por frecuencia mínima
    frecuencia_minima = 10
    colonias_unicas = [col for col in grupos.keys() if frecuencias.get(col, 0) >= frecuencia_minima]
    colonias_unicas = sorted(colonias_unicas)

    # Guardar resultados
    print("\nGuardando resultados...")

    # 1. Guardar lista simple de colonias únicas
    output_file_1 = output_dir / 'colonias_unicas_reportes_911.csv'
    df_colonias_unicas = pd.DataFrame({'COLONIA': colonias_unicas})
    df_colonias_unicas.to_csv(output_file_1, index=False)
    print(f"[OK] Guardado: {output_file_1}")
    
    # 2. Guardar reporte detallado con variantes
    reporte = []
    for colonia_repr, variantes in sorted(grupos.items()):
        if len(variantes) > 1:
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            reporte.append({
                'COLONIA_REPRESENTATIVA': colonia_repr,
                'NUM_VARIANTES': len(variantes),
                'VARIANTES': ' | '.join(sorted(variantes)),
                'FRECUENCIA_TOTAL': freq_total
            })
    
    if reporte:
        output_file_2 = output_dir / 'colonias_reportes_911_agrupadas_reporte.csv'
        df_reporte = pd.DataFrame(reporte)
        df_reporte = df_reporte.sort_values('FRECUENCIA_TOTAL', ascending=False)
        df_reporte.to_csv(output_file_2, index=False)
        print(f"[OK] Guardado: {output_file_2}")
        print(f"\nSe encontraron {len(reporte)} grupos con variantes ortograficas")
    
    # 3. Crear mapeo para normalización
    mapeo = {}
    for colonia_repr, variantes in grupos.items():
        for variante in variantes:
            mapeo[variante] = colonia_repr
    
    output_file_3 = output_dir / 'mapeo_colonias_reportes_911.csv'
    df_mapeo = pd.DataFrame([
        {'COLONIA_ORIGINAL': original, 'COLONIA_NORMALIZADA': normalizada}
        for original, normalizada in sorted(mapeo.items())
    ])
    df_mapeo.to_csv(output_file_3, index=False)
    print(f"[OK] Guardado: {output_file_3}")
    
    # Mostrar ejemplos
    print("\n" + "="*60)
    print("EJEMPLOS DE COLONIAS CON VARIANTES DETECTADAS:")
    print("="*60)
    
    ejemplos_mostrados = 0
    for colonia_repr, variantes in sorted(grupos.items(), key=lambda x: -len(x[1])):
        if len(variantes) > 1 and ejemplos_mostrados < 10:
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            print(f"\n'{colonia_repr}' ({freq_total:,} registros)")
            print(f"  Variantes encontradas:")
            for var in sorted(variantes):
                freq = frecuencias.get(var, 0)
                print(f"    - {var} ({freq:,})")
            ejemplos_mostrados += 1
    
    print("="*70)
    print("RESUMEN FINAL:")
    print("="*70)
    print(f"Colonias unicas finales: {len(colonias_unicas):,}")
    print(f"\nArchivos generados en {output_dir}/:")
    print(f"  - colonias_unicas_reportes_911.csv (lista simple)")
    print(f"  - mapeo_colonias_reportes_911.csv (mapeo original -> normalizada)")
    print(f"  - colonias_reportes_911_agrupadas_reporte.csv (reporte de variantes)")
    print("="*70)


if __name__ == "__main__":
    main()
