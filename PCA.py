import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from difflib import get_close_matches
import numpy as np
import os
import sys
import matplotlib.pyplot as plt # Importar matplotlib

# =================================================================
# I. CONFIGURACIÓN Y FUNCIONES AUXILIARES
# =================================================================

# --- NÚMERO DE COMPONENTES DEFINITIVO ---
N_COMPONENTES_FINALES = 8
N_TOP_INCIDENTES = 5 # Para el análisis de cargas
UMBRAL_VARIANZA = 0.80 # Usaremos 80% para fines del gráfico de codo, aunque el resultado final es 8 CPs

# --- Rutas de Archivos (¡VERIFICA ESTA RUTA BASE!) ---
PROJECT_ROOT = r"C:\Users\cazar\Downloads\indice-delictivo-hermosillo" 

# Rutas de entrada
DATA_INPUT_DIR = os.path.join(PROJECT_ROOT, "data") 
RUTA_REPORTES = os.path.join(DATA_INPUT_DIR, "interim", "reportes_de_incidentes_procesados_2018_2025.csv")
RUTA_DEMOGRAFIA = os.path.join(DATA_INPUT_DIR, "processed", "demografia_hermosillo_limpio.csv")

# RUTA DE SALIDA CORREGIDA: Directorio raíz del proyecto
RUTA_OUTPUT_FINAL = PROJECT_ROOT / "data" / "processed" / "unificado"

# --- Función de Validación Inteligente de Columnas ---
def validar_columnas(df, columnas_esperadas, umbral_similitud=0.8):
    """Valida si las columnas existen o encuentra la coincidencia más cercana."""
    columnas_actuales = df.columns.tolist()
    columnas_corregidas = {}
    for esperada in columnas_esperadas:
        if esperada in columnas_actuales:
            columnas_corregidas[esperada] = esperada
        else:
            coincidencias = get_close_matches(esperada, columnas_actuales, n=1, cutoff=umbral_similitud)
            if coincidencias:
                print(f"⚠️ La columna '{esperada}' no se encontró. Usando '{coincidencias[0]}' como reemplazo.")
                columnas_corregidas[esperada] = coincidencias[0]
            else:
                raise ValueError(f"❌ No se encontró ninguna columna similar a '{esperada}' en el DataFrame.")
    return columnas_corregidas

# =================================================================
# II. CARGA, AGREGACIÓN Y ESTANDARIZACIÓN DE DATOS
# =================================================================

print("--- Iniciando Pipeline Completo de PCA (k=8) ---")

