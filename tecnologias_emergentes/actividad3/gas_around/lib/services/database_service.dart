import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/gas_station.dart';

// Gestiona la base de datos SQLite local que actúa como caché de las gasolineras
// Persiste los datos entre sesiones para que la app funcione sin conexión
class DatabaseService {
  // Constructor privado: impide instanciar la clase desde fuera
  DatabaseService._();

  // Instancia única creada una sola vez al cargar la clase (eager initialization)
  static final DatabaseService instance = DatabaseService._();

  // La conexión SQLite sí necesita inicialización async, de ahí el ??= aquí
  static Database? _db;

  static const _dbName = 'gas_around.db';
  static const _tableStations = 'stations';
  static const _tableMeta = 'meta';

  Future<Database> get database async {
    _db ??= await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _dbName);
    return openDatabase(path, version: 1, onCreate: _onCreate);
  }

  // Crea las tablas en el primer arranque de la app
  Future<void> _onCreate(Database db, int version) async {
    // Tabla principal con los datos de cada gasolinera
    await db.execute('''
      CREATE TABLE $_tableStations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        address         TEXT,
        municipality    TEXT,
        postal_code     TEXT,
        latitude        REAL,
        longitude       REAL,
        price_gasolina95 TEXT,
        price_gasoil_a  TEXT
      )
    ''');

    // Tabla auxiliar de metadatos (clave-valor) para guardar la fecha de última sincronización
    await db.execute('''
      CREATE TABLE $_tableMeta (
        key   TEXT PRIMARY KEY,
        value TEXT
      )
    ''');
  }

  // Reemplaza todos los registros con los datos frescos recibidos de la API
  // Usa batch para insertar ~11.000 registros de forma eficiente en una sola transacción
  Future<void> seedStations(List<GasStation> stations) async {
    final db = await database;
    final batch = db.batch();

    batch.delete(_tableStations);

    for (final s in stations) {
      batch.insert(_tableStations, {
        'name':             s.name,
        'address':          s.address,
        'municipality':     s.municipality,
        'postal_code':      s.postalCode,
        'latitude':         s.latitude,
        'longitude':        s.longitude,
        'price_gasolina95': s.priceGasolina95,
        'price_gasoil_a':   s.priceGasoilA,
      });
    }

    await batch.commit(noResult: true);
    // Registra el momento de la sincronización para saber cuándo caducan los datos
    await _setMeta('last_sync', DateTime.now().toIso8601String());
  }

  // Recupera todas las gasolineras almacenadas localmente
  Future<List<GasStation>> getAllStations() async {
    final db = await database;
    final rows = await db.query(_tableStations);
    return rows.map((row) => GasStation(
      name:             row['name'] as String,
      address:          row['address'] as String? ?? '',
      municipality:     row['municipality'] as String? ?? '',
      postalCode:       row['postal_code'] as String? ?? '',
      latitude:         row['latitude'] as double? ?? 0.0,
      longitude:        row['longitude'] as double? ?? 0.0,
      priceGasolina95:  row['price_gasolina95'] as String?,
      priceGasoilA:     row['price_gasoil_a'] as String?,
    )).toList();
  }

  Future<bool> isEmpty() async {
    final db = await database;
    final count = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM $_tableStations'),
    );
    return (count ?? 0) == 0;
  }

  // Devuelve cuándo se sincronizó por última vez, o null si nunca
  Future<DateTime?> lastSync() async {
    final value = await _getMeta('last_sync');
    if (value == null) return null;
    return DateTime.tryParse(value);
  }

  Future<void> _setMeta(String key, String value) async {
    final db = await database;
    await db.insert(
      _tableMeta,
      {'key': key, 'value': value},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<String?> _getMeta(String key) async {
    final db = await database;
    final rows = await db.query(_tableMeta, where: 'key = ?', whereArgs: [key]);
    if (rows.isEmpty) return null;
    return rows.first['value'] as String?;
  }
}
