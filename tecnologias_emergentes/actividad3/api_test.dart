/// Script de prueba para la API REST de carburantes del Ministerio (MineTur)
/// Uso: dart run api_test.dart [endpoint]
///
/// Endpoints disponibles:
///   estaciones   — todas las estaciones terrestres (~11.000)
///   municipios   — lista de municipios con su ID
///   productos    — catálogo de carburantes con su ID
///   ccaa         — comunidades autónomas
///
/// Ejemplos:
///   dart run api_test.dart municipios
///   dart run api_test.dart productos

import 'dart:convert' show jsonDecode, utf8, JsonEncoder;
import 'dart:io' show HttpClient, exit;

const _base =
    'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes';

final _endpoints = {
  'estaciones': '$_base/EstacionesTerrestres/',
  'municipios': '$_base/Municipios/',
  'productos':  '$_base/Productos/',
  'ccaa':       '$_base/ComunidadesAutonomas/',
};

Future<void> main(List<String> args) async {
  final cmd = args.isNotEmpty ? args[0] : 'estaciones';

  if (!_endpoints.containsKey(cmd)) {
    print('Endpoint desconocido: $cmd');
    print('Disponibles: ${_endpoints.keys.join(', ')}');
    exit(1);
  }

  final url = _endpoints[cmd]!;
  print('→ GET $url\n');

  final client = HttpClient();
  try {
    final request  = await client.getUrl(Uri.parse(url));
    final response = await request.close();

    if (response.statusCode != 200) {
      print('Error HTTP ${response.statusCode}');
      exit(1);
    }

    final body = await response.transform(utf8.decoder).join();
    final data = jsonDecode(body);

    if (cmd == 'estaciones') {
      // Solo muestra la estructura del primer registro de estaciones
      final lista = data['ListaEESSPrecio'] as List;
      print('Total estaciones: ${lista.length}');
      print('\nCampos del primer registro:');
      final primero = lista.first as Map<String, dynamic>;
      primero.forEach((k, v) => print('  "$k": "$v"'));
    } else if (data is List) {
      print('Total registros: ${data.length}\n');
    } else if (data is Map) {
      final encoder = JsonEncoder.withIndent('  ');
      // Para listas grandes muestra solo metadata + primeros registros
      final preview = Map.fromEntries(data.entries.map((e) {
        if (e.value is List && (e.value as List).length > 3) {
          return MapEntry(e.key, (e.value as List).take(3).toList());
        }
        return e;
      }));
      print(encoder.convert(preview));
    }
  } finally {
    client.close();
  }
}
