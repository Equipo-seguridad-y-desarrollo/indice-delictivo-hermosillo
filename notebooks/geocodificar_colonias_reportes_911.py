"""
Script para obtener coordenadas de colonias usando Google Maps Geocoding API
Procesa el archivo de colonias únicas y genera un archivo con coordenadas
"""

import pandas as pd
import googlemaps
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path


# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configurar API key de Google Maps desde variable de entorno
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

if not API_KEY:
    raise ValueError(
        "❌ ERROR: No se encontró la variable de entorno GOOGLE_MAPS_API_KEY\n"
        "Por favor, crea un archivo .env en la raíz del proyecto con:\n"
        "GOOGLE_MAPS_API_KEY=tu_api_key_aqui"
    )

gmaps = googlemaps.Client(key=API_KEY)


def obtener_coordenadas_google(colonia, ciudad="Hermosillo", estado="Sonora", pais="México"):
    """
    Obtiene coordenadas y información de una colonia usando Google Maps Geocoding API
    
    Args:
        colonia: Nombre de la colonia
        ciudad: Ciudad (default: Hermosillo)
        estado: Estado (default: Sonora)
        pais: País (default: México)
    
    Returns:
        tuple: (dict con información de ubicación, tipo de resultado)
               tipo de resultado: 'success', 'not_found', 'error'
    """
    # Construir la dirección
    direccion = f"{colonia}, {ciudad}, {estado}, {pais}"
    
    try:
        # Geocodificar
        resultado = gmaps.geocode(direccion)
        
        if resultado:
            return resultado[0], 'success'
        else:
            print(f"  ⚠️  No se encontró: {colonia}")
            return None, 'not_found'
    except Exception as e:
        print(f"  ❌ Error con {colonia}: {e}")
        return None, 'error'


def procesar_colonias(archivo_colonias, archivo_salida, limite=None, delay=0.1):
    """
    Procesa el archivo de colonias únicas y obtiene coordenadas para cada una.
    Si el archivo de salida existe, solo procesa colonias nuevas (modo incremental).
    
    Args:
        archivo_colonias: Ruta al CSV con colonias únicas
        archivo_salida: Ruta donde guardar el resultado
        limite: Número máximo de colonias a procesar (None = todas)
        delay: Segundos de espera entre peticiones (para no exceder límites de API)
    """
    print("="*70)
    print("GEOCODIFICACIÓN DE COLONIAS - HERMOSILLO, SONORA")
    print("="*70)
    
    # Leer colonias únicas
    print(f"\n📂 Leyendo colonias desde: {archivo_colonias}")
    df_colonias = pd.read_csv(archivo_colonias)
    
    total_colonias = len(df_colonias)
    print(f"✓ Total de colonias en archivo: {total_colonias:,}")
    
    # Verificar si existe archivo de salida con geocodificaciones previas
    colonias_ya_geocodificadas = set()
    df_previas = None
    
    if os.path.exists(archivo_salida):
        print(f"\n[i] Archivo de salida ya existe: {archivo_salida}")
        df_previas = pd.read_csv(archivo_salida)
        colonias_ya_geocodificadas = set(df_previas['COLONIA'].unique())
        print(f"[i] Colonias ya geocodificadas: {len(colonias_ya_geocodificadas):,}")
        
        # Filtrar solo colonias nuevas
        df_colonias = df_colonias[~df_colonias['COLONIA'].isin(colonias_ya_geocodificadas)]
        
        if len(df_colonias) == 0:
            print(f"\n[OK] Todas las colonias ya están geocodificadas. No hay nada que procesar.")
            return df_previas, pd.DataFrame()  # Retornar DataFrame vacío como df_nuevas
        
        print(f"[i] Colonias nuevas a geocodificar: {len(df_colonias):,}")
    else:
        print(f"\n[i] No existe archivo previo. Geocodificando todas las colonias.")
    
    print(f"✓ Total de colonias a procesar ahora: {len(df_colonias):,}")
    
    if limite:
        df_colonias = df_colonias.head(limite)
        print(f"⚠️  Limitando a: {limite} colonias")
    
    # Preparar lista para resultados
    resultados = []
    exitosas = 0
    no_encontradas = 0
    errores = 0
    
    print(f"\n🌍 Iniciando geocodificación...")
    print(f"⏱️  Delay entre peticiones: {delay}s")
    print("-"*70)
    
    inicio = time.time()
    
    for contador, (idx, row) in enumerate(df_colonias.iterrows(), start=1):
        colonia = row['COLONIA']
        
        # Mostrar progreso cada 10 colonias
        if contador % 10 == 0:
            print(f"Procesando: {contador}/{len(df_colonias)} ({contador/len(df_colonias)*100:.1f}%)")
        
        # Obtener coordenadas
        info, tipo_resultado = obtener_coordenadas_google(colonia)
        
        if tipo_resultado == 'success':
            # Extraer información relevante
            location = info['geometry']['location']
            
            resultado = {
                'COLONIA': colonia,
                'LATITUD': location['lat'],
                'LONGITUD': location['lng'],
                'DIRECCION_FORMATEADA': info['formatted_address'],
                'TIPO_UBICACION': info['geometry']['location_type'],
                'PLACE_ID': info.get('place_id', ''),
                'TIPOS': ', '.join(info.get('types', [])),
                'TIMESTAMP': datetime.now().isoformat()
            }
            
            resultados.append(resultado)
            exitosas += 1
        elif tipo_resultado == 'not_found':
            # Registrar colonias no encontradas
            resultado = {
                'COLONIA': colonia,
                'LATITUD': None,
                'LONGITUD': None,
                'DIRECCION_FORMATEADA': 'NO ENCONTRADA',
                'TIPO_UBICACION': None,
                'PLACE_ID': None,
                'TIPOS': None,
                'TIMESTAMP': datetime.now().isoformat()
            }
            resultados.append(resultado)
            no_encontradas += 1
        else:  # tipo_resultado == 'error'
            # Registrar errores de API
            resultado = {
                'COLONIA': colonia,
                'LATITUD': None,
                'LONGITUD': None,
                'DIRECCION_FORMATEADA': 'ERROR',
                'TIPO_UBICACION': None,
                'PLACE_ID': None,
                'TIPOS': None,
                'TIMESTAMP': datetime.now().isoformat()
            }
            resultados.append(resultado)
            errores += 1
        
        # Delay para no exceder límites de la API
        time.sleep(delay)
    
    tiempo_total = time.time() - inicio
    
    # Crear DataFrame con resultados nuevos
    df_resultados_nuevos = pd.DataFrame(resultados)
    
    # Si había geocodificaciones previas, combinar con las nuevas
    if df_previas is not None:
        print(f"\n[i] Combinando {len(df_previas):,} geocodificaciones previas con {len(df_resultados_nuevos):,} nuevas")
        df_resultados = pd.concat([df_previas, df_resultados_nuevos], ignore_index=True)
    else:
        df_resultados = df_resultados_nuevos
    
    # Guardar resultados combinados
    print(f"\n💾 Guardando resultados en: {archivo_salida}")
    df_resultados.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE GEOCODIFICACIÓN")
    print("="*70)
    print(f"Colonias procesadas ahora: {len(df_colonias):,}")
    print(f"✓ Exitosas:                {exitosas:,} ({exitosas/len(df_colonias)*100 if len(df_colonias) > 0 else 0:.1f}%)")
    print(f"⚠️  No encontradas:         {no_encontradas:,} ({no_encontradas/len(df_colonias)*100 if len(df_colonias) > 0 else 0:.1f}%)")
    print(f"❌ Errores:                {errores:,}")
    if len(df_colonias) > 0:
        print(f"⏱️  Tiempo total:           {tiempo_total:.1f} segundos")
        print(f"⚡ Promedio:               {tiempo_total/len(df_colonias):.2f} seg/colonia")
    print("-"*70)
    print(f"Total en archivo final:    {len(df_resultados):,} colonias")
    print("="*70)
    
    # Mostrar colonias no encontradas si hay pocas
    if no_encontradas > 0 and no_encontradas <= 20:
        print("\n🔍 Colonias no encontradas en esta ejecución:")
        colonias_no_encontradas = df_resultados_nuevos[df_resultados_nuevos['LATITUD'].isna()]['COLONIA'].tolist()
        for col in colonias_no_encontradas:
            print(f"  - {col}")
    
    return df_resultados, df_resultados_nuevos


