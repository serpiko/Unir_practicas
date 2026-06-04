import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/gas_station.dart';
import '../services/sync_service.dart';
import '../services/database_service.dart';

// Nombres oficiales de las 19 Comunidades Autónomas indexados por IDCCAA de MineTur
const _ccaaNames = {
  '01': 'Andalucía',
  '02': 'Aragón',
  '03': 'Asturias',
  '04': 'Illes Balears',
  '05': 'Canarias',
  '06': 'Cantabria',
  '07': 'Castilla-La Mancha',
  '08': 'Castilla y León',
  '09': 'Cataluña',
  '10': 'C. Valenciana',
  '11': 'Extremadura',
  '12': 'Galicia',
  '13': 'Madrid',
  '14': 'Murcia',
  '15': 'Navarra',
  '16': 'País Vasco',
  '17': 'La Rioja',
  '18': 'Ceuta',
  '19': 'Melilla',
};

// Tipos de carburante disponibles como filtro de precio
enum FuelFilter { all, gasolina95, gasoilA }

// Pantalla principal: muestra gasolineras por proximidad GPS o por zona (CCAA + municipio)
class StationListScreen extends StatefulWidget {
  const StationListScreen({super.key});

  @override
  State<StationListScreen> createState() => _StationListScreenState();
}

class _StationListScreenState extends State<StationListScreen> {
  final _sync = SyncService.instance;
  final _db   = DatabaseService.instance;

  List<GasStation> _allStations = [];
  bool _loading  = false;
  bool _syncing  = false;
  String? _error;
  FuelFilter _filter = FuelFilter.all;

  // Estado del filtro por zona
  List<String> _ccaaIds     = [];       // IDs de CCAA presentes en la BD
  String?      _selectedCcaa;           // CCAA activa
  List<String> _municipios  = [];       // Municipios de la CCAA seleccionada
  String?      _selectedMunicipio;      // Municipio activo
  bool         _zoneMode    = false;    // true cuando la lista viene del filtro de zona

  @override
  void initState() {
    super.initState();
    _loadCcaaIds();
  }

  // Carga los IDs de CCAA disponibles en la BD para poblar los chips
  Future<void> _loadCcaaIds() async {
    final ids = await _db.getDistinctCcaa();
    if (mounted) setState(() => _ccaaIds = ids);
  }

  // Al pulsar un chip de CCAA: carga los municipios de esa CCAA
  Future<void> _onCcaaSelected(String idCcaa) async {
    setState(() {
      _selectedCcaa      = idCcaa;
      _selectedMunicipio = null;
      _municipios        = [];
    });
    final munis = await _db.getMunicipiosByCcaa(idCcaa);
    if (mounted) setState(() => _municipios = munis);
  }

