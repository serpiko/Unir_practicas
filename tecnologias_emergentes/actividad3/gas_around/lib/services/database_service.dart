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
      version: 4,
      onCreate: _onCreate,
      // onUpgrade borra y recrea stations para aplicar cambios de esquema
      // meta no se toca: persiste entre versiones
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
        price_gasoil_a   REAL,
        id_ccaa          TEXT,
        horario          TEXT
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
        'id_ccaa':          s.idCcaa,
        'horario':          s.horario,
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
    return rows.map(_rowToStation).toList();
  }

  // Devuelve los IDs de CCAA distintos presentes en la BD, ordenados
  Future<List<String>> getDistinctCcaa() async {
    final db = await database;
    final rows = await db.rawQuery(
      'SELECT DISTINCT id_ccaa FROM $_tableStations WHERE id_ccaa IS NOT NULL AND id_ccaa != "" ORDER BY id_ccaa',
    );
    return rows.map((r) => r['id_ccaa'] as String).toList();
  }

  // Devuelve los nombres de municipio de una CCAA, ordenados alfabéticamente
  Future<List<String>> getMunicipiosByCcaa(String idCcaa) async {
    final db = await database;
    final rows = await db.rawQuery(
      'SELECT DISTINCT municipality FROM $_tableStations WHERE id_ccaa = ? AND municipality != "" ORDER BY municipality',
      [idCcaa],
    );
    return rows.map((r) => r['municipality'] as String).toList();
  }

  // Devuelve todas las estaciones de un municipio concreto
  Future<List<GasStation>> getStationsByMunicipio(String municipio) async {
    final db = await database;
    final rows = await db.query(
      _tableStations,
      where: 'municipality = ?',
      whereArgs: [municipio],
      orderBy: 'name ASC',
    );
    return rows.map(_rowToStation).toList();
  }

  GasStation _rowToStation(Map<String, Object?> row) => GasStation(
    name:             row['name'] as String,
    address:          row['address'] as String? ?? '',
    municipality:     row['municipality'] as String? ?? '',
    postalCode:       row['postal_code'] as String? ?? '',
    latitude:         row['latitude'] as double? ?? 0.0,
    longitude:        row['longitude'] as double? ?? 0.0,
    idCcaa:           row['id_ccaa'] as String? ?? '',
    priceGasolina95:  row['price_gasolina95'] as double?,
    priceGasoilA:     row['price_gasoil_a'] as double?,
    horario:          row['horario'] as String?,
  );

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
