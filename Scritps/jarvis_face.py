"""Interfaz holográfica animada para el asistente Jarvis."""

import math
import queue
import threading
import time

try:
    import tkinter as tk
except ImportError:
    tk = None


VALID_STATES = {"idle", "listening", "thinking", "speaking", "error"}
STATE_LABELS = {
    "idle": "EN ESPERA",
    "listening": "ESCUCHANDO",
    "thinking": "PROCESANDO",
    "speaking": "RESPONDIENDO",
    "error": "INCIDENCIA",
}
STATE_COLORS = {
    "idle": "#21d4fd",
    "listening": "#46ff9a",
    "thinking": "#ffd166",
    "speaking": "#79f7ff",
    "error": "#ff5577",
}


def normalize_state(state):
    """Devuelve un estado visual válido."""
    return state if state in VALID_STATES else "idle"


def mouth_levels(state, phase):
    """Calcula siete niveles de boca para la animación de voz."""
    if normalize_state(state) != "speaking":
        return (0.08,) * 7

    frequencies = (1.7, 2.6, 3.4, 4.3, 3.1, 2.2, 1.4)
    return tuple(
        0.22 + 0.78 * abs(math.sin(phase * frequency + index * 0.83))
        for index, frequency in enumerate(frequencies)
    )


class JarvisFace:
    """Ventana de Tkinter que representa los estados del asistente."""

    def __init__(self, worker):
        if tk is None:
            raise RuntimeError(
                "Tkinter no está disponible en esta instalación de Python."
            )

        self.worker = worker
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.state = "idle"
        self.detail = "SISTEMAS PREPARADOS"
        self.user_text = ""
        self.jarvis_text = ""
        self.started_at = time.monotonic()

        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. // Interfaz neuronal")
        self.root.geometry("980x740")
        self.root.minsize(760, 600)
        self.root.configure(bg="#02070d")
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)

        self.canvas = tk.Canvas(
            self.root,
            bg="#02070d",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.close_button = tk.Button(
            self.root,
            text="DESCONECTAR",
            command=self.request_close,
            bg="#071a25",
            fg="#79f7ff",
            activebackground="#10384a",
            activeforeground="#ffffff",
            relief="flat",
            font=("Consolas", 10, "bold"),
            padx=18,
            pady=7,
            cursor="hand2",
        )
        self.close_button.place(relx=0.97, rely=0.035, anchor="ne")

    def set_state(self, state, detail=None):
        """Encola un cambio de estado desde cualquier hilo."""
        self.events.put(("state", normalize_state(state), detail))

    def show_user(self, text):
        """Muestra la última frase reconocida del usuario."""
        self.events.put(("user", str(text)))

    def show_jarvis(self, text):
        """Muestra la última frase pronunciada por Jarvis."""
        self.events.put(("jarvis", str(text)))

    def is_running(self):
        return not self.stop_event.is_set()

    def request_close(self):
        """Solicita detener el asistente y cerrar la ventana."""
        self.stop_event.set()
        self.events.put(("close",))

    def _process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "state":
                    self.state = event[1]
                    if event[2]:
                        self.detail = event[2]
                elif event[0] == "user":
                    self.user_text = event[1]
                elif event[0] == "jarvis":
                    self.jarvis_text = event[1]
                elif event[0] == "close":
                    self.root.destroy()
                    return
        except queue.Empty:
            pass

        if not self.stop_event.is_set():
            self.root.after(40, self._process_events)

    @staticmethod
    def _darken(hex_color, factor):
        value = hex_color.lstrip("#")
        channels = [int(value[index:index + 2], 16) for index in (0, 2, 4)]
        return "#" + "".join(f"{int(channel * factor):02x}" for channel in channels)

    def _draw_grid(self, width, height, color, phase):
        grid_color = self._darken(color, 0.16)
        horizon = height * 0.68
        for offset in range(-8, 9):
            x_bottom = width / 2 + offset * width * 0.12
            self.canvas.create_line(
                width / 2,
                horizon,
                x_bottom,
                height,
                fill=grid_color,
                width=1,
            )

        shift = (phase * 18) % 34
        y = horizon + shift
        while y < height:
            self.canvas.create_line(0, y, width, y, fill=grid_color, width=1)
            y += 34

    def _draw_rings(self, center_x, center_y, radius, color, phase):
        pulse = 0.5 + 0.5 * math.sin(phase * 1.8)
        for index in range(3):
            expansion = index * 27 + pulse * 5
            ring_radius = radius + expansion
            ring_color = self._darken(color, 0.42 - index * 0.09)
            self.canvas.create_arc(
                center_x - ring_radius,
                center_y - ring_radius,
                center_x + ring_radius,
                center_y + ring_radius,
                start=18 + phase * 14 + index * 48,
                extent=92,
                style="arc",
                outline=ring_color,
                width=2,
            )
            self.canvas.create_arc(
                center_x - ring_radius,
                center_y - ring_radius,
                center_x + ring_radius,
                center_y + ring_radius,
                start=204 + phase * 10 + index * 37,
                extent=68,
                style="arc",
                outline=ring_color,
                width=2,
            )

    def _draw_face(self, center_x, center_y, scale, color, phase):
        glow = self._darken(color, 0.28)
        secondary = self._darken(color, 0.62)
        pulse = 0.5 + 0.5 * math.sin(phase * 2.1)

        face_points = (
            center_x - 130 * scale, center_y - 176 * scale,
            center_x - 178 * scale, center_y - 72 * scale,
            center_x - 148 * scale, center_y + 86 * scale,
            center_x - 74 * scale, center_y + 174 * scale,
            center_x, center_y + 202 * scale,
            center_x + 74 * scale, center_y + 174 * scale,
            center_x + 148 * scale, center_y + 86 * scale,
            center_x + 178 * scale, center_y - 72 * scale,
            center_x + 130 * scale, center_y - 176 * scale,
            center_x, center_y - 214 * scale,
        )
        self.canvas.create_polygon(
            face_points,
            fill="#03131d",
            outline=glow,
            width=max(5, int(9 * scale)),
            smooth=True,
        )
        self.canvas.create_polygon(
            face_points,
            fill="",
            outline=color,
            width=max(1, int(2 * scale)),
            smooth=True,
        )

        temple_y = center_y - 45 * scale
        for side in (-1, 1):
            self.canvas.create_line(
                center_x + side * 151 * scale,
                center_y - 112 * scale,
                center_x + side * 105 * scale,
                temple_y,
                center_x + side * 135 * scale,
                center_y + 83 * scale,
                fill=secondary,
                width=max(1, int(2 * scale)),
                smooth=True,
            )

        blink = abs(math.sin(phase * 0.42)) > 0.985
        eye_height = 2 if blink else (14 + 3 * pulse) * scale
        for side in (-1, 1):
            eye_x = center_x + side * 70 * scale
            eye_y = center_y - 55 * scale
            eye_width = 55 * scale
            self.canvas.create_oval(
                eye_x - eye_width,
                eye_y - eye_height,
                eye_x + eye_width,
                eye_y + eye_height,
                fill=glow,
                outline="",
            )
            self.canvas.create_line(
                eye_x - eye_width,
                eye_y,
                eye_x + eye_width,
                eye_y,
                fill=color,
                width=max(2, int((3 + pulse * 2) * scale)),
            )

        self.canvas.create_line(
            center_x,
            center_y - 26 * scale,
            center_x - 15 * scale,
            center_y + 42 * scale,
            center_x + 20 * scale,
            center_y + 50 * scale,
            fill=secondary,
            width=max(1, int(2 * scale)),
            smooth=True,
        )

        levels = mouth_levels(self.state, phase)
        bar_width = 9 * scale
        spacing = 16 * scale
        mouth_y = center_y + 105 * scale
        for index, level in enumerate(levels):
            x = center_x + (index - 3) * spacing
            height = (4 + level * 29) * scale
            self.canvas.create_rectangle(
                x - bar_width / 2,
                mouth_y - height / 2,
                x + bar_width / 2,
                mouth_y + height / 2,
                fill=color,
                outline="",
            )

    def _draw_panels(self, width, height, color, phase):
        dim = self._darken(color, 0.55)
        font_small = ("Consolas", max(8, int(width / 115)))
        self.canvas.create_text(
            35,
            82,
            anchor="nw",
            text="NEURAL LINK\nVOICE MATRIX\nLOCAL CORE",
            fill=dim,
            font=font_small,
            justify="left",
        )
        self.canvas.create_text(
            width - 35,
            82,
            anchor="ne",
            text=(
                f"OLLAMA // LOCAL\n"
                f"UPTIME // {int(time.monotonic() - self.started_at):06d}\n"
                f"PHASE  // {phase % 10:04.1f}"
            ),
            fill=dim,
            font=font_small,
            justify="right",
        )

    def _animate(self):
        if self.stop_event.is_set():
            return

        width = max(self.canvas.winfo_width(), 760)
        height = max(self.canvas.winfo_height(), 600)
        phase = time.monotonic() - self.started_at
        color = STATE_COLORS[self.state]
        center_x = width / 2
        center_y = height * 0.40
        scale = min(width / 980, height / 740)

        self.canvas.delete("all")
        self._draw_grid(width, height, color, phase)
        self._draw_rings(center_x, center_y, 232 * scale, color, phase)
        self._draw_face(center_x, center_y, scale, color, phase)
        self._draw_panels(width, height, color, phase)

        scan_y = (phase * 95) % height
        self.canvas.create_line(
            0,
            scan_y,
            width,
            scan_y,
            fill=self._darken(color, 0.35),
        )

        self.canvas.create_text(
            center_x,
            35,
            text="J . A . R . V . I . S",
            fill=color,
            font=("Consolas", max(17, int(width / 42)), "bold"),
        )
        self.canvas.create_text(
            center_x,
            height * 0.73,
            text=STATE_LABELS[self.state],
            fill=color,
            font=("Consolas", max(13, int(width / 58)), "bold"),
        )
        self.canvas.create_text(
            center_x,
            height * 0.77,
            text=self.detail.upper(),
            fill=self._darken(color, 0.72),
            font=("Consolas", max(9, int(width / 95))),
        )

        transcript = ""
        if self.user_text:
            transcript += f"TÚ: {self.user_text}\n"
        if self.jarvis_text:
            transcript += f"JARVIS: {self.jarvis_text}"
        self.canvas.create_text(
            center_x,
            height * 0.86,
            text=transcript or "Di un comando o formula una pregunta",
            fill="#b9f7ff",
            font=("Segoe UI", max(10, int(width / 82))),
            width=width * 0.78,
            justify="center",
        )

        self.root.after(55, self._animate)

    def _run_worker(self):
        try:
            self.worker(self)
        except SystemExit:
            self.request_close()
        except Exception as error:
            self.set_state("error", str(error))
            self.show_jarvis("Se produjo un error inesperado. Revisa la consola.")
            print(f" Error inesperado en Jarvis: {error}")

    def run(self):
        """Inicia el hilo del asistente y el bucle gráfico."""
        self.root.after(40, self._process_events)
        self.root.after(55, self._animate)
        self.root.after(
            180,
            lambda: threading.Thread(
                target=self._run_worker,
                name="jarvis-voice-worker",
                daemon=True,
            ).start(),
        )
        self.root.mainloop()
