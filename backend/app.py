"""
API REST con Flask para el Mapa Interactivo de Hermosillo
Provee endpoints para filtrar incidentes dinámicamente
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from pathlib import Path
import json

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el mapa HTML

DB_PATH = Path(__file__).parent / 'delitos_hermosillo.db'


def get_db():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# ENDPOINTS DE FILTROS
# =============================================================================

@app.route('/api/filtros/opciones', methods=['GET'])
def obtener_opciones_filtros():
    """
    Obtener todas las opciones disponibles para los filtros
    
    Retorna:
        - años: lista de años disponibles
        - categorias: lista de categorías
        - severidades: lista de niveles de severidad
        - partes_dia: partes del día
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Años
    cursor.execute("SELECT DISTINCT año FROM incidentes ORDER BY año")
    años = [row[0] for row in cursor.fetchall()]
    
    # Categorías
    cursor.execute("SELECT DISTINCT categoria FROM incidentes WHERE categoria IS NOT NULL ORDER BY categoria")
    categorias = [row[0] for row in cursor.fetchall()]
    
    # Severidades
    cursor.execute("SELECT DISTINCT severidad FROM incidentes WHERE severidad IS NOT NULL ORDER BY severidad")
    severidades = [row[0] for row in cursor.fetchall()]
    
    # Partes del día
    cursor.execute("SELECT DISTINCT parte_del_dia FROM incidentes WHERE parte_del_dia IS NOT NULL")
    partes_dia = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'años': años,
        'categorias': categorias,
        'severidades': severidades,
        'partes_dia': partes_dia,
        'trimestres': [1, 2, 3, 4]
    })


@app.route('/api/incidentes/filtrar', methods=['GET'])
def filtrar_incidentes():
    """
    Filtrar incidentes según parámetros
    
    Parámetros:
        - año: int (opcional)
        - trimestre: int 1-4 (opcional)
        - categoria: string (opcional)
        - severidad: string ALTA/MEDIA/BAJA (opcional)
        - cve_col: string (opcional) - filtrar por colonia específica
        - parte_dia: string (opcional)
    
    Retorna:
        - total: número total de incidentes filtrados
        - por_colonia: agregado por CVE_COL
    """
    
    # Obtener parámetros
    año = request.args.get('año', type=int)
    trimestre = request.args.get('trimestre', type=int)
    categoria = request.args.get('categoria')
    severidad = request.args.get('severidad')
    cve_col = request.args.get('cve_col')
    parte_dia = request.args.get('parte_dia')
    
    # Construir query dinámicamente
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    
    if trimestre:
        conditions.append("trimestre = ?")
        params.append(trimestre)
    
    if categoria and categoria != 'todas':
        conditions.append("categoria = ?")
        params.append(categoria)
    
    if severidad and severidad != 'todas':
        conditions.append("severidad = ?")
        params.append(severidad)
    
    if cve_col:
        conditions.append("cve_col = ?")
        params.append(cve_col)
    
    if parte_dia:
        conditions.append("parte_del_dia = ?")
        params.append(parte_dia)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de incidentes
    cursor.execute(f"SELECT COUNT(*) FROM incidentes WHERE {where_clause}", params)
    total = cursor.fetchone()[0]
    
    # Agregado por colonia
    cursor.execute(f'''
        SELECT 
            cve_col,
            colonia,
            COUNT(*) as total,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta,
            SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media,
            SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja
        FROM incidentes 
        WHERE {where_clause}
        GROUP BY cve_col, colonia
        ORDER BY total DESC
    ''', params)
    
    por_colonia = {}
    for row in cursor.fetchall():
        if row['cve_col']:
            por_colonia[row['cve_col']] = {
                'colonia': row['colonia'],
                'total': row['total'],
                'alta': row['alta'],
                'media': row['media'],
                'baja': row['baja']
            }
    
    conn.close()
    
    return jsonify({
        'filtros_aplicados': {
            'año': año,
            'trimestre': trimestre,
            'categoria': categoria,
            'severidad': severidad,
            'cve_col': cve_col,
            'parte_dia': parte_dia
        },
        'total': total,
        'colonias_afectadas': len(por_colonia),
        'por_colonia': por_colonia
    })


