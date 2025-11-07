# 🗂️ Mejores Prácticas para Manejo de Datos en Git

## ⚠️ REGLA DE ORO
**Nunca subas archivos de datos grandes (>10MB) directamente a Git**

Git no está diseñado para archivos grandes. Cada cambio duplica el archivo en el historial, haciendo el repositorio pesado e inmanejable.

---

## 📋 ESTRATEGIAS PROFESIONALES

### 1. **Git + .gitignore (Proyectos Pequeños/Medianos)**
✅ **Mejor para**: Proyectos con datos < 100MB, equipos pequeños

#### Configuración `.gitignore`
```gitignore
# Excluir archivos grandes de datos procesados
/data/raw/*.csv
/data/interim/*.csv
/data/processed/**/*.csv
/data/processed/**/*.geojson

# Permitir archivos pequeños de metadatos
!/data/**/.gitkeep
!/data/**/README.md

# Excluir visualizaciones pesadas
*.html
mapa_*.html
```

#### Estructura recomendada:
```
data/
├── raw/
│   ├── .gitkeep          ✅ Incluir en Git
│   ├── README.md         ✅ Incluir (documenta fuentes)
│   └── datos.csv         ❌ Excluir (archivo grande)
├── interim/
│   ├── .gitkeep          ✅ Incluir
│   └── procesado.csv     ❌ Excluir
└── processed/
    ├── .gitkeep          ✅ Incluir
    └── final.csv         ❌ Excluir
```

#### Scripts para reproducibilidad:
```python
# download_raw_data.py - ✅ INCLUIR EN GIT
"""
Script para descargar datos desde fuente original
"""
import requests
from pathlib import Path

def download_data():
    url = "https://huggingface.co/datasets/..."
    output = Path("data/raw/datos.csv")
    # ... código de descarga
```

---

### 2. **Git LFS (Large File Storage)**
✅ **Mejor para**: Archivos binarios grandes (modelos ML, imágenes, datos < 2GB)

#### Instalación:
```bash
# Instalar Git LFS
git lfs install

# Trackear tipos de archivo específicos
git lfs track "*.csv"
git lfs track "*.parquet"
git lfs track "*.h5"
git lfs track "*.pkl"

# Esto crea/actualiza .gitattributes
```

#### Ventajas:
- Los archivos grandes se almacenan en servidor externo
- Git solo guarda punteros (~100 bytes)
- Clonación más rápida

#### Desventajas:
- **GitHub LFS**: 1GB gratis, luego $5/mes por 50GB
- **GitLab LFS**: 10GB gratis
- Requiere configuración adicional

#### Ejemplo `.gitattributes`:
```
*.csv filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
```

---

### 3. **DVC (Data Version Control)** 🌟
✅ **Mejor para**: Proyectos de ML/Data Science profesionales, pipelines reproducibles

#### Instalación:
```bash
pip install dvc
dvc init

# Configurar almacenamiento remoto
dvc remote add -d myremote s3://mybucket/dvc-storage
# o Google Drive, Azure, SSH, etc.
```

#### Uso básico:
```bash
# Trackear archivo de datos
dvc add data/raw/datos.csv
# Esto crea data/raw/datos.csv.dvc (ESTE sí va a Git)

# Subir datos al storage remoto
dvc push

# Otro miembro del equipo puede obtener los datos
git clone <repo>
dvc pull  # Descarga los datos desde storage remoto
```

#### Pipeline reproducible:
```yaml
# dvc.yaml - Define tu pipeline
stages:
  download:
    cmd: python download_raw_data.py
    outs:
      - data/raw/reportes.csv
  
  process:
    cmd: python process_data.py
    deps:
      - data/raw/reportes.csv
    outs:
      - data/processed/clean_data.csv
  
  train:
    cmd: python train_model.py
    deps:
      - data/processed/clean_data.csv
    outs:
      - models/model.pkl
```

