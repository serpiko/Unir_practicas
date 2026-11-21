import glfw
import numpy as np
import ctypes
import math
from OpenGL.GL import *


WINDOW_WIDTH=800
WINDOW_HEIGHT=600
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


def init_window(title):
    """
    Inicializa GLFW, crea una ventana y activa su contexto OpenGL.
    """
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW.")

    # Se solicita un contexto OpenGL 3.3 core
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, title, None, None)
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

    # los VAO describen la estructura mediante stride y offset
    # Cada vértice tiene 6 valores float: 3 de posición y 3 de color.
    stride = 6 * vertices.itemsize
    position_offset = ctypes.c_void_p(0)
    color_offset = ctypes.c_void_p(3*vertices.itemsize)

    # Se describe el atributo de posición:
    glVertexAttribPointer(
        0,                                      # location del atributo en el vertex shader.
        3,                                      # cada posición tiene 3 componentes: x, y, z.
        GL_FLOAT,                               # cada componente es un número float.
        GL_FALSE,                               # ignorar este parámetro.
        stride,                                 # salto entre posiciones consecutivas.
        position_offset                      # la posición empieza en el byte 0 del VBO.
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
        color_offset                            # el color comienza tras los 3 float de posición.
    )

    # Se habilita el atributo de vértice en la location 1.
    glEnableVertexAttribArray(1)

    # Se desactivan los enlaces actuales por limpieza del estado
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    # Cada vértice ocupa 6 valores float.
    vertex_count = len(vertices) // 6

    return vao_id, vbo_id, vertex_count

def create_wheel_vertices(center_x:float, center_y:float, radius:float, center_color:list, rim_color:list, segments=16):
    """
    genera los vértices de una rueda, con GL_TRIANGLE_FAN se dibuja
    primer vértice es el centro, resto son del borde
    """

    # centro concéntrico de todos los triángulos del abanico
    vertices = [center_x, center_y, 0.0, *center_color]

    # vértices del borde, repetimos el primero (+1) para cerrar el círculo
#    for i in range(segments +1):
#        angle = 2*math.pi*i/segments
#        vertices +=[center_x, center_y, *rim_color ]

    aspect_ratio = WINDOW_HEIGHT / WINDOW_WIDTH
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * aspect_ratio * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices += [x, y, 0.0, *rim_color]

    return vertices



