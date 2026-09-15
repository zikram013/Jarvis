import datetime
import os
import platform
import shutil
import subprocess

import pyttsx3
import requests
import speech_recognition as sr


# Configuración general
SO = platform.system()
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"
URL_PRONOSTICO = "https://api.openweathermap.org/data/2.5/forecast"

# Inicializar el motor de voz
engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("voice", "spanish")

# Comandos específicos para Windows
COMANDOS_SISTEMA_WINDOWS = {
    "configuración": "start ms-settings:",
    "configuracion": "start ms-settings:",
    "panel de control": "control",
    "administrador de tareas": "taskmgr",
    "bloc de notas": "notepad",
    "explorador de archivos": "explorer",
    "cmd": "cmd",
    "powershell": "powershell",
    "calculadora": "calc",
    "msi center": r'"C:\Program Files (x86)\MSI\MSI Center\MSI.CentralServer.exe"',
    "paint": "mspaint",
    "wordpad": "write",
    "registro de windows": "regedit",
    "administrador de discos": "diskmgmt.msc",
    "servicios": "services.msc",
}

# Comandos específicos para macOS
COMANDOS_SISTEMA_MAC = {
    "configuración": ["open", "-b", "com.apple.systempreferences"],
    "configuracion": ["open", "-b", "com.apple.systempreferences"],
    "explorador de archivos": ["open", "."],
    "terminal": ["open", "-a", "Terminal"],
    "safari": ["open", "-a", "Safari"],
    "calculadora": ["open", "-a", "Calculator"],
}

# Comandos específicos para Linux
COMANDOS_SISTEMA_LINUX = {
    "configuración": ["gnome-control-center"],
    "configuracion": ["gnome-control-center"],
    "explorador de archivos": ["xdg-open", "."],
    "terminal": ["gnome-terminal"],
    "firefox": ["firefox"],
    "calculadora": ["gnome-calculator"],
}

DIAS_SEMANA = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}

MESES = {
    "January": "enero",
    "February": "febrero",
    "March": "marzo",
    "April": "abril",
    "May": "mayo",
    "June": "junio",
    "July": "julio",
    "August": "agosto",
    "September": "septiembre",
    "October": "octubre",
    "November": "noviembre",
    "December": "diciembre",
}


def speak(text):
    """Convierte texto en voz."""
    engine.say(text)
    engine.runAndWait()