```bash
# Ejecutar todo el pipeline
dvc repro

# Ver diferencias en datos entre commits
dvc diff
```

#### Ventajas:
- Versionamiento de datos como si fuera código
- Pipelines reproducibles
- Soporta múltiples backends (S3, GCS, Azure, Drive, SSH)
- Gratuito y open-source
- Maneja archivos enormes (TB+)

#### Desventajas:
- Curva de aprendizaje
- Requiere configurar storage remoto

---

### 4. **Cloud Storage + Scripts de Descarga**
✅ **Mejor para**: Datos públicos, datasets enormes (GB-TB)

#### Fuentes comunes:
- **Hugging Face Datasets** (tu caso actual) ✅
- AWS S3 (con requester-pays o bucket público)
- Google Cloud Storage
- Azure Blob Storage
- Kaggle Datasets

#### Ejemplo con Hugging Face:
```python
# download_raw_data.py
from datasets import load_dataset
from pathlib import Path

def download_hermosillo_data():
    """Descarga datos desde Hugging Face"""
    dataset = load_dataset(
        "Equipo-seguridad-y-desarrollo/hermosillo-incidentes",
        split="train"
    )
    
    # Convertir a DataFrame y guardar
    df = dataset.to_pandas()
    output_path = Path("data/raw/reportes_de_incidentes_2018_2025.csv")
    df.to_csv(output_path, index=False)
    print(f"✓ Datos descargados: {output_path}")
    print(f"  Registros: {len(df):,}")

if __name__ == "__main__":
    download_hermosillo_data()
```

#### README.md con instrucciones:
```markdown
## Obtener los datos

Los datos NO están incluidos en el repositorio. Para obtenerlos:

1. Instala dependencias: `pip install -r requirements.txt`
2. Ejecuta: `python notebooks/download_raw_data.py`
3. Los datos se descargarán en `data/raw/`

**Fuente**: Hugging Face - Equipo-seguridad-y-desarrollo/hermosillo-incidentes
**Tamaño**: ~500MB (2.3M registros)
**Actualización**: Septiembre 2025
```

---

### 5. **Database + SQL Dumps**
✅ **Mejor para**: Datos estructurados, múltiples usuarios, consultas complejas

#### Setup:
```bash
# PostgreSQL local
pg_dump mydb > data/raw/dump.sql      # ❌ No incluir dump completo

# Solo esquema en Git
pg_dump --schema-only mydb > schema.sql  # ✅ Incluir esquema
```

#### Alternativa con seeds:
```python
# seed_database.py
import pandas as pd
from sqlalchemy import create_engine

def seed_from_cloud():
    """Carga datos desde cloud a DB local"""
    df = pd.read_csv("https://storage.url/data.csv")
    
    engine = create_engine('postgresql://localhost/mydb')
    df.to_sql('reportes', engine, if_exists='replace')
```

---

## 🎯 RECOMENDACIÓN PARA TU PROYECTO

### Situación Actual:
- Datos: 2.3M registros (~500MB CSV)
- Fuente: Hugging Face (público)
- Equipo: Pequeño
- Repositorio: GitHub

### ✅ Estrategia Recomendada: **Cloud Storage + Scripts**

#### Por qué:
1. **Ya tienes los datos en Hugging Face** ✅
2. **Datos son públicos** - cualquiera puede descargarlos
3. **No pagas por storage adicional** (HF es gratis)
4. **Reproducible** - `download_raw_data.py` automatiza la descarga
5. **Simple** - no requiere configuración compleja

#### Implementación:
```bash
# Ya lo tienes implementado:
notebooks/
├── download_raw_data.py          ✅ En Git
├── process_data.py               ✅ En Git
├── unificar_datos_poligonos.py   ✅ En Git
└── ...

data/
├── raw/
│   ├── .gitkeep                  ✅ En Git
│   ├── README.md                 ✅ En Git (documenta fuentes)
│   └── *.csv                     ❌ Excluido (.gitignore)
└── processed/
    ├── .gitkeep                  ✅ En Git
    └── *.csv                     ❌ Excluido (.gitignore)

.gitignore                        ✅ Configurado correctamente
requirements.txt                  ✅ En Git
```

