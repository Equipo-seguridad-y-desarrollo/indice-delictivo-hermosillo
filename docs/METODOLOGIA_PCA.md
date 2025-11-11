# 📊 Resumen Ejecutivo - Análisis de Componentes Principales (PCA)

## Proyecto: Índice Delictivo Hermosillo
**Fecha**: noviembre de 2025
**Herramienta Central**: Análisis de Componentes Principales (PCA)
**Estado**: Análisis Cuantitativo y Visualización Interesactiva ✅

---

## 1. ⚙️ Metodología: De Datos Crudos a Índices Ponderados

El objetivo del proceso fue simplificar la complejidad de 198 tipos de incidentes estandarizados por colonia en solo 8 índices significativos y un Score Compuesto para el mapeo.

### A. Pipeline de Preparación de Datos

| Paso | Datos de Entrada | Transformación Principal | Objetivo |
| :--- | :--- | :--- | :--- |
| **1. Agregación** | 2.3M Reportes (2018-2025) | Conteo de incidentes por Colonia. | Crear la matriz base de actividad delictiva (2297 Colonias x 198 Incidentes). |
| **2. Normalización** | Matriz de Frecuencia + Demografía | Cálculo de **Tasas de Incidencia** (por 100k habitantes/año). | Eliminar el sesgo de tamaño poblacional de las colonias. |
| **3. Estandarización** | Matriz de Tasas | Escalamiento ($\mu=0$, $\sigma=1$). | Preparar los datos para el PCA, garantizando la equidad de peso entre variables. |

---

## 2. 📈 PCA y Resultados Cuantitativos

El PCA se ejecutó para reducir la dimensionalidad y generar los índices finales.

### A. Ejecución PCA y Reducción Dimensional

| Métrica | Valor | Decisión |
| :--- | :--- | :--- |
| **Dimensionalidad Original** | 198 tipos de incidente | |
| **Número Óptimo de CPs** | **8 Componentes (CP1 - CP8)** | Determinado por el **Gráfico de Codo (Scree Plot)** para superar el 75% de la varianza. |
| **Varianza Retenida** | **~80.0%** | La información de 198 variables se resume en solo 8 índices. |

### B. Archivos de Salida Generados

| Archivo | Contenido | Uso Principal |
| :--- | :--- | :--- |
| **`colonias_pca_puntuaciones.csv`** | **2,297 Colonias** x **8 Columnas (CP1...CP8)**. | Fuente de datos para colorear el mapa. |
| **`colonias_pca_cargas_componentes.csv`** | **8 Filas (CP1...CP8)** x **198 Columnas (Incidentes)**. | Diccionario para la interpretación y nombramiento de los índices. |

---

## 3. 🗺️ Análisis Cualitativo y Nombramiento de Índices

El análisis de cargas identificó el perfil dominante de cada Componente Principal.

### A. Los 8 Perfiles Delictivos (CPs)

| CP | Cargas Positivas Dominantes | Nombre Interpretado |
| :--- | :--- | :--- |
| **CP1** | Emergencias Médicas, Accidente Vehicular, Abuso de Autoridad. | **Índice de Demanda de Emergencia General** |
| **CP2** | Extorsión Telefónica, Concentración Pacífica, Alteración por Alcohol. | **Índice de Desorden Público y Alertas** |
| **CP3** | Mordedura de Animal, Corrupción de Menores, Violación. | **Índice de Riesgo Social y Vulnerabilidad** |
| **CP4** | **Violación**, Caída de Barda, Vehículo en Huida. | **Índice de Delitos Sexuales y Riesgo Estructural** |
| **CP5** | Incendio en Escuela, Derrumbes, Infarto/Urgencia Cardiológica. | **Índice de Riesgo Físico y Fallas de Infraestructura** |
| **CP6** | Derrumbes, Incendio en Escuela, Epidemias, Restos Humanos. | **Índice de Riesgo Ambiental y Hallazgos** |
| **CP7** | Explotación de Menores, Quema Urbana, Venta Clandestina. | **Índice de Delitos de Explotación y Riesgo Regulatorio** |
| **CP8** | **Enfrentamiento de Grupos Armados**, Incendio de Residuos. | **Índice de Violencia Organizada y Contaminación** |

---

