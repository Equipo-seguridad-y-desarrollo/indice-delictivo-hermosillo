import pandas as pd
from pathlib import Path
import sys

def main():

    url = "https://raw.githubusercontent.com/Sonora-en-Datos/ColoniasSonora/main/resultados/sonora_colonias_2020.csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"Error al descargar o leer el archivo CSV: {e}", file=sys.stderr)
        return

    print("Filtrando colonias de 'Hermosillo'...")
    df_col = df[df['nom_loc'] == 'Hermosillo'].copy() 

    print("Ordenando por 'poblacion_total' (descendente)...")
    df_col_sorted = df_col.sort_values(by='poblacion_total', ascending=False)

    try:
        project_root = Path(__file__).resolve().parent.parent
    except NameError:
        print("Advertencia: __file__ no está definido. Asumiendo CWD es 'notebooks/'.")
        project_root = Path.cwd().parent


    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "hermosillo_colonias_poblacion.csv"

    print(f"Creando directorio si no existe: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Se verifica si el archivo ya existe
    if output_file.exists():
        print(f"El archivo ya existe en: {output_file}. No se sobrescribirá.")
    else:
        # Si no existe, se guarda
        print(f"Guardando archivo en: {output_file}")
        df_col_sorted.to_csv(output_file, index=False)
    print("--- ¡Proceso completado exitosamente! ---")

if __name__ == "__main__":
    main()