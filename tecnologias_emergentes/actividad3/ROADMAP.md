# Hoja de ruta — GasAround

App Flutter que consulta precios de carburantes en tiempo real contra la API REST
del Ministerio de Industria (MinETUR), con caché local SQLite y localización GPS.

UNIR · Tecnologías Emergentes · Grado en Informática · Actividad 3

---

## 1. Fuentes de datos

Ambas URLs del enunciado apuntan al mismo backend:

```
datos.gob.es/catalogo/e05068001...  →  botón "Servicio REST"
geoportalgasolineras.es             →  "Descargar ficheros" → servicios REST al pie
     └─ ambas redirigen a: sedeaplicaciones.minetur.gob.es
```

El Portal 2 (geoportalgasolineras.es) tiene los mismos datos pero actualmente
requiere autenticación para la descarga directa. Se usa solo Portal 1.

### Endpoints MinETUR

Todas las llamadas parten de la url base:
https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes

a la que se añade la ruta de cada servicio específico:
```
# Todas las estaciones terrestres (~11.000)
GET /ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/

# Filtro por municipio o carburante
GET .../EstacionesTerrestresFiltradas/<idMunicipio>
GET .../EstacionesTerrestresFiltradas/FiltroProducto/<idProducto>

# Catálogos auxiliares
GET .../Municipios/
GET .../Productos/
GET .../ComunidadesAutonomas/
```

### Formato de respuesta

```json
{
  "Fecha": "26/05/2026",
  "ListaEESSPrecio": [
    {
      "C.P.": "28001",
      "Dirección": "CALLE MAYOR 1",
      "Latitud": "40,416775",
      "Longitud (WGS84)": "-3,703790",
      "Rótulo": "REPSOL",
      "IDCCAA": "13",
      "Horario": "L-D: 07:00-22:00",
      "Precio Gasolina 95 E5": "1,659",
      "Precio Gasoleo A": "1,489"
    }
  ]
}
```

### Script de prueba

`actividad3/api_test.dart` — script Dart standalone (sin Flutter) para inspeccionar
las respuestas de la API desde línea de comandos:

```bash
dart run api_test.dart # descarga completa (~11.000)
```
Devuelve el json de ejemplo de la sección anterior.
Lógica:
```
  import 'dart:convert';
  import 'dart:io';

  const _url =
      'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes'
      '/PreciosCarburantes/EstacionesTerrestres/';

  Future<void> main() async {
    final client = HttpClient();
    try {
      final request  = await client.getUrl(Uri.parse(_url));
      final response = await request.close();

      if (response.statusCode != 200) {
        print('Error HTTP ${response.statusCode}');
        return;
      }

      final body = await response.transform(utf8.decoder).join();
      final data = jsonDecode(body) as Map<String, dynamic>;
      final lista = data['ListaEESSPrecio'] as List;

      print('Fecha: ${data['Fecha']}');
      print('Total estaciones: ${lista.length}');
      print('\nPrimer registro:');
      (lista.first as Map<String, dynamic>)
          .forEach((k, v) => print('  "$k": "$v"'));
    } finally {
      client.close();
    }
  }
```

---

## 2. Arquitectura

### Capas

```
StationListScreen
     │
     └─ SyncService          ← orquestador local-primero (caché o API)
          ├─ DatabaseService  ← SQLite, persistencia entre sesiones
          └─ MineTurService   ← API REST del Ministerio
```

La pantalla no habla directamente con la API ni con la BD sino con un servicio intermedio
SyncService, que decide de dónde vienen los datos.

### Modelo de datos (SQLite)

```
┌─────────────────────┐         ┌───────────────────────────────┐
│  ComunidadAutonoma  │         │           stations            │
│─────────────────────│         │───────────────────────────────│
│ id_ccaa  TEXT  PK   │──1───N─▶│ id               INTEGER PK   │
│ nombre   TEXT       │         │ name             TEXT         │
└─────────────────────┘         │ address          TEXT         │
                                │ municipality     TEXT         │
┌─────────────────────┐         │ postal_code      TEXT         │
│      Municipio      │         │ latitude         REAL         │
│─────────────────────│──1───N─▶│ longitude        REAL         │
│ municipality TEXT   │         │ price_gasolina95 REAL         │
└─────────────────────┘         │ price_gasoil_a   REAL         │
                                │ id_ccaa          TEXT  FK     │
┌─────────────────────┐         └───────────────────────────────┘
│        meta         │
│─────────────────────│
│ key    TEXT  PK     │  ← solo contiene 'last_sync'
│ value  TEXT         │
└─────────────────────┘
```

