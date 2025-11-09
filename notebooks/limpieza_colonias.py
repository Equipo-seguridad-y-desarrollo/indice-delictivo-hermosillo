import pandas as pd
from fuzzywuzzy import process, fuzz
import chardet
import re
import unicodedata 

# --- 1. limpieza y encoding ---

def get_encoding(file_path):
    """Detecta la codificación de un archivo."""
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read(100000))
        encoding = result['encoding']
        print(f"Codificación detectada para {file_path}: {encoding}")
        return encoding
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {file_path}")
        return None
    except Exception as e:
        print(f"Error detectando encoding: {e}")
        return 'utf-8'

def limpiar_texto(texto):
    """Limpia y estandariza un string para una mejor comparación."""
    if not isinstance(texto, str):
        return ""
    
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = texto.upper().strip()
    texto = re.sub(r'^(COLONIA|COL|FRACCIONAMIENTO|FRACC|RESIDENCIAL|RES|PRIVADA|PRIV)\s+', '', texto)
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def main():
    # --- 2. Carga y Preparación de Datos ---

    # Asumiendo que tus archivos de salida van al mismo directorio que el de entrada
    data_path = r"..\data\raw"
    file_path = fr"{data_path}\213.csv" 
    encoding = get_encoding(file_path)

    if encoding is None:
        return

    try:
        df_delitos = pd.read_csv(file_path, encoding=encoding, low_memory=False)
        print(f"Archivo '{file_path}' cargado exitosamente.")
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return

    # Guardamos la columna original antes de limpiarla
    df_delitos['Colonia_Original'] = df_delitos['COLONIA'].fillna('SIN INFORMACION')

    df_delitos['Colonia_Limpia'] = df_delitos['Colonia_Original'].apply(limpiar_texto)
    target_colonias = df_delitos['Colonia_Limpia'].dropna().unique()
    target_colonias.sort() 

    print(f"Se encontraron {len(target_colonias)} variaciones de colonias (limpias).")

    # --- 3. Lógica de Agrupación (Fuzzy Matching contra el mismo archivo) ---

    mapping_limpio_a_canonico = {}
    lista_canonica = [] 

    # --- CAMBIO 1: Umbral subido a 96 para diferenciar '4 DE MARZO' de '14 DE MARZO' 
    threshold = 96 

    print(f"Iniciando proceso de estandarización (umbral={threshold}%)...")

    for colonia in target_colonias:
        if not colonia or colonia == "SIN INFORMACION": 
            mapping_limpio_a_canonico[colonia] = "SIN INFORMACION"
            continue

        if not lista_canonica:
            lista_canonica.append(colonia)
            mapping_limpio_a_canonico[colonia] = colonia
            continue

        best_match, score = process.extractOne(colonia, lista_canonica, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            mapping_limpio_a_canonico[colonia] = best_match
        else:
            mapping_limpio_a_canonico[colonia] = colonia
            lista_canonica.append(colonia) 

    print(f"Proceso completado. Se agruparon en {len(lista_canonica)} colonias canónicas.")

    # --- 4. Crear y Guardar el Diccionario de Mapeo ---

    df_delitos['Colonia_Corregida'] = df_delitos['Colonia_Limpia'].map(mapping_limpio_a_canonico)

    diccionario_final = df_delitos[['Colonia_Original', 'Colonia_Corregida']].drop_duplicates()
    diccionario_final = diccionario_final.rename(columns={
        'Colonia_Original': 'Original', 
        'Colonia_Corregida': 'Corregida'
    })
    diccionario_final = diccionario_final.sort_values(by=['Corregida', 'Original'])

    # --- CAMBIO 2: Guardar el diccionario en la misma carpeta 'data\raw'
    output_dict_path = fr'{data_path}\diccionario_colonias.csv'
    try:
        diccionario_final.to_csv(output_dict_path, index=False, encoding='utf-8-sig')
        print(f"\nDiccionario de mapeo guardado en: {output_dict_path}")
    except Exception as e:
        print(f"Error al guardar el diccionario: {e}")

    # --- 5. Guardar el archivo corregido como 'delitos.csv' ---

    output_corrected_path = fr'{data_path}\delitos.csv' 

    try:
        # 1. Sobrescribe la columna original 'COLONIA' con los valores corregidos
        df_delitos['COLONIA'] = df_delitos['Colonia_Corregida']
        
        # 2. Crea un nuevo DataFrame final eliminando las columnas de ayuda
        df_final = df_delitos.drop(columns=['Colonia_Original', 'Colonia_Limpia', 'Colonia_Corregida'])
        
        # 3. Guarda el DataFrame limpio
        df_final.to_csv(output_corrected_path, index=False, encoding='utf-8-sig')
        
        print(f"Archivo con correcciones guardado en: {output_corrected_path}")
    except Exception as e:
        print(f"Error al guardar el archivo corregido: {e}")

if __name__ == '__main__':
    main()