## 4. 💻 Dashboard y Visualización Interesactiva

Los resultados del PCA se integraron en la aplicación web **Dash/Plotly** para su visualización interactiva.

### A. Implementación en el Panel de Control

| Opción de Visualización | Función |
| :--- | :--- |
| **`PCA: Perfil Delictivo (Seleccionar Abajo)`** | Única opción de radio que activa un **Dropdown** para elegir entre los 8 CPs (CP1 a CP8). |
| **Mapeo** | El mapa de calor se colorea según la puntuación de la colonia en el CP seleccionado (ej., seleccionar CP4 muestra dónde se concentra el riesgo de Delitos Sexuales). |
| **Filtrado** | Todos los filtros temporales (Año, Mes, Hora) y categóricos siguen siendo funcionales, aunque la puntuación del PCA es un score histórico (no filtrado por fecha). |

### B. Beneficio de la Consolidación

La consolidación de los 8 CPs bajo una única opción de menú mejora la **usabilidad** del *dashboard* y permite al usuario enfocar la visualización en un perfil de riesgo específico sin saturar la interfaz.

---
# 📚 Documentación de Perfiles - Componentes Principales (PCA)
## Proyecto: Índice Delictivo Hermosillo
**Archivo Fuente de Datos**: `colonias_pca_cargas_componentes.csv`
**Fecha de Análisis**:noviembre de 2025
**Metodología**: PCA (8 Componentes Retenidos, 80% de Varianza Explicada)

---

## 🧭 Guía de Interpretación

Cada Componente Principal (CP) representa un **eje de varianza** que agrupa tipos de incidentes que históricamente ocurren juntos. La **Carga** (Peso) indica la fuerza y la dirección de la correlación:

* **Carga Positiva Alta (✨):** El incidente *define* y *impulsa* la puntuación del índice.
* **Carga Negativa Alta (📉):** El incidente es *raro* o *inverso* al patrón que define el índice.

---

## 1. CP1: Índice de Demanda de Emergencia General (Cotidiano)

**Definición:** Este es el eje más general. Mide la **alta actividad de emergencias 911** que requiere respuesta inmediata (policial, médica o de tránsito), sin ser necesariamente un delito de alto impacto.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **OTROS INCIDENTES MÉDICOS TRAUMÁTICOS** | 0.094034 |
| ✨ **PERSONA INCONSCIENTE/URGENCIA NEUROLÓGICA** | 0.094022 |
| ✨ **ABUSO DE AUTORIDAD** | 0.093657 |
| ✨ **DAÑO A PROPIEDAD AJENA** | 0.093653 |
| ✨ **ACCIDENTE DE VEHÍCULO AUTOMOTOR CON LESIONADOS** | 0.093570 |
| ... | ... |
| 📉 **ROBO A EMPRESA DE TRASLADO DE VALORES** | -0.000100 |

---

## 2. CP2: Índice de Desorden Público y Alertas

**Definición:** Este eje capta el patrón de **alerta preventiva, desorden menor y fraude/extorsión no físico**. Se relaciona con colonias donde la actividad delictiva o social es ruidosa o basada en llamadas y reportes administrativos.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **DETECCIÓN DE VEHÍCULO CON REPORTE DE INCIDENTE PREVIO** | 0.168244 |
| ✨ **EXTORSIÓN TELEFÓNICA** | 0.168089 |
| ✨ **CONCENTRACIÓN PACÍFICA DE PERSONAS** | 0.166385 |
| ✨ **ALTERACIÓN DEL ORDEN PÚBLICO POR PERSONA ALCOHOLIZADA** | 0.165271 |
| ✨ **DAÑOS A PROPIEDAD AJENA** | 0.164972 |
| ... | ... |
| 📉 **ROBO DE COMBUSTIBLE O TOMA CLANDESTINA DE DUCTOS** | -0.110632 |

---

## 3. CP3: Índice de Riesgo Social y Vulnerabilidad

**Definición:** Este eje se enfoca en problemas de **violencia y riesgo dirigidos a víctimas vulnerables**, combinando la violencia sexual y la delincuencia de tránsito.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **MORDEDURA DE ANIMAL** | 0.306638 |
| ✨ **CORRUPCIÓN DE MENORES** | 0.272526 |
| ✨ **VIOLACIÓN** | 0.242204 |
| ✨ **ROBO A TRANSPORTISTA SIN VIOLENCIA** | 0.233466 |
| ✨ **VEHÍCULO EN HUIDA** | 0.231439 |
| ... | ... |
| 📉 **TALA ILEGAL** | -0.048347 |

