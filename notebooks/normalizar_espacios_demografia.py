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


def limpiar_colonia(texto: str) -> str:
    """Limpia una etiqueta de colonia SIN alterar su sentido.

    Acciones:
    - Convertir a str y recortar espacios al inicio/fin
    - Reemplazar espacios no separables (\u00A0) por espacios normales
    - Colapsar múltiples espacios a uno solo
    - Quitar comillas de borde y puntuación residual al inicio/fin
    - Mantener mayúsculas/minúsculas y acentos TAL CUAL (no se eliminan)
    """
    if pd.isna(texto):
        return ""

    s = str(texto)

    # Normaliza forma Unicode (no elimina acentos)
    s = unicodedata.normalize("NFC", s)

    # Reemplaza NBSP y otros espacios raros por espacio normal
    s = s.replace("\u00A0", " ")

    # Recorta y colapsa espacios
    s = s.strip()
    s = re.sub(r"\s+", " ", s)

    # Quita comillas de borde y puntuación suelta al inicio/fin
    s = s.strip("'\"“”‘’.;,|/\\- ")

    # Recolapsa por si quedaron dobles espacios tras recortes
    s = re.sub(r"\s+", " ", s)

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
    df['nom_col_limpio'] = df['nom_col'].apply(limpiar_colonia)
    
    # Contar cambios
    cambios = (df['nom_col'] != df['nom_col_limpio']).sum()
    print(f"✓ Registros con corrección aplicada: {cambios}")
    
    # Mostrar ejemplos de cambios
    if cambios > 0:
        print("\n📝 Ejemplos de correcciones:")
        ejemplos = df[df['nom_col'] != df['nom_col_limpio']][['nom_col', 'nom_col_limpio']].drop_duplicates()
        for _, row in ejemplos.head(10).iterrows():
            print(f"  '{row['nom_col']}' → '{row['nom_col_limpio']}'")
    
    # Reemplazar la columna original
    df['nom_col'] = df['nom_col_limpio']
    df = df.drop('nom_col_limpio', axis=1)
    
    # Contar colonias únicas después
    colonias_despues = df['nom_col'].nunique()
    print(f"\n📊 Colonias únicas (después de limpiar): {colonias_despues:,}")
    print(f"✓ Colonias consolidadas: {colonias_antes - colonias_despues}")
    
    # Guardar archivo limpio
    archivo_salida = project_root / 'data' / 'processed' / 'demografia_limpio.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"\n💾 Guardado: {archivo_salida}")
    
    # Guardar lista de colonias únicas
    colonias_unicas = sorted(df['nom_col'].unique())
    df_colonias = pd.DataFrame({'nom_col': colonias_unicas})
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
