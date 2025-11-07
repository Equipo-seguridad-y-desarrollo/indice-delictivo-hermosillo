"""
Mapa Interactivo con Folium - Índice Delictivo Hermosillo
Mapa simple: click en polígonos para ver estadísticas
Filtros temporales para explorar diferentes periodos
"""

import folium
from folium import plugins
import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import webbrowser

def cargar_datos():
    """Cargar datos unificados"""
    print("Cargando datos...")
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed' / 'unificado'
    
    # Polígonos con datos agregados
    gdf = gpd.read_file(data_dir / 'poligonos_unificados_completo.geojson')
    
    # Incidentes individuales
    df_inc = pd.read_csv(
        data_dir / 'incidentes_con_poligono_temporal.csv',
        dtype={
            'CVE_COL': 'str',
            'TIPO DE INCIDENTE': 'category',
            'Categoria_Incidente': 'category',
            'Nivel_Severidad': 'category'
        },
        parse_dates=['Timestamp']
    )
    
    print(f"✓ Polígonos: {len(gdf):,}")
    print(f"✓ Incidentes: {len(df_inc):,}")
    
    return gdf, df_inc


def agregar_incidentes_por_periodo(gdf, df_inc, año=None, mes=None):
    """
    Agregar incidentes filtrados por periodo a cada polígono
    """
    print(f"\nFiltrando periodo: Año={año or 'Todos'}, Mes={mes or 'Todos'}")
    
    # Filtrar por periodo
    df_filtrado = df_inc.copy()
    if año:
        df_filtrado = df_filtrado[df_filtrado['Timestamp'].dt.year == año]
    if mes:
        df_filtrado = df_filtrado[df_filtrado['Timestamp'].dt.month == mes]
    
    print(f"Incidentes en periodo: {len(df_filtrado):,}")
    
    # Agregar por polígono
    agg = df_filtrado.groupby('CVE_COL').agg({
        'TIPO DE INCIDENTE': 'count',
        'Nivel_Severidad': [
            ('alta', lambda x: (x == 'ALTA').sum()),
            ('media', lambda x: (x == 'MEDIA').sum()),
            ('baja', lambda x: (x == 'BAJA').sum())
        ]
    })
    agg.columns = ['total_periodo', 'alta_periodo', 'media_periodo', 'baja_periodo']
    agg = agg.reset_index()
    
    # Unir con polígonos
    gdf_periodo = gdf.merge(agg, on='CVE_COL', how='left')
    gdf_periodo['total_periodo'] = gdf_periodo['total_periodo'].fillna(0).astype(int)
    gdf_periodo['alta_periodo'] = gdf_periodo['alta_periodo'].fillna(0).astype(int)
    gdf_periodo['media_periodo'] = gdf_periodo['media_periodo'].fillna(0).astype(int)
    gdf_periodo['baja_periodo'] = gdf_periodo['baja_periodo'].fillna(0).astype(int)
    
    return gdf_periodo


def crear_popup_html(row):
    """Crear popup HTML con información del polígono"""
    
    # Información básica
    html = f"""
    <div style="font-family: Arial; width: 300px;">
        <h3 style="margin: 0 0 10px 0; color: #2c3e50;">{row['COLONIA']}</h3>
        <hr style="margin: 10px 0;">
        
        <h4 style="margin: 5px 0; color: #e74c3c;">📊 Incidentes en Periodo</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 3px;"><b>Total:</b></td>
                <td style="padding: 3px; text-align: right;">{int(row['total_periodo']):,}</td>
            </tr>
            <tr style="background-color: #fee;">
                <td style="padding: 3px;">Alta severidad:</td>
                <td style="padding: 3px; text-align: right;">{int(row['alta_periodo']):,}</td>
            </tr>
            <tr style="background-color: #fec;">
                <td style="padding: 3px;">Media severidad:</td>
                <td style="padding: 3px; text-align: right;">{int(row['media_periodo']):,}</td>
            </tr>
            <tr style="background-color: #def;">
                <td style="padding: 3px;">Baja severidad:</td>
                <td style="padding: 3px; text-align: right;">{int(row['baja_periodo']):,}</td>
            </tr>
        </table>
        
        <hr style="margin: 10px 0;">
        <h4 style="margin: 5px 0; color: #3498db;">📈 Total Histórico (2018-2025)</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 3px;"><b>Total:</b></td>
                <td style="padding: 3px; text-align: right;">{int(row['total_incidentes']):,}</td>
            </tr>
        </table>
    """
    
    # Demografía (si existe)
    if pd.notna(row['poblacion_total']):
        html += f"""
        <hr style="margin: 10px 0;">
        <h4 style="margin: 5px 0; color: #27ae60;">👥 Demografía</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 3px;">Población:</td>
                <td style="padding: 3px; text-align: right;">{int(row['poblacion_total']):,} hab</td>
            </tr>
            <tr>
                <td style="padding: 3px;">Viviendas:</td>
                <td style="padding: 3px; text-align: right;">{int(row['viviendas_totales']):,}</td>
            </tr>
        </table>
        """
        
        # Tasa per cápita
        if pd.notna(row['tasa_incidentes_per_1k']):
            html += f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 5px;">
                <tr style="background-color: #fef5e7;">
                    <td style="padding: 3px;"><b>Tasa histórica:</b></td>
                    <td style="padding: 3px; text-align: right;"><b>{row['tasa_incidentes_per_1k']:.1f} por 1k hab</b></td>
                </tr>
            </table>
            """
        
        # Índice de riesgo
        if pd.notna(row.get('indice_riesgo')):
            color_riesgo = '#27ae60' if row['indice_riesgo'] < 30 else '#f39c12' if row['indice_riesgo'] < 60 else '#e74c3c'
            html += f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 5px;">
                <tr style="background-color: {color_riesgo}20;">
                    <td style="padding: 3px;"><b>Índice de Riesgo:</b></td>
                    <td style="padding: 3px; text-align: right;"><b>{row['indice_riesgo']:.1f}/100</b></td>
                </tr>
            </table>
            """
    
    html += """
        <hr style="margin: 10px 0;">
        <p style="font-size: 10px; color: #7f8c8d; margin: 5px 0;">
            <b>CVE_COL:</b> {cve}<br>
            <b>CP:</b> {cp}
        </p>
    </div>
    """.format(cve=row['CVE_COL'], cp=row.get('CP', 'N/A'))
    
    return html