#### Para colaboradores:
```bash
# 1. Clonar repo
git clone https://github.com/Equipo-seguridad-y-desarrollo/indice-delictivo-hermosillo.git

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar datos
python notebooks/download_raw_data.py

# 4. Ejecutar pipeline
python notebooks/unificar_datos_poligonos.py
python notebooks/mapa_interactivo_folium_avanzado.py

# 5. Abrir mapa
# mapa_interactivo_hermosillo.html
```

---

## 📊 COMPARACIÓN DE ESTRATEGIAS

| Estrategia | Costo | Complejidad | Tamaño Max | Mejor para |
|-----------|-------|------------|-----------|-----------|
| **.gitignore** | Gratis | ⭐ Baja | - | Datos generables |
| **Git LFS** | $5+/mes | ⭐⭐ Media | 2GB | Binarios (modelos) |
| **DVC** | Variable | ⭐⭐⭐ Alta | Ilimitado | ML profesional |
| **Cloud + Scripts** | Gratis* | ⭐ Baja | Ilimitado | Datos públicos |
| **Database** | Variable | ⭐⭐⭐ Alta | Ilimitado | Datos relacionales |

*Asumiendo storage gratuito o existente

---

## 🚀 EVOLUCIÓN DEL PROYECTO

### Actual (v4.0): Cloud + Scripts ✅
- Perfecto para tu etapa actual
- Colaboración simple
- Costo cero

### Futuro (si escala):
1. **Datos privados/sensibles** → DVC + S3 privado
2. **Actualizaciones frecuentes** → Database + API
3. **Modelos ML grandes** → Git LFS para modelos
4. **Pipeline complejo** → DVC pipelines

---

## 📝 CHECKLIST DE MEJORES PRÁCTICAS

### ✅ Implementado en tu proyecto:
- [x] `.gitignore` excluye archivos grandes
- [x] Scripts de descarga versionados
- [x] Pipeline de procesamiento reproducible
- [x] Documentación de fuentes de datos
- [x] Estructura de directorios estándar

### 🔄 Opcional para mejorar:
- [ ] Crear `data/raw/README.md` documentando fuentes
- [ ] Agregar checksums/hashes para validar descargas
- [ ] Implementar tests de calidad de datos
- [ ] Configurar CI/CD para validar pipeline
- [ ] Documentar tamaños esperados de archivos

---

## 🔗 RECURSOS ADICIONALES

### Documentación:
- **Git LFS**: https://git-lfs.github.com/
- **DVC**: https://dvc.org/doc
- **Hugging Face Datasets**: https://huggingface.co/docs/datasets

### Artículos:
- [How to Version Control Large Files](https://dagshub.com/blog/version-control-large-files/)
- [Managing ML Projects with DVC](https://realpython.com/python-data-version-control/)

### Alternativas:
- **Delta Lake** (datos tipo data warehouse)
- **LakeFS** (Git para data lakes)
- **Pachyderm** (data versioning + pipelines)

---

## 💡 RESUMEN EJECUTIVO

### Para tu proyecto Hermosillo:
1. **Mantén el enfoque actual**: Cloud (Hugging Face) + Scripts
2. **No subas CSVs grandes a Git** - ya está bien configurado
3. **Versioná scripts, no datos** - exactamente lo que hiciste
4. **Documenta fuentes** - agrega README en data/raw/
5. **Si crece el equipo/datos** - considera DVC

### Filosofía clave:
> "Git versiona el CÓDIGO que genera los datos, no los datos mismos"

Los datos son **artefactos reproducibles**, no código fuente.

---

**Última actualización**: 7 de noviembre de 2025  
**Versión del proyecto**: v4.0  
**Estrategia actual**: Cloud Storage + Scripts de descarga
