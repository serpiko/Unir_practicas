import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

// Punto de entrada de la aplicación Flutter
void main() {
  runApp(const GasAroundApp());
}

// Widget raíz de la aplicación: configura el tema y la pantalla inicial
class GasAroundApp extends StatelessWidget {
  const GasAroundApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GasAround',
      // Tema visual de la app basado en un color semilla verde
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      // La app arranca con la pantalla de presentación
      home: const SplashScreen(),
    );
  }
}
