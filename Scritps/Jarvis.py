import subprocess

import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import requests

from speech_recognition.recognizers.google_cloud import recognize
#Tiempo
API_KEY = "cf2728055e15ce564e42025e26c00727"
URL_BASE = "http://api.openweathermap.org/data/2.5/weather"

# Diccionario de accesos directos
accesos_directos = {
    "discord": r"C:\Users\herna\Desktop\Discord.lnk",
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "spotify": "start spotify",
    "steam": r"C:\Users\herna\Desktop\Juegos\Steam.lnk"
}

# Inicializar el motor de voz
engine = pyttsx3.init()
engine.setProperty('rate', 150) #Velocidad
engine.setProperty('voice', 'spanish') #Ajustar idioma

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio,language='es-ES ')
            print(f"you said:{command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition service")
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
    """Abre una aplicación si está en el diccionario de accesos directos."""
    if nombre in accesos_directos:
        ruta = accesos_directos[nombre]

        # Si es una página web, abrir en el navegador
        if ruta.startswith("http"):
            speak(f"Abriendo {nombre}")
            webbrowser.open(ruta)
        elif ruta.startswith("start"):
            speak(f"Abriendo {nombre}")
            os.system(ruta)
        elif ruta.endswith(".lnk"):
            speak(f"Abriendo {nombre}")
            os.startfile(ruta)
        else:
            speak(f"Abriendo {nombre}")
            os.startfile(ruta)
    else:
        speak(f"No tengo registrado {nombre}, puedes agregarlo manualmente.")


def execute_command(command):
    if "hora" in command:
        hora = datetime.datetime.now().strftime("%H:%M")
        speak(f"La hora actual es {hora}")
    elif "abrir" in comando:
        nombre_app = comando.replace("abrir", "").strip()
        abrir_aplicacion(nombre_app)
    elif "tiempo en" in comando:
        ciudad = comando.replace("tiempo en", "").strip()
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