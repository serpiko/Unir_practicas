import glfw
import numpy as np
import ctypes
from OpenGL.GL import *


# Código fuente del vertex shader
VERTEX_SHADER_SOURCE = """
#version 330 core

layout (location = 0) in vec3 a_position;
layout (location = 1) in vec3 a_color;

out vec3 v_color;

void main()
{
    gl_Position = vec4(a_position, 1.0);

    v_color = a_color;
}
"""


# Código fuente del fragment shader
FRAGMENT_SHADER_SOURCE = """
#version 330 core

in vec3 v_color;

out vec4 frag_color;

void main()
{
    frag_color = vec4(v_color, 1.0);
}
"""


def init_window(width, height, title):
    """
    Inicializa GLFW, crea una ventana y activa su contexto OpenGL.
    """
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW.")

    # Se solicita un contexto OpenGL 3.3 core
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(width, height, title, None, None)
    if not window:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana GLFW.")

    glfw.make_context_current(window)
    return window


def compile_shader(source_code, shader_type):
    """
    Crea y compila un shader a partir de su código fuente.
    Comprueba si la compilación ha sido correcta.
    """
    shader_id = glCreateShader(shader_type)
    glShaderSource(shader_id, source_code)
    glCompileShader(shader_id)

    success = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
    if not success:
        error_message = glGetShaderInfoLog(shader_id).decode()

        if shader_type == GL_VERTEX_SHADER:
            shader_name = "vertex"
        elif shader_type == GL_FRAGMENT_SHADER:
            shader_name = "fragment"
        else:
            shader_name = "desconocido"

        raise Exception(
            f"Error al compilar el shader {shader_name}:\n{error_message}"
        )

    return shader_id


def create_shader_program(vertex_source, fragment_source):
    """
    Compila los shaders, crea el programa, enlaza ambos shaders y
    comprueba si el enlazado ha sido correcto.
    """
    vertex_shader = compile_shader(vertex_source, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_source, GL_FRAGMENT_SHADER)

    program_id = glCreateProgram()
    glAttachShader(program_id, vertex_shader)
    glAttachShader(program_id, fragment_shader)
    glLinkProgram(program_id)

    success = glGetProgramiv(program_id, GL_LINK_STATUS)
    if not success:
        error_message = glGetProgramInfoLog(program_id).decode()
        raise Exception(
            f"Error al enlazar el programa de shaders:\n{error_message}"
        )

    # Una vez enlazado el programa, los shaders individuales ya no son necesarios
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program_id


def create_object_vao(vertices):
    """
    Define los datos de los vértices de un objeto, los almacena en un VBO y configura
    un VAO para indicar cómo deben interpretarse esos datos.

    Devuelve:
        vao_id: identificador del VAO configurado.
        vbo_id: identificador del VBO que almacena los datos de los vértices.
        vertex_count: número de vértices del objeto.
    """

    vertices = np.array(vertices, dtype=np.float32)

    # Se obtiene un identificador para un buffer de OpenGL.
    # Este buffer será el VBO que almacenará los datos de los vértices.
    vbo_id = glGenBuffers(1)

    # Se vincula el buffer al objetivo GL_ARRAY_BUFFER, usado para atributos
    # de vértice como posiciones, colores o coordenadas de textura.
    glBindBuffer(GL_ARRAY_BUFFER, vbo_id)

    # Se copian los datos de vertices al buffer activo de tipo GL_ARRAY_BUFFER (vbo_id).
    # GL_STATIC_DRAW indica que los datos no cambiarán durante el renderizado.
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Se crea un VAO.
    # El VAO guardará la configuración necesaria para interpretar
    # los datos de los vértices.
    vao_id = glGenVertexArrays(1)

    # Se activa el VAO.
    # A partir de este momento, las llamadas que configuren atributos
    # de vértice quedarán asociadas a este VAO.
    glBindVertexArray(vao_id)

    # Cada vértice tiene 6 valores float: 3 de posición y 3 de color.
    stride = 6 * vertices.itemsize

    # Se describe el atributo de posición:
    glVertexAttribPointer(
        0,                                      # location del atributo en el vertex shader.
        3,                                      # cada posición tiene 3 componentes: x, y, z.
        GL_FLOAT,                               # cada componente es un número float.
        GL_FALSE,                               # ignorar este parámetro.
        stride,                                 # salto entre posiciones consecutivas.
        ctypes.c_void_p(0)                      # la posición empieza en el byte 0 del VBO.
    )

    # Se habilita el atributo de vértice en la location 0.
    # Si no se habilita, OpenGL no usará este atributo al dibujar.
    glEnableVertexAttribArray(0)

    # Se describe el atributo de color:
    glVertexAttribPointer(
        1,                                      # location del atributo en el vertex shader.
        3,                                      # cada color tiene 3 componentes: r, g, b.
        GL_FLOAT,                               # cada componente es un número float.
        GL_FALSE,                               # ignorar este parámetro.
        stride,                                 # salto entre colores consecutivos.
        ctypes.c_void_p(3 * vertices.itemsize)  # el color comienza tras los 3 float de posición.
    )

    # Se habilita el atributo de vértice en la location 1.
    glEnableVertexAttribArray(1)

    # Se desactivan los enlaces actuales por limpieza del estado
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    # Cada vértice ocupa 6 valores float.
    vertex_count = len(vertices) // 6

    return vao_id, vbo_id, vertex_count



