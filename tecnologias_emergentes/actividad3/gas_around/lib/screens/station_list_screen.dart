import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../models/gas_station.dart';
import '../services/sync_service.dart';

// Tipos de carburante disponibles como filtro
// 'all' muestra todas las estaciones ordenadas por distancia
// Los demás filtran a estaciones que venden ese carburante y ordenan por precio
enum FuelFilter { all, gasolina95, gasoilA }

// Pantalla principal: muestra las gasolineras más cercanas a la ubicación del dispositivo
// Lee de la caché SQLite local primero y actualiza en background si los datos están caducados
class StationListScreen extends StatefulWidget {
  const StationListScreen({super.key});

  @override
  State<StationListScreen> createState() => _StationListScreenState();
}

class _StationListScreenState extends State<StationListScreen> {
  // Accede al SyncService a través de su instancia Singleton
  final _sync = SyncService.instance;

  // Estado interno de la pantalla
  List<GasStation> _allStations = []; // Todas las estaciones cargadas (con distancia calculada)
  bool _loading = false;              // Controla el indicador de carga inicial
  bool _syncing = false;              // Indica sincronización en background (datos caducados)
  String? _error;                     // Mensaje de error, null si no hay error
  FuelFilter _filter = FuelFilter.all; // Filtro activo seleccionado por el usuario

  // Aplica el filtro activo sobre _allStations y devuelve la lista a mostrar
  // Siempre parte de las 50 más cercanas para no mostrar estaciones de otras provincias
  // Si hay filtro de carburante: filtra las que venden ese combustible y ordena por precio
  // Si no hay filtro: devuelve las 7 más cercanas ordenadas por distancia
  List<GasStation> get _filteredStations {
    // Universo de búsqueda: las 50 gasolineras más cercanas al usuario
    final nearby = _allStations.take(50).toList();

    switch (_filter) {
      case FuelFilter.gasolina95:
        final withFuel = nearby
            .where((s) => s.priceGasolina95 != null)
            .toList()
          ..sort((a, b) => a.priceGasolina95!.compareTo(b.priceGasolina95!));
        return withFuel.take(7).toList();

      case FuelFilter.gasoilA:
        final withFuel = nearby
            .where((s) => s.priceGasoilA != null)
            .toList()
          ..sort((a, b) => a.priceGasoilA!.compareTo(b.priceGasoilA!));
        return withFuel.take(7).toList();

      case FuelFilter.all:
        return nearby.take(7).toList();
    }
  }

  // Función principal: obtiene el GPS y carga las gasolineras desde la caché local
  // La primera vez descarga de la API y persiste en SQLite; las siguientes veces es instantáneo
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

      // Solicita las gasolineras al SyncService, que decide si usar caché o API
      // El record devuelto contiene los datos y si hay un sync activo en background
      final (stations: all, :isSyncing) = await _sync.getStations(
        onSyncComplete: () {
          if (mounted) setState(() => _syncing = false);
        },
      );

      // isSyncing viene directamente de SyncService — true solo si los datos estaban caducados
      _syncing = isSyncing;

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

      // Ordena por distancia — base para el filtro 'all' y punto de partida para los demás
      all.sort((a, b) => (a.distanceKm ?? 0).compareTo(b.distanceKm ?? 0));

      setState(() {
        _allStations = all;
        _loading = false;
      });
    } catch (e) {
      // Captura errores de GPS desactivado o permisos denegados
      // Los errores de red no llegan aquí: SyncService los absorbe y usa la caché
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
        // Indicador de sincronización en background: barra sutil bajo el AppBar
        bottom: _syncing
            ? const PreferredSize(
                preferredSize: Size.fromHeight(2),
                child: LinearProgressIndicator(),
              )
            : null,
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loading ? null : _loadNearbyStations,
        icon: const Icon(Icons.my_location),
        label: const Text('Buscar cerca'),
      ),
    );
  }

  // Construye el cuerpo de la pantalla según el estado actual
  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_error!, style: const TextStyle(color: Colors.red)),
        ),
      );
    }

    if (_allStations.isEmpty) {
      return const Center(
        child: Text('Pulsa el botón para buscar gasolineras cercanas'),
      );
    }

    // Estado con datos: barra de filtros + lista
    return Column(
      children: [
        _buildFilterBar(),
        Expanded(child: _buildList()),
      ],
    );
  }

  // Fila de chips para seleccionar el tipo de carburante
  // Al seleccionar un chip se reordena la lista por precio de ese carburante
  Widget _buildFilterBar() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          _filterChip(FuelFilter.all,        'Distancia',   Icons.near_me),
          _filterChip(FuelFilter.gasolina95, 'Gasolina 95', Icons.local_gas_station),
          _filterChip(FuelFilter.gasoilA,    'Gasoleo A',   Icons.opacity),
        ],
      ),
    );
  }

  // Chip individual: resaltado cuando es el filtro activo
  Widget _filterChip(FuelFilter value, String label, IconData icon) {
    final selected = _filter == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        selected: selected,
        label: Text(label),
        avatar: Icon(icon, size: 16),
        // Al pulsar cambia el filtro activo y la lista se recalcula via _filteredStations
        onSelected: (_) => setState(() => _filter = value),
      ),
    );
  }

  Widget _buildList() {
    final stations = _filteredStations;

    if (stations.isEmpty) {
      return const Center(
        child: Text('No hay estaciones cercanas con ese carburante'),
      );
    }

    return ListView.builder(
      itemCount: stations.length,
      itemBuilder: (context, index) {
        final s = stations[index];
        // Precio destacado según el filtro activo
        final highlightPrice = switch (_filter) {
          FuelFilter.gasolina95 => s.priceGasolina95,
          FuelFilter.gasoilA    => s.priceGasoilA,
          FuelFilter.all        => null,
        };

        return ListTile(
          leading: const Icon(Icons.local_gas_station),
          title: Text(s.name),
          subtitle: Text('${s.address}, ${s.municipality}'),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Si hay filtro activo muestra ese precio en grande, si no muestra ambos
              if (highlightPrice != null)
                Text('${highlightPrice.toStringAsFixed(3)} €',
                    style: const TextStyle(
                        fontSize: 14, fontWeight: FontWeight.bold))
              else ...[
                if (s.priceGasolina95 != null)
                  Text('95: ${s.priceGasolina95!.toStringAsFixed(3)} €',
                      style: const TextStyle(fontSize: 12)),
                if (s.priceGasoilA != null)
                  Text('Gleo: ${s.priceGasoilA!.toStringAsFixed(3)} €',
                      style: const TextStyle(fontSize: 12)),
              ],
              Text('${s.distanceKm!.toStringAsFixed(1)} km',
                  style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        );
      },
    );
  }
}
