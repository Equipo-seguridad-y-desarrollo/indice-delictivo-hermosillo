"""
Consultas SQL útiles para el Índice Delictivo de Hermosillo
Módulo con funciones de consulta reutilizables
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any

DB_PATH = Path(__file__).parent / 'delitos_hermosillo.db'


def get_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# CONSULTAS DE INCIDENTES
# =============================================================================

def total_incidentes_por_periodo(
    año: Optional[int] = None,
    trimestre: Optional[int] = None,
    mes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtener total de incidentes por período
    
    SELECT COUNT(*), 
           SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta,
           SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media,
           SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja
    FROM incidentes
    WHERE año = ? AND trimestre = ? AND mes = ?
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if trimestre:
        conditions.append("trimestre = ?")
        params.append(trimestre)
    if mes:
        conditions.append("mes = ?")
        params.append(mes)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    cursor.execute(f'''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta,
            SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media,
            SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja
        FROM incidentes
        WHERE {where}
    ''', params)
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)


def incidentes_por_categoria(
    año: Optional[int] = None,
    limite: int = 10
) -> List[Dict]:
    """
    Top categorías de incidentes
    
    SELECT categoria, COUNT(*) as total
    FROM incidentes
    WHERE año = ?
    GROUP BY categoria
    ORDER BY total DESC
    LIMIT ?
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if año:
        cursor.execute('''
            SELECT categoria, COUNT(*) as total
            FROM incidentes
            WHERE año = ? AND categoria IS NOT NULL
            GROUP BY categoria
            ORDER BY total DESC
            LIMIT ?
        ''', (año, limite))
    else:
        cursor.execute('''
            SELECT categoria, COUNT(*) as total
            FROM incidentes
            WHERE categoria IS NOT NULL
            GROUP BY categoria
            ORDER BY total DESC
            LIMIT ?
        ''', (limite,))
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


def incidentes_por_colonia(
    año: Optional[int] = None,
    categoria: Optional[str] = None,
    severidad: Optional[str] = None,
    limite: int = 20
) -> List[Dict]:
    """
    Incidentes agrupados por colonia con filtros
    
    SELECT cve_col, colonia, COUNT(*) as total,
           AVG(CASE WHEN severidad='ALTA' THEN 3 
                    WHEN severidad='MEDIA' THEN 2 
                    ELSE 1 END) as score_severidad
    FROM incidentes
    WHERE año = ? AND categoria = ? AND severidad = ?
    GROUP BY cve_col, colonia
    ORDER BY total DESC
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = ["cve_col IS NOT NULL"]
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if categoria:
        conditions.append("categoria = ?")
        params.append(categoria)
    if severidad:
        conditions.append("severidad = ?")
        params.append(severidad)
    
    where = " AND ".join(conditions)
    params.append(limite)
    
    cursor.execute(f'''
        SELECT 
            cve_col, 
            colonia, 
            COUNT(*) as total,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta,
            SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media,
            SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja,
            AVG(CASE 
                WHEN severidad = 'ALTA' THEN 3 
                WHEN severidad = 'MEDIA' THEN 2 
                ELSE 1 
            END) as score_severidad_promedio
        FROM incidentes
        WHERE {where}
        GROUP BY cve_col, colonia
        ORDER BY total DESC
        LIMIT ?
    ''', params)
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


def tendencia_mensual(
    año: Optional[int] = None,
    categoria: Optional[str] = None
) -> List[Dict]:
    """
    Tendencia mensual de incidentes
    
    SELECT año, mes, COUNT(*) as total
    FROM incidentes
    GROUP BY año, mes
    ORDER BY año, mes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if categoria:
        conditions.append("categoria = ?")
        params.append(categoria)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    cursor.execute(f'''
        SELECT 
            año, 
            mes,
            COUNT(*) as total,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta
        FROM incidentes
        WHERE {where}
        GROUP BY año, mes
        ORDER BY año, mes
    ''', params)
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


