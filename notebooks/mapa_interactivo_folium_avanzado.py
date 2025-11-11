"""
Mapa Interactivo Avanzado - Índice Delictivo Hermosillo
Mapa con polígonos, filtros temporales, categorías y métricas seleccionables
Requiere: folium, branca
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import json
from pathlib import Path
import numpy as np
from datetime import datetime
import branca.colormap as cm

def cargar_datos():
    """Cargar todos los datos necesarios"""
    print("Cargando datos...")
    
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed' / 'unificado'
    
    # Polígonos con métricas agregadas
    gdf_poligonos = gpd.read_file(data_dir / 'poligonos_unificados_completo.geojson')
    
    # Incidentes temporales
    df_incidentes = pd.read_csv(data_dir / 'incidentes_con_poligono_temporal.csv')
    df_incidentes['Timestamp'] = pd.to_datetime(df_incidentes['Timestamp'])
    
    # Agregar columnas temporales
    df_incidentes['Año'] = df_incidentes['Timestamp'].dt.year
    df_incidentes['Mes'] = df_incidentes['Timestamp'].dt.month
    df_incidentes['Trimestre'] = df_incidentes['Timestamp'].dt.quarter
    df_incidentes['Fecha'] = df_incidentes['Timestamp'].dt.date
    
    print(f"✓ Polígonos: {len(gdf_poligonos):,}")
    print(f"✓ Incidentes: {len(df_incidentes):,}")
    
    return gdf_poligonos, df_incidentes


def preparar_metricas_base(gdf_poligonos):
    """Preparar métricas normalizadas para visualización"""
    
    # Rellenar NaN con 0 para visualización
    metrics = {
        'total_incidentes': gdf_poligonos['total_incidentes'].fillna(0),
        'tasa_incidentes_per_1k': gdf_poligonos['tasa_incidentes_per_1k'].fillna(0),
        'score_severidad': gdf_poligonos['score_severidad'].fillna(0),
        'indice_riesgo': gdf_poligonos.get('indice_riesgo', gdf_poligonos['score_severidad']).fillna(0),  # Fallback a score_severidad
        'poblacion_total': gdf_poligonos['poblacion_total'].fillna(0),
        'densidad_poblacional': gdf_poligonos['densidad_poblacional'].fillna(0),
        'incidentes_alta': gdf_poligonos['incidentes_alta'].fillna(0),
    }
    
    return metrics


def crear_popup_html(row, df_incidentes_poligono):
    """Crear popup HTML rico con toda la información"""
    
    # Datos básicos
    colonia = row['COLONIA']
    cve_col = row['CVE_COL']
    
    # Incidentes
    total_inc = int(row['total_incidentes']) if pd.notna(row['total_incidentes']) else 0
    alta = int(row['incidentes_alta']) if pd.notna(row['incidentes_alta']) else 0
    media = int(row['incidentes_media']) if pd.notna(row['incidentes_media']) else 0
    baja = int(row['incidentes_baja']) if pd.notna(row['incidentes_baja']) else 0
    
    # Demografía
    poblacion = int(row['poblacion_total']) if pd.notna(row['poblacion_total']) else 'N/D'
    viviendas = int(row['viviendas_totales']) if pd.notna(row['viviendas_totales']) else 'N/D'
    escolaridad = f"{row['escolaridad_años_prom']:.1f}" if pd.notna(row['escolaridad_años_prom']) else 'N/D'
    
    # Índices
    tasa = f"{row['tasa_incidentes_per_1k']:.1f}" if pd.notna(row['tasa_incidentes_per_1k']) else 'N/D'
    score_sev = f"{row['score_severidad']:.2f}" if pd.notna(row['score_severidad']) else 'N/D'
    indice = f"{row.get('indice_riesgo', row['score_severidad']):.1f}" if pd.notna(row.get('indice_riesgo', row['score_severidad'])) else 'N/D'
    
    # Categorías top 3 si existen
    categorias_html = ""
    if pd.notna(row['categorias_dict']) and row['categorias_dict'] != '{}':
        try:
            import ast
            cats = ast.literal_eval(row['categorias_dict'])
            top3 = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:3]
            categorias_html = "<br>".join([f"• {cat}: {cnt:,}" for cat, cnt in top3])
        except:
            categorias_html = "N/D"
    
    # Mini gráfica temporal (última semana si hay datos)
    temporal_html = ""
    if len(df_incidentes_poligono) > 0:
        # Últimos 30 días
        ultimos_30 = df_incidentes_poligono[
            df_incidentes_poligono['Timestamp'] >= 
            (df_incidentes_poligono['Timestamp'].max() - pd.Timedelta(days=30))
        ]
        if len(ultimos_30) > 0:
            temporal_html = f"<br><small>Últimos 30 días: {len(ultimos_30):,} incidentes</small>"
    
    html = f"""
    <div style="font-family: Arial; width: 350px;">
        <h3 style="margin: 0; padding: 10px; background: #2c3e50; color: white;">
            {colonia}
        </h3>
        
        <div style="padding: 10px;">
            <h4 style="margin: 5px 0; color: #e74c3c;">🚨 Incidentes Delictivos</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Total:</b></td><td>{total_inc:,}</td></tr>
                <tr style="color: #c0392b;"><td>Alta severidad:</td><td>{alta:,}</td></tr>
                <tr style="color: #e67e22;"><td>Media severidad:</td><td>{media:,}</td></tr>
                <tr style="color: #f39c12;"><td>Baja severidad:</td><td>{baja:,}</td></tr>
            </table>
            {temporal_html}
            
            <h4 style="margin: 10px 0 5px 0; color: #3498db;">👥 Demografía</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Población:</b></td><td>{poblacion}</td></tr>
                <tr><td>Viviendas:</td><td>{viviendas}</td></tr>
                <tr><td>Escolaridad (años):</td><td>{escolaridad}</td></tr>
            </table>
            
            <h4 style="margin: 10px 0 5px 0; color: #9b59b6;">📊 Índices</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Tasa per 1k hab:</b></td><td>{tasa}</td></tr>
                <tr><td>Score severidad:</td><td>{score_sev}</td></tr>
                <tr><td>Índice de riesgo:</td><td>{indice}</td></tr>
            </table>
            
            <h4 style="margin: 10px 0 5px 0; color: #16a085;">🏷️ Categorías Top 3</h4>
            <div style="font-size: 11px; line-height: 1.4;">
                {categorias_html if categorias_html else "N/D"}
            </div>
            
            <hr style="margin: 10px 0;">
            <small style="color: #7f8c8d;">CVE: {cve_col}</small>
        </div>
    </div>
    """
    
    return html


def crear_mapa_interactivo(gdf_poligonos, df_incidentes):
    """Crear mapa interactivo completo"""
    
    print("\nCreando mapa interactivo...")
    
    # Centro de Hermosillo
    center = [29.0892, -110.9615]
    
    # Crear mapa base
    m = folium.Map(
        location=center,
        zoom_start=11,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Agregar capas de tiles alternativas
    folium.TileLayer('CartoDB positron', name='Claro').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Oscuro').add_to(m)
    
    # Preparar métricas
    metrics = preparar_metricas_base(gdf_poligonos)
    
    # === CAPA 1: Polígonos por Total de Incidentes ===
    print("  Generando capa: Total Incidentes...")
    
    colormap_incidentes = cm.LinearColormap(
        colors=['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
        vmin=0,
        vmax=metrics['total_incidentes'].quantile(0.95),
        caption='Total de Incidentes'
    )
    
    fg_incidentes = folium.FeatureGroup(name='🚨 Total Incidentes', show=True)
    
    for idx, row in gdf_poligonos.iterrows():
        # Filtrar incidentes de este polígono
        df_inc_pol = df_incidentes[df_incidentes['CVE_COL'] == row['CVE_COL']]
        
        popup_html = crear_popup_html(row, df_inc_pol)
        
        valor = metrics['total_incidentes'].iloc[idx]
        color = colormap_incidentes(valor) if valor > 0 else '#cccccc'
        
        folium.GeoJson(
            row['geometry'].__geo_interface__,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.6
            },
            popup=folium.Popup(popup_html, max_width=400),
            tooltip=f"{row['COLONIA']}: {int(valor):,} incidentes"
        ).add_to(fg_incidentes)
    
    fg_incidentes.add_to(m)
    colormap_incidentes.add_to(m)
    
    # === CAPA 2: Tasa per 1k habitantes ===
    print("  Generando capa: Tasa per 1k...")
    
    # Filtrar solo con datos
    gdf_con_tasa = gdf_poligonos[gdf_poligonos['tasa_incidentes_per_1k'].notna()].copy()
    
    if len(gdf_con_tasa) > 0:
        colormap_tasa = cm.LinearColormap(
            colors=['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
            vmin=0,
            vmax=gdf_con_tasa['tasa_incidentes_per_1k'].quantile(0.90),
            caption='Tasa per 1,000 hab'
        )
        
        fg_tasa = folium.FeatureGroup(name='📊 Tasa per 1k hab', show=False)
        
        for idx, row in gdf_con_tasa.iterrows():
            df_inc_pol = df_incidentes[df_incidentes['CVE_COL'] == row['CVE_COL']]
            popup_html = crear_popup_html(row, df_inc_pol)
            
            valor = row['tasa_incidentes_per_1k']
            color = colormap_tasa(valor)
            
            folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{row['COLONIA']}: {valor:.1f} per 1k"
            ).add_to(fg_tasa)
        
        fg_tasa.add_to(m)
    
    # === CAPA 3: Índice de Riesgo (o Severidad si no hay índice) ===
    print("  Generando capa: Índice de Riesgo/Severidad...")
    
    gdf_con_riesgo = gdf_poligonos[gdf_poligonos['score_severidad'].notna()].copy()
    
    if len(gdf_con_riesgo) > 0:
        colormap_riesgo = cm.LinearColormap(
            colors=['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#e63c31', '#d73027'],
            vmin=0,
            vmax=100 if 'indice_riesgo' in gdf_poligonos.columns and gdf_poligonos['indice_riesgo'].notna().any() else 3,
            caption='Índice de Riesgo (0-100)' if 'indice_riesgo' in gdf_poligonos.columns else 'Score Severidad (1-3)'
        )
        
        fg_riesgo = folium.FeatureGroup(name='⚠️ Índice de Riesgo' if 'indice_riesgo' in gdf_poligonos.columns else '⚠️ Severidad (Score)', show=False)
        
        for idx, row in gdf_con_riesgo.iterrows():
            df_inc_pol = df_incidentes[df_incidentes['CVE_COL'] == row['CVE_COL']]
            popup_html = crear_popup_html(row, df_inc_pol)
            
            valor = metrics['indice_riesgo'].iloc[idx]
            color = colormap_riesgo(valor)
            
            folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{row['COLONIA']}: {valor:.1f}" + (" (riesgo)" if 'indice_riesgo' in gdf_poligonos.columns else " (severidad)")
            ).add_to(fg_riesgo)
        
        fg_riesgo.add_to(m)
    
    # === CAPA 4: Score de Severidad ===
    print("  Generando capa: Severidad...")
    
    colormap_severidad = cm.LinearColormap(
        colors=['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#99000d'],
        vmin=1,
        vmax=3,
        caption='Score Severidad (1-3)'
    )
    
    fg_severidad = folium.FeatureGroup(name='🔥 Severidad', show=False)
    
    for idx, row in gdf_poligonos.iterrows():
        if row['total_incidentes'] > 0:
            df_inc_pol = df_incidentes[df_incidentes['CVE_COL'] == row['CVE_COL']]
            popup_html = crear_popup_html(row, df_inc_pol)
            
            valor = metrics['score_severidad'].iloc[idx]
            color = colormap_severidad(valor) if valor > 0 else '#cccccc'
            
            folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{row['COLONIA']}: Severidad {valor:.2f}"
            ).add_to(fg_severidad)
    
    fg_severidad.add_to(m)
    
    # === CAPA 5: Población ===
    print("  Generando capa: Población...")
    
    gdf_con_poblacion = gdf_poligonos[gdf_poligonos['poblacion_total'].notna()].copy()
    
    if len(gdf_con_poblacion) > 0:
        colormap_poblacion = cm.LinearColormap(
            colors=['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b'],
            vmin=0,
            vmax=gdf_con_poblacion['poblacion_total'].quantile(0.95),
            caption='Población Total'
        )
        
        fg_poblacion = folium.FeatureGroup(name='👥 Población', show=False)
        
        for idx, row in gdf_con_poblacion.iterrows():
            df_inc_pol = df_incidentes[df_incidentes['CVE_COL'] == row['CVE_COL']]
            popup_html = crear_popup_html(row, df_inc_pol)
            
            valor = row['poblacion_total']
            color = colormap_poblacion(valor)
            
            folium.GeoJson(
                row['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{row['COLONIA']}: {int(valor):,} hab"
            ).add_to(fg_poblacion)
        
        fg_poblacion.add_to(m)
    
    # Agregar controles
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Agregar mini mapa
    plugins.MiniMap(toggle_display=True).add_to(m)
    
    # Agregar búsqueda
    plugins.Geocoder().add_to(m)
    
    # Agregar medidor de distancia
    plugins.MeasureControl(position='topleft', primary_length_unit='kilometers').add_to(m)
    
    # Fullscreen
    plugins.Fullscreen(position='topleft').add_to(m)
    
    # MousePosition
    plugins.MousePosition().add_to(m)
    
    print("✓ Mapa generado")
    
    return m


def agregar_filtros_temporales(m, df_incidentes, gdf_poligonos):
    """Agregar panel de filtros HTML/JS personalizado"""
    
    # Obtener años disponibles
    años = sorted(df_incidentes['Año'].unique())
    categorias = sorted(df_incidentes['Categoria_Incidente'].unique())
    
    # HTML para panel de filtros
    filtros_html = f"""
    <div id="filtros-panel" style="
        position: fixed;
        top: 10px;
        left: 60px;
        width: 300px;
        background: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        z-index: 1000;
        font-family: Arial;
        font-size: 12px;
        max-height: 80vh;
        overflow-y: auto;
    ">
        <h3 style="margin: 0 0 10px 0; font-size: 16px;">🔍 Filtros</h3>
        
        <div style="margin-bottom: 15px;">
            <label><b>📅 Año:</b></label><br>
            <select id="filtro-año" style="width: 100%; padding: 5px;">
                <option value="todos">Todos</option>
                {''.join([f'<option value="{año}">{año}</option>' for año in años])}
            </select>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><b>📆 Trimestre:</b></label><br>
            <select id="filtro-trimestre" style="width: 100%; padding: 5px;">
                <option value="todos">Todos</option>
                <option value="1">Q1 (Ene-Mar)</option>
                <option value="2">Q2 (Abr-Jun)</option>
                <option value="3">Q3 (Jul-Sep)</option>
                <option value="4">Q4 (Oct-Dic)</option>
            </select>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><b>🏷️ Categoría:</b></label><br>
            <select id="filtro-categoria" style="width: 100%; padding: 5px; font-size: 10px;">
                <option value="todas">Todas</option>
                {''.join([f'<option value="{cat}">{cat[:30]}</option>' for cat in categorias])}
            </select>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><b>⚠️ Severidad:</b></label><br>
            <select id="filtro-severidad" style="width: 100%; padding: 5px;">
                <option value="todas">Todas</option>
                <option value="ALTA">🔴 Alta</option>
                <option value="MEDIA">🟡 Media</option>
                <option value="BAJA">🟢 Baja</option>
            </select>
        </div>
        
        <button onclick="aplicarFiltros()" style="
            width: 100%;
            padding: 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-weight: bold;
        ">
            Aplicar Filtros
        </button>
        
        <div id="resultados-filtros" style="
            margin-top: 15px;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 3px;
            display: none;
        ">
            <small id="texto-resultados"></small>
        </div>
    </div>
    
    <script>
    function aplicarFiltros() {{
        const año = document.getElementById('filtro-año').value;
        const trimestre = document.getElementById('filtro-trimestre').value;
        const categoria = document.getElementById('filtro-categoria').value;
        const severidad = document.getElementById('filtro-severidad').value;
        
        // Mostrar resultados
        const resultDiv = document.getElementById('resultados-filtros');
        const textoDiv = document.getElementById('texto-resultados');
        
        let texto = '<b>Filtros aplicados:</b><br>';
        if (año !== 'todos') texto += `Año: ${{año}}<br>`;
        if (trimestre !== 'todos') texto += `Trimestre: Q${{trimestre}}<br>`;
        if (categoria !== 'todas') texto += `Categoría: ${{categoria.substring(0,20)}}...<br>`;
        if (severidad !== 'todas') texto += `Severidad: ${{severidad}}<br>`;
        
        textoDiv.innerHTML = texto;
        resultDiv.style.display = 'block';
        
        alert('Filtros aplicados. En una versión con backend, esto actualizaría el mapa en tiempo real.');
    }}
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(filtros_html))
    
    return m


