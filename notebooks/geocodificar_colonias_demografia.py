"""
Script para obtener coordenadas de colonias de demografía usando Google Maps Geocoding API
Procesa el archivo de colonias únicas del dataset demográfico
"""

import pandas as pd
import googlemaps
import time
import os
from datetime import datetime
from dotenv import load_dotenv


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
    Procesa el archivo de colonias únicas y obtiene coordenadas para cada una
    
    Args:
        archivo_colonias: Ruta al CSV con colonias únicas
        archivo_salida: Ruta donde guardar el resultado
        limite: Número máximo de colonias a procesar (None = todas)
        delay: Segundos de espera entre peticiones (para no exceder límites de API)
    """
    print("="*70)
    print("GEOCODIFICACIÓN DE COLONIAS - DEMOGRAFÍA HERMOSILLO")
    print("="*70)
    
    # Leer colonias únicas
    print(f"\n📂 Leyendo colonias desde: {archivo_colonias}")
    df_colonias = pd.read_csv(archivo_colonias)
    
    total_colonias = len(df_colonias)
    print(f"✓ Total de colonias a procesar: {total_colonias:,}")
    
    # Limitar si se especifica
    if limite:
        df_colonias = df_colonias.head(limite)
        print(f"⚠️  Limitando a: {limite} colonias")
    
    print(f"\n🌍 Iniciando geocodificación...")
    print(f"⏱️  Delay entre peticiones: {delay}s")
    print("-"*70)
    
    # Almacenar resultados
    resultados = []
    exitosas = 0
    no_encontradas = 0
    errores = 0
    
    inicio = time.time()
    
    # Procesar cada colonia
    for idx, row in df_colonias.iterrows():
        colonia = row['nom_col']
        
        # Mostrar progreso cada 10 colonias
        if (idx + 1) % 10 == 0:
            print(f"Procesando: {idx + 1}/{len(df_colonias)} ({(idx+1)/len(df_colonias)*100:.1f}%)")
        
        # Obtener coordenadas
        info, tipo_resultado = obtener_coordenadas_google(colonia)
        
        if tipo_resultado == 'success':
            # Extraer información relevante
            location = info['geometry']['location']
            
            resultado = {
                'nom_col': colonia,
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
                'nom_col': colonia,
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
                'nom_col': colonia,
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
    
    # Crear DataFrame con resultados
    df_resultados = pd.DataFrame(resultados)
    
    # Guardar resultados
    print(f"\n💾 Guardando resultados en: {archivo_salida}")
    df_resultados.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE GEOCODIFICACIÓN")
    print("="*70)
    print(f"Total procesadas:     {len(df_colonias):,}")
    print(f"✓ Exitosas:           {exitosas:,} ({exitosas/len(df_colonias)*100:.1f}%)")
    print(f"⚠️  No encontradas:    {no_encontradas:,} ({no_encontradas/len(df_colonias)*100:.1f}%)")
    print(f"❌ Errores:           {errores:,}")
    print(f"⏱️  Tiempo total:      {tiempo_total:.1f} segundos")
    print(f"⚡ Promedio:          {tiempo_total/len(df_colonias):.2f} seg/colonia")
    print("="*70)
    
    # Mostrar colonias no encontradas si hay pocas
    if no_encontradas > 0 and no_encontradas <= 20:
        print("\n🔍 Colonias no encontradas:")
        colonias_no_encontradas = df_resultados[df_resultados['LATITUD'].isna()]['nom_col'].tolist()
        for col in colonias_no_encontradas:
            print(f"  - {col}")
    
    return df_resultados


def main():
    # Rutas de archivos
    archivo_colonias = '../data/processed/colonias_unicas_demografia.csv'
    archivo_salida = '../data/processed/colonias_demografia_con_coordenadas.csv'
    
    # Procesar todas las colonias
    print("\n🌍 GEOCODIFICACIÓN COMPLETA: Procesando todas las colonias")
    print("   Tiempo estimado: ~3-4 minutos (659 colonias)\n")
    
    df_resultados = procesar_colonias(
        archivo_colonias=archivo_colonias,
        archivo_salida=archivo_salida,
        limite=None,  # None = procesar todas las colonias
        delay=0.2     # 0.2 segundos entre peticiones (más seguro)
    )
    
    # Mostrar ejemplos de resultados exitosos
    print("\n📍 EJEMPLOS DE COORDENADAS OBTENIDAS:")
    print("-"*70)
    exitosos = df_resultados[df_resultados['LATITUD'].notna()].head(10)
    for _, row in exitosos.iterrows():
        print(f"\n{row['nom_col']}")
        print(f"  Lat: {row['LATITUD']:.6f}, Lng: {row['LONGITUD']:.6f}")
        print(f"  {row['DIRECCION_FORMATEADA']}")
    
    print("\n✅ Proceso completado!")
    print(f"📂 Archivo guardado: {archivo_salida}")


if __name__ == "__main__":
    main()
