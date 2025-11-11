import pandas as pd

unicas = pd.read_csv('data/processed/colonias_unicas_reportes_911.csv')
coords = pd.read_csv('data/processed/colonias_reportes_911_con_coordenadas.csv')

faltantes = set(unicas['COLONIA']) - set(coords['COLONIA'])

print(f'Colonias únicas: {len(unicas)}')
print(f'Ya geocodificadas: {len(coords)}')
print(f'Faltantes por geocodificar: {len(faltantes)}')

print(f'\nPrimeras 30 colonias faltantes:')
for i, col in enumerate(sorted(faltantes)[:30]):
    print(f'  {i+1}. {col}')
