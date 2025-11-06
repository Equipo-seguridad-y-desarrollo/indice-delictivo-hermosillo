# main.py

import sys
from pathlib import Path

# --- 0. Definición de Rutas (Paths) ---
# BASE_DIR es la carpeta raíz del proyecto (donde está este 'main.py')
BASE_DIR = Path.cwd()

# Ruta a la carpeta que contiene tus scripts de funciones
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# Rutas para los datos
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
INTERIM_DATA_DIR = BASE_DIR / "data" / "interim"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# --- 1. Modificación de Ruta (Sys.Path) ---
# Le decimos a Python que también busque módulos en la carpeta 'notebooks'
# Esto nos permite importar los scripts de esa carpeta.
sys.path.append(str(NOTEBOOKS_DIR))

try:
    # --- 2. Importar Funciones (Después de modificar la ruta) ---
    from download_raw_data import fetch_and_consolidate_raw_data

    # Asumiendo que el script 'make_interim_data.py' contiene la función 'process_raw_to_interim'
    from make_interim_data import process_raw_to_interim
except ImportError as e:
    print(f"Error: No se pudieron importar las funciones desde la carpeta 'notebooks'.", file=sys.stderr)
    print("Asegúrate de que los archivos 'download_raw_data.py' y 'make_interim_data.py' existan en esa carpeta.", file=sys.stderr)
    print(f"Detalle del error: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    """
    Función principal que orquesta el pipeline de 2 etapas.
    """

    # --- ETAPA 1: OBTENER Y CONSOLIDAR DATOS RAW ---
    print("Iniciando Etapa 1: Descarga y consolidación de datos raw...")
    # (Esta función usará 'credentials.json' desde BASE_DIR, como está programada)
    raw_file_path = fetch_and_consolidate_raw_data(output_dir=RAW_DATA_DIR)

    if not raw_file_path:
        print("Fallo en la Etapa 1. El pipeline se ha detenido.")
        return # Detener ejecución si falla

    print("Etapa 1 completada.")

    # --- ETAPA 2: PROCESAMIENTO INTERIM (LIMPIEZA Y FEATURE ENG.) ---
    print("\nIniciando Etapa 2: Limpieza, Estandarización y Feature Engineering...")

    success_interim = process_raw_to_interim(
        input_dir=RAW_DATA_DIR,
        output_dir=INTERIM_DATA_DIR
    )

    if not success_interim:
        print("Fallo en la Etapa 2. El pipeline se ha detenido.")
        return # Detener ejecución si falla

    print("\nEtapa 2 (Interim) completada exitosamente.")
    print(f"Tus datos enriquecidos están en: {INTERIM_DATA_DIR}")


if __name__ == "__main__":
    main()