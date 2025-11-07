"""
Mapa Interactivo Dinámico con Folium + HTML/JS
Filtros temporales en tiempo real: Año, Mes, Día, Hora
Click en polígonos para ver estadísticas del periodo seleccionado
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
    print("Cargando incidentes (puede tardar un momento)...")
    df_inc = pd.read_csv(
        data_dir / 'incidentes_con_poligono_temporal.csv',
        dtype={
            'CVE_COL': 'str',
            'TIPO DE INCIDENTE': 'str',
            'Categoria_Incidente': 'str',
            'Nivel_Severidad': 'str'
        },
        parse_dates=['Timestamp']
    )
    
    # Extraer componentes temporales
    df_inc['Año'] = df_inc['Timestamp'].dt.year
    df_inc['Mes'] = df_inc['Timestamp'].dt.month
    df_inc['Dia'] = df_inc['Timestamp'].dt.day
    df_inc['Hora'] = df_inc['Timestamp'].dt.hour
    
    print(f"✓ Polígonos: {len(gdf):,}")
    print(f"✓ Incidentes: {len(df_inc):,}")
    
    return gdf, df_inc


def preparar_datos_js(gdf, df_inc):
    """
    Preparar datos en formato JSON para JavaScript
    Agrupa incidentes por polígono y componentes temporales
    """
    print("\nPreparando datos para JavaScript...")
    
    # Eliminar columnas problemáticas del GeoDataFrame
    gdf_clean = gdf.copy()
    cols_to_drop = []
    for col in gdf_clean.columns:
        if col != 'geometry':
            try:
                if pd.api.types.is_datetime64_any_dtype(gdf_clean[col]):
                    cols_to_drop.append(col)
            except:
                pass
    if cols_to_drop:
        gdf_clean = gdf_clean.drop(columns=cols_to_drop)
    
    # Convertir a GeoJSON
    geojson_data = json.loads(gdf_clean.to_json())
    
    # Crear estructura de datos: {CVE_COL: {año: {mes: {dia: {hora: {alta:X, media:Y, baja:Z, total:T}}}}}}
    print("Agregando incidentes por periodo temporal...")
    
    incidentes_por_poligono = {}
    
    for cve_col in df_inc['CVE_COL'].unique():
        if pd.isna(cve_col):
            continue
            
        df_pol = df_inc[df_inc['CVE_COL'] == cve_col]
        incidentes_por_poligono[cve_col] = {}
        
        for año in df_pol['Año'].unique():
            df_año = df_pol[df_pol['Año'] == año]
            incidentes_por_poligono[cve_col][int(año)] = {}
            
            for mes in df_año['Mes'].unique():
                df_mes = df_año[df_año['Mes'] == mes]
                incidentes_por_poligono[cve_col][int(año)][int(mes)] = {}
                
                for dia in df_mes['Dia'].unique():
                    df_dia = df_mes[df_mes['Dia'] == dia]
                    incidentes_por_poligono[cve_col][int(año)][int(mes)][int(dia)] = {}
                    
                    for hora in df_dia['Hora'].unique():
                        df_hora = df_dia[df_dia['Hora'] == hora]
                        
                        incidentes_por_poligono[cve_col][int(año)][int(mes)][int(dia)][int(hora)] = {
                            'total': len(df_hora),
                            'alta': int((df_hora['Nivel_Severidad'] == 'ALTA').sum()),
                            'media': int((df_hora['Nivel_Severidad'] == 'MEDIA').sum()),
                            'baja': int((df_hora['Nivel_Severidad'] == 'BAJA').sum())
                        }
    
    print(f"✓ Datos preparados para {len(incidentes_por_poligono)} polígonos")
    
    return geojson_data, incidentes_por_poligono


def crear_mapa_dinamico(geojson_data, incidentes_data, gdf):
    """Crear mapa interactivo con filtros dinámicos"""
    
    print("\nCreando mapa interactivo...")
    
    # Crear mapa base
    m = folium.Map(
        location=[29.0892, -110.9615],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Agregar capas de tiles
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)
    
    # HTML/CSS/JS para controles y lógica
    controls_html = """
    <style>
        #controls-panel {
            position: fixed;
            top: 80px;
            left: 10px;
            width: 300px;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 1000;
            font-family: Arial, sans-serif;
        }
        
        #controls-panel h3 {
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 16px;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 5px;
        }
        
        .filter-group {
            margin-bottom: 12px;
        }
        
        .filter-group label {
            display: block;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 3px;
            color: #34495e;
        }
        
        .filter-group select {
            width: 100%;
            padding: 5px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 12px;
        }
        
        #apply-filters {
            width: 100%;
            padding: 10px;
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            margin-top: 10px;
        }
        
        #apply-filters:hover {
            background-color: #c0392b;
        }
        
        #stats-display {
            margin-top: 15px;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            font-size: 11px;
        }
        
        #stats-display p {
            margin: 3px 0;
        }
        
        .stat-label {
            font-weight: bold;
            color: #2c3e50;
        }
        
        #info-panel {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 1001;
            text-align: center;
        }
        
        #info-panel h2 {
            margin: 0;
            font-size: 18px;
            color: #e74c3c;
        }
    </style>
    
    <div id="info-panel">
        <h2>🚨 Índice Delictivo Hermosillo - Mapa Dinámico</h2>
        <p style="margin: 5px 0; font-size: 12px;">Selecciona periodo y haz click en polígonos para ver detalles</p>
    </div>
    
    <div id="controls-panel">
        <h3>⏰ Filtros Temporales</h3>
        
        <div class="filter-group">
            <label>Año:</label>
            <select id="filter-year">
                <option value="all">Todos</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Mes:</label>
            <select id="filter-month">
                <option value="all">Todos</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Día:</label>
            <select id="filter-day">
                <option value="all">Todos</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Hora:</label>
            <select id="filter-hour">
                <option value="all">Todas</option>
            </select>
        </div>
        
        <button id="apply-filters">🔍 Aplicar Filtros</button>
        
        <div id="stats-display">
            <p><span class="stat-label">Periodo:</span> <span id="periodo-text">Todos</span></p>
            <p><span class="stat-label">Total incidentes:</span> <span id="total-incidentes">-</span></p>
            <p><span class="stat-label">Polígonos afectados:</span> <span id="poligonos-afectados">-</span></p>
        </div>
    </div>
    
    <script>
        // Datos de incidentes por polígono
        var incidentesData = """ + json.dumps(incidentes_data) + """;
        
        // Información demográfica por polígono
        var demografiaData = {};
        """ + "\n".join([
            f"demografiaData['{row['CVE_COL']}'] = {{"
            f"'COLONIA': '{row['COLONIA']}', "
            f"'poblacion_total': {int(row['poblacion_total']) if pd.notna(row['poblacion_total']) else 'null'}, "
            f"'viviendas_totales': {int(row['viviendas_totales']) if pd.notna(row['viviendas_totales']) else 'null'}, "
            f"'total_historico': {int(row['total_incidentes'])}, "
            f"'tasa_per_1k': {row['tasa_incidentes_per_1k']:.1f if pd.notna(row.get('tasa_incidentes_per_1k')) else 'null'}, "
            f"'indice_riesgo': {row['indice_riesgo']:.1f if pd.notna(row.get('indice_riesgo')) else 'null'}"
            f"}};"
            for _, row in gdf.iterrows()
        ]) + """
        
        // Poblar selectores
        function populateSelectors() {
            // Años
            var years = Object.keys(incidentesData).length > 0 ? 
                        [...new Set(Object.values(incidentesData).flatMap(p => Object.keys(p)))].sort() : 
                        [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
            var yearSelect = document.getElementById('filter-year');
            years.forEach(year => {
                var option = document.createElement('option');
                option.value = year;
                option.text = year;
                yearSelect.add(option);
            });
            
            // Meses
            var monthSelect = document.getElementById('filter-month');
            var meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
            for (var i = 1; i <= 12; i++) {
                var option = document.createElement('option');
                option.value = i;
                option.text = i + ' - ' + meses[i-1];
                monthSelect.add(option);
            }
            
            // Días
            var daySelect = document.getElementById('filter-day');
            for (var i = 1; i <= 31; i++) {
                var option = document.createElement('option');
                option.value = i;
                option.text = i;
                daySelect.add(option);
            }
            
            // Horas
            var hourSelect = document.getElementById('filter-hour');
            for (var i = 0; i < 24; i++) {
                var option = document.createElement('option');
                option.value = i;
                option.text = i.toString().padStart(2, '0') + ':00';
                hourSelect.add(option);
            }
        }
        
        // Calcular incidentes para periodo seleccionado
        function calcularIncidentesPeriodo(year, month, day, hour) {
            var totales = {};
            
            Object.keys(incidentesData).forEach(cveCol => {
                var suma = {total: 0, alta: 0, media: 0, baja: 0};
                
                var years = (year === 'all') ? Object.keys(incidentesData[cveCol]) : [year];
                
                years.forEach(y => {
                    if (!incidentesData[cveCol][y]) return;
                    
                    var months = (month === 'all') ? Object.keys(incidentesData[cveCol][y]) : [month];
                    
                    months.forEach(m => {
                        if (!incidentesData[cveCol][y][m]) return;
                        
                        var days = (day === 'all') ? Object.keys(incidentesData[cveCol][y][m]) : [day];
                        
                        days.forEach(d => {
                            if (!incidentesData[cveCol][y][m][d]) return;
                            
                            var hours = (hour === 'all') ? Object.keys(incidentesData[cveCol][y][m][d]) : [hour];
                            
                            hours.forEach(h => {
                                if (incidentesData[cveCol][y][m][d][h]) {
                                    var data = incidentesData[cveCol][y][m][d][h];
                                    suma.total += data.total;
                                    suma.alta += data.alta;
                                    suma.media += data.media;
                                    suma.baja += data.baja;
                                }
                            });
                        });
                    });
                });
                
                if (suma.total > 0) {
                    totales[cveCol] = suma;
                }
            });
            
            return totales;
        }
        
        // Actualizar popup de polígono
        function crearPopupHtml(cveCol, incidentesPeriodo) {
            var demo = demografiaData[cveCol];
            if (!demo) return '<p>Datos no disponibles</p>';
            
            var inc = incidentesPeriodo[cveCol] || {total: 0, alta: 0, media: 0, baja: 0};
            
            var html = '<div style="font-family: Arial; width: 300px;">';
            html += '<h3 style="margin: 0 0 10px 0; color: #2c3e50;">' + demo.COLONIA + '</h3>';
            html += '<hr style="margin: 10px 0;">';
            
            html += '<h4 style="margin: 5px 0; color: #e74c3c;">📊 Incidentes en Periodo Seleccionado</h4>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<tr><td style="padding: 3px;"><b>Total:</b></td><td style="padding: 3px; text-align: right;">' + inc.total.toLocaleString() + '</td></tr>';
            html += '<tr style="background-color: #fee;"><td style="padding: 3px;">Alta severidad:</td><td style="padding: 3px; text-align: right;">' + inc.alta.toLocaleString() + '</td></tr>';
            html += '<tr style="background-color: #fec;"><td style="padding: 3px;">Media severidad:</td><td style="padding: 3px; text-align: right;">' + inc.media.toLocaleString() + '</td></tr>';
            html += '<tr style="background-color: #def;"><td style="padding: 3px;">Baja severidad:</td><td style="padding: 3px; text-align: right;">' + inc.baja.toLocaleString() + '</td></tr>';
            html += '</table>';
            
            html += '<hr style="margin: 10px 0;">';
            html += '<h4 style="margin: 5px 0; color: #3498db;">📈 Total Histórico (2018-2025)</h4>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<tr><td style="padding: 3px;"><b>Total:</b></td><td style="padding: 3px; text-align: right;">' + demo.total_historico.toLocaleString() + '</td></tr>';
            html += '</table>';
            
            if (demo.poblacion_total !== null) {
                html += '<hr style="margin: 10px 0;">';
                html += '<h4 style="margin: 5px 0; color: #27ae60;">👥 Demografía</h4>';
                html += '<table style="width: 100%; border-collapse: collapse;">';
                html += '<tr><td style="padding: 3px;">Población:</td><td style="padding: 3px; text-align: right;">' + demo.poblacion_total.toLocaleString() + ' hab</td></tr>';
                html += '<tr><td style="padding: 3px;">Viviendas:</td><td style="padding: 3px; text-align: right;">' + demo.viviendas_totales.toLocaleString() + '</td></tr>';
                html += '</table>';
                
                if (demo.tasa_per_1k !== null) {
                    html += '<table style="width: 100%; border-collapse: collapse; margin-top: 5px;">';
                    html += '<tr style="background-color: #fef5e7;"><td style="padding: 3px;"><b>Tasa histórica:</b></td><td style="padding: 3px; text-align: right;"><b>' + demo.tasa_per_1k + ' por 1k hab</b></td></tr>';
                    html += '</table>';
                }
                
                if (demo.indice_riesgo !== null) {
                    var colorRiesgo = demo.indice_riesgo < 30 ? '#27ae60' : demo.indice_riesgo < 60 ? '#f39c12' : '#e74c3c';
                    html += '<table style="width: 100%; border-collapse: collapse; margin-top: 5px;">';
                    html += '<tr style="background-color: ' + colorRiesgo + '20;"><td style="padding: 3px;"><b>Índice de Riesgo:</b></td><td style="padding: 3px; text-align: right;"><b>' + demo.indice_riesgo + '/100</b></td></tr>';
                    html += '</table>';
                }
            }
            
            html += '<hr style="margin: 10px 0;">';
            html += '<p style="font-size: 10px; color: #7f8c8d; margin: 5px 0;"><b>CVE_COL:</b> ' + cveCol + '</p>';
            html += '</div>';
            
            return html;
        }
        
        // Aplicar filtros
        var currentLayer = null;
        
        document.getElementById('apply-filters').addEventListener('click', function() {
            var year = document.getElementById('filter-year').value;
            var month = document.getElementById('filter-month').value;
            var day = document.getElementById('filter-day').value;
            var hour = document.getElementById('filter-hour').value;
            
            // Actualizar texto de periodo
            var periodoText = '';
            if (year !== 'all') periodoText += 'Año: ' + year + ' ';
            if (month !== 'all') periodoText += 'Mes: ' + month + ' ';
            if (day !== 'all') periodoText += 'Día: ' + day + ' ';
            if (hour !== 'all') periodoText += 'Hora: ' + hour + ':00';
            if (periodoText === '') periodoText = 'Todos (2018-2025)';
            document.getElementById('periodo-text').textContent = periodoText;
            
            // Calcular incidentes
            var incidentesPeriodo = calcularIncidentesPeriodo(year, month, day, hour);
            
            // Actualizar estadísticas
            var totalIncidentes = Object.values(incidentesPeriodo).reduce((sum, p) => sum + p.total, 0);
            var poligonosAfectados = Object.keys(incidentesPeriodo).length;
            
            document.getElementById('total-incidentes').textContent = totalIncidentes.toLocaleString();
            document.getElementById('poligonos-afectados').textContent = poligonosAfectados.toLocaleString();
            
            // Remover capa anterior si existe
            if (currentLayer !== null) {
                window.map.removeLayer(currentLayer);
            }
            
            // Crear nueva capa con colores actualizados
            var maxIncidentes = Math.max(...Object.values(incidentesPeriodo).map(p => p.total), 1);
            
            currentLayer = L.geoJSON(""" + json.dumps(geojson_data) + """, {
                style: function(feature) {
                    var cveCol = feature.properties.CVE_COL;
                    var total = incidentesPeriodo[cveCol] ? incidentesPeriodo[cveCol].total : 0;
                    var ratio = total / maxIncidentes;
                    
                    var color = total === 0 ? '#d3d3d3' :
                                ratio > 0.8 ? '#800026' :
                                ratio > 0.6 ? '#BD0026' :
                                ratio > 0.4 ? '#E31A1C' :
                                ratio > 0.2 ? '#FC4E2A' :
                                '#FD8D3C';
                    
                    return {
                        fillColor: color,
                        weight: 1,
                        opacity: 0.8,
                        color: 'white',
                        fillOpacity: 0.6
                    };
                },
                onEachFeature: function(feature, layer) {
                    var cveCol = feature.properties.CVE_COL;
                    var popupHtml = crearPopupHtml(cveCol, incidentesPeriodo);
                    layer.bindPopup(popupHtml, {maxWidth: 350});
                    
                    layer.on('mouseover', function() {
                        layer.setStyle({weight: 3, color: '#666'});
                    });
                    layer.on('mouseout', function() {
                        layer.setStyle({weight: 1, color: 'white'});
                    });
                }
            }).addTo(window.map);
        });
        
        // Inicializar
        populateSelectors();
        document.getElementById('apply-filters').click();
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(controls_html))
    
    # Variable global del mapa para JavaScript
    m.get_root().html.add_child(folium.Element("<script>window.map = " + m.get_name() + ";</script>"))
    
    # Agregar controles
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    
    return m