### Ficheros principales

```
main.dart                      — punto de entrada; tema verde; arranca SplashScreen
screens/
  splash_screen.dart           — presentación animada, navega a StationListScreen
  station_list_screen.dart     — pantalla principal: GPS, filtros, lista, detalle
models/
  gas_station.dart             — modelo de datos; factory fromJson; precios double?
services/
  minetur_service.dart         — llamadas HTTP; parsea ~11.000 estaciones
  database_service.dart        — SQLite (sqflite); schema v3; batch insert
  sync_service.dart            — estrategia local-primero; record Dart 3
```

---

## 3. Modelos

### GasStation (`lib/models/gas_station.dart`)

Se ha definido la clase GasStation para gestionar los datos de la entidad,
a partir de la información que nos ha interesado capturar de la respuesta API:
```
name, address, municipality, postalCode  — datos de la estación
horario          String?                 — horario de apertura; nullable
latitude, longitude  double              — coordenadas WGS84
priceGasolina95, priceGasoilA  double?  — null si no vende ese carburante
idCcaa           String                 — ID de Comunidad Autónoma (01–19)
distanceKm       double?                — calculado en runtime, no viene de la API
```

En caso de que quisieramos ampliar la funcionalidad de la App Flutter, empezaríamos añadiendo
al modelo de datos, los campos necesarios.
Los servicios de esta API tienen información sobre Puntos de Recarga electricos o Postes Marítimos,
 además de otros tipos de carburantes.

Lógica:
```
  class GasStation {
    final String  name;
    final String  address;
    final String  municipality;
    final String  postalCode;
    final String? horario;
    final double  latitude;
    final double  longitude;
    final String  idCcaa;
    final double? priceGasolina95;
    final double? priceGasoilA;
    double?       distanceKm;

    GasStation({
      required this.name,
      required this.address,
      required this.municipality,
      required this.postalCode,
      required this.latitude,
      required this.longitude,
      required this.idCcaa,
      this.horario,
      this.priceGasolina95,
      this.priceGasoilA,
      this.distanceKm,
    });

    static double? _parsePrice(String? s) =>
        (s == null || s.trim().isEmpty) ? null : double.tryParse(s.replaceAll(',', '.'));

    static double _parseCoord(String s) =>
        double.tryParse(s.replaceAll(',', '.')) ?? 0.0;

    factory GasStation.fromJson(Map<String, dynamic> json) => GasStation(
      name:            json['Rótulo']            ?? '',
      address:         json['Dirección']         ?? '',
      municipality:    json['Municipio']         ?? '',
      postalCode:      json['C.P.']              ?? '',
      horario:         json['Horario'],
      latitude:        _parseCoord(json['Latitud']          ?? '0'),
      longitude:       _parseCoord(json['Longitud (WGS84)'] ?? '0'),
      idCcaa:          json['IDCCAA']            ?? '',
      priceGasolina95: _parsePrice(json['Precio Gasolina 95 E5']),
      priceGasoilA:    _parsePrice(json['Precio Gasoleo A']),
    );
  }
```

Funciones de conversión:

```dart
_parsePrice("1,659")      → 1.659   // coma → punto; null si vacío
_parseCoord("40,416775")  → 40.416775
```

`factory GasStation.fromJson()` mapea los nombres exactos de la API:
`'Rótulo'`, `'Dirección'`, `'Latitud'`, `'Longitud (WGS84)'`, `'IDCCAA'`,
`'Horario'` (H mayúscula), `'Precio Gasolina 95 E5'`, `'Precio Gasoleo A'` (no "Gasoil").

---

## 4. Servicios y persistencia

### MineTurService (`lib/services/minetur_service.dart`)

Descarga el volcado completo de `EstacionesTerrestres/` y devuelve
`List<GasStation>` parseando el array `'ListaEESSPrecio'`.

### DatabaseService (`lib/services/database_service.dart`)

Singleton (constructor privado + `static final instance`).
Base de datos: `gas_around.db`.

Evolución del schema:

```
v1 — columnas básicas; price_gasolina95 y price_gasoil_a como TEXT
v2 — precios cambian a REAL para poder ordenar numéricamente
v3 — añade id_ccaa TEXT para filtro por comunidad autónoma
```

`onUpgrade`: borra y recrea `stations` (migración destructiva aceptable; los datos
vienen de la API y se re-descargan). `meta` no se toca entre versiones.

