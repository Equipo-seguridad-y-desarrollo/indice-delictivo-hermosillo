"""
Script para limpiar nombres de colonias en demografia_hermosillo.csv

Objetivo:
- SOLO corregir errores ortográficos obvios (espacios extra, espacios no separables,
    comillas/límites basura, caracteres invisibles)
- Mantener colonias diferentes como entidades separadas (NO fuzzy matching, NO
    eliminación de palabras como 'EL', 'LA', ni sufijos como 'INDECO')
- Deduplicar solo por coincidencia EXACTA tras la limpieza (e.g., "Col  X" == "Col X")

Ejemplos que deben permanecer distintos:
- "EL SAHUARO" ≠ "SAHUARO" ≠ "SAHUARO INDECO"
"""

import pandas as pd
import unicodedata
import re
from typing import Dict


def reparar_mojibake(s: str) -> str:
    """Intenta reparar texto con mojibake típico (UTF-8 leído como Latin-1).

    Si el round-trip latin1->utf-8 falla, retorna el original.
    """
    if not s:
        return s
    try:
        return s.encode('latin1').decode('utf-8')
    except Exception:
        return s


def limpiar_colonia(texto: str, alias_map: Dict[str, str]) -> str:
    """Limpia etiqueta de colonia y aplica alias controlados para homogeneizar joins.

    Pasos:
    1. Normalización unicode NFC.
    2. Reparar mojibake simple.
    3. Espacios (NBSP -> espacio, colapso, trim, retirar puntuación periférica).
    4. Aplicar alias EXACTOS (en mayúsculas) definidos en alias_map.
    5. NO eliminar stopwords (EL, LA, DE, etc.).
    """
    if pd.isna(texto):
        return ""
    s = str(texto)
    s = unicodedata.normalize("NFC", s)
    s = reparar_mojibake(s)
    s = s.replace("\u00A0", " ")
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip("'\"“”‘’.;,|/\\- ")
    s = re.sub(r"\s+", " ", s)
    # Alias: trabajamos en mayúsculas para la clave, pero retornamos en la forma destino del alias
    upper = s.upper()
    if upper in alias_map:
        return alias_map[upper]
    return s


def main():
    print("="*70)
    print("LIMPIEZA DE COLONIAS - DEMOGRAFÍA HERMOSILLO")
    print("="*70)
    
    # Leer datos (usar pathlib para rutas relativas correctas)
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    archivo = project_root / 'data' / 'raw' / 'demografia_hermosillo.csv'
    print(f"\n📂 Leyendo datos desde: {archivo}")
    df = pd.read_csv(archivo)
    
    print(f"✓ Total de registros: {len(df):,}")
    
    # Contar colonias únicas antes
    colonias_antes = df['nom_col'].nunique()
    print(f"\n📊 Colonias únicas (antes de limpiar): {colonias_antes:,}")
    
    # Aplicar limpieza ortográfica mínima (sin agrupar nombres distintos)
    print("\n🔧 Limpiando etiquetas (espacios, NBSP, bordes/puntuación)...")
    # Construir alias controlados únicamente para casos detectados que impiden join.
    # Mantenerlos mínimos y documentados.
    alias_map = {
        # Correcciones de truncación / falta de tilde / letras perdidas
        'AMPLIACIN 4 DE MARZO': 'AMPLIACION 4 DE MARZO',
        'ARGANGEL RESIDENCIAL': 'ARCANGEL RESIDENCIAL',
        'BUROCRATA MUNICIPAL': 'BURÓCRATA MUNICIPAL',  # si en polígono aparece con acento
        'CASA ALTA RDCIAL': 'CASA ALTA RESIDENCIAL',
        'CARDENO RESIDENCIAL': 'CARDENO RESIDENCIAL',  # placeholder (permite consistencia si ya existe así en polígonos)
        'CARDENO ENTORNO': 'CARDENO ENTORNO',  # sin cambio aún; revisar si existe homónimo
        'CAÑAÑA DE LOS NEGROS': 'CAÑADA DE LOS NEGROS',  # mojibake doble
        'LA CORUÑA SECCION PRIVADA ORZAN': 'LA CORUÑA SECCION PRIVADA ORZAN',
        'LA CORUÑA SECCION  PRIVADA ALMAR': 'LA CORUÑA SECCION PRIVADA ALMAR',
        'LAS LOMAS SECC CASTAÑOS': 'LAS LOMAS SECCION CASTAÑOS',
        'LAS PLASITAS PRIMERAS': 'LAS PLAZITAS PRIMERAS',
        'NUEVA ESPAÑA': 'NUEVA ESPAÑA',  # identidad
        'PARAISO PITIC': 'PARAISO PITIC',
        # Casos de mojibake comunes sin alias específico se corrigen en reparar_mojibake
    }

    df['nom_col_norm'] = df['nom_col'].apply(lambda x: limpiar_colonia(x, alias_map))
    
    # Contar cambios
    cambios = (df['nom_col'] != df['nom_col_norm']).sum()
    print(f"✓ Registros con corrección aplicada: {cambios}")
    
    # Mostrar ejemplos de cambios
    if cambios > 0:
        print("\n📝 Ejemplos de correcciones:")
        ejemplos = df[df['nom_col'] != df['nom_col_norm']][['nom_col', 'nom_col_norm']].drop_duplicates()
        for _, row in ejemplos.head(10).iterrows():
            print(f"  '{row['nom_col']}' → '{row['nom_col_norm']}'")
    
    # Mantener ambas columnas: nom_col (original) y nom_col_norm (normalizada)
    # Esto evita romper joins existentes basados en el nombre original y permite usar la normalizada como fallback.
    
    # Contar colonias únicas después
    colonias_despues = df['nom_col_norm'].nunique()
    print(f"\n📊 Colonias únicas (después de limpiar): {colonias_despues:,}")
    print(f"✓ Colonias consolidadas: {colonias_antes - colonias_despues}")
    
    # Guardar archivo limpio
    archivo_salida = project_root / 'data' / 'processed' / 'demografia_limpio.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"\n💾 Guardado: {archivo_salida}")
    
    # Guardar lista de colonias únicas
    colonias_unicas = sorted(df['nom_col_norm'].unique())
    df_colonias = pd.DataFrame({'nom_col_norm': colonias_unicas})
    archivo_colonias = project_root / 'data' / 'processed' / 'colonias_unicas_demografia.csv'
    df_colonias.to_csv(archivo_colonias, index=False, encoding='utf-8-sig')
    print(f"💾 Guardado: {archivo_colonias}")
    
    print("\n" + "="*70)
    print("RESUMEN:")
    print("="*70)
    print(f"Total de registros: {len(df):,}")
    print(f"Colonias únicas: {colonias_despues:,}")
    print(f"Correcciones aplicadas: Espacios/NBSP, recortes de borde y puntuación")
    print("="*70)


if __name__ == "__main__":
    main()