  // Al seleccionar un municipio en el dropdown: carga sus estaciones sin GPS
  Future<void> _onMunicipioSelected(String municipio) async {
    setState(() {
      _selectedMunicipio = municipio;
      _loading           = true;
      _error             = null;
    });
    try {
      final stations = await _db.getStationsByMunicipio(municipio);
      setState(() {
        _allStations = stations;
        _zoneMode    = true;
        _loading     = false;
      });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  // Aplica el filtro de carburante sobre la lista activa
  // En modo zona muestra hasta 20 resultados; en modo GPS las 7 más cercanas
  List<GasStation> get _filteredStations {
    final pool = _zoneMode ? _allStations : _allStations.take(50).toList();
    final limit = _zoneMode ? 20 : 7;

    switch (_filter) {
      case FuelFilter.gasolina95:
        return (pool.where((s) => s.priceGasolina95 != null).toList()
              ..sort((a, b) => a.priceGasolina95!.compareTo(b.priceGasolina95!)))
            .take(limit)
            .toList();
      case FuelFilter.gasoilA:
        return (pool.where((s) => s.priceGasoilA != null).toList()
              ..sort((a, b) => a.priceGasoilA!.compareTo(b.priceGasoilA!)))
            .take(limit)
            .toList();
      case FuelFilter.all:
        return pool.take(limit).toList();
    }
  }

  // Busca las gasolineras más cercanas usando el GPS del dispositivo
  Future<void> _loadNearbyStations() async {
    setState(() {
      _loading           = true;
      _error             = null;
      _zoneMode          = false;
      _selectedCcaa      = null;
      _selectedMunicipio = null;
      _municipios        = [];
    });

    try {
      final permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        await Geolocator.requestPermission();
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      );

      final (stations: all, :isSyncing) = await _sync.getStations(
        onSyncComplete: () {
          if (mounted) setState(() => _syncing = false);
        },
      );

      _syncing = isSyncing;

      for (final s in all) {
        s.distanceKm = Geolocator.distanceBetween(
              position.latitude, position.longitude,
              s.latitude,        s.longitude,
            ) / 1000;
      }
      all.sort((a, b) => (a.distanceKm ?? 0).compareTo(b.distanceKm ?? 0));

      setState(() { _allStations = all; _loading = false; });

      // Recarga los IDs de CCAA por si la BD se acaba de poblar por primera vez
      _loadCcaaIds();
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GasAround'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
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
        tooltip: 'Usa el GPS para mostrar las gasolineras más cercanas',
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_error!, style: const TextStyle(color: Colors.red)),
        ),
      );
    }

    if (_allStations.isEmpty && !_zoneMode) {
      return Column(
        children: [
          _buildFilterBar(),
          const Expanded(
            child: Center(child: Text('Pulsa el botón para buscar gasolineras cercanas')),
          ),
        ],
      );
    }

    return Column(
      children: [
        _buildFilterBar(),
        if (_allStations.isNotEmpty || _zoneMode) Expanded(child: _buildList()),
      ],
    );
  }

  Widget _buildFilterBar() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Fila 1: filtro por tipo de carburante
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
          child: Row(
            children: [
              _fuelChip(FuelFilter.all,        'Distancia',   Icons.near_me),
              _fuelChip(FuelFilter.gasolina95, 'Gasolina 95', Icons.local_gas_station),
              _fuelChip(FuelFilter.gasoilA,    'Gasoleo A',   Icons.opacity),
            ],
          ),
        ),
        // Fila 2: filtro por CCAA (solo si hay datos en la BD)
        if (_ccaaIds.isNotEmpty)
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 4, 12, 0),
            child: Row(
              children: _ccaaIds.map((id) {
                final selected = _selectedCcaa == id;
                return Tooltip(
                  message: selected
                      ? 'Toca para quitar el filtro de ${_ccaaNames[id] ?? id}'
                      : 'Filtrar gasolineras de ${_ccaaNames[id] ?? id}',
                  child: Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      selected: selected,
                      label: Text(_ccaaNames[id] ?? id),
                      onSelected: (_) => selected
                          ? setState(() { _selectedCcaa = null; _municipios = []; _selectedMunicipio = null; })
                          : _onCcaaSelected(id),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        // Fila 3: dropdown de municipio (solo si hay una CCAA seleccionada)
        if (_selectedCcaa != null && _municipios.isNotEmpty)
          Tooltip(
            message: 'Selecciona un municipio para ver sus gasolineras sin necesidad de GPS',
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
              child: DropdownButton<String>(
                isExpanded: true,
                hint: const Text('Selecciona municipio'),
                value: _selectedMunicipio,
                items: _municipios
                    .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                    .toList(),
                onChanged: (m) { if (m != null) _onMunicipioSelected(m); },
              ),
            ),
          ),
      ],
    );
  }

  static const _fuelTooltips = {
    FuelFilter.all:        'Ordena las gasolineras cercanas por distancia',
    FuelFilter.gasolina95: 'Muestra las más baratas en Gasolina 95 entre las cercanas',
    FuelFilter.gasoilA:    'Muestra las más baratas en Gasoleo A entre las cercanas',
  };

  Widget _fuelChip(FuelFilter value, String label, IconData icon) {
    return Tooltip(
      message: _fuelTooltips[value] ?? '',
      child: Padding(
        padding: const EdgeInsets.only(right: 8),
        child: FilterChip(
          selected: _filter == value,
          label: Text(label),
          avatar: Icon(icon, size: 16),
          onSelected: (_) => setState(() => _filter = value),
        ),
      ),
    );
  }

  // Muestra un panel inferior con el detalle completo de la estación
  void _showDetail(GasStation s) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Nombre
            Text(s.name,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            // Dirección
            Row(children: [
              const Icon(Icons.location_on, size: 16, color: Colors.grey),
              const SizedBox(width: 6),
              Expanded(child: Text('${s.address}, ${s.municipality} ${s.postalCode}')),
            ]),
            // Horario
            if (s.horario != null && s.horario!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(children: [
                const Icon(Icons.access_time, size: 16, color: Colors.grey),
                const SizedBox(width: 6),
                Text(s.horario!),
              ]),
            ],
            const Divider(height: 24),
            // Precios
            if (s.priceGasolina95 != null)
              _priceRow('Gasolina 95 E5', s.priceGasolina95!),
            if (s.priceGasoilA != null)
              _priceRow('Gasoleo A', s.priceGasoilA!),
            if (s.distanceKm != null) ...[
              const SizedBox(height: 4),
              Text('Distancia: ${s.distanceKm!.toStringAsFixed(1)} km',
                  style: const TextStyle(color: Colors.grey, fontSize: 13)),
            ],
            const SizedBox(height: 16),
            // Botón de navegación
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                icon: const Icon(Icons.directions),
                label: const Text('Cómo llegar'),
                onPressed: () {
                  Navigator.pop(context);
                  _openInMaps(s);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _priceRow(String label, double price) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label),
            Text('${price.toStringAsFixed(3)} €',
                style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
      );

  // Abre Google Maps (o cualquier app de mapas del sistema) con navegación a la estación
  Future<void> _openInMaps(GasStation s) async {
    final uri = Uri.parse(
      'geo:${s.latitude},${s.longitude}?q=${s.latitude},${s.longitude}(${Uri.encodeComponent(s.name)})',
    );
    if (!await launchUrl(uri)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se encontró app de mapas instalada')),
        );
      }
    }
  }

  Widget _buildList() {
    final stations = _filteredStations;

    if (stations.isEmpty) {
      return const Center(child: Text('No hay estaciones con ese carburante'));
    }

    return ListView.builder(
      itemCount: stations.length,
      itemBuilder: (context, index) {
        final s = stations[index];
        final highlightPrice = switch (_filter) {
          FuelFilter.gasolina95 => s.priceGasolina95,
          FuelFilter.gasoilA    => s.priceGasoilA,
          FuelFilter.all        => null,
        };

        return ListTile(
          dense: true,
          leading: const Icon(Icons.local_gas_station),
          onTap: () => _showDetail(s),
          title: Text(s.name, style: const TextStyle(fontSize: 14)),
          subtitle: Text('${s.address}, ${s.municipality}',
              style: const TextStyle(fontSize: 12)),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (highlightPrice != null)
                Text('${highlightPrice.toStringAsFixed(3)} €',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold))
              else ...[
                if (s.priceGasolina95 != null)
                  Text('95: ${s.priceGasolina95!.toStringAsFixed(3)} €',
                      style: const TextStyle(fontSize: 11)),
                if (s.priceGasoilA != null)
                  Text('A: ${s.priceGasoilA!.toStringAsFixed(3)} €',
                      style: const TextStyle(fontSize: 11)),
              ],
              if (s.distanceKm != null)
                Text('${s.distanceKm!.toStringAsFixed(1)} km',
                    style: const TextStyle(fontSize: 10, color: Colors.grey)),
            ],
          ),
        );
      },
    );
  }
}
