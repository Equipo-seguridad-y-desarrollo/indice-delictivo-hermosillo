# Backend - Índice Delictivo Hermosillo

API REST con SQLite para el mapa interactivo con filtros dinámicos.

## 📁 Estructura

```
backend/
├── database.py      # Configuración y carga de datos a SQLite
├── app.py           # API REST con Flask
├── queries.py       # Consultas SQL reutilizables
├── mapa_dinamico.html  # Frontend del mapa con filtros dinámicos
└── delitos_hermosillo.db  # Base de datos SQLite (generada)
```

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install flask flask-cors pandas geopandas
```

### 2. Crear la base de datos

```bash
cd backend
python database.py
```

Esto cargará los datos desde los CSV a SQLite (~200k+ registros).

### 3. Iniciar el servidor

```bash
python app.py
```

El servidor estará disponible en: `http://localhost:5000`

### 4. Abrir el mapa

Abre `mapa_dinamico.html` en tu navegador. El mapa se conectará automáticamente a la API.

## 📚 Endpoints de la API

### Filtros

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/filtros/opciones` | GET | Obtener opciones de filtros (años, categorías, etc.) |

### Incidentes

| Endpoint | Método | Parámetros |
|----------|--------|------------|
| `/api/incidentes/filtrar` | GET | `año`, `trimestre`, `categoria`, `severidad`, `cve_col` |
| `/api/incidentes/agregado_temporal` | GET | `agrupacion` (año/mes/trimestre), filtros |

### Polígonos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/poligonos` | GET | Todos los polígonos con métricas |
| `/api/poligonos/<cve_col>` | GET | Detalle de un polígono |
| `/api/poligonos/geojson` | GET | GeoJSON con filtros aplicados (para el mapa) |

### Estadísticas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/estadisticas/resumen` | GET | Resumen general |
| `/api/estadisticas/heatmap` | GET | Datos para heatmap día/hora |

### Ranking de Colonias

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/colonias/ranking` | GET | Ranking personalizable de colonias |
| `/api/colonias/buscar` | GET | Búsqueda de colonias por nombre |

#### Parámetros de `/api/colonias/ranking`

**Filtros de Universo:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `año` | int | Filtrar por año específico |
| `trimestre` | int (1-4) | Filtrar por trimestre |
| `severidades` | string | Severidades a incluir: `ALTA,MEDIA,BAJA` |
| `categorias_incluir` | string | Categorías a incluir separadas por coma |
| `categorias_excluir` | string | Categorías a excluir separadas por coma |
| `tipos_incluir` | string | Tipos de incidente específicos a incluir |
| `tipos_excluir` | string | Tipos de incidente específicos a excluir |
| `poblacion_min` | int | Población mínima de la colonia |

**Métricas de Ordenamiento:**
| Parámetro | Valores | Descripción |
|-----------|---------|-------------|
| `metrica` | `total` | Total de incidentes (default) |
| | `alta` | Solo incidentes de severidad ALTA |
| | `media` | Solo incidentes de severidad MEDIA |
| | `baja` | Solo incidentes de severidad BAJA |
| | `tasa_1k` | Incidentes por cada 1,000 habitantes |
| | `tasa_km2` | Densidad: incidentes por km² |
| | `tasa_alta_1k` | Incidentes ALTA por 1,000 hab |
| | `indice_peligrosidad` | Índice ponderado (ALTA×3 + MEDIA×2 + BAJA×1) |
| | `indice_peligrosidad_1k` | Índice ponderado per 1,000 hab |
| `limit` | int | Número de resultados (default: 20) |
| `ascendente` | bool | Ordenar de menor a mayor (default: false) |

**Ejemplo:**
```
GET /api/colonias/ranking?año=2024&severidades=ALTA,MEDIA&metrica=tasa_1k&limit=10
```

## 🔍 Ejemplos de Consultas

### Filtrar incidentes del 2023, categoría VIOLENCIA, severidad ALTA

```
GET /api/incidentes/filtrar?año=2023&categoria=VIOLENCIA&severidad=ALTA
```

### Obtener GeoJSON filtrado para el mapa

```
GET /api/poligonos/geojson?año=2024&trimestre=1
```

### Tendencia temporal por mes

```
GET /api/incidentes/agregado_temporal?agrupacion=mes&año=2023
```

## 💾 Esquema de Base de Datos

### Tabla `incidentes`

```sql
CREATE TABLE incidentes (
    id INTEGER PRIMARY KEY,
    cve_col TEXT,
    colonia TEXT,
    tipo_incidente TEXT,
    timestamp DATETIME,
    año INTEGER,
    mes INTEGER,
    trimestre INTEGER,
    parte_del_dia TEXT,
    dia_semana TEXT,
    categoria TEXT,
    severidad TEXT,
    latitud REAL,
    longitud REAL
);