def main():

    # Se crea la ventana y se activa el contexto OpenGL asociado.
    # A partir de este momento ya se pueden realizar llamadas a OpenGL.
    window = init_window("Actividad1 de Informática Gráfica, UNIR")

    # Se crea el programa shader a partir del código fuente del
    # vertex shader y del fragment shader.
    shader_program = create_shader_program(
        VERTEX_SHADER_SOURCE,
        FRAGMENT_SHADER_SOURCE
    )

    # Datos de los vértices del triángulo, convertido en montaña.
    # Cada vértice contiene posición (x, y, z) y color (r, g, b).
    mountain_vertices = [
        -0.95, -0.5, 0.0,   0.15, 0.45, 0.15, # base izquierda, verde oscuro
        -0.15, -0.5, 0.0,   0.25, 0.60, 0.25, # base derecha, verde claro
        -0.55,  0.45, 0.0,   1.0, 1.0, 1.0    # cima
    ]

    # Datos de los vértices del pentágono, convertido en sol.
    sun_vertices = [
        0.600, 0.800, 0.0, 1.00, 0.85, 0.00,
        0.743, 0.662, 0.0, 1.00, 0.50, 0.00,
        0.688, 0.438, 0.0, 1.00, 0.85, 0.00,
        0.512, 0.438, 0.0, 1.00, 0.50, 0.00,
        0.457, 0.662, 0.0, 1.00, 0.85, 0.00
    ]
    # Datos de los vértices del coche
    # Todos los vértices tienen el mismo color: no hay interpolación visible.
    car_color = [0.85, 0.15, 0.15] # aplicamos mismo color con expansión de listas
    car_vertices = [
        -0.50, -0.750, 0.0,   *car_color,
        -0.40, -0.700, 0.0,   *car_color,
        -0.30, -0.675, 0.0,   *car_color,
        -0.25, -0.600, 0.0,   *car_color,
         0.00, -0.600, 0.0,   *car_color,
         0.20, -0.600, 0.0,   *car_color,
         0.40, -0.700, 0.0,   *car_color,
         0.55, -0.710, 0.0,   *car_color,
         0.50, -0.900, 0.0,   *car_color,
         0.40, -0.900, 0.0,   *car_color,
         0.30, -0.900, 0.0,   *car_color,
        -0.50, -0.900, 0.0,   *car_color
    ]

    # Vértices de las ruedas:centro gris, borde negro
    center_color = [0.5, 0.5, 0.5]
    rim_color = [0.05,0.05,0.05]
    rear_wheel_vertices = create_wheel_vertices(-0.30, -0.90, 0.06, center_color, rim_color)
    front_wheel_vertices = create_wheel_vertices(0.30, -0.90, 0.06, center_color, rim_color)

    # Datos de los vértices del asfalto: rectángulo con GL_TRIANGLE_STRIP.
    # 4 vértices en ZIGZAG: cada vértice nuevo forma un triángulo con los 2 anteriores.
    #   v2 ──────── v3      triángulo 1: v0, v1, v2
    #   │  ╲         │      triángulo 2: v1, v2, v3
    #   v0 ──────── v1
    road_color = [0.30, 0.30, 0.30]
    road_vertices = [
        -1.0, -1.00, 0.0,   *road_color,   # v0 abajo izquierda
         1.0, -1.00, 0.0,   *road_color,   # v1 abajo derecha
         1.0, -0.96, 0.0,   *road_color,    # v3 arriba derecha
        - 1.0, -0.96, 0.0, *road_color  # v2 arriba izquierda
    ]

    # Datos de los vértices de las marcas viales: cada par de vértices es un segmento.
    road_line_color = [1.0, 1.0, 1.0]
    road_line_vertices = [
        -0.90, -0.98, 0.0, *road_line_color,   -0.78, -0.98, 0.0, *road_line_color,
        -0.65, -0.98, 0.0, *road_line_color,   -0.53, -0.98, 0.0, *road_line_color,
        -0.40, -0.98, 0.0, *road_line_color,   -0.28, -0.98, 0.0, *road_line_color,
        -0.15, -0.98, 0.0, *road_line_color,   -0.03, -0.98, 0.0, *road_line_color,
         0.10, -0.98, 0.0, *road_line_color,    0.22, -0.98, 0.0, *road_line_color,
         0.35, -0.98, 0.0, *road_line_color,    0.47, -0.98, 0.0, *road_line_color,
         0.60, -0.98, 0.0, *road_line_color,    0.72, -0.98, 0.0, *road_line_color,
         0.85, -0.98, 0.0, *road_line_color,    0.97, -0.98, 0.0, *road_line_color
    ]
    # Se crean y configuran los recursos necesarios para dibujar cada objeto.
    # Cada objeto dispone de su propio VAO y VBO.
    mountain_vao, mountain_vbo, mountain_vertex_count = create_object_vao(
        mountain_vertices
    )
    sun_vao, sun_vbo, sun_vertex_count = create_object_vao(
        sun_vertices
    )

    car_vao, car_vbo, car_vertex_count = create_object_vao(car_vertices)
    rear_wheel_vao, rear_wheel_vbo, rear_wheel_vertex_count = create_object_vao(rear_wheel_vertices)
    front_wheel_vao, front_wheel_vbo, front_wheel_vertex_count = create_object_vao(front_wheel_vertices)

    road_vao, road_vbo, road_vertex_count = create_object_vao(road_vertices)
    road_line_vao, road_line_vbo, road_line_vertex_count = create_object_vao(road_line_vertices)

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
        glBindVertexArray(mountain_vao)

        # Se lanza la llamada de dibujo de la montaña
        glDrawArrays(GL_TRIANGLES, 0, mountain_vertex_count)

        # Se activa el VAO del sol
        # Al cambiar de VAO, OpenGL pasa a utilizar los datos y la configuración
        # correspondientes al segundo objeto.
        glBindVertexArray(sun_vao)

        # Se establece el grosor con el que se dibujarán las líneas.
        glLineWidth(8.0)

        # Se lanza una segunda llamada de dibujo.
        # GL_LINE_LOOP conecta los vértices mediante segmentos y une
        # también el último vértice con el primero.
        glDrawArrays(GL_LINE_LOOP, 0, sun_vertex_count)

        # Dibujo 3: Carretera
        glBindVertexArray(road_vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, road_vertex_count)

        glBindVertexArray(road_line_vao)
        glLineWidth(2.0)
        glDrawArrays(GL_LINES, 0, road_line_vertex_count)

        # Dibujo 1: Car
        # se activa el VAO del coche
        glBindVertexArray(car_vao)
        glLineWidth(5.0)
        # llamada de dibujo
        glDrawArrays(GL_LINE_LOOP, 0, car_vertex_count)

        # Dibujo 2: Ruedas
        glBindVertexArray(rear_wheel_vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, rear_wheel_vertex_count)

        glBindVertexArray(front_wheel_vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, front_wheel_vertex_count)
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Se intercambian los buffers.
        glfw.swap_buffers(window)

    # Se liberan los recursos de OpenGL creados durante la ejecución del programa.
    glDeleteVertexArrays(1, [mountain_vao])
    glDeleteVertexArrays(1, [sun_vao])
    glDeleteVertexArrays(1, [car_vao])
    glDeleteVertexArrays(1, [rear_wheel_vao])
    glDeleteVertexArrays(1, [front_wheel_vao])
    glDeleteVertexArrays(1, [road_vao])
    glDeleteVertexArrays(1, [road_line_vao])
    glDeleteBuffers(1, [mountain_vbo])
    glDeleteBuffers(1, [sun_vbo])
    glDeleteBuffers(1, [car_vbo])
    glDeleteBuffers(1, [rear_wheel_vbo])
    glDeleteBuffers(1, [front_wheel_vbo])
    glDeleteBuffers(1, [road_vbo])
    glDeleteBuffers(1, [road_line_vbo])

    glDeleteProgram(shader_program)

    # Se finaliza GLFW y se liberan los recursos asociados a la ventana
    # y al contexto OpenGL.
    glfw.terminate()


if __name__ == "__main__":
    main()
