"""
Script para analizar colonias en demografia_hermosillo.csv
Detecta y agrupa colonias con errores ortográficos similares
"""

import pandas as pd
from difflib import SequenceMatcher
import unicodedata
import re


def normalizar_texto(texto):
    """Normaliza el texto removiendo acentos, convirtiendo a mayúsculas"""
    if pd.isna(texto):
        return ""
    
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
    """Calcula la similitud entre dos textos"""
    return SequenceMatcher(None, texto1, texto2).ratio()


def son_variantes_validas(texto1, texto2, texto1_norm, texto2_norm):
    """Verifica si dos colonias son realmente variantes ortográficas válidas"""
    
    # Regla 1: Si solo difieren en acentos/mayúsculas, son variantes válidas
    if texto1_norm == texto2_norm:
        return True
    
    # Regla 2: Detectar nombres de santos diferentes (cerradas Villa Verde)
    # Ejemplo: "SAN JOEL" vs "SAN NOE" son diferentes
    patron_santo = r'\bSAN\s+\w+|\bSANTA\s+\w+|\bSANTO\s+\w+'
    santos1 = re.findall(patron_santo, texto1.upper())
    santos2 = re.findall(patron_santo, texto2.upper())
    
    if santos1 and santos2 and santos1 != santos2:
        return False
    
    # Regla 3: Si tienen palabras diferentes al inicio (nombres propios)
    # Ejemplo: "ALTARIA" vs "ANTARA", "SEDONA" vs "SIENA"
    palabras1 = texto1_norm.split()
    palabras2 = texto2_norm.split()
    
    if palabras1 and palabras2:
        # Si la primera palabra es completamente diferente, no agrupar
        # (a menos que sean artículos/preposiciones)
        articulos = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL'}
        primera1 = palabras1[0] if palabras1[0] not in articulos else (palabras1[1] if len(palabras1) > 1 else palabras1[0])
        primera2 = palabras2[0] if palabras2[0] not in articulos else (palabras2[1] if len(palabras2) > 1 else palabras2[0])
        
        # Si las primeras palabras principales son diferentes, no agrupar
        if primera1 != primera2 and similitud(primera1, primera2) < 0.9:
            return False
    
    return True


def agrupar_colonias_similares(colonias_con_freq, umbral_similitud=0.90):
    """
    Agrupa colonias similares considerando su frecuencia
    
    Args:
        colonias_con_freq: Dict {colonia: frecuencia}
        umbral_similitud: Umbral de similitud (default: 0.90)
    
    Returns:
        dict: Diccionario con colonias agrupadas
    """
    colonias = list(colonias_con_freq.keys())
    colonias_normalizadas = {col: normalizar_texto(col) for col in colonias}
    
    # Ordenar por longitud (más cortas primero)
    colonias_ordenadas = sorted(colonias, key=lambda x: len(x))
    
    grupos_temp = {}
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
        
        grupos_temp[colonia] = grupo
    
    # Elegir la variante más frecuente como representativa
    grupos = {}
    for _, variantes in grupos_temp.items():
        # Ordenar por frecuencia (mayor primero)
        variantes_con_freq = [(var, colonias_con_freq.get(var, 0)) for var in variantes]
        variantes_con_freq.sort(key=lambda x: -x[1])
        representativa = variantes_con_freq[0][0]
        grupos[representativa] = variantes
    
    return grupos


def main():
    print("="*70)
    print("ANÁLISIS DE COLONIAS - DEMOGRAFÍA HERMOSILLO")
    print("="*70)
    
    # Leer datos
    archivo = '../data/raw/demografia_hermosillo.csv'
    print(f"\n📂 Leyendo datos desde: {archivo}")
    df = pd.read_csv(archivo)
    
    print(f"✓ Total de registros: {len(df):,}")
    
    # Obtener colonias únicas
    colonias_originales = df['nom_col'].dropna().unique()
    print(f"\n📊 Colonias únicas (sin procesar): {len(colonias_originales):,}")
    
    # Obtener frecuencia (conteo de registros por colonia)
    frecuencias = df['nom_col'].value_counts().to_dict()
    
    # Agrupar colonias similares
    print("\n🔍 Agrupando colonias similares...")
    grupos = agrupar_colonias_similares(frecuencias, umbral_similitud=0.90)
    
    print(f"\n✓ Colonias únicas (después de agrupar): {len(grupos):,}")
    
    # Identificar grupos con variantes
    grupos_con_variantes = {k: v for k, v in grupos.items() if len(v) > 1}
    print(f"✓ Grupos con variantes detectadas: {len(grupos_con_variantes):,}")
    
    # Crear DataFrame con resultados
    colonias_unicas = sorted(grupos.keys())
    df_colonias_unicas = pd.DataFrame({'nom_col': colonias_unicas})
    df_colonias_unicas.to_csv('../data/processed/colonias_unicas_demografia.csv', 
                               index=False, encoding='utf-8-sig')
    print(f"\n💾 Guardado: ../data/processed/colonias_unicas_demografia.csv")
    
    # Crear reporte de variantes
    if grupos_con_variantes:
        reporte = []
        for colonia_repr, variantes in sorted(grupos_con_variantes.items(),
                                              key=lambda x: -len(x[1])):
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            reporte.append({
                'COLONIA_REPRESENTATIVA': colonia_repr,
                'NUM_VARIANTES': len(variantes),
                'VARIANTES': ' | '.join(sorted(variantes)),
                'REGISTROS_TOTAL': freq_total
            })
        
        df_reporte = pd.DataFrame(reporte)
        df_reporte = df_reporte.sort_values('REGISTROS_TOTAL', ascending=False)
        df_reporte.to_csv('../data/processed/demografia_agrupadas_reporte.csv',
                         index=False, encoding='utf-8-sig')
        print(f"💾 Guardado: ../data/processed/demografia_agrupadas_reporte.csv")
    
    # Crear mapeo
    mapeo = {}
    for colonia_repr, variantes in grupos.items():
        for variante in variantes:
            mapeo[variante] = colonia_repr
    
    df_mapeo = pd.DataFrame([
        {'COLONIA_ORIGINAL': original, 'COLONIA_NORMALIZADA': normalizada}
        for original, normalizada in sorted(mapeo.items())
    ])
    df_mapeo.to_csv('../data/processed/mapeo_colonias_demografia.csv',
                   index=False, encoding='utf-8-sig')
    print(f"💾 Guardado: ../data/processed/mapeo_colonias_demografia.csv")
    
    # Mostrar ejemplos
    if grupos_con_variantes:
        print("\n" + "="*70)
        print("EJEMPLOS DE VARIANTES DETECTADAS:")
        print("="*70)
        
        ejemplos = list(grupos_con_variantes.items())[:15]
        for colonia_repr, variantes in ejemplos:
            freq_total = sum(frecuencias.get(var, 0) for var in variantes)
            print(f"\n'{colonia_repr}' ({freq_total} registros)")
            print(f"  Variantes encontradas:")
            for var in sorted(variantes):
                freq = frecuencias.get(var, 0)
                print(f"    - {var} ({freq})")
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN:")
    print("="*70)
    print(f"Colonias únicas finales: {len(grupos):,}")
    print(f"Grupos con variantes: {len(grupos_con_variantes):,}")
    print(f"Archivos generados en ../data/processed/:")
    print(f"  - colonias_unicas_demografia.csv")
    print(f"  - mapeo_colonias_demografia.csv")
    if grupos_con_variantes:
        print(f"  - demografia_agrupadas_reporte.csv")
    print("="*70)


if __name__ == "__main__":
    main()