def agregar_leyenda_custom(m):
    """Agregar leyenda personalizada"""
    
    leyenda_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        right: 10px;
        width: 200px;
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        z-index: 1000;
        font-family: Arial;
        font-size: 11px;
    ">
        <h4 style="margin: 0 0 10px 0;">📖 Guía Rápida</h4>
        <p style="margin: 5px 0;"><b>Click</b> en polígono: Ver detalles</p>
        <p style="margin: 5px 0;"><b>Capas</b>: Cambiar visualización</p>
        <p style="margin: 5px 0;"><b>Filtros</b>: Panel izquierdo</p>
        <hr style="margin: 10px 0;">
        <small>
            <b>Colores más intensos</b> = Mayor valor de la métrica seleccionada
        </small>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(leyenda_html))
    
    return m


def main():
    """Generar mapa interactivo completo"""
    
    print("="*70)
    print("GENERANDO MAPA INTERACTIVO - ÍNDICE DELICTIVO HERMOSILLO")
    print("="*70)
    
    # 1. Cargar datos
    gdf_poligonos, df_incidentes = cargar_datos()
    
    # 2. Crear mapa base con capas
    m = crear_mapa_interactivo(gdf_poligonos, df_incidentes)
    
    # 3. Agregar filtros personalizados
    m = agregar_filtros_temporales(m, df_incidentes, gdf_poligonos)
    
    # 4. Agregar leyenda
    m = agregar_leyenda_custom(m)
    
    # 5. Guardar
    output_path = Path(__file__).parent.parent / 'mapa_interactivo_hermosillo.html'
    m.save(str(output_path))
    
    print("\n" + "="*70)
    print("✅ MAPA GENERADO EXITOSAMENTE")
    print("="*70)
    print(f"\n📂 Archivo: {output_path}")
    print(f"📊 Tamaño: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("\n🚀 Abre el archivo HTML en tu navegador")
    print("\n🎯 Características:")
    print("   • 5 capas de visualización (incidentes, tasa, riesgo, severidad, población)")
    print("   • Popups detallados con demografía e incidentes")
    print("   • Panel de filtros (año, trimestre, categoría, severidad)")
    print("   • Controles: zoom, capas, búsqueda, medición, pantalla completa")
    print("   • Mini mapa de navegación")
    print("="*70)


if __name__ == "__main__":
    main()