def main():
    # Rutas de archivos usando Path para resolver rutas absolutas
    project_root = Path(__file__).parent.parent
    archivo_colonias = project_root / 'data' / 'processed' / 'colonias_unicas_reportes_911.csv'
    archivo_salida = project_root / 'data' / 'processed' / 'colonias_reportes_911_con_coordenadas.csv'
    
    # Procesar colonias (modo incremental automático)
    print("\n🌍 GEOCODIFICACIÓN INCREMENTAL")
    print("   El script detectará automáticamente colonias ya geocodificadas")
    print("   y solo procesará las nuevas para ahorrar costos de API\n")
    
    df_resultados, df_nuevas = procesar_colonias(
        archivo_colonias=str(archivo_colonias),
        archivo_salida=str(archivo_salida),
        limite=None,  # None = procesar todas las colonias nuevas
        delay=0.2     # 0.2 segundos entre peticiones (más seguro)
    )
    
    # Mostrar ejemplos de resultados exitosos (solo de nuevas geocodificaciones)
    if len(df_nuevas) > 0:
        exitosos_nuevos = df_nuevas[df_nuevas['LATITUD'].notna()].head(10)
        
        if len(exitosos_nuevos) > 0:
            print("\n📍 EJEMPLOS DE COORDENADAS OBTENIDAS (nuevas):")
            print("-"*70)
            for _, row in exitosos_nuevos.iterrows():
                print(f"\n{row['COLONIA']}")
                print(f"  Lat: {row['LATITUD']:.6f}, Lng: {row['LONGITUD']:.6f}")
                print(f"  {row['DIRECCION_FORMATEADA']}")
    
    print("\n✅ Proceso completado!")
    print(f"📂 Archivo guardado: {archivo_salida}")
    print(f"📊 Total de colonias geocodificadas en archivo: {len(df_resultados):,}")



if __name__ == "__main__":
    main()
