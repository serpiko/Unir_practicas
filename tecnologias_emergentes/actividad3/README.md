# Actividad 3 
# Asignatura Tecnologías Emergentes
# Curso de adapdación al Grado en Informática
# Universidad Internacional de la Rioja (UNIR)

# Actividad 3 (individual): Trabajando con datos provenientes de API

## Objetivos

    • Familiarizarse con las plataformas de datos abiertos.
    • Familiarizarse con las API que ofrecen determinadas plataformas.
    • Diseñar e implementar una aplicación que haga uso de API para el tratamiento de datos.

## Descripción de la actividad

El acceso a datos de todo tipo es un elemento fundamental que hoy en día permiten los organismos, tanto públicos como privados, con el fin de poder obtener datos actualizados de manera sencilla y fáci de gestionar. En este sentido, además de los formatos estándar de ficheros de intercambio (CSV, JSON, XML, etc.), tenemos disponibles una gran variedad de API que dotan de cierta automatización al proceso de obtención. Una de las API disponibles, que tiene carácter público, está relacionada con los hidrocarburos y es con la que practicaremos en la presente actividad.

## Fuentes de datos 
El Gobierno de España nos ofrece dos portales relativos a los hidrocarburos:

    • Datos abiertos: contiene datos diarios actualizados relativos a los precios de los carburantes, así como a la localización de las diferentes estaciones de servicio. Además, ofrece ficheros de datos en diferentes formatos (XLS, KML y JSON), así como servicios REST para su acceso.

geoportales de hidrocarburos:
https://datos.gob.es/es/catalogo/e05068001-precio-de-carburantes-en-las-gasolineras-espanolas
https://geoportalgasolineras.es/geoportal-instalaciones/Inicio

# Acceso a los datos
En esta actividad se podrán utilizar ambos portales, ya que la idea será aprovechar las API que nos ofrecen para poder obtener y mostrar datos.

En el primer portal nos vamos a encontrar con que algunos textos poseen una terminación «Servicio REST», lo que nos indica que este es el servicio que debemos seleccionar.

Pulsando el botón Acceder, ubicado a la derecha del texto, se abrirá la llamada a la API REST correspondiente. 

En el segundo portal, debemos ir a la pestaña «Descargar ficheros» y, dentro de esta, seleccionar la opción «Información actualizada de precios».

En la parte inferior se mostrarán diferentes servicios REST, algunos de los cuales permiten filtrar los datos por días, municipios y productos.

## Pautas de elaboración

• Apartado 1. Tomando contacto con la API:

El primer punto será familiarizarse con la API de los portales. Para ello, revisando la documentación de ayuda de los portales, accederemos a los mismos para obtener la información que indique el profesorado de la asignatura.

En este punto se debe adjuntar el código de las consultas a la API, es decir, las direcciones de la API REST que se han introducido, para obtener los datos.

• Apartado 2. Creando la aplicación para la lectura de datos:

Llega el momento de implementar la solución, en el lenguaje que seleccione el alumnado, que nos permitirá gestionar los datos de la API de los portales que hemos revisado en el apartado anterior. La aplicación desarrollada deberá permitir la localización del dispositivo móvil, así como la gestión de los datos que indique el profesorado de la asignatura.