def heatmap_dia_hora(
    año: Optional[int] = None,
    colonia: Optional[str] = None
) -> List[Dict]:
    """
    Datos para heatmap día de semana vs parte del día
    
    SELECT dia_semana, parte_del_dia, COUNT(*) as total
    FROM incidentes
    GROUP BY dia_semana, parte_del_dia
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if colonia:
        conditions.append("colonia = ?")
        params.append(colonia)
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    cursor.execute(f'''
        SELECT 
            dia_semana,
            parte_del_dia,
            COUNT(*) as total
        FROM incidentes
        WHERE {where} AND dia_semana IS NOT NULL AND parte_del_dia IS NOT NULL
        GROUP BY dia_semana, parte_del_dia
    ''', params)
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


# =============================================================================
# CONSULTAS DE POLÍGONOS/COLONIAS
# =============================================================================

def colonias_mas_peligrosas(limite: int = 10) -> List[Dict]:
    """
    Colonias con mayor índice de riesgo
    
    SELECT colonia, total_incidentes, tasa_incidentes_per_1k, score_severidad
    FROM poligonos
    WHERE poblacion_total > 0
    ORDER BY tasa_incidentes_per_1k DESC
    LIMIT ?
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            colonia,
            total_incidentes,
            poblacion_total,
            tasa_incidentes_per_1k,
            score_severidad,
            incidentes_alta
        FROM poligonos
        WHERE poblacion_total > 0 AND tasa_incidentes_per_1k IS NOT NULL
        ORDER BY tasa_incidentes_per_1k DESC
        LIMIT ?
    ''', (limite,))
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


def colonias_por_poblacion(limite: int = 10) -> List[Dict]:
    """
    Colonias más pobladas con sus incidentes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            colonia,
            poblacion_total,
            total_incidentes,
            tasa_incidentes_per_1k,
            densidad_poblacional
        FROM poligonos
        WHERE poblacion_total IS NOT NULL
        ORDER BY poblacion_total DESC
        LIMIT ?
    ''', (limite,))
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


def comparar_colonias(cve_cols: List[str]) -> List[Dict]:
    """
    Comparar métricas entre colonias específicas
    
    SELECT * FROM poligonos WHERE cve_col IN (?, ?, ?)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in cve_cols])
    
    cursor.execute(f'''
        SELECT 
            cve_col,
            colonia,
            total_incidentes,
            incidentes_alta,
            incidentes_media,
            incidentes_baja,
            poblacion_total,
            tasa_incidentes_per_1k,
            score_severidad,
            escolaridad_años_prom
        FROM poligonos
        WHERE cve_col IN ({placeholders})
    ''', cve_cols)
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


# =============================================================================
# CONSULTAS AVANZADAS
# =============================================================================

def analisis_estacional(categoria: Optional[str] = None) -> Dict:
    """
    Análisis de patrones estacionales
    
    SELECT trimestre, COUNT(*) as total
    FROM incidentes
    GROUP BY trimestre
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if categoria:
        cursor.execute('''
            SELECT 
                trimestre,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN severidad = 'ALTA' THEN 3 
                    WHEN severidad = 'MEDIA' THEN 2 
                    ELSE 1 
                END) as severidad_promedio
            FROM incidentes
            WHERE categoria = ?
            GROUP BY trimestre
            ORDER BY trimestre
        ''', (categoria,))
    else:
        cursor.execute('''
            SELECT 
                trimestre,
                COUNT(*) as total,
                AVG(CASE 
                    WHEN severidad = 'ALTA' THEN 3 
                    WHEN severidad = 'MEDIA' THEN 2 
                    ELSE 1 
                END) as severidad_promedio
            FROM incidentes
            GROUP BY trimestre
            ORDER BY trimestre
        ''')
    
    resultados = {f'Q{row["trimestre"]}': dict(row) for row in cursor.fetchall()}
    conn.close()
    
    return resultados


def correlacion_poblacion_incidentes() -> List[Dict]:
    """
    Datos para análisis de correlación población vs incidentes
    
    SELECT poblacion_total, total_incidentes, tasa_incidentes_per_1k
    FROM poligonos
    WHERE poblacion_total > 0
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            colonia,
            poblacion_total,
            total_incidentes,
            tasa_incidentes_per_1k,
            score_severidad,
            escolaridad_años_prom
        FROM poligonos
        WHERE poblacion_total > 0 AND total_incidentes > 0
        ORDER BY poblacion_total
    ''')
    
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return resultados


# =============================================================================
# EJEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("EJEMPLOS DE CONSULTAS SQL")
    print("="*60)
    
    # Total por período
    print("\n📊 Total incidentes 2023:")
    print(total_incidentes_por_periodo(año=2023))
    
    # Por categoría
    print("\n📋 Top 5 categorías:")
    for cat in incidentes_por_categoria(limite=5):
        print(f"  - {cat['categoria']}: {cat['total']:,}")
    
    # Colonias más peligrosas
    print("\n⚠️ Top 5 colonias por tasa:")
    for col in colonias_mas_peligrosas(limite=5):
        print(f"  - {col['colonia']}: {col['tasa_incidentes_per_1k']:.1f} per 1k hab")
    
    # Análisis estacional
    print("\n🗓️ Análisis por trimestre:")
    for q, datos in analisis_estacional().items():
        print(f"  - {q}: {datos['total']:,} incidentes")
    
    print("\n" + "="*60)
