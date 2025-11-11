import geopandas as gpd
import folium
from pathlib import Path
import sys

def visualizar_shapefile(shp_path, nombre_capa="Polígonos", color="blue", output_html=None):
    """
    Visualiza un shapefile usando folium
    """
    try:
        # Cargar shapefile
        gdf = gpd.read_file(shp_path)
        print(f"✓ Shapefile cargado: {shp_path}")
        print(f"  - {len(gdf)} features")
        print(f"  - Columnas: {list(gdf.columns)}")
        print(f"  - CRS: {gdf.crs}")

        # Verificar si tiene geometría válida
        if gdf.empty:
            print("❌ El shapefile está vacío")
            return None

        # Crear mapa centrado en Hermosillo
        centro_hermosillo = [29.0892, -110.9615]
        m = folium.Map(location=centro_hermosillo, zoom_start=11)

        # Agregar capa del shapefile
        folium.GeoJson(
            gdf,
            name=nombre_capa,
            style_function=lambda x: {
                'fillColor': color,
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.3
            },
            tooltip=folium.GeoJsonTooltip(
                fields=list(gdf.columns[:5]),  # Mostrar primeras 5 columnas
                aliases=list(gdf.columns[:5]),
                localize=True
            )
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl().add_to(m)

        # Guardar mapa
        if output_html is None:
            output_html = f"visualizacion_{Path(shp_path).stem}.html"

        m.save(output_html)
        print(f"✓ Mapa guardado como: {output_html}")

        return m

    except Exception as e:
        print(f"❌ Error al procesar {shp_path}: {e}")
        return None

def main():
    print("="*60)
    print("VISUALIZADOR DE SHAPEFILES - HERMOSILLO")
    print("="*60)

    # Directorio de datos
    data_dir = Path(__file__).parent.parent / "data" / "raw"

    # Shapefiles disponibles
    shapefiles = {
        "colonias_imc2020.shp": {
            "nombre": "Colonias IMC 2020",
            "color": "green",
            "path": data_dir / "colonias_imc2020.shp"
        },
        "INE_Limpio.shp": {
            "nombre": "Datos INE",
            "color": "red",
            "path": data_dir / "INE_Limpio.shp"
        },
        "poligonos.shp": {
            "nombre": "Polígonos Generales",
            "color": "blue",
            "path": data_dir / "poligonos.shp"
        }
    }

    # Procesar cada shapefile
    for shp_file, config in shapefiles.items():
        if config["path"].exists():
            print(f"\n📁 Procesando: {shp_file}")
            print("-"*40)
            mapa = visualizar_shapefile(
                config["path"],
                config["nombre"],
                config["color"],
                f"mapa_{Path(shp_file).stem}.html"
            )
        else:
            print(f"❌ No encontrado: {config['path']}")

    print("\n" + "="*60)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("="*60)
    print("\n📂 Archivos HTML generados:")
    for shp_file in shapefiles.keys():
        html_file = f"mapa_{Path(shp_file).stem}.html"
        if Path(html_file).exists():
            print(f"   • {html_file}")

    print("\n🚀 Abre los archivos HTML en tu navegador para visualizar los datos")
    print("\n💡 Consejos:")
    print("   • Usa el control de capas para activar/desactivar visualizaciones")
    print("   • Haz click en los polígonos para ver información detallada")
    print("   • Usa zoom para explorar áreas específicas")

if __name__ == "__main__":
    main()