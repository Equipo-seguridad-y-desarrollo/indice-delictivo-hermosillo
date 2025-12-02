import sqlite3

conn = sqlite3.connect('c:/Users/marce/Documents/Ciencia de datos/indice-delictivo-hermosillo/backend/delitos_hermosillo.db')
c = conn.cursor()

# Ver formato de cve_col en incidentes
c.execute('SELECT DISTINCT cve_col FROM incidentes LIMIT 5')
print('CVE_COL en incidentes:')
for r in c.fetchall(): 
    print(f'  [{r[0]}]')

# Ver formato de cve_col en polígonos
c.execute('SELECT cve_col FROM poligonos LIMIT 5')
print('\nCVE_COL en poligonos:')
for r in c.fetchall(): 
    print(f'  [{r[0]}]')

# Ver si hay match
c.execute('''
    SELECT COUNT(*) FROM incidentes i 
    JOIN poligonos p ON i.cve_col = p.cve_col
''')
print(f'\nMatches entre tablas: {c.fetchone()[0]}')

# Buscar BALDERRAMA específicamente
c.execute("SELECT cve_col FROM poligonos WHERE colonia LIKE '%BALDERRAMA%'")
result = c.fetchone()
if result:
    cve_balderrama = result[0]
    print(f'\nBALDERRAMA cve_col en poligonos: [{cve_balderrama}]')
    
    c.execute("SELECT COUNT(*) FROM incidentes WHERE cve_col = ?", (cve_balderrama,))
    print(f'Incidentes con ese cve_col exacto: {c.fetchone()[0]}')
    
    c.execute("SELECT COUNT(*) FROM incidentes WHERE cve_col LIKE ?", (f'%{cve_balderrama[-6:]}%',))
    print(f'Incidentes con cve_col similar: {c.fetchone()[0]}')