def main():

    # Se crea la ventana y se activa el contexto OpenGL asociado.
    # A partir de este momento ya se pueden realizar llamadas a OpenGL.
    window = init_window(800, 600, "Ejemplo 3.3")

    # Se crea el programa shader a partir del código fuente del
    # vertex shader y del fragment shader.
    shader_program = create_shader_program(
        VERTEX_SHADER_SOURCE,
        FRAGMENT_SHADER_SOURCE
    )

    # Datos de los vértices del triángulo izquierdo.
    # Cada vértice contiene posición (x, y, z) y color (r, g, b).
    triangle_vertices = [
        -0.8, -0.5, 0.0,   1.0, 0.0, 0.0,
        -0.2, -0.5, 0.0,   0.0, 1.0, 0.0,
        -0.5,  0.3, 0.0,   0.0, 0.0, 1.0
    ]

    # Datos de los vértices del pentágono derecho.
    pentagon_vertices = [
         0.45,  0.35, 0.0,   0.0, 0.0, 1.0,
         0.75,  0.15, 0.0,   0.0, 1.0, 1.0,
         0.65, -0.20, 0.0,   1.0, 0.0, 1.0,
         0.25, -0.20, 0.0,   0.0, 0.0, 1.0,
         0.15,  0.15, 0.0,   0.0, 1.0, 1.0
    ]
    # Datos de los vértices de la carrocería del coche (franja inferior).
    # Todos los vértices tienen el mismo color: no hay interpolación visible.
    car_vertices = [
        -0.50, -0.750, 0.0,   0.85, 0.15, 0.15,
        -0.40, -0.700, 0.0,   0.85, 0.15, 0.15,
        -0.30, -0.675, 0.0,   0.85, 0.15, 0.15,
        -0.25, -0.600, 0.0,   0.85, 0.15, 0.15,
         0.00, -0.600, 0.0,   0.85, 0.15, 0.15,
         0.20, -0.600, 0.0,   0.85, 0.15, 0.15,
         0.40, -0.700, 0.0,   0.85, 0.15, 0.15,
         0.55, -0.710, 0.0,   0.85, 0.15, 0.15,
         0.50, -0.900, 0.0,   0.85, 0.15, 0.15,
         0.40, -0.900, 0.0,   0.85, 0.15, 0.15,
         0.30, -0.900, 0.0,   0.85, 0.15, 0.15
    ]

    # Se crean y configuran los recursos necesarios para dibujar cada objeto.
    # Cada objeto dispone de su propio VAO y VBO.
    triangle_vao, triangle_vbo, triangle_vertex_count = create_object_vao(
        triangle_vertices
    )
    pentagon_vao, pentagon_vbo, pentagon_vertex_count = create_object_vao(
        pentagon_vertices
    )

    car_vao, car_vbo, car_vertex_count = create_object_vao(car_vertices)

    # Bucle principal de renderizado.
    # Se ejecuta una vez por cada frame hasta que el usuario cierre la ventana.
    while not glfw.window_should_close(window):

        # Se procesan los eventos pendientes de la ventana.
        glfw.poll_events()

        # Se define el color de limpieza del buffer de color, y se limpia.
        glClearColor(0.8, 0.8, 0.8, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # Se activa el programa shader que se utilizará para dibujar.
        # A partir de este momento, las llamadas de dibujo usarán este programa.
        # En este ejemplo, ambos objetos utilizan el mismo programa shader.
        glUseProgram(shader_program)

        # Se activa el VAO del triángulo.
        # El VAO contiene la configuración necesaria para que OpenGL sepa
        # de qué VBO leer los datos y cómo interpretar sus atributos.

        glLineWidth(1.0)
        glBindVertexArray(triangle_vao)

        # Se lanza la llamada de dibujo del triángulo.
        glDrawArrays(GL_TRIANGLES, 0, triangle_vertex_count)

        # Se activa el VAO del pentágono.
        # Al cambiar de VAO, OpenGL pasa a utilizar los datos y la configuración
        # correspondientes al segundo objeto.
        glBindVertexArray(pentagon_vao)

        # Se establece el grosor con el que se dibujarán las líneas.
        glLineWidth(8.0)

        # Se lanza una segunda llamada de dibujo.
        # GL_LINE_LOOP conecta los vértices mediante segmentos y une
        # también el último vértice con el primero.
        glDrawArrays(GL_LINE_LOOP, 0, pentagon_vertex_count)

        # Dibujo 1: Car
        # se activa el VAO del coche
        glBindVertexArray(car_vao)
        glLineWidth(5.0)
        # llamada de dibujo
        glDrawArrays(GL_LINE_STRIP, 0, car_vertex_count)

        # Se intercambian los buffers.
        glfw.swap_buffers(window)

    # Se liberan los recursos de OpenGL creados durante la ejecución del programa.
    glDeleteVertexArrays(1, [triangle_vao])
    glDeleteVertexArrays(1, [pentagon_vao])
    glDeleteVertexArrays(1, [car_vao])
    glDeleteBuffers(1, [triangle_vbo])
    glDeleteBuffers(1, [pentagon_vbo])
    glDeleteBuffers(1, [car_vbo])
    glDeleteProgram(shader_program)

    # Se finaliza GLFW y se liberan los recursos asociados a la ventana
    # y al contexto OpenGL.
    glfw.terminate()


if __name__ == "__main__":
    main()
