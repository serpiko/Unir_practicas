Hoja de ruta de implementación
  
  Fase 0 — Explorando las APIs (Apartado 1)

El enunciado define 2 urls principales de las que consumir datos vía API Rest, pero resulta que ambas atacan a la misma
API por detrás:

  datos.gob.es/catalogo/e05068001...  →  portal web
      └─ botón "Servicio REST" → Acceder  →  sedeaplicaciones.minetur.gob.es  ✓ ya implementado

  geoportalgasolineras.es  →  portal web
      └─ pestaña "Descargar ficheros" → "Información actualizada de precios"
          └─ servicios REST al final de la página  →  también apunta a sedeaplicaciones.minetur.gob.es

Así que vamos a implementar nuestras consultas directamente contra este endpoint, definiendo el servicio Minetur en nuestra app flutter.


  Portal 1 — MinETUR REST (datos.gob.es backbone):
  # todas las estaciones
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/

  # filtro por ID de municipio
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestresFiltradas/<
  idMunicipio>
  
  # filtrado por ID de carburante
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestresFiltradas/F
  iltroProducto/<idProducto>
  
  # Lista de minicipios ( resuelve GPS por municipio )
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/Municipios/

  # listado de carburantes
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/Productos/

  Portal 2 — Geoportal gasolineras:
  # Precios actuales (volcado completo, mismos datos, diferente formato)
  https://geoportalgasolineras.es/resources/files/preciosEESS_es.json

 Ambos devuelven un json, mientras que Portal 1 soporta filtrado, Portal 2 parece útil como fallback.

  ---
  Fase 1 — estructura del proyecto

  - Creación de proyecto Flutter (es.unir org, Android target)
  - Añadir dependencias a pubspec.yaml:
  http: ^1.2.0          # API calls
  geolocator: ^13.0.0   # GPS
  permission_handler: ^11.0.0  # permisos en tiempo de ejecución
  - Añadir permisos GPS al AndroidManifest.xml

  ---
  Fase 2 — Capa de datos

  Definimos 3 model classes en Dart sincronizando la API json:

  ┌──────────────┬───────────────────────────────────────────────┐
  │    Clase     │                    Propósito                  │
  ├──────────────┼───────────────────────────────────────────────┤
  │ GasStation   │una estación:nombre, dirección, lat/lon,precios│
  ├──────────────┼───────────────────────────────────────────────┤
  │ FuelProduct  │ catalogo de productos (Gasolina95, Gasoil A)  │
  ├──────────────┼───────────────────────────────────────────────┤
  │ Municipality │ id + nombre, resuelve posiciones GPS          │
  └──────────────┴───────────────────────────────────────────────┘

  Una service class por fuente de datos:
  - MineTurService — consulta el Portal 1, resuelve el municipio desde coordenadas
  - GeoportalService — consulta el Portal 2 como fallback

  ---
  Fase 3 — Lógica de ubicación

  1. Solicitar permiso ACCESS_FINE_LOCATION en tiempo de ejecución
  2. Obtener la posición actual (lat/lon) via geolocator
  3. Llamar al endpoint Municipios/, encontrar el municipio más cercano comparando coordenadas — o usar reverse-geocoding
  4. Usar ese idMunicipio para filtrar la consulta de gasolineras

  ---
  Fase 4 — UI (3 pantallas)

  HomeScreen
    └─ botón "Buscar cerca" → lanza GPS + llamada API
  StationListScreen
    └─ ListView de gasolineras, ordenadas por distancia
    └─ barra de filtro: selector de tipo de carburante (Gasolina 95, Gasoil A, etc.)
  StationDetailScreen
    └─ dirección completa, todos los precios, distancia desde el usuario

  ---
  Fase 5 — Acabados y gestión de errores

  - Spinner de carga mientras se obtienen los datos
  - Estados de error "sin conexión" / "GPS desactivado"
  - Cachear la última respuesta correcta para que la app funcione offline tras la primera carga

  ---
  Fase 6 — Caché local con SQLite (implementada)

  La inestabilidad de la API motivó añadir una capa de persistencia local con SQLite,
  usando el paquete sqflite. Se añadieron dos servicios nuevos:

  DatabaseService (lib/services/database_service.dart)
    └─ Singleton con constructor privado
    └─ Crea y gestiona la base de datos gas_around.db con dos tablas:
         stations — ~11.000 gasolineras con nombre, dirección, coordenadas y precios
         meta     — clave-valor para guardar la fecha de última sincronización
    └─ seedStations() usa batch insert para eficiencia con grandes volúmenes

  SyncService (lib/services/sync_service.dart)
    └─ Singleton que orquesta la estrategia local-primero:
         1. BD vacía (primer arranque) → descarga API completa → persiste en SQLite
         2. BD con datos recientes (< 24h) → devuelve SQLite directamente
         3. BD con datos caducados (> 24h) → devuelve SQLite Y lanza refresh en background
    └─ El callback onSyncComplete (void Function()?) notifica a la UI cuando
       el refresh termina sin haberla bloqueado — patrón de función como parámetro

  StationListScreen actualizada:
    └─ Ya no llama a MineTurService directamente
    └─ Usa SyncService.instance.getStations()
    └─ Muestra LinearProgressIndicator bajo el AppBar durante el sync en background
    └─ Los errores de red no interrumpen la app: SyncService los absorbe y usa la caché

  ---
  Fase 7 — Precios como double y filtro por carburante (implementada)

  GasStation (lib/models/gas_station.dart)
    └─ priceGasolina95 y priceGasoilA cambian de String? a double?
    └─ _parsePrice() nuevo helper: convierte "1,659" → 1.659 (coma → punto), devuelve null si vacío
    └─ Permite comparar y ordenar precios directamente sin conversión posterior

  DatabaseService (lib/services/database_service.dart)
    └─ Esquema sube de versión 1 a versión 2
    └─ Columnas price_gasolina95 y price_gasoil_a: TEXT → REAL
    └─ onUpgrade añadido: borra y recrea la tabla stations en dispositivos con v1 instalada
    └─ _createStationsTable extraída como método independiente para evitar duplicar el SQL
       entre onCreate y onUpgrade — meta no se toca en el upgrade porque persiste entre versiones

  SyncService (lib/services/sync_service.dart)
    └─ Tipo de retorno cambia de List<GasStation> a record de Dart 3:
       ({List<GasStation> stations, bool isSyncing})
    └─ isSyncing=true solo cuando los datos estaban caducados y se lanzó refresh en background
    └─ Permite a la UI saber exactamente cuándo mostrar el indicador de sync

  StationListScreen (lib/screens/station_list_screen.dart)
    └─ Enum FuelFilter: all | gasolina95 | gasoilA — define los filtros disponibles
    └─ _allStations guarda todas las estaciones con distancia calculada
    └─ _filteredStations getter: aplica el filtro activo sobre _allStations
         all       → las 7 más cercanas, ordenadas por distancia
         gasolina95 → estaciones con ese carburante, ordenadas por precio ascendente
         gasoilA   → ídem para gasoil
    └─ _buildFilterBar(): fila de FilterChip horizontales desplazables
    └─ Precio destacado en negrita cuando hay filtro activo; ambos precios si no hay filtro
    └─ Destructuring de record Dart 3: final (stations: all, :isSyncing) = await ...

  ---
  Fase 8 — Splash screen y corrección de filtros (implementada)

  SplashScreen (lib/screens/splash_screen.dart)
    └─ Pantalla de presentación nueva: fondo verde, icono + nombre + subtítulo
    └─ Fade-in de 800ms con AnimationController + CurvedAnimation
    └─ Navega a StationListScreen tras 3 segundos con pushReplacement
       (pushReplacement evita que "back" vuelva al splash)
    └─ main.dart actualizado: home apunta a SplashScreen en vez de StationListScreen

  Corrección filtros por carburante (lib/screens/station_list_screen.dart)
    └─ Bug: los chips Gasolina 95 y Gasoil A ordenaban por precio sobre las ~11.000
       estaciones de toda España → mostraban las más baratas del país, no las cercanas
    └─ Fix: _filteredStations ahora parte de las 50 más cercanas (nearby) antes de
       filtrar y reordenar por precio
    └─ Resultado: "las más baratas entre las gasolineras cercanas a ti"

  ---
  Orden de implementación:
  1. Fase 0 (entender las respuestas de la API) → 2 (modelos + servicios con datos de prueba) → 3 (GPS) → 4 (UI conectada a datos reales) → 5

  Así la integración con la API se puede probar de forma aislada antes de que exista la UI.