def main():
    """Pipeline principal"""
    print("="*70)
    print("MAPA INTERACTIVO DINÁMICO - FILTROS EN TIEMPO REAL")
    print("="*70)
    
    # Cargar datos
    gdf, df_inc = cargar_datos()
    
    # Preparar datos para JavaScript
    geojson_data, incidentes_data = preparar_datos_js(gdf, df_inc)
    
    # Crear mapa dinámico
    mapa = crear_mapa_dinamico(geojson_data, incidentes_data, gdf)
    
    # Guardar
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'mapas_interactivos'
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / 'mapa_dinamico_filtros.html'
    mapa.save(str(filepath))
    
    print("\n" + "="*70)
    print("✅ MAPA DINÁMICO GENERADO")
    print("="*70)
    print(f"\n📂 Ubicación: {filepath}")
    print(f"\n🎯 Características:")
    print("   - Filtros: Año, Mes, Día, Hora")
    print("   - Click en polígonos para ver detalles")
    print("   - Estadísticas en tiempo real")
    print("   - Colores dinámicos según periodo")
    
    # Abrir en navegador
    print("\n🚀 Abriendo mapa en navegador...")
    webbrowser.open('file://' + str(filepath.absolute()))
    
    print("="*70)


if __name__ == "__main__":
    main()
