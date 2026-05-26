// Modelo de datos que representa una estación de servicio (gasolinera)
// Los campos reflejan la estructura JSON devuelta por la API de MineTur
class GasStation {
  final String name;        // Nombre comercial (Rótulo)
  final String address;     // Dirección postal
  final String municipality; // Municipio
  final String postalCode;  // Código postal
  final double latitude;    // Latitud WGS84
  final double longitude;   // Longitud WGS84
  final String? priceGasolina95; // Precio Gasolina 95 E5 (puede estar vacío)
  final String? priceGasoilA;    // Precio Gasoil A (puede estar vacío)
  double? distanceKm; // Distancia calculada en tiempo de ejecución, no viene de la API

  GasStation({
    required this.name,
    required this.address,
    required this.municipality,
    required this.postalCode,
    required this.latitude,
    required this.longitude,
    this.priceGasolina95,
    this.priceGasoilA,
    this.distanceKm,
  });

  // La API devuelve coordenadas con coma decimal ("40,416775") en lugar de punto
  // Este helper convierte ese formato al double estándar de Dart
  static double _parseCoord(String s) =>
      double.tryParse(s.replaceAll(',', '.')) ?? 0.0;

  // Constructor factory: construye un GasStation a partir del Map JSON de la API
  // Se usa 'factory' porque aplica lógica de transformación antes de crear el objeto
  factory GasStation.fromJson(Map<String, dynamic> json) {
    return GasStation(
      name:             json['Rótulo'] ?? '',
      address:          json['Dirección'] ?? '',
      municipality:     json['Municipio'] ?? '',
      postalCode:       json['C.P.'] ?? '',
      latitude:         _parseCoord(json['Latitud'] ?? '0'),
      longitude:        _parseCoord(json['Longitud (WGS84)'] ?? '0'),
      // Los precios son opcionales: una estación puede no vender cierto combustible
      priceGasolina95:  json['Precio Gasolina 95 E5'],
      priceGasoilA:     json['Precio Gasoil A'],
    );
  }
}
