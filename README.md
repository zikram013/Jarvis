# Jarvis

Asistente de voz en Python capaz de abrir aplicaciones, consultar el tiempo y
responder preguntas mediante un modelo de lenguaje ejecutado localmente. Para
datos actuales puede realizar búsquedas web sin utilizar una API de pago.

## Preparación en Windows

1. Instala [Ollama para Windows](https://ollama.com/download/windows) y descarga
   el modelo local predeterminado:

   ```powershell
   ollama pull qwen3:4b
   ```

2. Crea y activa un entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Si quieres utilizar los comandos meteorológicos, crea una clave gratuita en
   OpenWeatherMap y configúrala para la sesión actual:

   ```powershell
   $env:OPENWEATHER_API_KEY="tu-clave"
   ```

5. Inicia Jarvis. Ollama debe permanecer abierto en segundo plano:

   ```powershell
   py Scritps/Jarvis.py
   ```

## Ejemplos de comandos de voz

- `Abre la calculadora`
- `Abrir bloc de notas`
- `Abre el explorador de archivos`
- `Ejecuta Steam`
- `Quiero que abras Visual Studio Code`
- `¿Puedes iniciar Spotify, por favor?`
- `Tiempo en Madrid`
- `¿Qué temperatura hace en Cercedilla?`
- `Pronóstico en Barcelona`
- `¿Qué hora es?`
- `¿Cuál es el próximo partido del Atlético de Madrid?`
- `¿Cuánto se tarda de Madrid a Toledo en coche?`
- `¿Quién fue el primer emperador romano?`
- `¿Y quién le sucedió?`
- `Salir`

Jarvis entiende distintas formas cotidianas de pedir la apertura de una
aplicación: `abre`, `ejecuta`, `inicia`, `lanza` y `arranca`, incluidas varias de
sus conjugaciones.

Para encontrar una aplicación, primero consulta las aplicaciones del sistema y
el `PATH`. En Windows también revisa el menú Inicio, las aplicaciones de
Microsoft Store y el Registro. Si aún no la encuentra, realiza una búsqueda por
nombre en las unidades locales; esta última búsqueda puede tardar la primera
vez. Los resultados encontrados se conservan en memoria mientras Jarvis siga
abierto.

## Preguntas generales y datos actuales

Las preguntas que no sean comandos locales se envían a Ollama a través de
`http://localhost:11434`. El texto se procesa en el ordenador y no hace falta
una clave de OpenAI ni existe un coste por pregunta. Jarvis conserva las últimas
intervenciones mientras permanezca abierto para entender preguntas de
seguimiento.

Cuando detecta una pregunta que puede depender de información actual —deportes,
noticias, precios, horarios o trayectos— obtiene hasta cinco resultados mediante
la biblioteca `ddgs` y se los entrega al modelo local. Los resultados consultados
se muestran en la consola. Esta búsqueda no requiere clave, pero depende de un
servicio externo sin garantía de disponibilidad y envía a Internet el texto de
la búsqueda. Si falla, Jarvis avisará y no debería inventar datos actuales.

La configuración se puede modificar mediante variables de entorno:

```powershell
# Usar otro modelo que ya hayas descargado con Ollama
$env:JARVIS_OLLAMA_MODEL="qwen3:4b"

# auto: solo datos actuales; always: todas las preguntas; never: desactivada
$env:JARVIS_WEB_SEARCH="auto"

# Región preferida para los resultados
$env:JARVIS_SEARCH_REGION="es-es"
```

En equipos con pocos recursos se puede utilizar `qwen3:1.7b`; ofrecerá
respuestas más rápidas, aunque normalmente serán menos precisas:

```powershell
ollama pull qwen3:1.7b
$env:JARVIS_OLLAMA_MODEL="qwen3:1.7b"
```
 
