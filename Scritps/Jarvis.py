import datetime
import os
import re

import pyttsx3
import requests
import speech_recognition as sr

from application_finder import find_application, launch_application
from local_assistant import (
    LocalAssistantError,
    LocalKnowledgeAssistant,
    OllamaUnavailable,
    text_for_speech,
)


# Configuración general
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"
URL_PRONOSTICO = "https://api.openweathermap.org/data/2.5/forecast"

# Inicializar el motor de voz
engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("voice", "spanish")
knowledge_assistant = LocalKnowledgeAssistant()

VERBOS_APERTURA = (
    "abre",
    "ábreme",
    "abreme",
    "abrir",
    "abrirme",
    "abra",
    "abres",
    "abras",
    "ejecuta",
    "ejecútame",
    "ejecutame",
    "ejecutar",
    "ejecutas",
    "ejecute",
    "ejecutes",
    "inicia",
    "iníciame",
    "iniciame",
    "iniciar",
    "inicias",
    "inicie",
    "inicies",
    "lanza",
    "lánzame",
    "lanzame",
    "lanzar",
    "lanzas",
    "lance",
    "lances",
    "arranca",
    "arráncame",
    "arrancame",
    "arrancar",
    "arrancas",
    "arranque",
    "arranques",
)
PATRON_APERTURA = re.compile(
    rf"\b(?:{'|'.join(VERBOS_APERTURA)})\b(?P<nombre>.*)$",
    re.IGNORECASE,
)

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
    print(f" {mensaje}")
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
        print(f" Error al consultar el clima: {error}")
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
        print(f" {ciudad}: {temperatura}°C, {descripcion.capitalize()}")
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
        print(f" Error al consultar el pronóstico: {error}")
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
    print(f" Pronóstico para {ciudad}:")

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


def normalizar_nombre_aplicacion(nombre):
    """Elimina palabras conversacionales que no forman parte del nombre."""
    nombre = nombre.strip(" ,:¿?¡!.")
    prefijos = (
        "por favor, ",
        "por favor ",
        "ahora, ",
        "ahora ",
        "ya, ",
        "ya ",
        "la aplicación de ",
        "la aplicacion de ",
        "el programa de ",
        "la aplicación ",
        "la aplicacion ",
        "el programa ",
        "la app ",
        "aplicación ",
        "aplicacion ",
        "programa ",
        "app ",
        "el ",
        "la ",
        "los ",
        "las ",
        "un ",
        "una ",
    )
    sufijos = (
        " por favor",
        " si puedes",
        " cuando puedas",
        " para mí",
        " para mi",
        " ahora",
        " ya",
    )

    cambiado = True
    while cambiado:
        cambiado = False
        for prefijo in prefijos:
            if nombre.startswith(prefijo):
                nombre = nombre[len(prefijo):].strip()
                cambiado = True
                break

    for sufijo in sufijos:
        if nombre.endswith(sufijo):
            nombre = nombre[: -len(sufijo)].strip()
            break
    return nombre.strip(" ,:¿?¡!.")


def extraer_nombre_aplicacion(command):
    """Extrae una aplicación de órdenes expresadas en lenguaje cotidiano."""
    coincidencia = PATRON_APERTURA.search(command)
    if coincidencia is None:
        return None

    prefix = command[: coincidencia.start()].strip(" ,:¿?¡!.")
    explanatory_prefixes = ("cómo ", "como ", "por qué ", "por que ")
    if prefix.startswith(explanatory_prefixes):
        return None

    request_clues = (
        "jarvis",
        "oye",
        "por favor",
        "quiero",
        "puedes",
        "podrías",
        "podrias",
        "necesito",
        "debes",
        "tienes que",
    )
    prefix_words = set(prefix.split())
    if prefix and not (
        any(clue in prefix for clue in request_clues) or "me" in prefix_words
    ):
        return None
    return normalizar_nombre_aplicacion(coincidencia.group("nombre"))


def abrir_aplicacion(nombre):
    """Localiza y abre una aplicación conocida o instalada."""
    if not nombre:
        speak("¿Qué aplicación quieres abrir?")
        nombre = listen()
        if not nombre:
            return

    nombre = normalizar_nombre_aplicacion(nombre)

    try:
        def avisar_busqueda_profunda():
            mensaje = f"Estoy buscando {nombre} en las unidades del equipo."
            print(f" {mensaje}")
            speak(mensaje)

        target = find_application(nombre, on_deep_search=avisar_busqueda_profunda)
        if target:
            print(f" Aplicación encontrada: {target.name} ({target.value})")
            speak(f"Abriendo {target.name}")
            launch_application(target)
            return True

        speak(f"No encontré {nombre} en tu sistema.")
        print(f" No se encontró la aplicación: {nombre}")
    except (OSError, RuntimeError) as error:
        speak(f"No pude abrir {nombre}.")
        print(f" Error al abrir {nombre}: {error}")
    return False


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


