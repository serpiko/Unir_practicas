# Hoja de ruta — GasAround

App Flutter que consulta precios de carburantes en tiempo real contra la API REST
del Ministerio de Industria (MinETUR), con caché local SQLite y localización GPS.

UNIR · Tecnologías Emergentes · Grado en Informática · Actividad 3

---

## 1. Fuentes de datos

El enunciado define dos URLs principales de las que consumir los datos, de sus correspondientes APIs RESTful, sin embargo hemos descubierto que ambas apuntan a la misma API, por tanto se ha descartado cualquier implementación que balancee la carga de ambos recursos, o usar uno como failover del otro.

```
datos.gob.es/catalogo/e05068001...  →  botón "Servicio REST"
geoportalgasolineras.es             →  "Descargar ficheros" → servicios REST al pie
     └─ ambas redirigen a: sedeaplicaciones.minetur.gob.es
```

A la hora de diseñar el volcado en bloque a nuestra capa de persistencia local ( sqlite) se había considerado usar el volcado  de precios del geoportal, que los expone en un volcado en XLS (`/resources/files/preciosEESS_es.xls`).  Pero la implementación para XLS con Dart suponía una mayor complejidad comparado con el formato JSON del portal 1. ( [excel](https://pub.dev/packages/excel)),
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
las respuestas de la API desde bash:

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
main.dart                      — punto de entrada; llama a SplashScreen
screens/
  splash_screen.dart           — presentación animada, navega a StationListScreen
  station_list_screen.dart     — pantalla principal: GPS, filtros, lista, detalle
models/
  gas_station.dart             — modelo de datos
services/
  minetur_service.dart         — llamadas HTTP; parsea ~11.000 estaciones
  database_service.dart        — SQLite (sqflitev3); batch insert
  sync_service.dart            — estrategia local-primero
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
`'Horario'`, `'Precio Gasolina 95 E5'`, `'Precio Gasoleo A'`.

---

## 4. Servicios y persistencia

### MineTurService (`lib/services/minetur_service.dart`)

Capa de acceso a la API REST del Ministerio. Su única responsabilidad es realizar
la llamada HTTP al endpoint `EstacionesTerrestres/` y transformar la respuesta JSON
en una lista de objetos `GasStation` que el resto de la app pueda consumir.
El array `'ListaEESSPrecio'` que devuelve la API se mapea elemento a elemento
mediante el constructor `GasStation.fromJson()`.

```dart
import 'dart:convert' show jsonDecode;
import 'package:http/http.dart' as http;
import '../models/gas_station.dart';

class MineTurService {
  MineTurService._();                                          // constructor privado
  static final MineTurService instance = MineTurService._();  // única instancia (Singleton)

  static const _base =
      'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes';

  Future<List<GasStation>> fetchAllStations() async {
    final response = await http.get(Uri.parse('$_base/EstacionesTerrestres/'));

    if (response.statusCode != 200) {
      throw Exception('Error API MineTur: ${response.statusCode}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>; // JSON → Map Dart
    final list = data['ListaEESSPrecio'] as List<dynamic>;          // extrae el array
    return list.map((e) => GasStation.fromJson(e as Map<String, dynamic>)).toList();
    // map() transforma cada elemento del array en un GasStation via factory fromJson
  }
}
```

### DatabaseService (`lib/services/database_service.dart`)

Capa de persistencia local. Gestiona la base de datos SQLite `gas_around.db`
mediante el paquete `sqflite`, actuando como caché entre sesiones para que la app
funcione sin conexión tras la primera carga. 
Implementa el patrón Singleton para garantizar que toda la app comparte una única conexión a la base de datos.
El esquema ha evolucionado en tres versiones; `onUpgrade` aplica los cambios
de forma destructiva sobre `stations` (los datos se re-descargan de la API),
conservando la tabla `meta` que almacena la fecha de última sincronización.

```dart
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' show join;
import '../models/gas_station.dart';

class DatabaseService {
  DatabaseService._();
  static final DatabaseService instance = DatabaseService._();  // Singleton

  static Database? _db;  // null hasta el primer acceso

  Future<Database> get database async {
    _db ??= await _initDb();  // inicializa solo la primera vez (lazy)
    return _db!;              // ! porque sabemos que ya no es null
  }

  Future<Database> _initDb() async {
    final path = join(await getDatabasesPath(), 'gas_around.db');
    return openDatabase(
      path,
      version: 3,
      onCreate: (db, _) async {          // primer arranque: crea todo
        await _createStationsTable(db);
        await db.execute(
          'CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)',
        );
      },
      onUpgrade: (db, oldVersion, newVersion) async {  // cambio de schema:
        await db.execute('DROP TABLE IF EXISTS stations'); // borra y recrea stations
        await _createStationsTable(db);                    // meta se conserva
      },
    );
  }

  Future<void> _createStationsTable(Database db) async {
    await db.execute('''
      CREATE TABLE stations (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        address          TEXT,
        municipality     TEXT,
        postal_code      TEXT,
        latitude         REAL,
        longitude        REAL,
        price_gasolina95 REAL,  -- REAL para poder ordenar por precio en SQLite
        price_gasoil_a   REAL,
        id_ccaa          TEXT
      )
    ''');
  }

  Future<void> seedStations(List<GasStation> stations) async {
    final db    = await database;
    final batch = db.batch();   // agrupa todas las inserciones en una sola transacción
    batch.delete('stations');   // limpia datos anteriores antes de insertar
    for (final s in stations) {
      batch.insert('stations', {
        'name':             s.name,
        'address':          s.address,
        'municipality':     s.municipality,
        'postal_code':      s.postalCode,
        'latitude':         s.latitude,
        'longitude':        s.longitude,
        'price_gasolina95': s.priceGasolina95,
        'price_gasoil_a':   s.priceGasoilA,
        'id_ccaa':          s.idCcaa,
      });
    }
    await batch.commit(noResult: true);  // ejecuta todo de golpe (~11.000 filas)
  }

  Future<List<GasStation>> getAllStations() async {
    final db   = await database;
    final rows = await db.query('stations');
    return rows.map(_rowToStation).toList();  // cada fila → GasStation
  }

  GasStation _rowToStation(Map<String, Object?> row) => GasStation(
    name:            row['name']             as String,
    address:         row['address']          as String? ?? '',  // cast nullable + fallback
    municipality:    row['municipality']     as String? ?? '',
    postalCode:      row['postal_code']      as String? ?? '',
    latitude:        row['latitude']         as double? ?? 0.0,
    longitude:       row['longitude']        as double? ?? 0.0,
    idCcaa:          row['id_ccaa']          as String? ?? '',
    priceGasolina95: row['price_gasolina95'] as double?,  // null si no vende ese carburante
    priceGasoilA:    row['price_gasoil_a']   as double?,
  );
}
```

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

> Esquema v4: columna `horario TEXT` añadida. `seedStations`, `_rowToStation`
> y `_createStationsTable` actualizados. `onUpgrade` re-crea `stations` al detectar v3.

### SyncService (`lib/services/sync_service.dart`)

Orquestador de la estrategia local-primero. Su responsabilidad es decidir en cada
consulta de dónde provienen los datos, de forma que la pantalla siempre recibe
una respuesta inmediata sin preocuparse por el estado de la red. Para ello combina
`DatabaseService` y `MineTurService` aplicando tres casos según la antigüedad
de los datos almacenados:

```
1. BD vacía (primer arranque)  → descarga API completa → persiste en SQLite
2. Datos recientes (< 24h)     → devuelve SQLite directamente
3. Datos caducados (> 24h)     → devuelve SQLite + lanza refresh en background
```

En el caso 3 el refresh se ejecuta sin bloquear la UI: la pantalla recibe los datos
locales de inmediato y se actualiza sola cuando la descarga termina, a través del
callback `onSyncComplete`. Si la API falla, el error se absorbe silenciosamente y
los datos locales siguen siendo válidos.


```dart
import '../models/gas_station.dart';
import 'database_service.dart';
import 'minetur_service.dart';

class SyncService {
  SyncService._();
  static final SyncService instance = SyncService._();

  final _db  = DatabaseService.instance;  // accede a los otros Singletons
  final _api = MineTurService.instance;

  static const _maxAgeHours = 24;

  Future<({List<GasStation> stations, bool isSyncing})> getStations({
    void Function()? onSyncComplete,  // callback opcional: avisa cuando termina el sync
  }) async {
    if (await _db.isEmpty()) {
      // caso 1: primer arranque, no hay datos locales
      final stations = await _api.fetchAllStations();
      await _db.seedStations(stations);
      return (stations: stations, isSyncing: false);
    }

    final lastSync = await _db.lastSync();
    final isStale  = lastSync == null ||
        DateTime.now().difference(lastSync).inHours >= _maxAgeHours;

    if (isStale) {
      // caso 3: datos caducados — lanza refresh sin await (no bloquea la UI)
      // catchError absorbe fallos de red silenciosamente
      _api.fetchAllStations().then((stations) async {
        await _db.seedStations(stations);
        onSyncComplete?.call();
      }).catchError((_) {});
    }

    // casos 2 y 3: devuelve SQLite inmediatamente
    final stations = await _db.getAllStations();
    return (stations: stations, isSyncing: isStale);
  }
}
```

---

## 5. Pantallas

### SplashScreen (`lib/screens/splash_screen.dart`)

Pantalla de presentación: fondo verde, icono + nombre + subtítulo.
Fade-in de 800ms con `AnimationController` + `CurvedAnimation`.
Navega a `StationListScreen` tras 3s con `pushReplacement`
(`pushReplacement` evita que "atrás" vuelva al splash).

```dart
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

// SingleTickerProviderStateMixin: proporciona el vsync que necesita AnimationController
class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double>   _fadeIn;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..forward();  // ..forward() encadena la llamada: crea el controller y arranca la animación

    _fadeIn = CurvedAnimation(parent: _controller, curve: Curves.easeIn);

    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) {  // guard: evita navegar si el widget ya fue destruido
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const StationListScreen()),
        );
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();  // libera recursos de la animación al salir
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: colors.primary,
      body: FadeTransition(  // aplica la animación de opacidad al árbol de widgets hijo
        opacity: _fadeIn,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.local_gas_station, size: 80, color: colors.onPrimary),
              const SizedBox(height: 24),
              Text('GasAround',
                  style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold,
                      color: colors.onPrimary, letterSpacing: 2)),
              Text('Gasolineras cerca de ti',
                  style: TextStyle(fontSize: 14, color: colors.onPrimary.withValues(alpha: 0.8))),
            ],
          ),
        ),
      ),
    );
  }
}
```

<!-- CAPTURA: pantalla de splash en el dispositivo -->

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

```dart
enum FuelFilter { all, gasolina95, gasoilA }

class StationListScreen extends StatefulWidget {
  const StationListScreen({super.key});
  @override
  State<StationListScreen> createState() => _StationListScreenState();
}

class _StationListScreenState extends State<StationListScreen> {
  final _sync = SyncService.instance;
  final _db   = DatabaseService.instance;

  List<GasStation> _allStations = [];
  bool       _loading  = false;
  bool       _syncing  = false;
  String?    _error;
  FuelFilter _filter   = FuelFilter.all;
  bool       _zoneMode = false;

  String?      _selectedCcaa;
  List<String> _municipios = [];
  String?      _selectedMunicipio;

  @override
  void initState() {
    super.initState();
    _loadCcaaIds();  // carga los chips de CCAA al arrancar, sin esperar al GPS
  }

  // getter calculado: no usa setState, se recalcula en cada build()
  List<GasStation> get _filteredStations {
    final pool  = _zoneMode ? _allStations : _allStations.take(50).toList();
    final limit = _zoneMode ? 20 : 7;
    switch (_filter) {
      case FuelFilter.gasolina95:
        return (pool.where((s) => s.priceGasolina95 != null).toList()
              ..sort((a, b) => a.priceGasolina95!.compareTo(b.priceGasolina95!)))
            .take(limit).toList();
      case FuelFilter.gasoilA:
        return (pool.where((s) => s.priceGasoilA != null).toList()
              ..sort((a, b) => a.priceGasoilA!.compareTo(b.priceGasoilA!)))
            .take(limit).toList();
      case FuelFilter.all:
        return pool.take(limit).toList();
    }
  }

  Future<void> _loadNearbyStations() async {
    setState(() { _loading = true; _zoneMode = false; });  // spinner ON

    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      await Geolocator.requestPermission();
    }

    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );

    // destructuring del record Dart 3 devuelto por SyncService
    final (stations: all, :isSyncing) = await _sync.getStations(
      onSyncComplete: () {
        if (mounted) setState(() => _syncing = false);  // apaga el indicador de sync
      },
    );
    _syncing = isSyncing;

    for (final s in all) {
      s.distanceKm = Geolocator.distanceBetween(
        position.latitude, position.longitude,
        s.latitude,        s.longitude,
      ) / 1000;  // metros → km
    }
    all.sort((a, b) => (a.distanceKm ?? 0).compareTo(b.distanceKm ?? 0));

    setState(() { _allStations = all; _loading = false; });  // spinner OFF, lista visible
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GasAround'),
        bottom: _syncing                          // barra de progreso bajo el AppBar
            ? const PreferredSize(
                preferredSize: Size.fromHeight(2),
                child: LinearProgressIndicator())
            : null,
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loading ? null : _loadNearbyStations,  // desactivado mientras carga
        icon: const Icon(Icons.my_location),
        label: const Text('Buscar cerca'),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!));
    if (_allStations.isEmpty && !_zoneMode) {
      return Column(children: [
        _buildFilterBar(),
        const Expanded(child: Center(child: Text('Pulsa el botón para buscar gasolineras cercanas'))),
      ]);
    }
    // caso normal: barra de filtros + lista
    return Column(children: [
      _buildFilterBar(),
      Expanded(child: _buildList()),
    ]);
  }

  Widget _buildList() {
    final stations = _filteredStations;
    return ListView.builder(
      itemCount: stations.length,
      itemBuilder: (context, index) {
        final s = stations[index];
        return ListTile(
          dense: true,
          leading: const Icon(Icons.local_gas_station),
          title: Text(s.name),
          subtitle: Text('${s.address}, ${s.municipality}'),
          onTap: () => _showDetail(s),  // abre el BottomSheet con el detalle
        );
      },
    );
  }

  void _showDetail(GasStation s) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,  // panel solo ocupa lo necesario
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Text('${s.address}, ${s.municipality}'),
            if (s.horario != null) Text(s.horario!),  // solo si la estación lo publica
            if (s.priceGasolina95 != null) Text('Gasolina 95: ${s.priceGasolina95!.toStringAsFixed(3)} €'),
            if (s.priceGasoilA    != null) Text('Gasoleo A:   ${s.priceGasoilA!.toStringAsFixed(3)} €'),
            FilledButton.icon(
              icon: const Icon(Icons.directions),
              label: const Text('Cómo llegar'),
              onPressed: () { Navigator.pop(context); _openInMaps(s); },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openInMaps(GasStation s) async {
    final uri = Uri.parse(
      'geo:${s.latitude},${s.longitude}?q=${s.latitude},${s.longitude}(${Uri.encodeComponent(s.name)})',
    );
    if (!await launchUrl(uri)) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se encontró app de mapas instalada')),
      );
    }
  }
}
```

<!-- CAPTURA: lista principal con resultados GPS y chips de filtro visibles -->

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

<!-- CAPTURA: filtro de CCAA activo con dropdown de municipios desplegado -->

BottomSheet de detalle (`_showDetail`):
nombre, dirección, horario (si existe), precios, distancia, botón "Cómo llegar".

<!-- CAPTURA: BottomSheet abierto mostrando detalle de una gasolinera -->

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
