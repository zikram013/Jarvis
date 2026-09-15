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
        spec.loader.exec_module(modulo)
    return modulo


jarvis = cargar_jarvis()


class ExecuteCommandTest(unittest.TestCase):
    def test_abre_una_aplicacion(self):
        with patch.object(jarvis, "abrir_aplicacion") as abrir:
            jarvis.execute_command("abre calculadora")

        abrir.assert_called_once_with("calculadora")

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


if __name__ == "__main__":
    unittest.main()
