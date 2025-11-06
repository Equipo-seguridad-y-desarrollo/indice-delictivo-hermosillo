"""
Script para limpiar nombres de colonias en demografia_hermosillo.csv
Solo corrige errores ortográficos obvios (espacios dobles, acentos, etc.)
Mantiene colonias diferentes como entidades separadas
"""

import pandas as pd
import unicodedata


def normalizar_espacios(texto):
    """Normaliza espacios múltiples a uno solo"""
    if pd.isna(texto):
        return texto
    return ' '.join(str(texto).split())


def main():
    print("="*70)
    print("LIMPIEZA DE COLONIAS - DEMOGRAFÍA HERMOSILLO")
    print("="*70)
    
    # Leer datos
    archivo = '../data/raw/demografia_hermosillo.csv'
    print(f"\n📂 Leyendo datos desde: {archivo}")
    df = pd.read_csv(archivo)
    
    print(f"✓ Total de registros: {len(df):,}")
    
    # Contar colonias únicas antes
    colonias_antes = df['nom_col'].nunique()
    print(f"\n📊 Colonias únicas (antes de limpiar): {colonias_antes:,}")
    
    # Aplicar normalización de espacios
    print("\n🔧 Normalizando espacios...")
    df['nom_col_limpio'] = df['nom_col'].apply(normalizar_espacios)
    
    # Contar cambios
    cambios = (df['nom_col'] != df['nom_col_limpio']).sum()
    print(f"✓ Registros con espacios corregidos: {cambios}")
    
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
    archivo_salida = '../data/processed/demografia_limpio.csv'
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"\n💾 Guardado: {archivo_salida}")
    
    # Guardar lista de colonias únicas
    colonias_unicas = sorted(df['nom_col'].unique())
    df_colonias = pd.DataFrame({'nom_col': colonias_unicas})
    df_colonias.to_csv('../data/processed/colonias_unicas_demografia.csv',
                       index=False, encoding='utf-8-sig')
    print(f"💾 Guardado: ../data/processed/colonias_unicas_demografia.csv")
    
    print("\n" + "="*70)
    print("RESUMEN:")
    print("="*70)
    print(f"Total de registros: {len(df):,}")
    print(f"Colonias únicas: {colonias_despues:,}")
    print(f"Correcciones aplicadas: Normalización de espacios")
    print("="*70)


if __name__ == "__main__":
    main()
