# src/data/get_raw_data.py

import pandas as pd
from pathlib import Path
import sys
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- Configuración (Actualizada) ---
FOLDER_ID = "1D6czfzLQZcUdn-oo2kJU5Vn4JjIgFdc4"
# -----------------------------------

# Ruta al archivo de credenciales
CREDENTIALS_PATH = Path.cwd() / "credentials.json"
# Alcances de la API (necesitamos 'drive')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
# Nombre del archivo de salida (Como lo pediste)
OUTPUT_FILE = "reportes_de_incidentes_2018_2025.csv"

def fetch_and_consolidate_raw_data(output_dir: Path):
    """
    Se conecta a la API de Google Drive, descarga todos los CSV
    de una carpeta, los consolida en un DataFrame y los guarda
    en el directorio 'raw'.
    """
    try:
        # 1. Autenticación
        print("Autenticando con Google Drive API...")
        if not CREDENTIALS_PATH.exists():
            print(f"Error: No se encuentra 'credentials.json' en {Path.cwd()}", file=sys.stderr)
            print("Por favor, asegúrate de que el archivo .json esté en la raíz del proyecto.", file=sys.stderr)
            return None

        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH), scopes=SCOPES)

        # 2. Construir el servicio de la API
        service = build('drive', 'v3', credentials=creds)

        # 3. Listar archivos en la carpeta
        print(f"Buscando archivos CSV en la carpeta (ID: {FOLDER_ID})...")

        query = f"'{FOLDER_ID}' in parents and mimeType='text/csv'"
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name)"
        ).execute()

        items = results.get('files', [])

        if not items:
            print("Error: No se encontraron archivos CSV en la carpeta.", file=sys.stderr)
            print("Verifica que la carpeta esté compartida con tu email de servicio.", file=sys.stderr)
            return None

        # 4. Descargar y consolidar cada archivo
        print(f"Se encontro el archivo. Iniciando descarga...")
        all_dfs = []

        for item in items:
            file_id = item['id']
            file_name = item['name']

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()

            fh.seek(0)

            try:
                df_sheet = pd.read_csv(io.StringIO(fh.read().decode('utf-8')))
            except UnicodeDecodeError:
                fh.seek(0)
                df_sheet = pd.read_csv(io.StringIO(fh.read().decode('latin1')))

            year = file_name.replace('.csv', '').split('_')[-1]
            df_sheet['Año_Reporte'] = year

            all_dfs.append(df_sheet)

        df_consolidado = pd.concat(all_dfs, ignore_index=True)

        print(f"Total de reportes: {len(df_consolidado)}")

        # 5. Guardar en 'raw'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / OUTPUT_FILE

        df_consolidado.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"Exito: Datos raw consolidados guardados en: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error durante el procesamiento: {e}", file=sys.stderr)
        return None

# --- Bloque de ejecución para pruebas ---
if __name__ == "__main__":
    """
    Este bloque solo se ejecuta cuando corres este archivo directamente
    """
    test_output_dir = Path.cwd() / "data" / "raw"
    fetch_and_consolidate_raw_data(output_dir=test_output_dir)