def crear_mapa(gdf_periodo, año=None, mes=None):
    """Crear mapa de Folium con polígonos interactivos"""
    
    print("\nCreando mapa...")
    
    # Limpiar columnas problemáticas para JSON
    gdf_clean = gdf_periodo.copy()
    
    # Eliminar columnas con timestamps y otros objetos problemáticos
    cols_to_drop = []
    for col in gdf_clean.columns:
        if col != 'geometry':
            try:
                # Intentar detectar timestamps
                if pd.api.types.is_datetime64_any_dtype(gdf_clean[col]):
                    cols_to_drop.append(col)
            except:
                pass
    
    if cols_to_drop:
        gdf_clean = gdf_clean.drop(columns=cols_to_drop)
        print(f"Columnas eliminadas: {cols_to_drop}")
    
    # Crear mapa centrado en Hermosillo
    m = folium.Map(
        location=[29.0892, -110.9615],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Agregar capas de tiles adicionales
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)
    
    # Determinar escala de colores según incidentes del periodo
    # Usar bins con valores mínimos seguros
    max_val = gdf_clean['total_periodo'].max()
    min_val = gdf_clean['total_periodo'].min()
    
    if max_val > 0:
        # Crear bins con valores safe
        bins = [0, max(1, max_val*0.2), max(2, max_val*0.4), max(3, max_val*0.6), max(4, max_val*0.8), max(5, max_val)]
    else:
        bins = [0, 1, 2, 3, 4, 5]
    
    # Crear choropleth con incidentes del periodo
    folium.Choropleth(
        geo_data=gdf_clean,
        data=gdf_clean,
        columns=['CVE_COL', 'total_periodo'],
        key_on='feature.properties.CVE_COL',
        fill_color='YlOrRd',
        fill_opacity=0.6,
        line_opacity=0.8,
        legend_name=f'Incidentes en periodo (Año: {año or "Todos"}, Mes: {mes or "Todos"})',
        nan_fill_color='lightgray',
        nan_fill_opacity=0.2,
        highlight=True,
        bins=bins
    ).add_to(m)
    
    # Agregar popups interactivos a cada polígono
    print("Agregando popups interactivos...")
    for idx, row in gdf_periodo.iterrows():
        # Crear popup con información
        popup_html = crear_popup_html(row)
        popup = folium.Popup(popup_html, max_width=350)
        
        # Agregar GeoJson con popup
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'transparent',
                'weight': 0
            },
            popup=popup
        ).add_to(m)
    
    # Agregar control de capas
    folium.LayerControl().add_to(m)
    
    # Agregar título
    periodo_str = f"Año: {año or 'Todos'}, Mes: {mes or 'Todos'}"
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h3 style="margin: 0;">🚨 Índice Delictivo Hermosillo</h3>
        <p style="margin: 5px 0;"><b>Periodo seleccionado:</b> {periodo_str}</p>
        <p style="margin: 5px 0; font-size: 12px;">Haz click en cualquier polígono para ver detalles</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Agregar minimapa
    minimap = plugins.MiniMap(toggle_display=True)
    m.add_child(minimap)
    
    # Agregar fullscreen
    plugins.Fullscreen().add_to(m)
    
    return m


