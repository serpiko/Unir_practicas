# compare_gpx.py

Herramienta de línea de comandos para comparar una ruta GPX planificada contra un recorrido real grabado, generando métricas estadísticas y un gráfico multipanel.

Trabajo práctico para la asignatura de **Tecnologías Emergentes** — Adaptación al Grado, UNIR 2025/26.

## Uso

```bash
python compare_gpx.py <teorica.gpx> <real.gpx>
```

| Argumento | Descripción |
|---|---|
| `teorica` | Fichero GPX de la ruta planificada (p.ej. dibujada en gpx.studio) |
| `actual` | Fichero GPX del recorrido real con marcas de tiempo (p.ej. exportado de Samsung Health) |

El gráfico se guarda como `gpx_comparison.png` en el directorio de trabajo.

## Salida

### Informe por consola

- **Distancias** — longitud total de cada ruta y diferencia entre ellas
- **Desviación** — con qué fidelidad se siguió la ruta planificada: media, mediana, desviación típica, máximo y percentil 95, más el porcentaje de puntos GPS dentro de 10 / 20 / 50 / 100 m de la ruta planificada
- **Elevación** — mínimo, máximo, desnivel positivo y negativo acumulados para ambas rutas
- **Tiempo y velocidad** — hora de inicio/fin, duración, velocidad media/mediana/máxima y porcentaje de tiempo parado (< 1 km/h); solo disponible cuando el fichero real contiene marcas de tiempo

### Gráfico (`gpx_comparison.png`)

Cinco paneles:

1. **Mapa de rutas** — ambas rutas superpuestas; los puntos reales coloreados según su desviación respecto al plan
2. **Desviación vs distancia** — desviación en metros a lo largo del recorrido real, con líneas de media y mediana
3. **Perfiles de altitud** — altitud teórica y real representadas contra la distancia recorrida
4. **Perfil de velocidad** — velocidad instantánea suavizada del recorrido real
5. **Histograma de desviaciones** — distribución de las desviaciones de los puntos GPS con líneas de referencia a 10 / 20 / 50 m

## API

### Clases de datos

| Clase | Campos | Descripción |
|---|---|---|
| `Point` | `lat`, `lon`, `ele`, `time` | Representa un waypoint GPS |
| `SpeedData` | `times`, `duration`, `avg_speed_kmh`, `speeds`, `stopped_pct`, `cum_r` | Datos de velocidad calculados del recorrido real |

### Funciones

| Función | Descripción |
|---|---|
| `parse_gpx(path)` | Parsea un fichero GPX y devuelve una lista de objetos `Point` |
| `haversine(a, b)` | Distancia en metros entre dos objetos `Point` mediante la fórmula de Haversine |
| `total_distance(points)` | Devuelve el array de distancia acumulada y la longitud total en metros |
| `assign_buckets(real, cum_r, dist_r, teorica, cum_t, dist_t)` | Asigna a cada punto real el índice del punto teórico correspondiente según la fracción de distancia recorrida |
| `elevation_gain_loss(points)` | Desnivel positivo y negativo acumulados en metros (vectorizado con NumPy) |
| `print_route_summary(...)` | Imprime cabecera y comparativa de distancias totales |
| `print_deviation_stats(dev, label)` | Imprime estadísticas descriptivas de la desviación |
| `compute_elevation(teorica, real)` | Extrae listas de altitud y calcula desniveles de ambas rutas |
| `print_elevation_stats(...)` | Imprime estadísticas de altitud y desnivel |
| `compute_speed_data(real, dist_r, cum_r)` | Calcula velocidades instantáneas y estadísticas de tiempo; devuelve `SpeedData` o `None` |
| `print_speed_stats(sd)` | Imprime estadísticas de tiempo y velocidad |
| `build_plots(...)` | Genera y guarda el gráfico multipanel |

## Dependencias

```
numpy
matplotlib
```

Ambas forman parte de cualquier entorno científico estándar de Python (`pip install numpy matplotlib`).

## Calidad del código

El linting y el formateo se gestionan con [Ruff](https://docs.astral.sh/ruff/):
También se usa pylint con un score de 9.25/10

```bash
# Verificar
.venv/bin/ruff check compare_gpx.py

# Corregir y formatear
.venv/bin/ruff check --fix compare_gpx.py
.venv/bin/ruff format compare_gpx.py
```

La configuración se encuentra en `ruff.toml`.