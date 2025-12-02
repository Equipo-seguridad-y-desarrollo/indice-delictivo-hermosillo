"""
Base de datos SQLite para el Índice Delictivo de Hermosillo
Carga los datos desde CSV y crea las tablas necesarias
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'processed' / 'unificado'
DB_PATH = PROJECT_ROOT / 'backend' / 'delitos_hermosillo.db'


def crear_conexion():
    """Crear conexión a la base de datos SQLite"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
    return conn


def inicializar_base_datos():
    """Crear las tablas e índices en la base de datos"""
    
    conn = crear_conexion()
    cursor = conn.cursor()
    
    # Tabla de incidentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cve_col TEXT,
            colonia TEXT,
            tipo_incidente TEXT,
            timestamp DATETIME,
            año INTEGER,
            mes INTEGER,
            trimestre INTEGER,
            parte_del_dia TEXT,
            dia_semana TEXT,
            categoria TEXT,
            severidad TEXT,
            latitud REAL,
            longitud REAL
        )
    ''')
    
    # Tabla de polígonos/colonias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poligonos (
            cve_col TEXT PRIMARY KEY,
            colonia TEXT,
            cp TEXT,
            total_incidentes INTEGER,
            incidentes_alta INTEGER,
            incidentes_media INTEGER,
            incidentes_baja INTEGER,
            poblacion_total REAL,
            viviendas_totales REAL,
            escolaridad_años_prom REAL,
            pctj_menores18 TEXT,
            pctj_hombres TEXT,
            pctj_mujeres TEXT,
            tasa_incidentes_per_1k REAL,
            tasa_alta_severidad_per_1k REAL,
            score_severidad REAL,
            area_km2 REAL,
            densidad_poblacional REAL,
            categorias_json TEXT,
            geometry_json TEXT
        )
    ''')
    
    # Índices para consultas rápidas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_año ON incidentes(año)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_trimestre ON incidentes(trimestre)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_categoria ON incidentes(categoria)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_severidad ON incidentes(severidad)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_cve_col ON incidentes(cve_col)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidentes_timestamp ON incidentes(timestamp)')
    
    conn.commit()
    conn.close()
    
    print("✓ Base de datos inicializada")