---
Conceptos básicos de Dart para llamadas a API REST
1. Las llamadas de red tardan tiempo, Dart lo gestiona con Future, que devuelve una "promesa" de un String, no el String en sí:

Future<String> fetchData() async {
    String result = await requestAPI();
    return result;
}
2. HTTP request:
// add http to pubspec.yaml
import 'package:http/http.dart' as http;
import 'dart:convert'; // for jsonDecode
const EstacionesTerrestres ='https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/';
Future<void> fetchStations() async{
    final url = Uri.parse(EstacionesTerrestres);
    final response = await http.get(url);
    if (response.statusCode == 200){
        final data = jsonDecode(response.body);
        print(data);
    }else {
     print('error ${response.statusCode}');
    }
}

 3. Entendiendo lo que devuelve la API

  La API de MineTur devuelve algo así:

  {
    "Fecha": "26/05/2026",
    "ListaEESSPrecio": [
      {
        "C.P.": "28001",
        "Dirección": "CALLE MAYOR 1",
        "Latitud": "40,416775",
        "Longitud": "-3,703790",
        "Rótulo": "REPSOL",
        "Precio Gasolina 95 E5": "1,659",
        "Precio Gasoil A": "1,489"
      },
      ...
    ]
  }

En Dart, después de jsonDecode, eso se convierte en:
Map<String, dynamic> data = jsonDecode(response.body);
List<dynamic> stations = data['ListaEESSPrecio'];