def es_consulta_hora_actual(command):
    """Distingue la hora actual de preguntas como 'a qué hora juega'."""
    patterns = (
        r"^\s*hora\s*[?.!]*$",
        r"\b(?:que|qué) hora es\b",
        r"\bdime (?:la )?hora\b",
        r"\bhora actual\b",
    )
    return any(re.search(pattern, command) for pattern in patterns)


def es_consulta_meteorologica(command):
    """Evita confundir el tiempo meteorológico con la duración de un trayecto."""
    travel_words = (
        r"\b(?:tarda|tardar|trayecto|viaje|llegar|distancia|ruta|camino|"
        r"coche|andando|a pie|tren|metro|autobús|autobus)\b"
    )
    if re.search(travel_words, command):
        return False
    if re.search(r"\b(?:clima|temperatura|grados)\b", command):
        return True
    weather_patterns = (
        r"^\s*(?:dime (?:el )?)?tiempo\s*[?.!]*$",
        r"\btiempo\s+(?:en|para)\b",
        r"\b(?:que|qué|como|cómo)\s+(?:esta|está|hace|hara|hará)\s+(?:el )?tiempo\b",
        r"\b(?:que|qué) tiempo\s+(?:hace|hara|hará)\b",
    )
    return any(re.search(pattern, command) for pattern in weather_patterns)


def es_consulta_pronostico_meteorologico(command):
    """Distingue el pronóstico del tiempo de predicciones deportivas u otras."""
    patterns = (
        r"\bpron[oó]stico\s+(?:del tiempo|meteorol[oó]gico)\b",
        r"\bpron[oó]stico\s+en\b",
        r"\b(?:tiempo|clima)\b.*\bpr[oó]ximos d[ií]as\b",
        r"\bpr[oó]ximos d[ií]as\s+en\b",
    )
    return any(re.search(pattern, command) for pattern in patterns)


def es_comando_salida(command):
    """Distingue cerrar Jarvis de preguntas que contienen 'salir' o 'apagar'."""
    normalized = command.strip(" ,:¿?¡!.")
    patterns = (
        r"^(?:jarvis[ ,]+)?(?:sal|salir|apagar|ap[aá]gate)$",
        r"^(?:cierra|apaga|termina) (?:jarvis|el asistente|el programa)$",
        r"^quiero salir (?:de jarvis|del asistente|del programa)$",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def responder_pregunta(question):
    """Consulta Ollama y, cuando hace falta, resultados web gratuitos."""
    print(" Consultando el asistente local...")
    try:
        answer = knowledge_assistant.ask(question)
    except OllamaUnavailable as error:
        message = str(error)
        print(f" {message}")
        speak(message)
        return None
    except LocalAssistantError as error:
        print(f" Error al consultar el asistente: {error}")
        speak("No pude consultar la información en este momento.")
        return None

    print(f"Jarvis: {answer.text}")
    if answer.sources:
        print("Resultados web consultados:")
        for source in answer.sources:
            print(f"- {source.title}: {source.url}")

    speak(text_for_speech(answer.text))
    return answer


def execute_command(command):
    """Ejecuta el comando de voz del usuario."""
    nombre_app = extraer_nombre_aplicacion(command)

    if es_consulta_hora_actual(command):
        hora = datetime.datetime.now().strftime("%H:%M")
        speak(f"La hora actual es {hora}")
    elif nombre_app is not None:
        abrir_aplicacion(nombre_app)
    elif es_consulta_pronostico_meteorologico(command):
        obtener_pronostico(extraer_ciudad(command))
    elif es_consulta_meteorologica(command):
        resolver_consulta_tiempo(command)
    elif es_comando_salida(command):
        speak("Apagando el asistente. Hasta luego.")
        raise SystemExit
    else:
        responder_pregunta(command)


def main():
    """Inicia el bucle principal del asistente."""
    speak("Hola, soy tu asistente. ¿En qué puedo ayudarte?")
    while True:
        comando = listen()
        if comando:
            execute_command(comando)


if __name__ == "__main__":
    main()
