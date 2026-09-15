import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


def cargar_asistente():
    class RequestException(Exception):
        pass

    class ConnectionError(RequestException):
        pass

    requests = types.ModuleType("requests")
    requests.RequestException = RequestException
    requests.ConnectionError = ConnectionError
    requests.post = Mock()

    ruta = Path(__file__).parents[1] / "Scritps" / "local_assistant.py"
    spec = importlib.util.spec_from_file_location("local_assistant_test", ruta)
    modulo = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"requests": requests}):
        spec.loader.exec_module(modulo)
    return modulo


assistant_module = cargar_asistente()


class FakeResponse:
    def __init__(self, text="Respuesta local."):
        self.data = {"message": {"role": "assistant", "content": text}}

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeSearch:
    queries = []

    def __init__(self, timeout):
        self.timeout = timeout

    def text(self, query, **kwargs):
        self.queries.append((query, kwargs))
        return [
            {
                "title": "Calendario oficial",
                "href": "https://example.com/calendario",
                "body": "El siguiente partido se juega el domingo.",
            }
        ]

    def close(self):
        return None


class LocalKnowledgeAssistantTest(unittest.TestCase):
    def setUp(self):
        FakeSearch.queries.clear()

    def test_detecta_consultas_que_necesitan_internet(self):
        self.assertTrue(
            assistant_module.needs_web_search(
                "¿Cuál es el próximo partido del Atlético de Madrid?"
            )
        )
        self.assertTrue(
            assistant_module.needs_web_search(
                "¿Cuánto se tarda de Madrid a Toledo en coche?"
            )
        )
        self.assertTrue(
            assistant_module.needs_web_search(
                "¿Cuánto tiempo se tarda de Madrid a Toledo?"
            )
        )
        self.assertFalse(
            assistant_module.needs_web_search("¿Quién fue el emperador Augusto?")
        )

    def test_responde_con_ollama_sin_clave_api(self):
        post = Mock(return_value=FakeResponse("Augusto fue emperador romano."))
        assistant = assistant_module.LocalKnowledgeAssistant(
            http_post=post,
            search_factory=FakeSearch,
        )

        with patch.dict(os.environ, {"JARVIS_WEB_SEARCH": "auto"}, clear=True):
            answer = assistant.ask("¿Quién fue Augusto?")

        self.assertEqual(answer.text, "Augusto fue emperador romano.")
        self.assertFalse(answer.used_web)
        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["json"]["model"], assistant_module.DEFAULT_MODEL
        )
        self.assertEqual(
            post.call_args.args[0], "http://localhost:11434/api/chat"
        )

    def test_busca_en_la_web_para_informacion_actual(self):
        post = Mock(return_value=FakeResponse("El partido es el domingo [1]."))
        assistant = assistant_module.LocalKnowledgeAssistant(
            http_post=post,
            search_factory=FakeSearch,
        )

        answer = assistant.ask("¿Cuál es el próximo partido del Atlético?")

        self.assertTrue(answer.used_web)
        self.assertEqual(len(answer.sources), 1)
        self.assertEqual(answer.sources[0].url, "https://example.com/calendario")
        sent_messages = post.call_args.kwargs["json"]["messages"]
        self.assertIn("Resultados recientes de Internet", sent_messages[-1]["content"])

    def test_conserva_el_contexto_entre_preguntas(self):
        post = Mock(
            side_effect=(
                FakeResponse("Augusto fue el primero."),
                FakeResponse("Le sucedió Tiberio."),
            )
        )
        assistant = assistant_module.LocalKnowledgeAssistant(
            http_post=post,
            search_factory=FakeSearch,
        )

        assistant.ask("¿Quién fue el primer emperador romano?")
        assistant.ask("¿Y quién le sucedió?")

        second_messages = post.call_args_list[1].kwargs["json"]["messages"]
        self.assertIn(
            {"role": "assistant", "content": "Augusto fue el primero."},
            second_messages,
        )

    def test_informa_si_ollama_no_esta_disponible(self):
        connection_error = assistant_module.requests.ConnectionError(
            "connection refused"
        )
        post = Mock(side_effect=connection_error)
        assistant = assistant_module.LocalKnowledgeAssistant(
            http_post=post,
            search_factory=FakeSearch,
        )

        with self.assertRaises(assistant_module.OllamaUnavailable):
            assistant.ask("¿Quién fue Augusto?")

    def test_indica_como_descargar_un_modelo_que_no_existe(self):
        response = FakeResponse()
        response.status_code = 404
        response.data = {"error": "model not found"}
        assistant = assistant_module.LocalKnowledgeAssistant(
            http_post=Mock(return_value=response),
            search_factory=FakeSearch,
        )

        with self.assertRaisesRegex(
            assistant_module.OllamaUnavailable,
            r"ollama pull qwen3:4b",
        ):
            assistant.ask("¿Quién fue Augusto?")

    def test_limpia_citas_y_razonamiento_para_la_voz(self):
        text = (
            "<think>razonamiento interno</think> "
            "El partido es el domingo [1]. https://example.com"
        )

        self.assertEqual(
            assistant_module.text_for_speech(text),
            "El partido es el domingo.",
        )


if __name__ == "__main__":
    unittest.main()