// accede una estación
Map<String, dynamic> first = stations[0];
print(first['Rótulo']);
print(first['Dirección']);

4. Creando una model class

En lugar de trabajar con Map<String, dynamic> crudo, los mapeamos a clases Dart:
class GasStation{
  final String name;
  final String address;
  final String postalCode;
  final double latitude;
  final double longitude;
  final Strint? priceGasolina95; // ? es nullable
  final String? priceGasoilA;
  
  GasStation({
    required this.name,
    required this.address,
    required this.postalCode,
    required this.latitude,
    required this.longitude,
    required this.priceGasolina95,
    required this.priceGasoilA,
    });
  // API envia "40,416775"(coma) -> convertimos a double
  static double _parseCoord(String s) => 
    double.parse(s.replaceAll(',','.'));
  // Named constructor: construye GasStation desde el raw API map
  factory GasStation.fromJson(Map<String, dynamic> json){
    return GasStation(
       name: json['Rótulo'] ?? '',
       name: json['Dirección'] ?? '',
       name: json['C.P.'] ?? '',
       name: _parseCoord(json['Latitud'] ?? '0'),
       name: _parseCoord(json['Longitud (wGS84)'] ?? '0'),
       name: json['Precio Gasolina 95 ES'] ?? '',
       name: json['Precio GasoilA'] ?? '',
    );
   }
}

5. Lo unimos todo en una service class

import 'package:http/http.dart' as http;
import 'dart:convert'; // for jsonDecode

class MineturService{
  static const _base =        
'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes';
  Future<List<GasStation>> fetchAllStations() async{
    final response = await http.get(Uri.parse('$_base/EstacionesTerrestres/'));
    if ( response.statusCode != 200){
       throw Exception('AP eror: ${response.statusCode}');
    }
    final data = jsonDecode(response.body);
    final List<dynamic> list = data['ListaEESSPrecio'];
    return list.map(json) => GasStation.fromJson(json)).toList();
   }
}

