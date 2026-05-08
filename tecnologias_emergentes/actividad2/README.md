# Sistema Androide IoT — Gestión de datos con ThingSpeak

Aplicación de escritorio desarrollada en Python con Tkinter para la monitorización y gestión de datos IoT a través de la plataforma ThingSpeak.

## Descripción

La aplicación genera datos sintéticos en tiempo real simulando los sensores de un androide y los envía periódicamente al canal ThingSpeak configurado. Permite además consultar el último registro almacenado en la nube.

## Instalación

1. Clona o descarga el repositorio.
2. Crea un entorno virtual e instala las dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests matplotlib python-dotenv
```

3. Crea el fichero `.env` en la raíz del proyecto con tus credenciales de ThingSpeak:

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales:

```ini
THINGSPEAK_CHANNEL_ID=tu_channel_id
THINGSPEAK_WRITE_KEY=tu_write_api_key
THINGSPEAK_READ_KEY=tu_read_api_key
```

> El fichero `.env` está en `.gitignore` y nunca se sube al repositorio.

4. Ejecuta la aplicación:

```bash
python sensores_androide.py
```

## Uso

La aplicación tiene tres secciones accesibles desde el panel lateral:

- **Dashboard** — Muestra las gráficas en tiempo real de los 5 campos del canal, actualizadas cada segundo con datos sintéticos.
- **Canal Androide** — Permite enviar manualmente valores a ThingSpeak o leer el último registro almacenado.
- **API Keys** — Muestra el Channel ID y las claves de lectura/escritura configuradas.

## Canal ThingSpeak

| Parámetro     | Valor                  |
|---------------|------------------------|
| Channel ID    | *******                |
| Write API Key | F1234512345            |
| Read API Key  | 6T123456789            |
| Acceso        | Público                |

### Campos del canal

| Campo   | Nombre                  |
|---------|-------------------------|
| field1  | Carga Cognitiva         |
| field2  | Nivel de Coherencia     |
| field3  | Intensidad Emocional    |
| field4  | Latencia de Inferencia  |
| field5  | Consumo Energético      |

## Interacción con la API de ThingSpeak

La aplicación implementa las tres operaciones principales de la API REST de ThingSpeak.

### 1. Escritura en bulk — mecanismo de ahorro energético

En dispositivos IoT alimentados por batería, la transmisión de datos por red (WiFi, LoRa, etc.) es con diferencia la operación más costosa energéticamente, muy por encima del procesamiento local. Enviar un dato cada segundo mantendría la radio encendida de forma continua, agotando la batería rápidamente.

La aplicación implementa un patrón estándar de eficiencia energética en IoT:

1. **Adquisición local continua** — los datos se generan cada segundo y se almacenan en un buffer en memoria (sin coste de red).
2. **Transmisión en batch cada 15 segundos** — se agrupa la ráfaga de 15 registros en una única petición HTTP, reduciendo el número de transmisiones de 15 a 1. Esto permite apagar la radio entre envíos y alargar significativamente la vida de la batería.

Este enfoque además preserva la resolución temporal de 1 segundo en el canal ThingSpeak, ya que cada entrada incluye su marca de tiempo relativa mediante el parámetro `delta_t`.

**Endpoint:**
```
POST https://api.thingspeak.com/channels/{channel_id}/bulk_update.csv
Content-Type: application/x-www-form-urlencoded
```

**Cuerpo de la petición:**
```
write_api_key=F1234512345&time_format=relative&updates=1,52.3,0.47,38.1,162.5,61.2|1,53.1,0.49,39.4,158.3,62.0|...
```

Cada entrada del campo `updates` sigue el formato `delta_t,field1,field2,...,field5` y se separa con `|`. El parámetro `delta_t` indica los segundos transcurridos desde la entrada anterior (`time_format=relative`). ThingSpeak responde con HTTP `202 Accepted` y `{"success":true}` si el batch se ha procesado correctamente.

### 2. Escritura individual (manual)

Desde la pestaña *Canal Androide* el usuario puede introducir valores manualmente y enviarlos al canal con una petición GET estándar:

**Endpoint:**
```
GET https://api.thingspeak.com/update?api_key={write_key}&field1=X&field2=Y&...
```

ThingSpeak devuelve el número de entrada asignado (p. ej. `42`) si el envío fue correcto, o `0` si fue rechazado.

### 3. Lectura del último registro

El botón *Lectura* recupera la entrada más reciente del canal:

**Endpoint:**
```
GET https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_key}&results=1
```

**Respuesta (JSON):**
```json
{
  "channel": { "id": 3312345, "name": "Androide", ... },
  "feeds": [
    { "created_at": "2026-05-07T22:00:00Z", "field1": "53.1", "field2": "0.49", ... }
  ]
}
```

---

## Límites de la API de ThingSpeak (plan gratuito)

ThingSpeak impone restricciones en su plan gratuito que es importante tener en cuenta:

- **Intervalo mínimo entre envíos: 15 segundos.** Si se intenta escribir en el canal antes de que transcurran 15 segundos desde el último envío, ThingSpeak devuelve `0` como respuesta, indicando que la petición ha sido rechazada.
- **Máximo de mensajes por día: 8.200** entradas por canal.
- La aplicación respeta automáticamente este límite enviando datos a la API **cada 15 segundos**, mientras que las gráficas se actualizan cada segundo con datos generados localmente para mantener una visualización fluida.

### Persistencia local: `datos_pendientes.csv`

Cada segundo, antes de cualquier transmisión, el dato generado se escribe en un fichero CSV local con su timestamp ISO 8601 real:

```
timestamp,Carga_Cognitiva,Nivel_de_Coherencia,Intensidad_Emocional,Latencia_de_Inferencia,Consumo_Energético
2026-05-07T22:00:00Z,52.3100,0.4700,38.1200,162.5000,61.2300
2026-05-07T22:00:01Z,53.0800,0.4900,39.4100,158.3000,62.0100
...
```

Este fichero actúa como **buffer persistente**: si el dispositivo pierde conectividad, los datos siguen acumulándose localmente. En cuanto se restaura la conexión, el siguiente ciclo de 15 segundos enviará **todos los registros pendientes** de una vez, preservando sus timestamps originales gracias a `time_format=absolute`.

El CSV solo se vacía (manteniendo la cabecera) cuando ThingSpeak confirma el envío con HTTP `200` o `202`. Si el envío falla, los datos permanecen intactos para el siguiente intento.

### ¿Por qué datos sintéticos y persistencia local?

Esta arquitectura refleja el comportamiento real de un dispositivo IoT con recursos limitados:

- **Procesamiento local barato** — generar y almacenar datos localmente consume mínima energía.
- **Red como recurso escaso** — la transmisión se activa solo cada 15 segundos, simulando el ciclo de *sleep/wake* de un microcontrolador con radio.
- **Resiliencia ante desconexión** — los datos nunca se pierden: el CSV garantiza que cualquier dato capturado llegará a ThingSpeak en cuanto haya red, con su timestamp de captura original.
- **Sin pérdida de resolución** — todos los datos acumulados se suben íntegros en un solo batch con `time_format=absolute`, manteniendo la granularidad de 1 segundo en ThingSpeak.

El resultado es una aplicación que se comporta de forma fluida visualmente, eficiente energéticamente y resiliente ante fallos de conectividad.

## Estructura del proyecto

```
actividad2/
├── sensores_androide.py      # Aplicación principal
├── datos_pendientes.csv      # Buffer persistente (generado en ejecución)
├── README.md                 # Este archivo
└── requirements.txt          # Dependencias pip
```