Métodos principales:

```
seedStations(List<GasStation>)      — batch insert (~11.000 filas)
getAllStations()                     — todas las estaciones
getDistinctCcaa()                   — IDs de CCAA presentes en la BD
getMunicipiosByCcaa(idCcaa)         — municipios de esa CCAA, orden alfabético
getStationsByMunicipio(municipio)   — estaciones de un municipio
```

> `horario` no se persiste todavía (schema v4 pendiente). Cuando los datos
> vienen de caché, `horario` siempre es `null`.

### SyncService (`lib/services/sync_service.dart`)

Singleton. Estrategia local-primero:

```
1. BD vacía (primer arranque)  → API completa → persiste en SQLite
2. Datos recientes (< 24h)     → SQLite directamente
3. Datos caducados (> 24h)     → SQLite + refresh en background
```

Retorna record Dart 3: `({List<GasStation> stations, bool isSyncing})`
`isSyncing=true` solo en el caso 3, para que la UI muestre el indicador.
El callback `onSyncComplete` notifica cuando el background refresh termina.

---

## 5. Pantallas

### SplashScreen (`lib/screens/splash_screen.dart`)

Pantalla de presentación: fondo verde, icono + nombre + subtítulo.
Fade-in de 800ms con `AnimationController` + `CurvedAnimation`.
Navega a `StationListScreen` tras 3s con `pushReplacement`
(`pushReplacement` evita que "atrás" vuelva al splash).

### StationListScreen (`lib/screens/station_list_screen.dart`)

Pantalla principal. Variables de estado:

```
_allStations        — estaciones con distancia calculada
_loading            — muestra spinner mientras carga
_syncing            — muestra LinearProgressIndicator en el AppBar
_error              — texto de error si algo falla
_filter             — FuelFilter: all | gasolina95 | gasoilA
_zoneMode           — true cuando la lista viene del filtro de zona (sin GPS)
_ccaaIds            — IDs de CCAA presentes en la BD
_selectedCcaa       — CCAA activa (null = ninguna)
_municipios         — municipios de la CCAA seleccionada
_selectedMunicipio  — municipio activo (null = ninguno)
```

Modos de carga:

```
GPS (FAB "Buscar cerca")  → distancias calculadas, muestra 7 resultados
Zona (CCAA + municipio)   → sin GPS, muestra 20 resultados
```

Filtros de carburante (`_filteredStations` getter):
parte de las 50 más cercanas como universo para no mostrar las más baratas
de toda España; ordena por precio ascendente dentro de ese subconjunto.

Barra de filtros (3 filas):

```
Fila 1 — chips: Distancia | Gasolina 95 | Gasoleo A
Fila 2 — chips de CCAA (carrusel horizontal, solo si hay datos en la BD)
Fila 3 — dropdown de municipios (solo si hay CCAA seleccionada)
```

BottomSheet de detalle (`_showDetail`):
nombre, dirección, horario (si existe), precios, distancia, botón "Cómo llegar".

Navegación a Maps (`_openInMaps`):
URI `geo:LAT,LON?q=LAT,LON(Nombre)` vía `url_launcher`.
`AndroidManifest.xml` declara intent `geo:` en `<queries>`.
Si no hay app de mapas instalada, muestra `SnackBar` de aviso.

---

## 6. Build y distribución

### Firma del APK

```bash
# Generar keystore (una sola vez)
keytool -genkey -v -keystore ~/gas_around.jks \
        -keyalg RSA -keysize 2048 -validity 10000 -alias gas_around
```

`android/key.properties` (excluido de git — nunca subir):

```
storeFile=/home/serpiko/gas_around.jks
storePassword=<contraseña>
keyAlias=gas_around
keyPassword=<contraseña>
```

`android/app/build.gradle.kts` lee el fichero con Kotlin DSL:

```kotlin
import java.util.Properties
val keyProperties = Properties()
keyProperties.load(rootProject.file("key.properties").inputStream())
// usar keyProperties.getProperty("key"), no keyProperties["key"]
```

```bash
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk
```

Si hay una versión debug instalada, desinstalar antes:

```bash
adb -s <device-id> uninstall es.unir.gas_around
```

### Publicación en GitHub Releases

```bash
gh release create v1.0.0 GasAround-v1.0.0.apk \
    --repo serpiko/Unir_practicas \
    --title "GasAround v1.0.0"
```

Publicado en: https://github.com/serpiko/Unir_practicas/releases/tag/v1.0.0