---

## 4. CP4: Índice de Delitos Sexuales y Riesgo Estructural

**Definición:** Similar al CP3, pero con mayor énfasis en el **riesgo de violencia sexual** y un fuerte vínculo a la **vulnerabilidad estructural** o fallas de infraestructura, lo que podría indicar marginalidad o zonas de riesgo ambiental.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **CAÍDA DE BARDA** | 0.382187 |
| ✨ **VIOLACIÓN** | 0.315786 |
| ✨ **VEHÍCULO EN HUIDA** | 0.311496 |
| ✨ **ROBO A TRANSPORTISTA SIN VIOLENCIA** | 0.292075 |
| ✨ **CORRUPCIÓN DE MENORES** | 0.196869 |
| ... | ... |
| 📉 **RESTOS HUMANOS** | -0.230725 |

---

## 5. CP5: Índice de Riesgo Físico y Fallas de Infraestructura

**Definición:** Este eje agrupa incidentes relacionados con **fallas físicas, estructurales y urgencias médicas graves**, indicando colonias donde la infraestructura y el control de ruido son deficientes.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **INCENDIO EN ESCUELA** | 0.370623 |
| ✨ **DERRUMBES** | 0.360529 |
| ✨ **INFARTO/URGENCIA CARDIOLÓGICA** | 0.177198 |
| ✨ **ROBO DE PLACA** | 0.149292 |
| ✨ **RUIDO EXCESIVO** | 0.149138 |
| ... | ... |
| 📉 **EPIDEMIAS** | -0.304717 |

---

## 6. CP6: Índice de Riesgo Ambiental y Hallazgos

**Definición:** Eje muy específico que relaciona **riesgos estructurales/ambientales** con **hallazgos** (que pueden ser indicadores de actividad criminal oculta o eventos anómalos).

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **DERRUMBES** | 0.352431 |
| ✨ **INCENDIO EN ESCUELA** | 0.333456 |
| ✨ **EPIDEMIAS** | 0.222795 |
| ✨ **ROBO DE ANIMALES-MASCOTAS** | 0.210273 |
| ✨ **RESTOS HUMANOS** | 0.196646 |
| ... | ... |
| 📉 **INTOXICACIÓN ETÍLICA** | -0.215774 |

---

## 7. CP7: Índice de Delitos de Explotación y Riesgo Regulatorio

**Definición:** Este eje capta el patrón de **delitos contra la libertad de las personas (explotación)** junto con problemas de **orden público y fraude** que requieren intervención regulatoria o judicial.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **EXPLOTACIÓN DE MENORES** | 0.517787 |
| ✨ **QUEMA URBANA** | 0.489343 |
| ✨ **OTROS ACTOS RELACIONADOS CON OTROS BIENES JURÍDICOS** | 0.219800 |
| ✨ **VENTA CLANDESTINA DE PIROTECNIA** | 0.197110 |
| ✨ **FRAUDE** | 0.196940 |
| ... | ... |
| 📉 **AMENAZA DE ABORTO** | -0.158919 |

---

## 8. CP8: Índice de Violencia Organizada y Contaminación

**Definición:** Este es el eje más concentrado en la **violencia extrema** y eventos de **alto impacto ambiental/orden público**, sugiriendo la presencia de grupos organizados o actividad criminal sin control.

| Tipo de Incidente | Carga (Peso) |
| :--- | :--- |
| ✨ **ENFRENTAMIENTO DE GRUPOS ARMADOS** | 0.531123 |
| ✨ **INCENDIO DE RESIDUOS/BASURA** | 0.513380 |
| ✨ **SUSTRACCIÓN DE MENORES** | 0.136010 |
| ✨ **ROBO A CASA HABITACIÓN SIN VIOLENCIA** | 0.132190 |
| ✨ **ACCIDENTE DE VEHÍCULO DE PASAJEROS CON LESIONADOS** | 0.119013 |
| ... | ... |
| 📉 **AMENAZA DE BOMBA** | -0.319979 |