@app.route('/api/incidentes/agregado_temporal', methods=['GET'])
def agregado_temporal():
    """
    Obtener agregado temporal de incidentes
    
    Parámetros:
        - agrupacion: 'año', 'mes', 'trimestre' (default: 'mes')
        - categoria: filtrar por categoría (opcional)
        - severidad: filtrar por severidad (opcional)
    """
    
    agrupacion = request.args.get('agrupacion', 'mes')
    categoria = request.args.get('categoria')
    severidad = request.args.get('severidad')
    
    conditions = []
    params = []
    
    if categoria and categoria != 'todas':
        conditions.append("categoria = ?")
        params.append(categoria)
    
    if severidad and severidad != 'todas':
        conditions.append("severidad = ?")
        params.append(severidad)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    if agrupacion == 'año':
        group_col = 'año'
        select_col = 'año'
    elif agrupacion == 'trimestre':
        group_col = 'año, trimestre'
        select_col = "año || '-Q' || trimestre as periodo"
    else:  # mes
        group_col = 'año, mes'
        select_col = "año || '-' || printf('%02d', mes) as periodo"
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(f'''
        SELECT 
            {select_col},
            COUNT(*) as total,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta,
            SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media,
            SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja
        FROM incidentes 
        WHERE {where_clause}
        GROUP BY {group_col}
        ORDER BY {group_col}
    ''', params)
    
    resultados = []
    for row in cursor.fetchall():
        resultados.append({
            'periodo': row[0],
            'total': row['total'],
            'alta': row['alta'],
            'media': row['media'],
            'baja': row['baja']
        })
    
    conn.close()
    
    return jsonify({
        'agrupacion': agrupacion,
        'datos': resultados
    })


# =============================================================================
# ENDPOINTS DE POLÍGONOS/COLONIAS
# =============================================================================