# Manejo de carga de datos
try:
    df_reportes = pd.read_csv(RUTA_REPORTES)
    df_demografia = pd.read_csv(RUTA_DEMOGRAFIA)
    print(f"DEBUG: Reportes: {df_reportes.shape[0]} filas. Demografía: {df_demografia.shape[0]} filas.")

    # A. Validación de columnas y asignación
    col_map_reportes = validar_columnas(df_reportes, ['COLONIA', 'TIPO DE INCIDENTE'])
    COLONIA_NORMALIZADA_COL = col_map_reportes['COLONIA']
    INCIDENTE_ESTANDARIZADO_COL = col_map_reportes['TIPO DE INCIDENTE']

    # B. Agregación de Frecuencias y Pivotaje
    print("\n[PASO 1/5] Creando matriz de tasas de incidencia...")
    df_conteo = (
        df_reportes.groupby([COLONIA_NORMALIZADA_COL, INCIDENTE_ESTANDARIZADO_COL])
        .size()
        .reset_index(name='Conteo')
    )
    df_matriz_incidentes = df_conteo.pivot_table(
        index=COLONIA_NORMALIZADA_COL, columns=INCIDENTE_ESTANDARIZADO_COL, values='Conteo', fill_value=0
    )
    columnas_incidentes = df_matriz_incidentes.columns.tolist()

    # C. Cálculo de Tasas (Normalización por Población)
    col_map_demo = validar_columnas(df_demografia, ['nom_col', 'poblacion_total'])
    df_demografia = df_demografia.rename(columns={col_map_demo['nom_col']: COLONIA_NORMALIZADA_COL, col_map_demo['poblacion_total']: 'Poblacion_2020'})

    df_matriz_final = df_matriz_incidentes.reset_index().merge(
        df_demografia[[COLONIA_NORMALIZADA_COL, 'Poblacion_2020']], on=COLONIA_NORMALIZADA_COL, how='left'
    )

    media_poblacion = df_demografia['Poblacion_2020'].mean()
    df_matriz_final['Poblacion_2020'] = df_matriz_final['Poblacion_2020'].fillna(media_poblacion).astype(int)

    periodo_años = 7.75
    for col in columnas_incidentes:
        df_matriz_final[col] = (df_matriz_final[col] / (df_matriz_final['Poblacion_2020'] * periodo_años)) * 100000

    X = df_matriz_final[columnas_incidentes].values

    # D. Estandarización de Datos
    print("[PASO 2/5] Estandarizando y preparando matriz para PCA...")
    X = np.where(np.isfinite(X), X, np.nan)
    imputer = SimpleImputer(strategy='mean')
    X = imputer.fit_transform(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print(f"✅ Matriz lista: {X_scaled.shape[0]} colonias x {X_scaled.shape[1]} incidentes/features.")

except Exception as e:
    print(f"Error fatal durante la preparación de datos: {e}")
    sys.exit(1)

# =================================================================
# III. APLICACIÓN Y VISUALIZACIÓN DEL PCA INICIAL
# =================================================================

# --- A. Ejecución Inicial del PCA (Todos los Componentes) ---
print("\n[PASO 3/5] Ejecutando PCA inicial y generando Gráfico de Codo...")
pca_inicial = PCA(n_components=None) 
pca_inicial.fit(X_scaled)

varianza_explicada = pca_inicial.explained_variance_ratio_
varianza_acumulada = np.cumsum(varianza_explicada)

# Determinar el número de CPs para el umbral deseado
n_componentes_optimo = np.where(varianza_acumulada >= UMBRAL_VARIANZA)[0][0] + 1
# Ya sabemos que este valor es 8, pero lo recalculamos para la gráfica
if n_componentes_optimo != N_COMPONENTES_FINALES:
    print(f"🚨 Advertencia: El umbral del {UMBRAL_VARIANZA*100}% requiere {n_componentes_optimo} CPs, pero usaremos {N_COMPONENTES_FINALES} según la configuración.")

# --- B. Generación del Gráfico de Codo (Scree Plot) ---
plt.figure(figsize=(10, 6))
plt.plot(range(1, len(varianza_explicada) + 1), varianza_acumulada, marker='o', linestyle='--', color='b')
plt.xlabel('Número de Componentes Principales')
plt.ylabel('Varianza Acumulada Explicada')
plt.title('Gráfico de Codo para PCA de Tasas de Incidencia')
plt.grid(True)
plt.axhline(y=varianza_acumulada[N_COMPONENTES_FINALES-1], color='g', linestyle='-', label=f'{N_COMPONENTES_FINALES} CPs ({varianza_acumulada[N_COMPONENTES_FINALES-1]*100:.2f}%)')
plt.axvline(x=N_COMPONENTES_FINALES, color='r', linestyle='--', label=f'{N_COMPONENTES_FINALES} CPs Seleccionados')
plt.legend()
plt.show() 

# =================================================================
# IV. APLICACIÓN DEL PCA FINAL (k=8) Y ANÁLISIS DE CARGAS
# =================================================================

# --- A. Aplicación del PCA con k=8 ---
k = N_COMPONENTES_FINALES 
print(f"\n[PASO 4/5] Aplicando PCA final con k={k} y transformando datos.")
pca_final = PCA(n_components=k) 
X_pca = pca_final.fit_transform(X_scaled)

# B. Creación del DataFrame de Puntuaciones (Los Índices)
nombres_cp = [f'CP{i+1}' for i in range(k)]
df_pca_puntuaciones = pd.DataFrame(data=X_pca, columns=nombres_cp)
df_pca_puntuaciones.insert(0, COLONIA_NORMALIZADA_COL, df_matriz_final[COLONIA_NORMALIZADA_COL].values)

# C. Creación del DataFrame de Cargas (La Interpretación)
df_cargas = pd.DataFrame(pca_final.components_, columns=columnas_incidentes, index=nombres_cp)

# D. Guardado de Resultados
try:
    df_pca_puntuaciones.to_csv(os.path.join(RUTA_OUTPUT_FINAL, 'colonias_pca_puntuaciones.csv'), index=False)
    df_cargas.to_csv(os.path.join(RUTA_OUTPUT_FINAL, 'colonias_pca_cargas_componentes.csv'))
except Exception as e:
    print(f"\n❌ ERROR AL GUARDAR ARCHIVOS: {e}")
    print("Verifica si los archivos están abiertos o si tienes permisos de escritura en la ruta.")
    sys.exit(1)


# =================================================================
# V. ANÁLISIS DE CARGAS DE LOS 8 CPS (INTEGRADO)
# =================================================================

print("\n[PASO 5/5] Analizando cargas de los 8 Componentes Principales...")

# 1. Iterar sobre todos los Componentes Principales
for cp_nombre in df_cargas.index:
    
    print(f"\n====================================================================")
    print(f"  🔍 ANALIZANDO {cp_nombre} (Eje de Varianza Explicada)")
    print(f"====================================================================")
    
    # Obtener las cargas de ese CP y ordenarlas
    cargas_ordenadas = df_cargas.loc[cp_nombre].sort_values(ascending=False)
    
    # a. Cargas Positivas (Incidentes que impulsan este índice)
    top_cargas_positivas = cargas_ordenadas.head(N_TOP_INCIDENTES)
    print(f"✨ Top {N_TOP_INCIDENTES} Incidentes Positivos (Definición del Eje):")
    print(top_cargas_positivas.to_string())
    
    # b. Cargas Negativas (Incidentes que están ausentes o son inversos en este índice)
    bottom_cargas_negativas = cargas_ordenadas.tail(N_TOP_INCIDENTES)
    print(f"\n📉 Top {N_TOP_INCIDENTES} Incidentes Negativos (Contrastes):")
    print(bottom_cargas_negativas.to_string())
    
    print("--------------------------------------------------------------------")
    
print("\n--- ✅ PROCESO COMPLETADO ---")
print(f"Archivos de resultados guardados en: {RUTA_OUTPUT_FINAL}")
print("¡Utiliza los datos impresos para nombrar tus 8 Índices Delictivos!")