Uso desde un widget u otro:
final service = MineturService();
final stations = await service.fetchAllStations();
print('Found ${stations.length} stations');
print(stations.first_name);

  Conceptos clave a recordar

  ┌──────────────────────┬────────────────────────────────────────────────────┐
  │       Concepto       │                   Qué significa                    │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ Future<T>            │ Un valor de tipo T que llegará más tarde           │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ async                │ Marca una función como asíncrona                   │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ await                │ Espera aquí hasta que el Future se resuelva        │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ Map<String, dynamic> │ Lo que devuelve jsonDecode — un diccionario        │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ factory constructor  │ Constructor que instancia objeto desde datos crudos│
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ ??                   │ "Si es null, usa este valor por defecto"           │
  ├──────────────────────┼────────────────────────────────────────────────────┤
  │ ? en un tipo         │ El valor es opcional (puede ser null)              │
  └──────────────────────┴────────────────────────────────────────────────────┘



# Gestión del proyecto flutter
flutter create --org es.unir gas_around
flutter run // corre una app linux con un botón + y un campo contador
flutter pub get // lee el archivo pubspec.yaml y descarga todos los paquetes declarados en dependencies desde el
  repositorio público pub.dev.
En nuestro caso descargará tres paquetes nuevos:

  http: ^1.2.0           # cliente HTTP para llamar a la API REST
  geolocator: ^13.0.0    # acceso al GPS del dispositivo
  permission_handler: ^11.0.0  # solicitar permisos en tiempo de ejecución

Además de los paquetes y sus dependencias a ~/.pub-cache/ que es una caché global para todas las apps fluter locales.
Genera fichero pubspec.lock con las versiones exactas del proyecto.
Crea .dart_tool/package_config.json con las rutas a cada paquete, necesario para el compilador.

# ejecutar en dispositivo específico
flutter run -d <device-id>

# Build APK
flutter build apk

# ejecutar tests
flutter test

# ejecutar fichero de test
flutter test test/widget_test.dart

# análisis de código
flutter analyze

# formateo de código
dart format .


# Diseño de Implementación inicial
3 módulos principales: 
screens para pantallas
models para modelos de datos
services para servicios de acceso API como MineturService
  ┌──────────────────────────┬────────────────────────────────────────────────────────────────────────────────────┐
  │           File           │                                Comentarios añadidos                                │
  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
  │ main.dart                │ Punto de entrada, configuración del tema y pantalla inicial                        │
  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
  │ gas_station.dart         │ Por qué se usa factory, por qué se reemplaza la coma decimal, qué campos son       │
  │                          │ opcionales                                                                         │
  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
  │ minetur_service.dart     │ Cuándo usar cada endpoint, por qué se usa Map para municipios, estructura de la    │
  │                          │ respuesta JSON                                                                     │
  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
  │ station_list_screen.dart │ Flujo GPS → HTTP → cálculo de distancia → ordenación, los tres estados del         │
  │                          │ _buildBody(), por qué se limita a 20 resultados                                    │
  └──────────────────────────┴────────────────────────────────────────────────────────────────────────────────────┘

# Capa de Datos local
Las APIs propuestas para esta práctica son muy inestables

# Depuración en dispositivo android conectado y con modo desarrollador activado

flutter devices  
Found 3 connected devices:
  Aquaris X2 Pro (mobile) • XV009147 • android-arm64  • Android 10 (API 29)
  Linux (desktop)         • linux    • linux-x64      • Ubuntu 24.04.4 LTS 6.8.0-117-generic
  Chrome (web)            • chrome   • web-javascript • Google Chrome 148.0.7778.178

El nuestro es el viejo Aquarix X2, la compilación tarda unos 2 minutos
```
flutter run -d XV009147
Launching lib/main.dart on Aquaris X2 Pro in debug mode...
Running Gradle task 'assembleDebug'...                  
```

