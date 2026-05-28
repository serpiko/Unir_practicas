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
  // Flujo:
  //   1. Si la BD está vacía (primer arranque) → descarga todo de la API y persiste
  //   2. Si la BD tiene datos recientes        → los devuelve directamente
  //   3. Si la BD tiene datos caducados        → los devuelve Y lanza refresh en background
  //
  // [onSyncComplete] se llama cuando el refresh en background termina,
  // permitiendo a la UI actualizarse sin bloquear al usuario
  Future<List<GasStation>> getStations({
    void Function()? onSyncComplete,
  }) async {
    final empty = await _db.isEmpty();

    if (empty) {
      // Primer arranque: sin datos locales, la descarga inicial es obligatoria
      final stations = await _api.fetchAllStations();
      await _db.seedStations(stations);
      return stations;
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

    // Devuelve siempre los datos locales (frescos o caducados) de forma instantánea
    return _db.getAllStations();
  }
}