-- Índices para consultas rápidas
CREATE INDEX idx_incidentes_año ON incidentes(año);
CREATE INDEX idx_incidentes_categoria ON incidentes(categoria);
CREATE INDEX idx_incidentes_severidad ON incidentes(severidad);
CREATE INDEX idx_incidentes_cve_col ON incidentes(cve_col);
```

### Tabla `poligonos`

```sql
CREATE TABLE poligonos (
    cve_col TEXT PRIMARY KEY,
    colonia TEXT,
    cp TEXT,
    total_incidentes INTEGER,
    incidentes_alta INTEGER,
    incidentes_media INTEGER,
    incidentes_baja INTEGER,
    poblacion_total REAL,
    tasa_incidentes_per_1k REAL,
    score_severidad REAL,
    geometry_json TEXT
);
```

## 📊 Consultas SQL Útiles

### Top 10 colonias más peligrosas (por tasa)

```sql
SELECT colonia, tasa_incidentes_per_1k, total_incidentes
FROM poligonos
WHERE poblacion_total > 0
ORDER BY tasa_incidentes_per_1k DESC
LIMIT 10;
```

### Incidentes por año y severidad

```sql
SELECT año, severidad, COUNT(*) as total
FROM incidentes
GROUP BY año, severidad
ORDER BY año, severidad;
```

### Tendencia mensual 2024

```sql
SELECT mes, COUNT(*) as total,
       SUM(CASE WHEN severidad = 'ALTA' THEN 1 ELSE 0 END) as alta
FROM incidentes
WHERE año = 2024
GROUP BY mes
ORDER BY mes;
```

### Heatmap día de semana vs parte del día

```sql
SELECT dia_semana, parte_del_dia, COUNT(*) as total
FROM incidentes
GROUP BY dia_semana, parte_del_dia;
```

## 🔧 Desarrollo

### Agregar nuevo endpoint

1. Agregar función en `app.py`
2. Usar decorador `@app.route('/api/...')`
3. Retornar `jsonify(data)`

### Agregar nueva consulta

1. Agregar función en `queries.py`
2. Usar `get_connection()` para obtener conexión
3. Ejecutar query y retornar resultados

## 📝 Notas

- La base de datos SQLite es portátil (un solo archivo `.db`)
- Los índices aceleran las consultas de filtrado
- El GeoJSON con geometrías se genera dinámicamente
- CORS está habilitado para desarrollo local

## 🗺️ Interfaz del Mapa (mapa_dinamico.html)

### Pestañas Principales

1. **🔍 Filtros**: Filtros para el mapa coroplético
2. **🏆 Ranking**: Sistema de ranking de colonias con filtros avanzados
3. **📊 Stats**: Estadísticas y gráficas

### Sistema de Ranking (Tab Ranking)

El sistema de ranking tiene un flujo de 2 pasos intuitivo:

#### Paso 1: Define tu Universo de Datos

- **Período**: Selecciona año y/o trimestre
- **Severidad**: 3 botones toggle (Alta/Media/Baja)
  - Los conteos del árbol se actualizan dinámicamente según las severidades activas
  - Tipos con 0 incidentes para las severidades seleccionadas se atenúan visualmente
- **Árbol de Categorías → Tipos**: 
  - Cada categoría es expandible (click en el header)
  - Checkbox de categoría marca/desmarca todos los tipos de esa categoría
  - Checkbox individual para cada tipo específico
  - Conteos muestran solo incidentes de las severidades activas

**Acciones Rápidas:**
- ✓ Todo: Selecciona todos los tipos
- ✗ Nada: Deselecciona todo  
- ⇄ Invertir: Invierte la selección actual

#### Paso 2: Elige tu Métrica

- **Volumen (#)**: Ordena por cantidad total de incidentes
- **x 1,000 Hab (👥)**: Normalizado por población
- **Densidad (🗺️)**: Incidentes por kilómetro cuadrado

### Características Técnicas

- **Conteos Dinámicos**: Al cambiar severidades, los números del árbol se recalculan en tiempo real usando los campos `ALTA`, `MEDIA`, `BAJA` de cada tipo
- **Filtro Jerárquico**: Severidad → Categoría → Tipo
- **Búsqueda de Colonias**: Autocompletado con resultados del API
- **Navegación al Mapa**: Click en cualquier resultado del ranking centra el mapa en esa colonia
