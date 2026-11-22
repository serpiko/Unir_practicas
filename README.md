# Actividad 1 — Primer render con OpenGL moderno

Informática Gráfica y Visualización · UNIR — Raúl Muñoz Díaz

Composición 2D "coche en la carretera" construida a partir del ejemplo 3.3:
OpenGL 3.3 core, shaders sencillos, atributos de posición y color, un VBO/VAO por figura.

## Requisitos

- Python 3.13 (versión con la que se ha probado)
- Tarjeta gráfica / driver con soporte de OpenGL 3.3

Las dependencias están en `requirements.txt` (glfw, numpy, PyOpenGL).
El entorno virtual no se incluye en la entrega porque no es portable entre sistemas.

## Ejecución

Linux / macOS:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python actividad1.py
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python actividad1.py
```

## Contenido

| Fichero | Descripción |
|---|---|
| `actividad1.py` | Programa completo (shaders incluidos en el propio código) |
| `requirements.txt` | Dependencias de Python |
