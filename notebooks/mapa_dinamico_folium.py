"""
Mapa Interactivo Dinámico con Folium + JavaScript
UN SOLO mapa con filtros de año/mes/categoría en tiempo real
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
    print("\n[1/4] Cargando polígonos...")
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed' / 'unificado'
    
    gdf = gpd.read_file(data_dir / 'poligonos_unificados_completo.geojson')
    print(f"      ✓ {len(gdf):,} polígonos")
    
    print("\n[2/4] Cargando incidentes (puede tardar 1-2 min)...")
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
    print(f"      ✓ {len(df_inc):,} incidentes")
    
    return gdf, df_inc


def preparar_datos_por_poligono(gdf, df_inc):
    """Preparar estructura de datos para JavaScript"""
    print("\n[3/4] Agregando incidentes por polígono y periodo...")
    
    # Extraer año, mes
    df_inc['Año'] = df_inc['Timestamp'].dt.year
    df_inc['Mes'] = df_inc['Timestamp'].dt.month
    
    # Agrupar por CVE_COL, Año, Mes, Categoría, Severidad
    print("      - Agrupando por año...")
    agg_año = df_inc.groupby(['CVE_COL', 'Año', 'Nivel_Severidad'], observed=False).size().reset_index(name='count')
    
    print("      - Agrupando por mes...")
    agg_mes = df_inc.groupby(['CVE_COL', 'Año', 'Mes', 'Nivel_Severidad'], observed=False).size().reset_index(name='count')
    
    print("      - Pivoteando datos para búsqueda rápida...")
    # Pivotar para tener severidad como columnas (mucho más rápido)
    pivot_año = agg_año.pivot_table(
        index=['CVE_COL', 'Año'], 
        columns='Nivel_Severidad', 
        values='count', 
        fill_value=0
    ).reset_index()
    
    pivot_mes = agg_mes.pivot_table(
        index=['CVE_COL', 'Año', 'Mes'], 
        columns='Nivel_Severidad', 
        values='count', 
        fill_value=0
    ).reset_index()
    
    print("      - Creando índices para búsqueda O(1)...")
    # Crear diccionarios indexados para búsqueda instantánea
    dict_año = pivot_año.set_index(['CVE_COL', 'Año']).to_dict('index')
    dict_mes = pivot_mes.set_index(['CVE_COL', 'Año', 'Mes']).to_dict('index')
    
    print("      - Estructurando datos por polígono...")
    # Crear diccionario por polígono usando búsqueda indexada
    datos_poligonos = {}
    
    for cve_col in gdf['CVE_COL'].unique():
        datos_poligonos[cve_col] = {
            'por_año': {},
            'por_mes': {}
        }
        
        # Datos por año - búsqueda O(1)
        for año in range(2018, 2026):
            key = (cve_col, año)
            if key in dict_año:
                row = dict_año[key]
                datos_poligonos[cve_col]['por_año'][str(año)] = {
                    'total': int(row.get('ALTA', 0) + row.get('MEDIA', 0) + row.get('BAJA', 0)),
                    'alta': int(row.get('ALTA', 0)),
                    'media': int(row.get('MEDIA', 0)),
                    'baja': int(row.get('BAJA', 0))
                }
            else:
                datos_poligonos[cve_col]['por_año'][str(año)] = {
                    'total': 0, 'alta': 0, 'media': 0, 'baja': 0
                }
        
        # Datos por mes - búsqueda O(1)
        for año in range(2018, 2026):
            for mes in range(1, 13):
                key = (cve_col, año, mes)
                mes_str = f"{año}-{mes:02d}"
                if key in dict_mes:
                    row = dict_mes[key]
                    datos_poligonos[cve_col]['por_mes'][mes_str] = {
                        'total': int(row.get('ALTA', 0) + row.get('MEDIA', 0) + row.get('BAJA', 0)),
                        'alta': int(row.get('ALTA', 0)),
                        'media': int(row.get('MEDIA', 0)),
                        'baja': int(row.get('BAJA', 0))
                    }
                else:
                    datos_poligonos[cve_col]['por_mes'][mes_str] = {
                        'total': 0, 'alta': 0, 'media': 0, 'baja': 0
                    }
    
    print(f"      ✓ Datos preparados para {len(datos_poligonos)} polígonos")
    return datos_poligonos


def crear_mapa_dinamico(gdf, datos_poligonos):
    """Crear mapa único con filtros JavaScript dinámicos"""
    print("\n[4/4] Generando mapa interactivo...")
    
    # Crear mapa base
    m = folium.Map(
        location=[29.0892, -110.9615],
        zoom_start=11,
        tiles='CartoDB positron'
    )
    
    # Agregar tiles adicionales
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)
    
    # Preparar GeoJSON con datos
    print("      - Preparando geometrías...")
    
    # Eliminar columnas problemáticas para JSON
    gdf_clean = gdf.copy()
    cols_to_drop = []
    for col in gdf_clean.columns:
        if col != 'geometry':  # No eliminar geometry
            dtype = gdf_clean[col].dtype
            if pd.api.types.is_datetime64_any_dtype(dtype):
                cols_to_drop.append(col)
            elif pd.api.types.is_object_dtype(dtype):
                # Verificar si hay dicts que no son serializables
                try:
                    sample = gdf_clean[col].dropna().iloc[0] if len(gdf_clean[col].dropna()) > 0 else None
                    if isinstance(sample, dict):
                        cols_to_drop.append(col)
                except:
                    pass
    
    if cols_to_drop:
        print(f"      - Eliminando columnas no serializables: {cols_to_drop}")
        gdf_clean = gdf_clean.drop(columns=cols_to_drop)
    
    geojson_data = json.loads(gdf_clean.to_json())
    
    # Inyectar datos de incidentes en properties
    for feature in geojson_data['features']:
        cve_col = feature['properties']['CVE_COL']
        if cve_col in datos_poligonos:
            feature['properties']['incidentes_data'] = datos_poligonos[cve_col]
    
    # Crear capa de polígonos con estilo dinámico
    print("      - Agregando polígonos con JavaScript dinámico...")
    
    # JavaScript para filtros y actualización dinámica
    js_code = """
    <script>
    // Variables globales
    let añoSeleccionado = 'todos';
    let mesSeleccionado = 'todos';
    let geojsonLayer = null;
    let geojsonData = """ + json.dumps(geojson_data) + """;
    
    // Función para obtener color según cantidad de incidentes
    function getColor(d) {
        return d > 50000 ? '#800026' :
               d > 20000 ? '#BD0026' :
               d > 10000 ? '#E31A1C' :
               d > 5000  ? '#FC4E2A' :
               d > 2000  ? '#FD8D3C' :
               d > 1000  ? '#FEB24C' :
               d > 500   ? '#FED976' :
                           '#FFEDA0';
    }
    
    // Función para calcular incidentes según filtros
    function getIncidentes(properties) {
        const data = properties.incidentes_data;
        if (!data) return {total: 0, alta: 0, media: 0, baja: 0};
        
        if (añoSeleccionado === 'todos') {
            // Sumar todos los años
            let result = {total: 0, alta: 0, media: 0, baja: 0};
            for (let año in data.por_año) {
                result.total += data.por_año[año].total;
                result.alta += data.por_año[año].alta;
                result.media += data.por_año[año].media;
                result.baja += data.por_año[año].baja;
            }
            return result;
        } else if (mesSeleccionado === 'todos') {
            // Solo año específico
            return data.por_año[añoSeleccionado] || {total: 0, alta: 0, media: 0, baja: 0};
        } else {
            // Año y mes específicos
            const key = añoSeleccionado + '-' + mesSeleccionado.padStart(2, '0');
            return data.por_mes[key] || {total: 0, alta: 0, media: 0, baja: 0};
        }
    }
    
    // Estilo de polígonos
    function style(feature) {
        const incidentes = getIncidentes(feature.properties);
        return {
            fillColor: getColor(incidentes.total),
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.7
        };
    }
    
    // Popup dinámico
    function onEachFeature(feature, layer) {
        layer.on('click', function(e) {
            const props = feature.properties;
            const inc = getIncidentes(props);
            
            let periodoStr = '';
            if (añoSeleccionado === 'todos') {
                periodoStr = '2018-2025 (Completo)';
            } else if (mesSeleccionado === 'todos') {
                periodoStr = 'Año ' + añoSeleccionado;
            } else {
                const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                periodoStr = meses[parseInt(mesSeleccionado)-1] + ' ' + añoSeleccionado;
            }
            
            const popupContent = `
                <div style="font-family: Arial; width: 320px;">
                    <h3 style="margin: 0 0 10px 0; color: #2c3e50;">${props.COLONIA}</h3>
                    <hr style="margin: 10px 0;">
                    
                    <h4 style="margin: 5px 0; color: #e74c3c;">📊 Periodo: ${periodoStr}</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 5px;"><b>Total:</b></td>
                            <td style="padding: 5px; text-align: right; font-size: 18px;"><b>${inc.total.toLocaleString()}</b></td>
                        </tr>
                        <tr style="background-color: #fee;">
                            <td style="padding: 5px;">🔴 Alta severidad:</td>
                            <td style="padding: 5px; text-align: right;">${inc.alta.toLocaleString()}</td>
                        </tr>
                        <tr style="background-color: #fec;">
                            <td style="padding: 5px;">🟡 Media severidad:</td>
                            <td style="padding: 5px; text-align: right;">${inc.media.toLocaleString()}</td>
                        </tr>
                        <tr style="background-color: #def;">
                            <td style="padding: 5px;">🔵 Baja severidad:</td>
                            <td style="padding: 5px; text-align: right;">${inc.baja.toLocaleString()}</td>
                        </tr>
                    </table>
                    
                    ${props.poblacion_total ? `
                    <hr style="margin: 10px 0;">
                    <h4 style="margin: 5px 0; color: #27ae60;">👥 Demografía</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 3px;">Población:</td>
                            <td style="padding: 3px; text-align: right;">${Math.round(props.poblacion_total).toLocaleString()} hab</td>
                        </tr>
                        ${props.tasa_incidentes_per_1k ? `
                        <tr style="background-color: #fef5e7;">
                            <td style="padding: 3px;"><b>Tasa histórica:</b></td>
                            <td style="padding: 3px; text-align: right;"><b>${props.tasa_incidentes_per_1k.toFixed(1)} por 1k hab</b></td>
                        </tr>
                        ` : ''}
                    </table>
                    ` : ''}
                    
                    <hr style="margin: 10px 0;">
                    <p style="font-size: 10px; color: #7f8c8d; margin: 5px 0;">
                        <b>CVE_COL:</b> ${props.CVE_COL}
                    </p>
                </div>
            `;
            
            layer.bindPopup(popupContent).openPopup();
        });
        
        layer.on('mouseover', function(e) {
            layer.setStyle({
                weight: 3,
                color: '#666',
                fillOpacity: 0.9
            });
        });
        
        layer.on('mouseout', function(e) {
            geojsonLayer.resetStyle(e.target);
        });
    }
    
    // Función para actualizar el mapa
    function actualizarMapa() {
        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
        }
        
        geojsonLayer = L.geoJSON(geojsonData, {
            style: style,
            onEachFeature: onEachFeature
        }).addTo(map);
        
        // Actualizar estadísticas globales
        let totalGlobal = 0;
        geojsonData.features.forEach(feature => {
            const inc = getIncidentes(feature.properties);
            totalGlobal += inc.total;
        });
        
        document.getElementById('stats-total').textContent = totalGlobal.toLocaleString();
    }
    
    // Event listeners para filtros
    document.addEventListener('DOMContentLoaded', function() {
        actualizarMapa();
        
        document.getElementById('filtro-año').addEventListener('change', function() {
            añoSeleccionado = this.value;
            actualizarMapa();
        });
        
        document.getElementById('filtro-mes').addEventListener('change', function() {
            mesSeleccionado = this.value;
            actualizarMapa();
        });
    });
    </script>
    """
    
    # HTML del panel de controles
    controles_html = """
    <div style="position: fixed; top: 10px; left: 50px; width: 400px; 
                background-color: white; border: 2px solid grey; z-index: 9999; 
                padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="margin: 0 0 15px 0; color: #2c3e50;">🚨 Índice Delictivo Hermosillo</h3>
        
        <div style="margin-bottom: 10px;">
            <label style="font-weight: bold;">📅 Año:</label>
            <select id="filtro-año" style="width: 100%; padding: 5px; margin-top: 5px;">
                <option value="todos">Todos (2018-2025)</option>
                <option value="2018">2018</option>
                <option value="2019">2019</option>
                <option value="2020">2020</option>
                <option value="2021">2021</option>
                <option value="2022">2022</option>
                <option value="2023">2023</option>
                <option value="2024">2024</option>
                <option value="2025">2025</option>
            </select>
        </div>
        
        <div style="margin-bottom: 10px;">
            <label style="font-weight: bold;">📆 Mes:</label>
            <select id="filtro-mes" style="width: 100%; padding: 5px; margin-top: 5px;">
                <option value="todos">Todos</option>
                <option value="1">Enero</option>
                <option value="2">Febrero</option>
                <option value="3">Marzo</option>
                <option value="4">Abril</option>
                <option value="5">Mayo</option>
                <option value="6">Junio</option>
                <option value="7">Julio</option>
                <option value="8">Agosto</option>
                <option value="9">Septiembre</option>
                <option value="10">Octubre</option>
                <option value="11">Noviembre</option>
                <option value="12">Diciembre</option>
            </select>
        </div>
        
        <hr style="margin: 10px 0;">
        
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
            <p style="margin: 5px 0; font-size: 14px;">
                <b>Total de incidentes:</b> <span id="stats-total" style="color: #e74c3c; font-size: 18px; font-weight: bold;">0</span>
            </p>
        </div>
        
        <p style="margin: 10px 0 0 0; font-size: 11px; color: #7f8c8d;">
            💡 Haz click en cualquier colonia para ver detalles
        </p>
    </div>
    """
    
    # Agregar HTML y JS al mapa
    m.get_root().html.add_child(folium.Element(controles_html))
    m.get_root().html.add_child(folium.Element(js_code))
    
    # Agregar controles adicionales
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    
    print("      ✓ Mapa generado con filtros dinámicos")
    
    return m


def main():
    """Pipeline principal"""
    print("="*70)
    print("GENERADOR DE MAPA INTERACTIVO DINÁMICO")
    print("="*70)
    print("\nEsto generará UN SOLO mapa con filtros de año/mes en tiempo real")
    
    # Cargar datos
    gdf, df_inc = cargar_datos()
    
    # Preparar estructura para JavaScript
    datos_poligonos = preparar_datos_por_poligono(gdf, df_inc)
    
    # Crear mapa
    mapa = crear_mapa_dinamico(gdf, datos_poligonos)
    
    # Guardar
    project_root = Path(__file__).parent.parent
    output_dir = project_root / 'mapas_interactivos'
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / 'mapa_dinamico_hermosillo.html'
    mapa.save(str(filepath))
    
    print("\n" + "="*70)
    print("✅ MAPA GENERADO EXITOSAMENTE")
    print("="*70)
    print(f"\n📂 Ubicación: {filepath}")
    print("\n🎯 Características:")
    print("   ✓ Filtros de Año (2018-2025 o todos)")
    print("   ✓ Filtros de Mes (Enero-Diciembre o todos)")
    print("   ✓ Actualización instantánea al cambiar filtros")
    print("   ✓ Click en colonias para ver estadísticas del periodo")
    print("   ✓ Colores dinámicos según cantidad de incidentes")
    
    print("\n🚀 Abriendo en navegador...")
    webbrowser.open('file://' + str(filepath.absolute()))
    print("="*70)


if __name__ == "__main__":
    main()
