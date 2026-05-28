// Modelo de datos que representa una estación de servicio (gasolinera)
// Los campos reflejan la estructura JSON devuelta por la API de MineTur
class GasStation {
  final String name;        // Nombre comercial (Rótulo)
  final String address;     // Dirección postal
  final String municipality; // Municipio
  final String postalCode;  // Código postal
  final double latitude;    // Latitud WGS84
  final double longitude;   // Longitud WGS84
  final double? priceGasolina95; // Precio Gasolina 95 E5 en €/litro (null si no se vende)
  final double? priceGasoilA;    // Precio Gasoil A en €/litro (null si no se vende)
  final String idCcaa;      // ID de Comunidad Autónoma (01–19), para filtro por zona
  double? distanceKm; // Distancia calculada en tiempo de ejecución, no viene de la API

  GasStation({
    required this.name,
    required this.address,
    required this.municipality,
    required this.postalCode,
    required this.latitude,
    required this.longitude,
    required this.idCcaa,
    this.priceGasolina95,
    this.priceGasoilA,
    this.distanceKm,
  });

  // La API devuelve números con coma decimal ("1,659") en lugar de punto
  // Este helper convierte ese formato al double estándar de Dart
  // Devuelve null si el campo está vacío o no es un número válido
  static double? _parsePrice(String? s) {
    if (s == null || s.trim().isEmpty) return null;
    return double.tryParse(s.replaceAll(',', '.'));
  }

  // La API devuelve coordenadas con coma decimal ("40,416775") en lugar de punto
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
      idCcaa:           json['IDCCAA'] ?? '',
      // Los precios son opcionales: una estación puede no vender cierto combustible
      priceGasolina95:  _parsePrice(json['Precio Gasolina 95 E5']),
      priceGasoilA:     _parsePrice(json['Precio Gasoleo A']),
    );
  }
}
