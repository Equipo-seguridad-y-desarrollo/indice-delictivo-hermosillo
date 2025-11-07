"""
Script para extraer colonias únicas del archivo 213.csv
Detecta y agrupa colonias con errores ortográficos usando fuzzy matching
"""

import pandas as pd
from difflib import SequenceMatcher
import unicodedata
from collections import defaultdict


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
    # Ejemplo: "PUERTA REAL VI" vs "PUERTA REAL VIII" son diferentes
    # Números romanos comunes: I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, etc.
    nums_romanos1 = re.findall(r'\b([IVX]+)\s*$', texto1.upper())
    nums_romanos2 = re.findall(r'\b([IVX]+)\s*$', texto2.upper())
    
    # Si ambas tienen números romanos diferentes, son colonias diferentes
    if nums_romanos1 and nums_romanos2 and nums_romanos1 != nums_romanos2:
        return False
    
    # Si solo una tiene número romano, son diferentes
    if bool(nums_romanos1) != bool(nums_romanos2):
        return False
    
    # Regla 2b: Detectar números arábigos al final del nombre (indican colonias diferentes)
    # Ejemplo: "LAS PEREDAS" vs "LAS PEREDAS 2" son diferentes
    nums_final1 = re.findall(r'\s+(\d+)\s*$', texto1.upper())
    nums_final2 = re.findall(r'\s+(\d+)\s*$', texto2.upper())
    
    # Si ambas tienen números finales diferentes, son colonias diferentes
    if nums_final1 and nums_final2 and nums_final1 != nums_final2:
        return False
    
    # Si solo una tiene número final, son diferentes
    if bool(nums_final1) != bool(nums_final2):
        return False
    
    # Regla 3: Detectar sectores/etapas diferentes (NO agrupar)
    palabras_sector = ['SECTOR', 'ETAPA', 'SECCION', 'SECC.', 'SECC']
    tiene_sector1 = any(p in texto1.upper() for p in palabras_sector)
    tiene_sector2 = any(p in texto2.upper() for p in palabras_sector)
    
    if tiene_sector1 or tiene_sector2:
        # Extraer números/letras de sector
        nums1 = set(re.findall(r'(?:SECTOR|ETAPA|SECCION|SECC\.?)\s*([A-Z0-9]+)', texto1.upper()))
        nums2 = set(re.findall(r'(?:SECTOR|ETAPA|SECCION|SECC\.?)\s*([A-Z0-9]+)', texto2.upper()))
        
        # Si tienen diferentes sectores/etapas, NO agrupar
        if nums1 and nums2 and nums1 != nums2:
            return False
    
    # Regla 4: Detectar nombres completamente diferentes
    # Extraer palabras principales (ignorar artículos, preposiciones, etc.)
    stop_words = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL'}
    
    palabras1 = set(texto1_norm.split()) - stop_words
    palabras2 = set(texto2_norm.split()) - stop_words
    
    # Si no comparten ninguna palabra principal, probablemente son diferentes
    if palabras1 and palabras2 and not palabras1.intersection(palabras2):
        return False
    
    # Regla 5: Detectar palabras clave que indican colonias diferentes
    # (ej: PINO vs ENCINO, PALMA vs SAUCE, etc.)
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
    
    # Si ambas tienen palabras distintivas diferentes, son colonias diferentes
    if palabras_dist1 and palabras_dist2 and palabras_dist1 != palabras_dist2:
        return False
    
    return True


def agrupar_colonias_similares(colonias, umbral_similitud=0.90):
    """
    Agrupa colonias que son muy similares (posibles errores ortográficos)
    
    Args:
        colonias: Lista de colonias únicas
        umbral_similitud: Valor de 0 a 1 que determina qué tan similares 
                         deben ser para agruparse (default: 0.90 - más estricto)
    
    Returns:
        dict: Diccionario donde la clave es la colonia representativa
              y el valor es una lista de variantes encontradas
    """
    colonias_normalizadas = {col: normalizar_texto(col) for col in colonias}
    
    # Ordenar por longitud (más cortas primero, suelen ser las correctas)
    colonias_ordenadas = sorted(colonias, key=lambda x: len(x))
    
    grupos = {}
    procesadas = set()
    
    for colonia in colonias_ordenadas:
        if colonia in procesadas:
            continue
        
        # Inicializar grupo con la colonia actual
        grupo = [colonia]
        procesadas.add(colonia)
        
        # Buscar colonias similares
        for otra_colonia in colonias:
            if otra_colonia in procesadas:
                continue
            
            col_norm = colonias_normalizadas[colonia]
            otra_norm = colonias_normalizadas[otra_colonia]
            
            # Calcular similitud
            sim = similitud(col_norm, otra_norm)
            
            # Verificar si son variantes válidas
            if sim >= umbral_similitud and son_variantes_validas(
                colonia, otra_colonia, col_norm, otra_norm
            ):
                grupo.append(otra_colonia)
                procesadas.add(otra_colonia)
        
        # Almacenar el grupo (usaremos la variante más frecuente después)
        grupos[colonia] = grupo
    
    return grupos


