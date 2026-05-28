import 'package:flutter/material.dart';
import 'station_list_screen.dart';

// Pantalla de presentación: se muestra al arrancar la app durante 2 segundos
// Usa pushReplacement para que el usuario no pueda volver atrás al pulsar "back"
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _fadeIn;

  @override
  void initState() {
    super.initState();

    // Animación de aparición gradual del contenido durante 800ms
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..forward();

    _fadeIn = CurvedAnimation(parent: _controller, curve: Curves.easeIn);

    // Navega a la pantalla principal tras 3 segundos
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const StationListScreen()),
        );
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colors.primary,
      body: FadeTransition(
        opacity: _fadeIn,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icono principal de la app
              Icon(
                Icons.local_gas_station,
                size: 80,
                color: colors.onPrimary,
              ),
              const SizedBox(height: 24),
              // Nombre de la app
              Text(
                'GasAround',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: colors.onPrimary,
                  letterSpacing: 2,
                ),
              ),
              const SizedBox(height: 8),
              // Subtítulo descriptivo
              Text(
                'Gasolineras cerca de ti',
                style: TextStyle(
                  fontSize: 14,
                  color: colors.onPrimary.withValues(alpha: 0.8),
                  letterSpacing: 1,
                ),
              ),
              // mi firma y referencia la asignatura y Unir
              Text(
                'por Raúl Muñoz para la asignatura',
                style: TextStyle(
                  fontSize: 10,
                  color: colors.onPrimary.withValues(alpha: 0.8),
                  letterSpacing: 1,
                ),
              ),
              Text(
                'Tecnologías Emergentes, Grado Unir',
                style: TextStyle(
                  fontSize: 10,
                  color: colors.onPrimary.withValues(alpha: 0.8, red: 1, green: 0.5),
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