@app.route('/api/poligonos', methods=['GET'])
def obtener_poligonos():
    """
    Obtener todos los polígonos con sus métricas
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            cve_col, colonia, total_incidentes, incidentes_alta, 
            incidentes_media, incidentes_baja, poblacion_total,
            tasa_incidentes_per_1k, score_severidad, geometry_json
        FROM poligonos
    ''')
    
    poligonos = []
    for row in cursor.fetchall():
        poligonos.append({
            'cve_col': row['cve_col'],
            'colonia': row['colonia'],
            'total_incidentes': row['total_incidentes'],
            'incidentes_alta': row['incidentes_alta'],
            'incidentes_media': row['incidentes_media'],
            'incidentes_baja': row['incidentes_baja'],
            'poblacion_total': row['poblacion_total'],
            'tasa_incidentes_per_1k': row['tasa_incidentes_per_1k'],
            'score_severidad': row['score_severidad'],
            'geometry': json.loads(row['geometry_json']) if row['geometry_json'] else None
        })
    
    conn.close()
    
    return jsonify({'poligonos': poligonos, 'total': len(poligonos)})


@app.route('/api/poligonos/<cve_col>', methods=['GET'])
def obtener_poligono(cve_col):
    """
    Obtener información detallada de un polígono específico
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Información del polígono
    cursor.execute('SELECT * FROM poligonos WHERE cve_col = ?', (cve_col,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': 'Polígono no encontrado'}), 404
    
    poligono = dict(row)
    if poligono.get('geometry_json'):
        poligono['geometry'] = json.loads(poligono['geometry_json'])
        del poligono['geometry_json']
    
    # Últimos 10 incidentes
    cursor.execute('''
        SELECT tipo_incidente, timestamp, categoria, severidad
        FROM incidentes 
        WHERE cve_col = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (cve_col,))
    
    ultimos_incidentes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'poligono': poligono,
        'ultimos_incidentes': ultimos_incidentes
    })


@app.route('/api/poligonos/geojson', methods=['GET'])
def obtener_geojson():
    """
    Obtener GeoJSON con métricas filtradas para el mapa
    
    Parámetros de filtro:
        - año, trimestre, categoria, severidad
    """
    
    año = request.args.get('año', type=int)
    trimestre = request.args.get('trimestre', type=int)
    categoria = request.args.get('categoria')
    severidad = request.args.get('severidad')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Construir filtros
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if trimestre:
        conditions.append("trimestre = ?")
        params.append(trimestre)
    if categoria and categoria != 'todas':
        conditions.append("categoria = ?")
        params.append(categoria)
    if severidad and severidad != 'todas':
        conditions.append("severidad = ?")
        params.append(severidad)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Obtener métricas filtradas por colonia
    cursor.execute(f'''
        SELECT 
            cve_col,
            COUNT(*) as total_filtrado,
            SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta_filtrado,
            SUM(CASE WHEN severidad = 'MEDIA' THEN 1 ELSE 0 END) as media_filtrado,
            SUM(CASE WHEN severidad = 'BAJA' THEN 1 ELSE 0 END) as baja_filtrado
        FROM incidentes 
        WHERE {where_clause}
        GROUP BY cve_col
    ''', params)
    
    metricas_filtradas = {row['cve_col']: dict(row) for row in cursor.fetchall()}
    
    # Obtener polígonos base
    cursor.execute('''
        SELECT cve_col, colonia, poblacion_total, geometry_json,
               total_incidentes, score_severidad
        FROM poligonos
    ''')
    
    features = []
    for row in cursor.fetchall():
        cve_col = row['cve_col']
        
        # Métricas filtradas o cero
        filtrado = metricas_filtradas.get(cve_col, {
            'total_filtrado': 0,
            'alta_filtrado': 0,
            'media_filtrado': 0,
            'baja_filtrado': 0
        })
        
        # Calcular tasa si hay población
        poblacion = row['poblacion_total'] or 0
        tasa_filtrada = (filtrado['total_filtrado'] / poblacion * 1000) if poblacion > 0 else 0
        
        if row['geometry_json']:
            feature = {
                'type': 'Feature',
                'geometry': json.loads(row['geometry_json']),
                'properties': {
                    'cve_col': cve_col,
                    'colonia': row['colonia'],
                    'poblacion': row['poblacion_total'],
                    'total_original': row['total_incidentes'],
                    'total_filtrado': filtrado['total_filtrado'],
                    'alta_filtrado': filtrado['alta_filtrado'],
                    'media_filtrado': filtrado['media_filtrado'],
                    'baja_filtrado': filtrado['baja_filtrado'],
                    'tasa_filtrada_per_1k': round(tasa_filtrada, 2),
                    'score_severidad': row['score_severidad']
                }
            }
            features.append(feature)
    
    conn.close()
    
    geojson = {
        'type': 'FeatureCollection',
        'filtros_aplicados': {
            'año': año,
            'trimestre': trimestre,
            'categoria': categoria,
            'severidad': severidad
        },
        'features': features
    }
    
    return jsonify(geojson)


# =============================================================================
# ENDPOINTS DE ESTADÍSTICAS
# =============================================================================

@app.route('/api/estadisticas/resumen', methods=['GET'])
def resumen_estadisticas():
    """
    Obtener resumen general de estadísticas
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Total incidentes
    cursor.execute("SELECT COUNT(*) FROM incidentes")
    total_incidentes = cursor.fetchone()[0]
    
    # Por severidad
    cursor.execute('''
        SELECT severidad, COUNT(*) as total
        FROM incidentes
        GROUP BY severidad
    ''')
    por_severidad = {row['severidad']: row['total'] for row in cursor.fetchall()}
    
    # Top 10 colonias
    cursor.execute('''
        SELECT colonia, COUNT(*) as total
        FROM incidentes
        WHERE colonia IS NOT NULL
        GROUP BY colonia
        ORDER BY total DESC
        LIMIT 10
    ''')
    top_colonias = [{'colonia': row['colonia'], 'total': row['total']} for row in cursor.fetchall()]
    
    # Top 5 categorías
    cursor.execute('''
        SELECT categoria, COUNT(*) as total
        FROM incidentes
        WHERE categoria IS NOT NULL
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT 5
    ''')
    top_categorias = [{'categoria': row['categoria'], 'total': row['total']} for row in cursor.fetchall()]
    
    # Rango de fechas
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM incidentes")
    rango = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'total_incidentes': total_incidentes,
        'por_severidad': por_severidad,
        'top_10_colonias': top_colonias,
        'top_5_categorias': top_categorias,
        'rango_fechas': {
            'desde': rango[0],
            'hasta': rango[1]
        }
    })


@app.route('/api/estadisticas/heatmap', methods=['GET'])
def datos_heatmap():
    """
    Obtener datos para heatmap (día de semana vs hora)
    """
    año = request.args.get('año', type=int)
    categoria = request.args.get('categoria')
    
    conditions = []
    params = []
    
    if año:
        conditions.append("año = ?")
        params.append(año)
    if categoria and categoria != 'todas':
        conditions.append("categoria = ?")
        params.append(categoria)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(f'''
        SELECT 
            dia_semana,
            parte_del_dia,
            COUNT(*) as total
        FROM incidentes
        WHERE {where_clause}
        GROUP BY dia_semana, parte_del_dia
    ''', params)
    
    datos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'datos': datos})


# =============================================================================
# MAIN
# =============================================================================

@app.route('/')
def index():
    """Endpoint raíz con información de la API"""
    return jsonify({
        'nombre': 'API Índice Delictivo Hermosillo',
        'version': '1.0',
        'endpoints': {
            'filtros': {
                '/api/filtros/opciones': 'GET - Opciones disponibles para filtros'
            },
            'incidentes': {
                '/api/incidentes/filtrar': 'GET - Filtrar incidentes con parámetros',
                '/api/incidentes/agregado_temporal': 'GET - Agregado por tiempo'
            },
            'poligonos': {
                '/api/poligonos': 'GET - Todos los polígonos',
                '/api/poligonos/<cve_col>': 'GET - Detalle de polígono',
                '/api/poligonos/geojson': 'GET - GeoJSON con filtros'
            },
            'estadisticas': {
                '/api/estadisticas/resumen': 'GET - Resumen general',
                '/api/estadisticas/heatmap': 'GET - Datos para heatmap'
            }
        }
    })


if __name__ == '__main__':
    print("="*60)
    print("API ÍNDICE DELICTIVO HERMOSILLO")
    print("="*60)
    print("🌐 Servidor: http://localhost:5000")
    print("📚 Documentación: http://localhost:5000/")
    print("="*60)
    
    app.run(debug=True, port=5000)