def cargar_incidentes():
    """Cargar incidentes desde CSV a SQLite"""
    
    print("Cargando incidentes desde CSV...")
    
    csv_path = DATA_DIR / 'incidentes_con_poligono_temporal.csv'
    
    # Leer CSV en chunks para archivos grandes
    chunks = pd.read_csv(csv_path, chunksize=50000)
    
    conn = crear_conexion()
    
    total_registros = 0
    
    for i, chunk in enumerate(chunks):
        # Procesar chunk
        chunk['timestamp'] = pd.to_datetime(chunk['Timestamp'])
        chunk['año'] = chunk['timestamp'].dt.year
        chunk['mes'] = chunk['timestamp'].dt.month
        chunk['trimestre'] = chunk['timestamp'].dt.quarter
        
        # Preparar datos para inserción
        datos = []
        for _, row in chunk.iterrows():
            datos.append((
                str(row['CVE_COL']) if pd.notna(row['CVE_COL']) else None,
                row['COLONIA_POLIGONO'] if pd.notna(row.get('COLONIA_POLIGONO')) else None,
                row['TIPO DE INCIDENTE'] if pd.notna(row.get('TIPO DE INCIDENTE')) else None,
                str(row['timestamp']),
                int(row['año']),
                int(row['mes']),
                int(row['trimestre']),
                row['ParteDelDia'] if pd.notna(row.get('ParteDelDia')) else None,
                row['DiaDeLaSemana'] if pd.notna(row.get('DiaDeLaSemana')) else None,
                row['Categoria_Incidente'] if pd.notna(row.get('Categoria_Incidente')) else None,
                row['Nivel_Severidad'] if pd.notna(row.get('Nivel_Severidad')) else None,
                float(row['LATITUD']) if pd.notna(row.get('LATITUD')) else None,
                float(row['LONGITUD']) if pd.notna(row.get('LONGITUD')) else None
            ))
        
        # Insertar en batch
        conn.executemany('''
            INSERT INTO incidentes 
            (cve_col, colonia, tipo_incidente, timestamp, año, mes, trimestre, 
             parte_del_dia, dia_semana, categoria, severidad, latitud, longitud)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos)
        
        conn.commit()
        total_registros += len(datos)
        print(f"  Chunk {i+1}: {len(datos):,} registros (Total: {total_registros:,})")
    
    conn.close()
    print(f"✓ {total_registros:,} incidentes cargados")


def cargar_poligonos():
    """Cargar polígonos desde CSV y GeoJSON a SQLite"""
    
    print("Cargando polígonos...")
    
    import geopandas as gpd
    
    csv_path = DATA_DIR / 'poligonos_unificados_completo.csv'
    geojson_path = DATA_DIR / 'poligonos_unificados_completo.geojson'
    
    # Leer CSV
    df = pd.read_csv(csv_path)
    
    # Leer GeoJSON para geometrías
    gdf = gpd.read_file(geojson_path)
    
    conn = crear_conexion()
    
    for _, row in df.iterrows():
        cve_col = str(row['CVE_COL'])
        
        # Buscar geometría correspondiente
        geom_json = None
        geom_row = gdf[gdf['CVE_COL'].astype(str) == cve_col]
        if len(geom_row) > 0:
            geom_json = json.dumps(geom_row.iloc[0]['geometry'].__geo_interface__)
        
        conn.execute('''
            INSERT OR REPLACE INTO poligonos 
            (cve_col, colonia, cp, total_incidentes, incidentes_alta, incidentes_media,
             incidentes_baja, poblacion_total, viviendas_totales, escolaridad_años_prom,
             pctj_menores18, pctj_hombres, pctj_mujeres, tasa_incidentes_per_1k,
             tasa_alta_severidad_per_1k, score_severidad, area_km2, densidad_poblacional,
             categorias_json, geometry_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cve_col,
            row['COLONIA'] if pd.notna(row.get('COLONIA')) else None,
            str(row['CP']) if pd.notna(row.get('CP')) else None,
            int(row['total_incidentes']) if pd.notna(row.get('total_incidentes')) else 0,
            int(row['incidentes_alta']) if pd.notna(row.get('incidentes_alta')) else 0,
            int(row['incidentes_media']) if pd.notna(row.get('incidentes_media')) else 0,
            int(row['incidentes_baja']) if pd.notna(row.get('incidentes_baja')) else 0,
            float(row['poblacion_total']) if pd.notna(row.get('poblacion_total')) else None,
            float(row['viviendas_totales']) if pd.notna(row.get('viviendas_totales')) else None,
            float(row['escolaridad_años_prom']) if pd.notna(row.get('escolaridad_años_prom')) else None,
            str(row['pctj_menores18']) if pd.notna(row.get('pctj_menores18')) else None,
            str(row['pctj_hombres']) if pd.notna(row.get('pctj_hombres')) else None,
            str(row['pctj_mujeres']) if pd.notna(row.get('pctj_mujeres')) else None,
            float(row['tasa_incidentes_per_1k']) if pd.notna(row.get('tasa_incidentes_per_1k')) else None,
            float(row['tasa_alta_severidad_per_1k']) if pd.notna(row.get('tasa_alta_severidad_per_1k')) else None,
            float(row['score_severidad']) if pd.notna(row.get('score_severidad')) else None,
            float(row['area_km2']) if pd.notna(row.get('area_km2')) else None,
            float(row['densidad_poblacional']) if pd.notna(row.get('densidad_poblacional')) else None,
            row['categorias_dict'] if pd.notna(row.get('categorias_dict')) else None,
            geom_json
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✓ {len(df):,} polígonos cargados")


def setup_completo():
    """Configuración completa de la base de datos"""
    
    print("="*60)
    print("CONFIGURANDO BASE DE DATOS - ÍNDICE DELICTIVO HERMOSILLO")
    print("="*60)
    
    # Crear directorio si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Si existe la BD, eliminarla para empezar fresco
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("✓ Base de datos anterior eliminada")
    
    # Inicializar
    inicializar_base_datos()
    
    # Cargar datos
    cargar_incidentes()
    cargar_poligonos()
    
    # Verificar
    conn = crear_conexion()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM incidentes")
    n_incidentes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM poligonos")
    n_poligonos = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ BASE DE DATOS LISTA")
    print("="*60)
    print(f"📂 Archivo: {DB_PATH}")
    print(f"📊 Incidentes: {n_incidentes:,}")
    print(f"🗺️  Polígonos: {n_poligonos:,}")
    print("="*60)


if __name__ == "__main__":
    setup_completo()