def generar_mapas_por_año(gdf, df_inc, output_dir):
    """Generar un mapa por cada año"""
    
    años = sorted(df_inc['Timestamp'].dt.year.unique())
    
    print(f"\nGenerando mapas para {len(años)} años...")
    
    for año in años:
        print(f"\nProcesando año {año}...")
        gdf_año = agregar_incidentes_por_periodo(gdf, df_inc, año=año)
        
        mapa = crear_mapa(gdf_año, año=año)
        
        filename = f'mapa_hermosillo_{año}.html'
        filepath = output_dir / filename
        mapa.save(str(filepath))
        print(f"✓ Guardado: {filename}")
    
    # Mapa con todos los años
    print(f"\nProcesando todos los años...")
    gdf_todos = agregar_incidentes_por_periodo(gdf, df_inc)
    mapa_todos = crear_mapa(gdf_todos)
    filepath_todos = output_dir / 'mapa_hermosillo_2018_2025_completo.html'
    mapa_todos.save(str(filepath_todos))
    print(f"✓ Guardado: mapa_hermosillo_2018_2025_completo.html")
    
    return filepath_todos


def crear_index_html(output_dir, años):
    """Crear página índice con links a todos los mapas"""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Índice Delictivo Hermosillo - Mapas Interactivos</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #e74c3c;
                padding-bottom: 10px;
            }
            .card {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .card h2 {
                margin-top: 0;
                color: #3498db;
            }
            ul {
                list-style: none;
                padding: 0;
            }
            li {
                margin: 10px 0;
            }
            a {
                display: inline-block;
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            a:hover {
                background-color: #2980b9;
            }
            .highlight {
                background-color: #e74c3c;
            }
            .highlight:hover {
                background-color: #c0392b;
            }
            .info {
                background-color: #ecf0f1;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <h1>🚨 Índice Delictivo Hermosillo</h1>
        <p style="font-size: 18px; color: #7f8c8d;">Mapas Interactivos 2018-2025</p>
        
        <div class="info">
            <b>📌 Instrucciones:</b>
            <ul style="list-style: disc; padding-left: 20px; margin: 10px 0;">
                <li>Haz click en cualquier mapa para abrirlo</li>
                <li>En el mapa, haz click sobre cualquier polígono (colonia) para ver sus estadísticas</li>
                <li>Los colores indican la cantidad de incidentes (rojo = más incidentes)</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>🗺️ Mapa Completo (2018-2025)</h2>
            <p>Todos los incidentes del periodo completo</p>
            <a href="mapa_hermosillo_2018_2025_completo.html" class="highlight" target="_blank">
                📊 Abrir Mapa Completo
            </a>
        </div>
        
        <div class="card">
            <h2>📅 Mapas por Año</h2>
            <ul>
    """
    
    for año in años:
        html += f"""
                <li>
                    <a href="mapa_hermosillo_{año}.html" target="_blank">
                        📍 Mapa {año}
                    </a>
                </li>
        """
    
    html += """
            </ul>
        </div>
        
        <div class="card">
            <h2>ℹ️ Información</h2>
            <p><b>Dataset:</b> 2,297,081 incidentes de 2018-2025</p>
            <p><b>Polígonos:</b> 693 colonias de Hermosillo</p>
            <p><b>Fuente:</b> Reportes 911 Hermosillo</p>
            <p><b>Última actualización:</b> """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 12px;">
            <p>Equipo-seguridad-y-desarrollo | indice-delictivo-hermosillo</p>
        </footer>
    </body>
    </html>
    """
    
    filepath = output_dir / 'index.html'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Índice creado: index.html")
    return filepath


def main():
    """Pipeline principal"""
    print("="*70)
    print("GENERADOR DE MAPAS INTERACTIVOS - FOLIUM")
    print("="*70)
    
    # Cargar datos
    gdf, df_inc = cargar_datos()
    
    # Crear directorio de salida
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'mapas_interactivos'
    output_dir.mkdir(exist_ok=True)
    
    # Generar mapas por año
    mapa_completo = generar_mapas_por_año(gdf, df_inc, output_dir)
    
    # Obtener años disponibles
    años = sorted(df_inc['Timestamp'].dt.year.unique())
    
    # Crear índice HTML
    index_path = crear_index_html(output_dir, años)
    
    print("\n" + "="*70)
    print("✅ MAPAS GENERADOS EXITOSAMENTE")
    print("="*70)
    print(f"\n📂 Directorio: {output_dir}/")
    print(f"\n🌐 Abre en tu navegador: {index_path}")
    print("\nMapas creados:")
    print(f"  - index.html (página principal)")
    print(f"  - mapa_hermosillo_2018_2025_completo.html")
    for año in años:
        print(f"  - mapa_hermosillo_{año}.html")
    
    # Abrir automáticamente en navegador
    print("\n🚀 Abriendo mapa en navegador...")
    webbrowser.open('file://' + str(index_path.absolute()))
    
    print("="*70)


if __name__ == "__main__":
    main()
