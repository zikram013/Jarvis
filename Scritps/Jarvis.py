import subprocess
import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import requests
import platform
import glob

# Detectar sistema operativo
SO = platform.system()

# Configurar API del clima
API_KEY = "cf2728055e15ce564e42025e26c00727"
URL_BASE = "http://api.openweathermap.org/data/2.5/weather"

# Inicializar el motor de voz
engine = pyttsx3.init()
engine.setProperty('rate', 180)  # Velocidad
engine.setProperty('voice', 'spanish')  # Ajustar idioma

# Comandos específicos para Windows
comandos_sistema_windows = {
    "configuración": "start ms-settings:",
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
    "servicios": "services.msc"
}

# Comandos específicos para macOS
comandos_sistema_mac = {
    "configuración": "open -b com.apple.systempreferences",
    "explorador de archivos": "open .",
    "terminal": "open -a Terminal",
    "safari": "open -a Safari",
    "calculadora": "open -a Calculator",
}

# Comandos específicos para Linux
comandos_sistema_linux = {
    "configuración": "gnome-control-center",
    "explorador de archivos": "xdg-open .",
    "terminal": "gnome-terminal",
    "firefox": "firefox",
    "calculadora": "gnome-calculator",
}

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio, language='es-ES')
            print(f"Dijiste: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("No pude entender el audio")
            return None
        except sr.RequestError:
            print("Error al conectar con el servicio de reconocimiento")
            return None

def obtener_clima(ciudad):
    parametros = {"q": ciudad, "appid": API_KEY, "units": "metric", "lang": "es"}
    respuesta = requests.get(URL_BASE, params=parametros)

    if respuesta.status_code == 200:
        datos = respuesta.json()
        temperatura = datos["main"]["temp"]
        descripcion = datos["weather"][0]["description"]
        speak(f"El clima en {ciudad} es de {temperatura} grados y está {descripcion}.")
    else:
        speak(f"No pude obtener el clima de {ciudad}. Verifica el nombre.")

def abrir_aplicacion(nombre):
    """
    Abre una aplicación del sistema o una aplicación instalada.
    """
    try:
        # Detectar sistema operativo y ejecutar el comando correcto
        if SO == "Windows" and nombre in comandos_sistema_windows:
            comando = comandos_sistema_windows[nombre]
        elif SO == "Darwin" and nombre in comandos_sistema_mac:
            comando = comandos_sistema_mac[nombre]
        elif SO == "Linux" and nombre in comandos_sistema_linux:
            comando = comandos_sistema_linux[nombre]
        else:
            comando = None

        if comando:
            print(f"🔍 Ejecutando: {comando}")
            speak(f"Abriendo {nombre}")
            subprocess.Popen(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        # Si no es un comando del sistema, buscar la aplicación instalada
        ruta = encontrar_ejecutable(nombre)
        if ruta:
            print(f"🔍 Encontrado: {ruta}")
            speak(f"Abriendo {nombre}")
            if SO == "Windows":
                try:
                    os.startfile(ruta)
                except Exception:
                    subprocess.Popen(f'"{ruta}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            speak(f"No encontré {nombre} en tu sistema.")
            print(f"❌ No se encontró la aplicación: {nombre}")
    except Exception as e:
        speak(f"No pude abrir {nombre}. Error: {e}")
        print(f"❌ Error al abrir {nombre}: {e}")

def encontrar_ejecutable(nombre):
    """
    Busca la ruta del ejecutable en todas las unidades disponibles.
    """
    if SO == "Windows":
        # Comando WHERE en Windows
        resultado = subprocess.run(["where", nombre], capture_output=True, text=True)
    else:
        # Comando WHICH en macOS/Linux
        resultado = subprocess.run(["which", nombre], capture_output=True, text=True)

    ruta = resultado.stdout.strip()
    if ruta:
        return ruta.split("\n")[0]  # Tomar la primera ruta si hay varias

    return None

def execute_command(command):
    if "hora" in command:
        hora = datetime.datetime.now().strftime("%H:%M")
        speak(f"La hora actual es {hora}")
    elif "abrir" in command:
        nombre_app = command.replace("abrir", "").strip()
        abrir_aplicacion(nombre_app)
    elif "tiempo en" in command:
        ciudad = command.replace("tiempo en", "").strip()
        obtener_clima(ciudad)
    elif "salir" in command or "apagar" in command:
        speak("Apagando el asistente. Hasta luego.")
        exit()
    else:
        speak("No reconozco ese comando.")

# Bucle principal
speak("Hola, soy tu asistente. ¿En qué puedo ayudarte?")
while True:
    comando = listen()
    if comando:
        execute_command(comando)
