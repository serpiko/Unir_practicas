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
    return openDatabase(
      path,
      version: 2,
      onCreate: _onCreate,
      // onUpgrade se ejecuta cuando el usuario ya tiene la v1 instalada
      // Borra y recrea la tabla para aplicar el cambio TEXT → REAL en precios
      onUpgrade: (db, oldVersion, newVersion) async {
        await db.execute('DROP TABLE IF EXISTS $_tableStations');
        await _createStationsTable(db);
      },
    );
  }

  // Crea las tablas en el primer arranque de la app
  Future<void> _onCreate(Database db, int version) async {
    await _createStationsTable(db);

    // meta solo se crea en onCreate — onUpgrade no la toca porque persiste entre versiones
    await db.execute('''
      CREATE TABLE $_tableMeta (
        key   TEXT PRIMARY KEY,
        value TEXT
      )
    ''');
  }

  // Extraída para poder reutilizarla tanto en onCreate como en onUpgrade
  // Solo crea la tabla stations — meta se crea únicamente en onCreate
  Future<void> _createStationsTable(Database db) async {
    // Los precios son REAL para poder ordenar y filtrar por precio en SQLite
    await db.execute('''
      CREATE TABLE $_tableStations (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        address          TEXT,
        municipality     TEXT,
        postal_code      TEXT,
        latitude         REAL,
        longitude        REAL,
        price_gasolina95 REAL,
        price_gasoil_a   REAL
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
        'price_gasolina95': s.priceGasolina95,  // double? → SQLite REAL
        'price_gasoil_a':   s.priceGasoilA,    // double? → SQLite REAL
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
      priceGasolina95:  row['price_gasolina95'] as double?,
      priceGasoilA:     row['price_gasoil_a'] as double?,
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
