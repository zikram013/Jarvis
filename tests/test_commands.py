import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


def cargar_jarvis():
    """Carga Jarvis sin requerir audio ni dependencias externas."""
    requests = types.ModuleType("requests")
    requests.RequestException = RuntimeError
    requests.ConnectionError = RuntimeError
    requests.post = Mock()

    speech_recognition = types.ModuleType("speech_recognition")
    speech_recognition.Recognizer = Mock
    speech_recognition.Microphone = Mock
    speech_recognition.UnknownValueError = RuntimeError
    speech_recognition.RequestError = RuntimeError

    pyttsx3 = types.ModuleType("pyttsx3")
    pyttsx3.init = Mock(return_value=Mock())

    modules = {
        "requests": requests,
        "speech_recognition": speech_recognition,
        "pyttsx3": pyttsx3,
    }

    ruta = Path(__file__).parents[1] / "Scritps" / "Jarvis.py"
    spec = importlib.util.spec_from_file_location("jarvis", ruta)
    modulo = importlib.util.module_from_spec(spec)

    with patch.dict(sys.modules, modules):
        with patch.object(sys, "path", [str(ruta.parent)] + sys.path):
            spec.loader.exec_module(modulo)
    return modulo


jarvis = cargar_jarvis()


class ExecuteCommandTest(unittest.TestCase):
    def test_abre_una_aplicacion(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("abre calculadora")

        abrir.assert_called_once_with("calculadora")

    def test_entiende_ejecuta_con_articulo(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("ejecuta el steam")

        abrir.assert_called_once_with("steam")

    def test_entiende_una_peticion_conversacional(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command(
                "quiero que abras la aplicación visual studio code por favor"
            )

        abrir.assert_called_once_with("visual studio code")

    def test_entiende_iniciar_como_sinonimo(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("puedes iniciar spotify")

        abrir.assert_called_once_with("spotify")

    def test_entiende_una_pregunta_cotidiana(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("me abres steam por favor")

        abrir.assert_called_once_with("steam")

    def test_pregunta_si_no_se_indica_aplicacion(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("¿puedes abrir?")

        abrir.assert_called_once_with("")

    def test_ahora_no_se_confunde_con_hora(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("abre ahora steam")

        abrir.assert_called_once_with("steam")

    def test_normaliza_el_articulo_de_la_aplicacion(self):
        self.assertEqual(
            jarvis.normalizar_nombre_aplicacion("el explorador de archivos"),
            "explorador de archivos",
        )

    def test_consulta_el_tiempo_de_una_ciudad(self):
        with patch.object(jarvis, "obtener_clima") as obtener_clima:
            jarvis.execute_command("qué tiempo hace hoy en madrid")

        obtener_clima.assert_called_once_with("madrid")

    def test_consulta_el_pronostico_de_una_ciudad(self):
        with patch.object(jarvis, "obtener_pronostico") as obtener_pronostico:
            jarvis.execute_command("pronóstico en cercedilla")

        obtener_pronostico.assert_called_once_with("cercedilla")

    def test_pregunta_la_ciudad_si_no_esta_en_el_comando(self):
        with patch.object(jarvis, "obtener_clima") as obtener_clima:
            jarvis.execute_command("qué temperatura hace")

        obtener_clima.assert_called_once_with(None)

    def test_pregunta_tipo_de_tiempo_si_el_comando_es_ambiguo(self):
        with patch.object(jarvis, "listen", return_value="el pronóstico"):
            with patch.object(jarvis, "speak"):
                with patch.object(
                    jarvis, "obtener_pronostico"
                ) as obtener_pronostico:
                    jarvis.execute_command("dime el tiempo")

        obtener_pronostico.assert_called_once_with()

    def test_pregunta_deportiva_se_envia_al_asistente_local(self):
        question = "cuál es el próximo partido del atlético de madrid"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)

    def test_duracion_de_trayecto_no_se_confunde_con_el_clima(self):
        question = "cuánto tiempo se tarda de madrid a toledo en coche"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)

    def test_hora_de_un_partido_no_se_confunde_con_la_hora_actual(self):
        question = "a qué hora juega el atlético de madrid"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)

    def test_pregunta_historica_se_envia_al_asistente_local(self):
        question = "quién fue el primer emperador romano"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)

    def test_como_abrir_algo_no_intenta_lanzar_una_aplicacion(self):
        question = "cómo abrir una cuenta bancaria"
        with patch.object(jarvis, "responder_pregunta") as responder:
            with patch.object(jarvis, "abrir_aplicacion") as abrir:
                jarvis.execute_command(question)

        responder.assert_called_once_with(question)
        abrir.assert_not_called()

    def test_pronostico_deportivo_no_se_confunde_con_el_clima(self):
        question = "cuál es tu pronóstico para el próximo partido"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)

    def test_pregunta_sobre_apagar_algo_no_cierra_jarvis(self):
        question = "cómo apagar un incendio pequeño"
        with patch.object(jarvis, "responder_pregunta") as responder:
            jarvis.execute_command(question)

        responder.assert_called_once_with(question)


if __name__ == "__main__":
    unittest.main()
