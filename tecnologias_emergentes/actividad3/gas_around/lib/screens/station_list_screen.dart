import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../models/gas_station.dart';
import '../services/minetur_service.dart';

// Pantalla principal: muestra las 20 gasolineras más cercanas a la ubicación del dispositivo
class StationListScreen extends StatefulWidget {
  const StationListScreen({super.key});

  @override
  State<StationListScreen> createState() => _StationListScreenState();
}

class _StationListScreenState extends State<StationListScreen> {
  final _service = MineTurService();

  // Estado interno de la pantalla
  List<GasStation> _stations = []; // Lista de gasolineras a mostrar
  bool _loading = false;           // Controla el indicador de carga
  String? _error;                  // Mensaje de error, null si no hay error

  // Función principal: obtiene la ubicación GPS y carga las gasolineras cercanas
  // Es async porque combina dos operaciones lentas: GPS y llamada HTTP
  Future<void> _loadNearbyStations() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Comprueba si el permiso de ubicación está concedido y lo solicita si no
      final permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        await Geolocator.requestPermission();
      }

      // Obtiene las coordenadas actuales del dispositivo con alta precisión (GPS)
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      );

      // Descarga todas las gasolineras de España desde la API de MineTur
      final all = await _service.fetchAllStations();

      // Calcula la distancia en km entre el dispositivo y cada gasolinera
      // Geolocator.distanceBetween devuelve metros, dividimos entre 1000
      for (final s in all) {
        s.distanceKm = Geolocator.distanceBetween(
              position.latitude,
              position.longitude,
              s.latitude,
              s.longitude,
            ) /
            1000;
      }

      // Ordena la lista de menor a mayor distancia
      all.sort((a, b) => (a.distanceKm ?? 0).compareTo(b.distanceKm ?? 0));

      // Actualiza el estado con las 20 más cercanas para no sobrecargar la lista
      setState(() {
        _stations = all.take(20).toList();
        _loading = false;
      });
    } catch (e) {
      // Captura errores de red, GPS desactivado o permisos denegados
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GasAround'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: _buildBody(),
      // Botón flotante que lanza la búsqueda; deshabilitado mientras carga
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loading ? null : _loadNearbyStations,
        icon: const Icon(Icons.my_location),
        label: const Text('Buscar cerca'),
      ),
    );
  }

  // Construye el cuerpo de la pantalla según el estado actual
  Widget _buildBody() {
    // Estado de carga: muestra spinner centrado
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    // Estado de error: muestra el mensaje en rojo
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_error!, style: const TextStyle(color: Colors.red)),
        ),
      );
    }

    // Estado inicial: aún no se ha buscado
    if (_stations.isEmpty) {
      return const Center(
        child: Text('Pulsa el botón para buscar gasolineras cercanas'),
      );
    }

    // Estado con datos: lista de gasolineras con nombre, dirección y precios
    return ListView.builder(
      itemCount: _stations.length,
      itemBuilder: (context, index) {
        final s = _stations[index];
        return ListTile(
          leading: const Icon(Icons.local_gas_station),
          title: Text(s.name),
          subtitle: Text('${s.address}, ${s.municipality}'),
          // Columna derecha: precios de los dos combustibles más comunes y distancia
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (s.priceGasolina95 != null && s.priceGasolina95!.isNotEmpty)
                Text('95: ${s.priceGasolina95} €',
                    style: const TextStyle(fontSize: 12)),
              if (s.priceGasoilA != null && s.priceGasoilA!.isNotEmpty)
                Text('A: ${s.priceGasoilA} €',
                    style: const TextStyle(fontSize: 12)),
              Text('${s.distanceKm!.toStringAsFixed(1)} km',
                  style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        );
      },
    );
  }
}
