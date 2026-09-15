# Jarvis

Asistente de voz en Python capaz de abrir aplicaciones del ordenador y consultar
el tiempo actual o el pronóstico de los próximos cinco días.

## Preparación en Windows

1. Crea y activa un entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Instala las dependencias:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Crea una clave en OpenWeatherMap y configúrala para la sesión actual:

   ```powershell
   $env:OPENWEATHER_API_KEY="tu-clave"
   ```

4. Inicia Jarvis:

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
 
