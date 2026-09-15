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
- `Tiempo en Madrid`
- `¿Qué temperatura hace en Cercedilla?`
- `Pronóstico en Barcelona`
- `¿Qué hora es?`
- `Salir`

Las aplicaciones conocidas se definen por sistema operativo en
`Scritps/Jarvis.py`. Jarvis también intenta encontrar otros ejecutables que estén
disponibles en `PATH`.
 
