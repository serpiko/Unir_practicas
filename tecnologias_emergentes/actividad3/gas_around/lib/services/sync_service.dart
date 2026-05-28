import '../models/gas_station.dart';
import 'database_service.dart';
import 'minetur_service.dart';

// Orquesta la estrategia local-primero: sirve datos de SQLite inmediatamente
// y lanza una actualización en background contra la API cuando los datos están caducados
class SyncService {
  // Constructor privado e instancia única — patrón Singleton
  SyncService._();
  static final SyncService instance = SyncService._();

  // Accede a las otras capas a través de sus propias instancias Singleton
  final _db  = DatabaseService.instance;
  final _api = MineTurService.instance;

  // Los datos se consideran caducados si tienen más de 24 horas
  static const _maxAgeHours = 24;

  // Punto de entrada principal para la pantalla de gasolineras
  //
  // Devuelve un record de Dart 3: (stations, isSyncing)
  //   isSyncing = true  → se lanzó un refresh en background (datos caducados)
  //   isSyncing = false → los datos locales son frescos, no hay sync activo
  //
  // Flujo:
  //   1. BD vacía (primer arranque) → descarga API completa, persiste, isSyncing=false
  //   2. BD con datos recientes     → devuelve SQLite, isSyncing=false
  //   3. BD con datos caducados     → devuelve SQLite, lanza refresh, isSyncing=true
  //
  // [onSyncComplete] se llama cuando el refresh en background termina
  Future<({List<GasStation> stations, bool isSyncing})> getStations({
    void Function()? onSyncComplete,
  }) async {
    final empty = await _db.isEmpty();

    if (empty) {
      // Primer arranque: sin datos locales, la descarga inicial es obligatoria
      final stations = await _api.fetchAllStations();
      await _db.seedStations(stations);
      return (stations: stations, isSyncing: false);
    }

    // Comprueba si los datos almacenados han superado el límite de antigüedad
    final lastSync = await _db.lastSync();
    final isStale  = lastSync == null ||
        DateTime.now().difference(lastSync).inHours >= _maxAgeHours;

    if (isStale) {
      // Lanza la actualización sin await: la UI no espera, recibe los datos locales ya
      // Si la API falla, catchError lo absorbe silenciosamente — los datos locales siguen válidos
      _api.fetchAllStations().then((stations) async {
        await _db.seedStations(stations);
        onSyncComplete?.call();
      }).catchError((_) {});
    }

    // Devuelve siempre los datos locales de forma instantánea
    final stations = await _db.getAllStations();
    return (stations: stations, isSyncing: isStale);
  }
}
