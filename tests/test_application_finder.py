import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

def cargar_buscador():
    ruta = Path(__file__).parents[1] / "Scritps" / "application_finder.py"
    spec = importlib.util.spec_from_file_location("application_finder_test", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


finder = cargar_buscador()


class ApplicationFinderTest(unittest.TestCase):
    def setUp(self):
        finder.APP_CACHE.clear()

    def test_normaliza_acentos_y_puntuacion(self):
        self.assertEqual(finder.normalize("  Configuración... "), "configuracion")

    def test_selecciona_nombre_registrado_aunque_incluya_marca(self):
        targets = [
            finder.ApplicationTarget("Steam", "C:/Steam/steam.exe", "path"),
            finder.ApplicationTarget("Google Chrome", "C:/Chrome/chrome.exe", "path"),
        ]

        target = finder._best_target("chrome", targets)

        self.assertEqual(target.value, "C:/Chrome/chrome.exe")

    def test_prioriza_una_aplicacion_conocida(self):
        with patch.object(finder, "SO", "Windows"):
            target = finder.find_application("calculadora")

        self.assertEqual(target.value, "calc")

    def test_recurre_a_busqueda_profunda_en_windows(self):
        expected = finder.ApplicationTarget("Steam", "D:/Games/Steam/steam.exe", "path")
        notification = []
        with patch.object(finder, "SO", "Windows"):
            with patch.object(finder, "_path_target", return_value=None):
                with patch.object(finder, "_windows_registered_targets", return_value=[]):
                    with patch.object(finder, "_deep_windows_search", return_value=expected):
                        target = finder.find_application(
                            "steam", on_deep_search=lambda: notification.append(True)
                        )

        self.assertEqual(target, expected)
        self.assertEqual(notification, [True])


if __name__ == "__main__":
    unittest.main()
