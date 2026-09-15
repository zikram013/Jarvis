import importlib.util
import unittest
from pathlib import Path


def cargar_interfaz():
    ruta = Path(__file__).parents[1] / "Scritps" / "jarvis_face.py"
    spec = importlib.util.spec_from_file_location("jarvis_face_test", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


face = cargar_interfaz()


class JarvisFaceAnimationTest(unittest.TestCase):
    def test_normaliza_estados_desconocidos(self):
        self.assertEqual(face.normalize_state("speaking"), "speaking")
        self.assertEqual(face.normalize_state("desconocido"), "idle")

    def test_la_boca_permanece_quieta_si_no_esta_hablando(self):
        self.assertEqual(face.mouth_levels("idle", 1.0), (0.08,) * 7)

    def test_la_boca_se_anima_mientras_habla(self):
        levels = face.mouth_levels("speaking", 1.25)

        self.assertEqual(len(levels), 7)
        self.assertGreater(max(levels), min(levels))
        self.assertTrue(all(0.0 <= level <= 1.0 for level in levels))


if __name__ == "__main__":
    unittest.main()
