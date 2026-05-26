import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/gas_station.dart';

// Servicio de acceso a la API REST del Ministerio para la Transición Ecológica
// Documentación: https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/
class MineTurService {
  static const _base =
      'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes';

  // Obtiene las gasolineras filtradas por ID de municipio
  // Más eficiente que fetchAllStations() porque reduce los datos descargados
  Future<List<GasStation>> fetchStationsByMunicipality(String municipalityId) async {
    final uri = Uri.parse('$_base/EstacionesTerrestresFiltradas/$municipalityId');
    final response = await http.get(uri);

    if (response.statusCode != 200) {
      throw Exception('Error API MineTur: ${response.statusCode}');
    }

    // La API devuelve un objeto con la clave 'ListaEESSPrecio' que contiene la lista
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final list = data['ListaEESSPrecio'] as List<dynamic>;
    return list.map((e) => GasStation.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Obtiene todas las gasolineras de España (~11.000 registros)
  // Usar solo cuando no se dispone del ID de municipio
  Future<List<GasStation>> fetchAllStations() async {
    final uri = Uri.parse('$_base/EstacionesTerrestres/');
    final response = await http.get(uri);

    if (response.statusCode != 200) {
      throw Exception('Error API MineTur: ${response.statusCode}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final list = data['ListaEESSPrecio'] as List<dynamic>;
    return list.map((e) => GasStation.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Obtiene el catálogo completo de municipios como Map: IDMunicipio → NombreMunicipio
  // Útil para resolver las coordenadas GPS al municipio más cercano
  Future<Map<String, String>> fetchMunicipalities() async {
    final uri = Uri.parse('$_base/Municipios/');
    final response = await http.get(uri);

    if (response.statusCode != 200) {
      throw Exception('Error obteniendo municipios: ${response.statusCode}');
    }

    // Transforma la lista JSON en un mapa ID→Nombre para búsquedas rápidas
    final list = jsonDecode(response.body) as List<dynamic>;
    return {
      for (var m in list)
        (m['IDMunicipio'] as String): (m['Municipio'] as String)
    };
  }
}