def main():
    # Ruta del archivo
    ruta_archivo = '../data/raw/213.csv'
    
    print("Cargando datos...")
    df = pd.read_csv(ruta_archivo)
    
    print(f"Total de registros: {len(df):,}")
    
    # Obtener colonias únicas (sin normalizar)
    colonias_originales = df['COLONIA'].dropna().unique()
    print(f"\nColonias únicas (sin procesar): {len(colonias_originales):,}")
    
    # Obtener frecuencia de cada colonia
    frecuencias = df['COLONIA'].value_counts()
    
    print("\nAgrupando colonias similares...")
    grupos_temp = agrupar_colonias_similares(colonias_originales, umbral_similitud=0.90)
    
    # Elegir la variante más frecuente como representativa de cada grupo
    grupos = {}
    for _, variantes in grupos_temp.items():
        # Calcular frecuencia de cada variante
        variantes_con_freq = [(var, frecuencias.get(var, 0)) for var in variantes]
        # Ordenar por frecuencia (mayor primero)
        variantes_con_freq.sort(key=lambda x: -x[1])
        # La más frecuente es la representativa
        representativa = variantes_con_freq[0][0]
        grupos[representativa] = variantes
    
    print(f"\nColonias únicas (después de agrupar similares): {len(grupos):,}")
    
    # Crear lista de colonias únicas finales
    colonias_unicas = sorted(grupos.keys())
    
    # Guardar resultados
    print("\nGuardando resultados...")
    
    # 1. Guardar lista simple de colonias únicas
    df_colonias_unicas = pd.DataFrame({'COLONIA': colonias_unicas})
    df_colonias_unicas.to_csv('../data/processed/colonias_unicas_reportes_911.csv', index=False)
    print(f"✓ Guardado: ../data/processed/colonias_unicas_reportes_911.csv")
    
    # 2. Guardar reporte detallado con variantes
    reporte = []
    for colonia_repr, variantes in sorted(grupos.items()):
        if len(variantes) > 1:
            # Calcular frecuencia total del grupo
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            reporte.append({
                'COLONIA_REPRESENTATIVA': colonia_repr,
                'NUM_VARIANTES': len(variantes),
                'VARIANTES': ' | '.join(sorted(variantes)),
                'FRECUENCIA_TOTAL': freq_total
            })
    
    if reporte:
        df_reporte = pd.DataFrame(reporte)
        df_reporte = df_reporte.sort_values('FRECUENCIA_TOTAL', ascending=False)
        df_reporte.to_csv('../data/processed/colonias_reportes_911_agrupadas_reporte.csv', index=False)
        print(f"✓ Guardado: ../data/processed/colonias_reportes_911_agrupadas_reporte.csv")
        print(f"\nSe encontraron {len(reporte)} grupos con variantes ortográficas")
    
    # 3. Crear mapeo para normalización
    mapeo = {}
    for colonia_repr, variantes in grupos.items():
        for variante in variantes:
            mapeo[variante] = colonia_repr
    
    df_mapeo = pd.DataFrame([
        {'COLONIA_ORIGINAL': original, 'COLONIA_NORMALIZADA': normalizada}
        for original, normalizada in sorted(mapeo.items())
    ])
    df_mapeo.to_csv('../data/processed/mapeo_colonias_reportes_911.csv', index=False)
    print(f"✓ Guardado: ../data/processed/mapeo_colonias_reportes_911.csv")
    
    # Mostrar ejemplos
    print("\n" + "="*60)
    print("EJEMPLOS DE COLONIAS CON VARIANTES DETECTADAS:")
    print("="*60)
    
    ejemplos_mostrados = 0
    for colonia_repr, variantes in sorted(grupos.items(), 
                                         key=lambda x: -len(x[1])):
        if len(variantes) > 1 and ejemplos_mostrados < 10:
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            print(f"\n'{colonia_repr}' ({freq_total:,} registros)")
            print(f"  Variantes encontradas:")
            for var in sorted(variantes):
                freq = frecuencias.get(var, 0)
                print(f"    - {var} ({freq:,})")
            ejemplos_mostrados += 1
    
    print("="*70)
    print("RESUMEN:")
    print("="*70)
    print(f"Colonias únicas finales: {len(colonias_unicas):,}")
    print(f"Archivos generados en ../data/processed/:")
    print(f"  - colonias_unicas_reportes_911.csv (lista simple)")
    print(f"  - mapeo_colonias_reportes_911.csv (mapeo original → normalizada)")
    print(f"  - colonias_reportes_911_agrupadas_reporte.csv (reporte de variantes)")


if __name__ == "__main__":
    main()
