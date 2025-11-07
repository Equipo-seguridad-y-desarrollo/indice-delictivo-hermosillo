"""
Dashboard Interactivo - Índice Delictivo Hermosillo
Mapa con control temporal para explorar incidentes por hora/día/mes
Incluye demografía y métricas por colonia
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
import json
from datetime import datetime, timedelta
from pathlib import Path

# =============================================
# CONFIGURACIÓN Y CARGA DE DATOS
# =============================================

print("Cargando datos...")
project_root = Path(__file__).parent.parent
data_dir = project_root / 'data' / 'processed' / 'unificado'

# Polígonos con datos agregados
gdf_poligonos = gpd.read_file(data_dir / 'poligonos_unificados_completo.geojson')

# Incidentes individuales con timestamp
df_incidentes = pd.read_csv(data_dir / 'incidentes_con_poligono_temporal.csv')
df_incidentes['Timestamp'] = pd.to_datetime(df_incidentes['Timestamp'])

# Extraer componentes temporales para filtros
df_incidentes['Año'] = df_incidentes['Timestamp'].dt.year
df_incidentes['Mes'] = df_incidentes['Timestamp'].dt.month
df_incidentes['Dia'] = df_incidentes['Timestamp'].dt.day
df_incidentes['Hora'] = df_incidentes['Timestamp'].dt.hour
df_incidentes['FechaStr'] = df_incidentes['Timestamp'].dt.strftime('%Y-%m-%d')

print(f"✓ Polígonos: {len(gdf_poligonos):,}")
print(f"✓ Incidentes: {len(df_incidentes):,}")
print(f"✓ Periodo: {df_incidentes['Timestamp'].min()} a {df_incidentes['Timestamp'].max()}")

# =============================================
# INICIALIZAR APP DASH
# =============================================

app = dash.Dash(__name__)
app.title = "Índice Delictivo Hermosillo"

# =============================================
# LAYOUT DEL DASHBOARD
# =============================================

app.layout = html.Div([
    html.Div([
        html.H1("🚨 Índice Delictivo Hermosillo 2018-2025", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
        html.H4("Mapa Interactivo con Control Temporal", 
                style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': 0}),
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
    
    # =============================================
    # PANEL DE CONTROLES
    # =============================================
    html.Div([
        html.Div([
            html.Label("🔍 Modo de Visualización:", style={'fontWeight': 'bold', 'marginBottom': 5}),
            dcc.RadioItems(
                id='modo-visualizacion',
                options=[
                    {'label': ' Calor: Total de incidentes por polígono', 'value': 'total'},
                    {'label': ' Calor: Tasa per 1k habitantes', 'value': 'tasa'},
                    {'label': ' Calor: Índice de riesgo', 'value': 'riesgo'},
                    {'label': ' Severidad: Alta/Media/Baja', 'value': 'severidad'},
                    {'label': ' Puntos: Incidentes individuales', 'value': 'puntos'},
                ],
                value='total',
                style={'marginBottom': 15}
            ),
        ], style={'width': '100%', 'marginBottom': 20}),
        
        html.Div([
            # Año
            html.Div([
                html.Label("📅 Año:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-año',
                    options=[{'label': 'Todos', 'value': 'todos'}] + 
                            [{'label': str(año), 'value': año} for año in sorted(df_incidentes['Año'].unique())],
                    value='todos',
                    clearable=False
                ),
            ], style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # Mes
            html.Div([
                html.Label("📆 Mes:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-mes',
                    options=[{'label': 'Todos', 'value': 'todos'}] + 
                            [{'label': f"{m:02d}", 'value': m} for m in range(1, 13)],
                    value='todos',
                    clearable=False
                ),
            ], style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # Día
            html.Div([
                html.Label("🗓️ Día:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-dia',
                    options=[{'label': 'Todos', 'value': 'todos'}] + 
                            [{'label': f"{d:02d}", 'value': d} for d in range(1, 32)],
                    value='todos',
                    clearable=False
                ),
            ], style={'width': '23%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # Hora
            html.Div([
                html.Label("🕐 Hora:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-hora',
                    options=[{'label': 'Todas', 'value': 'todas'}] + 
                            [{'label': f"{h:02d}:00", 'value': h} for h in range(24)],
                    value='todas',
                    clearable=False
                ),
            ], style={'width': '23%', 'display': 'inline-block'}),
        ], style={'marginBottom': 20}),
        
        html.Div([
            # Categoría
            html.Div([
                html.Label("🏷️ Categoría:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-categoria',
                    options=[{'label': 'Todas', 'value': 'todas'}] + 
                            [{'label': cat, 'value': cat} for cat in sorted(df_incidentes['Categoria_Incidente'].unique())],
                    value='todas',
                    clearable=False
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
            
            # Severidad
            html.Div([
                html.Label("⚠️ Severidad:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='filtro-severidad',
                    options=[{'label': 'Todas', 'value': 'todas'}, 
                            {'label': 'ALTA', 'value': 'ALTA'},
                            {'label': 'MEDIA', 'value': 'MEDIA'},
                            {'label': 'BAJA', 'value': 'BAJA'}],
                    value='todas',
                    clearable=False
                ),
            ], style={'width': '48%', 'display': 'inline-block'}),
        ], style={'marginBottom': 20}),
        
        # Slider de rango de fechas
        html.Div([
            html.Label("📊 Rango de Fechas:", style={'fontWeight': 'bold', 'marginBottom': 10}),
            dcc.RangeSlider(
                id='slider-fechas',
                min=0,
                max=len(df_incidentes['FechaStr'].unique()) - 1,
                step=1,
                value=[0, len(df_incidentes['FechaStr'].unique()) - 1],
                marks={
                    0: df_incidentes['Timestamp'].min().strftime('%Y-%m'),
                    len(df_incidentes['FechaStr'].unique()) - 1: df_incidentes['Timestamp'].max().strftime('%Y-%m')
                },
                tooltip={"placement": "bottom", "always_visible": False}
            ),
        ], style={'marginBottom': 20}),
        
    ], style={
        'backgroundColor': '#ffffff',
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    }),
    
    # =============================================
    # ESTADÍSTICAS DINÁMICAS
    # =============================================
    html.Div(id='estadisticas-panel', style={
        'backgroundColor': '#ffffff',
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    }),
    
    # =============================================
    # MAPA PRINCIPAL
    # =============================================
    dcc.Graph(
        id='mapa-principal',
        style={'height': '700px'},
        config={'displayModeBar': True, 'scrollZoom': True}
    ),
    
    # =============================================
    # GRÁFICAS AUXILIARES
    # =============================================
    html.Div([
        html.Div([
            dcc.Graph(id='grafica-temporal')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafica-categorias')
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ], style={'marginTop': '20px'}),
    
], style={'padding': '20px', 'backgroundColor': '#f5f5f5'})

# =============================================
# CALLBACKS
# =============================================

@app.callback(
    [Output('mapa-principal', 'figure'),
     Output('estadisticas-panel', 'children'),
     Output('grafica-temporal', 'figure'),
     Output('grafica-categorias', 'figure')],
    [Input('modo-visualizacion', 'value'),
     Input('filtro-año', 'value'),
     Input('filtro-mes', 'value'),
     Input('filtro-dia', 'value'),
     Input('filtro-hora', 'value'),
     Input('filtro-categoria', 'value'),
     Input('filtro-severidad', 'value'),
     Input('slider-fechas', 'value')]
)
def actualizar_visualizacion(modo, año, mes, dia, hora, categoria, severidad, rango_fechas):
    """Actualizar mapa y gráficas según filtros"""
    
    # FILTRAR INCIDENTES
    df_filtrado = df_incidentes.copy()
    
    if año != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Año'] == año]
    if mes != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
    if dia != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Dia'] == dia]
    if hora != 'todas':
        df_filtrado = df_filtrado[df_filtrado['Hora'] == hora]
    if categoria != 'todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria_Incidente'] == categoria]
    if severidad != 'todas':
        df_filtrado = df_filtrado[df_filtrado['Nivel_Severidad'] == severidad]
    
    # PANEL DE ESTADÍSTICAS
    stats = html.Div([
        html.Div([
            html.H3(f"{len(df_filtrado):,}", style={'color': '#e74c3c', 'margin': 0}),
            html.P("Incidentes", style={'margin': 0}),
        ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
        
        html.Div([
            html.H3(f"{df_filtrado['CVE_COL'].nunique():,}", style={'color': '#3498db', 'margin': 0}),
            html.P("Colonias Afectadas", style={'margin': 0}),
        ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
        
        html.Div([
            html.H3(f"{(df_filtrado['Nivel_Severidad']=='ALTA').sum():,}", style={'color': '#e67e22', 'margin': 0}),
            html.P("Alta Severidad", style={'margin': 0}),
        ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
        
        html.Div([
            html.H3(f"{df_filtrado['Timestamp'].min().strftime('%Y-%m-%d') if len(df_filtrado) > 0 else 'N/A'}", 
                   style={'color': '#2ecc71', 'margin': 0, 'fontSize': '20px'}),
            html.P("Fecha Inicio", style={'margin': 0}),
        ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
        
        html.Div([
            html.H3(f"{df_filtrado['Timestamp'].max().strftime('%Y-%m-%d') if len(df_filtrado) > 0 else 'N/A'}", 
                   style={'color': '#9b59b6', 'margin': 0, 'fontSize': '20px'}),
            html.P("Fecha Fin", style={'margin': 0}),
        ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
    ])
    
    # CREAR MAPA
    fig_mapa = go.Figure()
    
    if modo == 'puntos':
        # Modo puntos: incidentes individuales
        if len(df_filtrado) > 0:
            color_map = {'ALTA': '#e74c3c', 'MEDIA': '#f39c12', 'BAJA': '#3498db'}
            df_filtrado['color'] = df_filtrado['Nivel_Severidad'].map(color_map)
            
            fig_mapa.add_trace(go.Scattermapbox(
                lat=df_filtrado['LATITUD'],
                lon=df_filtrado['LONGITUD'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df_filtrado['color'],
                    opacity=0.6
                ),
                text=df_filtrado.apply(lambda x: f"<b>{x['COLONIA_POLIGONO']}</b><br>" +
                                                  f"{x['TIPO DE INCIDENTE']}<br>" +
                                                  f"Severidad: {x['Nivel_Severidad']}<br>" +
                                                  f"{x['Timestamp'].strftime('%Y-%m-%d %H:%M')}", axis=1),
                hoverinfo='text',
                name='Incidentes'
            ))
    else:
        # Modo polígonos: mapa de calor
        # Agregar incidentes filtrados por polígono
        agg_filtrado = df_filtrado.groupby('CVE_COL').agg({
            'TIPO DE INCIDENTE': 'count',
            'Nivel_Severidad': [
                ('alta', lambda x: (x == 'ALTA').sum()),
                ('media', lambda x: (x == 'MEDIA').sum()),
                ('baja', lambda x: (x == 'BAJA').sum())
            ]
        })
        agg_filtrado.columns = ['total_filtrado', 'alta', 'media', 'baja']
        agg_filtrado = agg_filtrado.reset_index()
        
        # Unir con polígonos
        gdf_temp = gdf_poligonos.merge(agg_filtrado, on='CVE_COL', how='left')
        gdf_temp['total_filtrado'] = gdf_temp['total_filtrado'].fillna(0)
        
        # Elegir métrica según modo
        if modo == 'total':
            gdf_temp['valor'] = gdf_temp['total_filtrado']
            colorbar_title = "Incidentes"
            colorscale = "Reds"
        elif modo == 'tasa':
            gdf_temp['valor'] = gdf_temp['tasa_incidentes_per_1k']
            colorbar_title = "Tasa per 1k hab"
            colorscale = "YlOrRd"
        elif modo == 'riesgo':
            gdf_temp['valor'] = gdf_temp['indice_riesgo']
            colorbar_title = "Índice Riesgo"
            colorscale = "Plasma"
        elif modo == 'severidad':
            # Calcular score de severidad para filtrados
            gdf_temp['valor'] = (
                (gdf_temp['alta'].fillna(0) * 3 + 
                 gdf_temp['media'].fillna(0) * 2 + 
                 gdf_temp['baja'].fillna(0) * 1) / 
                gdf_temp['total_filtrado'].replace(0, 1)
            )
            colorbar_title = "Score Severidad"
            colorscale = "Inferno"
        
        # Convertir a GeoJSON
        geojson = json.loads(gdf_temp.to_json())
        
        # Agregar choropleth
        fig_mapa.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=gdf_temp.index,
            z=gdf_temp['valor'],
            colorscale=colorscale,
            marker_opacity=0.6,
            marker_line_width=1,
            marker_line_color='white',
            colorbar=dict(title=colorbar_title),
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                         f'{colorbar_title}: ' + '%{z:.2f}<br>' +
                         'Población: %{customdata[1]:,}<br>' +
                         'Incidentes (filtrados): %{customdata[2]:,}<br>' +
                         '<extra></extra>',
            customdata=gdf_temp[['COLONIA', 'poblacion_total', 'total_filtrado']].values
        ))
    
    # Layout del mapa
    fig_mapa.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=29.0892, lon=-110.9615),
            zoom=10.5
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    
    # GRÁFICA TEMPORAL
    if len(df_filtrado) > 0:
        temporal = df_filtrado.groupby(df_filtrado['Timestamp'].dt.to_period('D')).size().reset_index()
        temporal.columns = ['Periodo', 'Incidentes']
        temporal['Periodo'] = temporal['Periodo'].dt.to_timestamp()
        
        fig_temporal = px.line(
            temporal, 
            x='Periodo', 
            y='Incidentes',
            title='Serie Temporal de Incidentes'
        )
        fig_temporal.update_traces(line_color='#e74c3c')
    else:
        fig_temporal = go.Figure()
        fig_temporal.add_annotation(text="No hay datos para mostrar", showarrow=False, 
                                   xref="paper", yref="paper", x=0.5, y=0.5)
    
    fig_temporal.update_layout(height=300, margin=dict(l=40, r=40, t=40, b=40))
    
    # GRÁFICA CATEGORÍAS
    if len(df_filtrado) > 0:
        categorias = df_filtrado['Categoria_Incidente'].value_counts().head(10).reset_index()
        categorias.columns = ['Categoria', 'Cantidad']
        
        fig_categorias = px.bar(
            categorias,
            x='Cantidad',
            y='Categoria',
            orientation='h',
            title='Top 10 Categorías de Incidentes'
        )
        fig_categorias.update_traces(marker_color='#3498db')
    else:
        fig_categorias = go.Figure()
        fig_categorias.add_annotation(text="No hay datos para mostrar", showarrow=False,
                                     xref="paper", yref="paper", x=0.5, y=0.5)
    
    fig_categorias.update_layout(height=300, margin=dict(l=40, r=40, t=40, b=40))
    
    return fig_mapa, stats, fig_temporal, fig_categorias


# =============================================
# EJECUTAR APP
# =============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 INICIANDO DASHBOARD")
    print("="*70)
    print("\nAbriendo en: http://127.0.0.1:8050/")
    print("Presiona Ctrl+C para detener\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)