Instalación: activar "Fuentes desconocidas" una sola vez en el dispositivo.
Requiere conexión en el primer arranque; offline después.

---

## 7. Conceptos Dart/Flutter

### async/await

Las llamadas de red y al GPS devuelven `Future`: una promesa de un valor
que llegará más tarde. `async`/`await` permite escribirlas de forma lineal:

```dart
// async va después de los paréntesis (al contrario que Python)
Future<void> _loadNearbyStations() async {
  final position = await Geolocator.getCurrentPosition(...);
  // aquí position ya tiene valor
}
```

`await` pausa la función hasta que el `Future` se resuelva, sin bloquear el hilo UI.

`async` no hace las operaciones más rápidas — la red tarda lo que tarda.
La diferencia es qué hace el hilo mientras espera:

```
Sin async:   hilo ──── espera HTTP ──────────────────── continúa
                        (hilo parado, no hace nada)

Con async:   hilo ──── lanza petición ── libre ── respuesta ── continúa
                                         (UI sigue respondiendo)
```

En Flutter esto es crítico: sin async el hilo de la UI se bloquea y la pantalla
se congela. En un script CLI como `api_test.dart` el efecto es imperceptible,
pero `HttpClient` de Dart solo existe en versión asíncrona, así que no hay opción.

Cuando sí hay ganancia real en velocidad es lanzando varias operaciones en paralelo:

```dart
await Future.wait([fetchStations(), fetchMunicipios()]); // viajan a la vez
```

### El Widget como unidad de UI y lógica

En Flutter no hay separación entre capa visual y lógica como en Android XML + Activity.
Un `StatefulWidget` tiene el estado (lógica) y el `build()` (UI) en el mismo objeto.

Ciclo de actualización:

```
acción del usuario
     │
     ▼
setState(() { _loading = true; })   ← actualiza estado
     │
     ▼
build() se ejecuta de nuevo         ← Flutter llama esto automáticamente
     │
     ▼
_buildBody() devuelve el widget correcto según el estado
     │
     ▼
Flutter compara árbol nuevo vs anterior y pinta solo lo que cambió
```

Esta comparación (reconciliation) es barata: el árbol de widgets es
una descripción en memoria, no el renderizado real.

Tres variantes:

| Tipo | Estado | Ejemplo en GasAround |
|---|---|---|
| `StatelessWidget` | Ninguno (inmutable) | `_priceRow()` |
| `StatefulWidget` | Propio, via `setState` | `StationListScreen` |
| Widget "tonto" | Recibe datos del padre | `ListTile` |

### mounted

Un widget puede desaparecer del árbol mientras hay callbacks asíncronos pendientes.
`mounted` es `true` mientras el widget vive en el árbol, `false` tras `dispose()`:

```dart
Future.delayed(duration, () {
  if (mounted) {           // ¿sigue vivo el widget?
    setState(() { ... });  // solo entonces toca el estado
  }
});
```

En `SplashScreen` evita llamar a `Navigator.pushReplacement` si el usuario
abandonó la pantalla antes de que expiren los 3 segundos.

### Tipos nullable (`String?`)

`String?` significa "puede ser un `String` o `null`". Sin `?`, el compilador
impide que la variable sea `null` en tiempo de compilación.

```dart
String? _selectedCcaa;       // null = ninguna CCAA seleccionada
String? _selectedMunicipio;  // null = ningún municipio seleccionado
```

`null` aquí no es un error — es un valor semántico: "el usuario no ha elegido nada".
Conduce la UI directamente:

```dart
if (_selectedCcaa != null && _municipios.isNotEmpty)
  DropdownButton(...)  // solo visible si hay CCAA seleccionada
```

---

## Comandos habituales

```bash
flutter run -d <device-id>          # ejecutar en dispositivo específico
flutter build apk --release         # build release
flutter test                        # todos los tests
flutter test test/widget_test.dart  # test concreto
flutter analyze                     # análisis estático
dart format .                       # formatear código
dart run api_test.dart estaciones # script de prueba de la API
adb devices                         # listar dispositivos conectados
adb -s <id> install app-release.apk
```

## Depuración en dispositivo

```
flutter devices
  Aquaris X2 Pro (mobile) • XV009147 • android-arm64  • Android 10 (API 29)
  Linux (desktop)         • linux    • linux-x64
  Chrome (web)            • chrome   • web-javascript

flutter run -d XV009147
```

La compilación en el Aquaris X2 tarda ~2 minutos.
