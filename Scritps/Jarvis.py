import requests
import datetime
import speech_recognition as sr
import pyttsx3

# API de OpenWeatherMap
API_KEY = "e4551bebb136eaa007fd7d195fcf0697"
URL_CLIMA = "http://api.openweathermap.org/data/2.5/weather"
URL_PRONOSTICO = "http://api.openweathermap.org/data/2.5/forecast"

# Inicializar el motor de voz
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Velocidad de voz
engine.setProperty('voice', 'spanish')  # Idioma en español

# Traducción de días de la semana y meses
dias_semana = {
    "Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles",
    "Thursday": "jueves", "Friday": "viernes", "Saturday": "sábado", "Sunday": "domingo"
}

meses = {
    "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
    "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
    "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
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
            command = recognizer.recognize_google(audio, language='es-ES')
            print(f"Dijiste: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("No pude entender el audio.")
            return None
        except sr.RequestError:
            print("Error al conectar con el servicio de reconocimiento.")
            return None

def obtener_clima(ciudad=None):
    """Obtiene la temperatura actual de una ciudad."""
    if not ciudad:
        speak("¿De qué ciudad quieres conocer el clima?")
        ciudad = listen()
        if not ciudad:
            speak("No pude entender la ciudad. Inténtalo de nuevo.")
            return

    parametros = {
        "q": ciudad,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es"
    }

    respuesta = requests.get(URL_CLIMA, params=parametros)

    if respuesta.status_code == 200:
        datos = respuesta.json()
        temperatura = round(datos["main"]["temp"])  # Redondear temperatura
        descripcion = datos["weather"][0]["description"]
        speak(f"La temperatura actual en {ciudad} es de {temperatura} grados y está {descripcion}.")
        print(f"📍 {ciudad}: {temperatura}°C, {descripcion.capitalize()}")
    else:
        speak(f"No pude obtener el clima de {ciudad}. Verifica el nombre o intenta otra ciudad.")

def obtener_pronostico(ciudad=None):
    """Obtiene el pronóstico del clima para los próximos 5 días en castellano."""
    if not ciudad:
        speak("¿Para qué ciudad quieres el pronóstico?")
        ciudad = listen()
        if not ciudad:
            speak("No pude entender la ciudad. Inténtalo de nuevo.")
            return

    parametros = {
        "q": ciudad,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es",
        "cnt": 40  # Obtener pronóstico de 5 días (cada 3 horas)
    }

    respuesta = requests.get(URL_PRONOSTICO, params=parametros)

    if respuesta.status_code == 200:
        datos = respuesta.json()
        pronostico_por_dia = {}

        for entrada in datos["list"]:
            fecha_texto = entrada["dt_txt"].split(" ")[0]
            temp_max = round(entrada["main"]["temp_max"])  # Redondear temperaturas
            temp_min = round(entrada["main"]["temp_min"])
            descripcion = entrada["weather"][0]["description"]

            if fecha_texto not in pronostico_por_dia:
                pronostico_por_dia[fecha_texto] = {
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "descripcion": descripcion
                }
            else:
                pronostico_por_dia[fecha_texto]["temp_max"] = max(pronostico_por_dia[fecha_texto]["temp_max"], temp_max)
                pronostico_por_dia[fecha_texto]["temp_min"] = min(pronostico_por_dia[fecha_texto]["temp_min"], temp_min)

        speak(f"Este es el pronóstico para {ciudad} en los próximos días:")
        print(f"📍 Pronóstico para {ciudad}:")

        for fecha, info in pronostico_por_dia.items():
            fecha_objeto = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            dia_semana = dias_semana[fecha_objeto.strftime("%A")]
            mes = meses[fecha_objeto.strftime("%B")]
            dia_num = fecha_objeto.strftime("%d")

            mensaje = f"El {dia_semana} {dia_num} de {mes} hará una máxima de {info['temp_max']} grados y una mínima de {info['temp_min']} grados, con {info['descripcion']}."
            speak(mensaje)
            print(mensaje)
    else:
        speak(f"No pude obtener el pronóstico para {ciudad}. Verifica el nombre o intenta otra ciudad.")

def execute_command(command):
    """Ejecuta el comando del usuario."""
    if "hora" in command:
        hora = datetime.datetime.now().strftime("%H:%M")
        speak(f"La hora actual es {hora}")
    elif "tiempo" in command or "clima" in command:
        if "hoy" in command or "actual" in command:
            ciudad = command.replace("tiempo en", "").replace("clima en", "").strip()
            obtener_clima(ciudad)
        elif "pronóstico" in command or "próximos días" in command:
            ciudad = command.replace("pronóstico en", "").replace("próximos días en", "").strip()
            obtener_pronostico(ciudad)
        else:
            speak("¿Quieres la temperatura actual o el pronóstico?")
            respuesta = listen()
            if respuesta and "pronóstico" in respuesta:
                obtener_pronostico()
            else:
                obtener_clima()
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