def listen():
    """Escucha la voz del usuario y la convierte en texto."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio, language="es-ES")
        print(f"Dijiste: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print("No pude entender el audio.")
    except sr.RequestError:
        print("Error al conectar con el servicio de reconocimiento.")
    return None


def comprobar_api_clima():
    """Comprueba que la clave de OpenWeatherMap está configurada."""
    if API_KEY:
        return True

    mensaje = (
        "No está configurada la clave de OpenWeatherMap. "
        "Define la variable OPENWEATHER_API_KEY antes de iniciar Jarvis."
    )
    print(f"❌ {mensaje}")
    speak(mensaje)
    return False


def solicitar_ciudad(pregunta):
    """Solicita una ciudad cuando no venía incluida en el comando."""
    speak(pregunta)
    ciudad = listen()
    if not ciudad:
        speak("No pude entender la ciudad. Inténtalo de nuevo.")
    return ciudad


def obtener_clima(ciudad=None):
    """Obtiene la temperatura actual de una ciudad."""
    if not comprobar_api_clima():
        return

    ciudad = ciudad or solicitar_ciudad("¿De qué ciudad quieres conocer el clima?")
    if not ciudad:
        return

    parametros = {
        "q": ciudad,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es",
    }

    try:
        respuesta = requests.get(URL_CLIMA, params=parametros, timeout=10)
    except requests.RequestException as error:
        print(f"❌ Error al consultar el clima: {error}")
        speak("No pude conectar con el servicio del clima.")
        return

    if respuesta.status_code == 200:
        datos = respuesta.json()
        temperatura = round(datos["main"]["temp"])
        descripcion = datos["weather"][0]["description"]
        mensaje = (
            f"La temperatura actual en {ciudad} es de {temperatura} grados "
            f"y está {descripcion}."
        )
        speak(mensaje)
        print(f"📍 {ciudad}: {temperatura}°C, {descripcion.capitalize()}")
    else:
        speak(
            f"No pude obtener el clima de {ciudad}. "
            "Verifica el nombre o intenta otra ciudad."
        )


def obtener_pronostico(ciudad=None):
    """Obtiene el pronóstico del clima para los próximos cinco días."""
    if not comprobar_api_clima():
        return

    ciudad = ciudad or solicitar_ciudad("¿Para qué ciudad quieres el pronóstico?")
    if not ciudad:
        return

    parametros = {
        "q": ciudad,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es",
        "cnt": 40,
    }

    try:
        respuesta = requests.get(URL_PRONOSTICO, params=parametros, timeout=10)
    except requests.RequestException as error:
        print(f"❌ Error al consultar el pronóstico: {error}")
        speak("No pude conectar con el servicio del clima.")
        return

    if respuesta.status_code != 200:
        speak(
            f"No pude obtener el pronóstico para {ciudad}. "
            "Verifica el nombre o intenta otra ciudad."
        )
        return

    pronostico_por_dia = {}
    for entrada in respuesta.json()["list"]:
        fecha_texto = entrada["dt_txt"].split(" ")[0]
        temp_max = round(entrada["main"]["temp_max"])
        temp_min = round(entrada["main"]["temp_min"])
        descripcion = entrada["weather"][0]["description"]

        if fecha_texto not in pronostico_por_dia:
            pronostico_por_dia[fecha_texto] = {
                "temp_max": temp_max,
                "temp_min": temp_min,
                "descripcion": descripcion,
            }
        else:
            pronostico = pronostico_por_dia[fecha_texto]
            pronostico["temp_max"] = max(pronostico["temp_max"], temp_max)
            pronostico["temp_min"] = min(pronostico["temp_min"], temp_min)

    speak(f"Este es el pronóstico para {ciudad} en los próximos días:")
    print(f"📍 Pronóstico para {ciudad}:")

    for fecha, info in pronostico_por_dia.items():
        fecha_objeto = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        dia_semana = DIAS_SEMANA[fecha_objeto.strftime("%A")]
        mes = MESES[fecha_objeto.strftime("%B")]
        dia_numero = fecha_objeto.day
        mensaje = (
            f"El {dia_semana} {dia_numero} de {mes} hará una máxima de "
            f"{info['temp_max']} grados y una mínima de {info['temp_min']} grados, "
            f"con {info['descripcion']}."
        )
        speak(mensaje)
        print(mensaje)


def comando_sistema(nombre):
    """Devuelve el comando conocido para el sistema operativo actual."""
    if SO == "Windows":
        return COMANDOS_SISTEMA_WINDOWS.get(nombre)
    if SO == "Darwin":
        return COMANDOS_SISTEMA_MAC.get(nombre)
    if SO == "Linux":
        return COMANDOS_SISTEMA_LINUX.get(nombre)
    return None


def encontrar_ejecutable(nombre):
    """Busca una aplicación instalada y disponible en PATH."""
    candidatos = (nombre, nombre.replace(" ", ""), nombre.replace(" ", "-"))
    for candidato in candidatos:
        ruta = shutil.which(candidato)
        if ruta:
            return ruta
    return None


def normalizar_nombre_aplicacion(nombre):
    """Elimina artículos habituales de una orden como 'abre la calculadora'."""
    nombre = nombre.strip()
    for articulo in ("el ", "la ", "los ", "las "):
        if nombre.startswith(articulo):
            return nombre[len(articulo):].strip()
    return nombre


def abrir_aplicacion(nombre):
    """Abre una aplicación conocida o un ejecutable instalado."""
    if not nombre:
        speak("¿Qué aplicación quieres abrir?")
        nombre = listen()
        if not nombre:
            return

    nombre = normalizar_nombre_aplicacion(nombre)

    try:
        comando = comando_sistema(nombre)
        if comando:
            print(f"🔍 Ejecutando: {comando}")
            speak(f"Abriendo {nombre}")
            if SO == "Windows":
                subprocess.Popen(
                    comando,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    comando,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return

        ruta = encontrar_ejecutable(nombre)
        if ruta:
            print(f"🔍 Encontrado: {ruta}")
            speak(f"Abriendo {nombre}")
            if SO == "Windows":
                os.startfile(ruta)
            else:
                subprocess.Popen(
                    [ruta],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return

        speak(f"No encontré {nombre} en tu sistema.")
        print(f"❌ No se encontró la aplicación: {nombre}")
    except (OSError, subprocess.SubprocessError) as error:
        speak(f"No pude abrir {nombre}.")
        print(f"❌ Error al abrir {nombre}: {error}")


def extraer_ciudad(command):
    """Extrae la ciudad situada después de la última preposición 'en'."""
    if " en " not in command:
        return None
    ciudad = command.rsplit(" en ", 1)[1].strip(" ?.!")
    return ciudad or None


def resolver_consulta_tiempo(command):
    """Decide entre clima actual y pronóstico cuando la orden es ambigua."""
    ciudad = extraer_ciudad(command)
    if ciudad or "hoy" in command or "actual" in command or "temperatura" in command:
        obtener_clima(ciudad)
        return

    speak("¿Quieres la temperatura actual o el pronóstico?")
    respuesta = listen()
    if respuesta and (
        "pronóstico" in respuesta
        or "pronostico" in respuesta
        or "próximos días" in respuesta
    ):
        obtener_pronostico()
    else:
        obtener_clima()


def execute_command(command):
    """Ejecuta el comando de voz del usuario."""
    if "hora" in command:
        hora = datetime.datetime.now().strftime("%H:%M")
        speak(f"La hora actual es {hora}")
    elif command.startswith("abrir ") or command.startswith("abre "):
        nombre_app = command.split(maxsplit=1)[1].strip()
        abrir_aplicacion(nombre_app)
    elif command in ("abrir", "abre"):
        abrir_aplicacion("")
    elif "pronóstico" in command or "pronostico" in command or "próximos días" in command:
        obtener_pronostico(extraer_ciudad(command))
    elif "tiempo" in command or "clima" in command or "temperatura" in command:
        resolver_consulta_tiempo(command)
    elif "salir" in command or "apagar" in command:
        speak("Apagando el asistente. Hasta luego.")
        raise SystemExit
    else:
        speak("No reconozco ese comando.")


def main():
    """Inicia el bucle principal del asistente."""
    speak("Hola, soy tu asistente. ¿En qué puedo ayudarte?")
    while True:
        comando = listen()
        if comando:
            execute_command(comando)


if __name__ == "__main__":
    main()
