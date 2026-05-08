import tkinter as tk
from tkinter import messagebox
import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
from datetime import datetime, timezone
from dotenv import load_dotenv
import csv
import os
import random

load_dotenv()

# Tamaño de la ventana deslizante (segundos de historial mostrados en las gráficas)
BUFFER_SIZE = 40

# Fichero CSV local donde se acumulan los datos pendientes de envío
CSV_PENDIENTE = "datos_pendientes.csv"
CSV_CABECERA = ["timestamp", "Carga_Cognitiva", "Nivel_de_Coherencia", "Intensidad_Emocional", "Latencia_de_Inferencia", "Consumo_Energético"]


class AppAndroide:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Datos - Sistema Androide")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f0f2f5")

        self.channel_id = os.getenv("THINGSPEAK_CHANNEL_ID")
        self.write_key = os.getenv("THINGSPEAK_WRITE_KEY")
        self.read_key = os.getenv("THINGSPEAK_READ_KEY")

        self.fields = [
            "Carga Cognitiva",
            "Nivel de Coherencia",
            "Intensidad Emocional",
            "Latencia de Inferencia",
            "Consumo Energético",
        ]

        # (mínimo, máximo, valor inicial) para la generación de datos sintéticos
        self.data_ranges = {
            "Carga Cognitiva":        (0,    100,  50.0),
            "Nivel de Coherencia":    (0,      1,   0.5),
            "Intensidad Emocional":   (0,    100,  40.0),
            "Latencia de Inferencia": (0,    500, 150.0),
            "Consumo Energético":     (0,    100,  60.0),
        }

        # Buffer circular con los últimos BUFFER_SIZE valores por campo
        self.historial_datos = {
            field: deque([init] * BUFFER_SIZE, maxlen=BUFFER_SIZE)
            for field, (lo, hi, init) in self.data_ranges.items()
        }

        # Valor actual para el paseo aleatorio
        self.current_vals = {
            field: init
            for field, (lo, hi, init) in self.data_ranges.items()
        }

        self.frames = {}
        self.graficos_ui = {}
        self._tick_count = 0

        # Crear el CSV local si no existe, escribiendo la cabecera
        if not os.path.exists(CSV_PENDIENTE):
            with open(CSV_PENDIENTE, "w", newline="") as f:
                csv.writer(f).writerow(CSV_CABECERA)

        self.setup_ui()

        # Arrancar el bucle de animación (1 segundo)
        self.root.after(1000, self._tick)

    # ── Generación de datos sintéticos ───────────────────────────────────────

    def _next_value(self, field: str) -> float:
        lo, hi, _ = self.data_ranges[field]
        step = (hi - lo) * 0.04          # paso máximo: 4 % del rango
        val = self.current_vals[field] + random.uniform(-step, step)
        val = max(lo, min(hi, val))
        self.current_vals[field] = val
        return val

    def _tick(self):
        """Genera un nuevo dato, lo persiste en CSV, actualiza gráficas y dispara el envío bulk."""
        self._tick_count += 1

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        fila = [ts] + [f"{self._next_value(field):.4f}" for field in self.fields]

        # Actualizar historial en memoria para las gráficas
        for i, field in enumerate(self.fields):
            self.historial_datos[field].append(float(fila[i + 1]))

        # Persistir en CSV local (resiliencia ante pérdida de conectividad)
        with open(CSV_PENDIENTE, "a", newline="") as f:
            csv.writer(f).writerow(fila)

        self._redraw_charts()

        # Cada 15 segundos intentar enviar todos los datos pendientes del CSV
        if self._tick_count % 15 == 0:
            self._enviar_batch_api()

        self.root.after(1000, self._tick)

    def _enviar_batch_api(self):
        """Lee el CSV pendiente y envía todos los registros acumulados a ThingSpeak en un único bulk update."""
        if not os.path.exists(CSV_PENDIENTE):
            return

        with open(CSV_PENDIENTE, newline="") as f:
            filas = list(csv.reader(f))

        # filas[0] es la cabecera, filas[1:] son los datos
        datos = filas[1:]
        if not datos:
            return

        # Construir el payload: timestamp_iso,field1,...,field5 separados por |
        # time_format=absolute para respetar los timestamps reales de captura
        entradas = []
        for fila in datos:
            ts = fila[0]
            valores = ",".join(fila[1:])
            entradas.append(f"{ts},{valores}")

        payload = {
            "write_api_key": self.write_key,
            "time_format": "absolute",
            "updates": "|".join(entradas),
        }

        url = f"https://api.thingspeak.com/channels/{self.channel_id}/bulk_update.csv"

        try:
            response = requests.post(url, data=payload, timeout=15)
            if response.status_code in (200, 202):
                print(f"[API] Batch enviado: {len(entradas)} registros")
                # Solo borrar el CSV si el envío fue exitoso
                with open(CSV_PENDIENTE, "w", newline="") as f:
                    csv.writer(f).writerow(CSV_CABECERA)
            else:
                print(f"[API] Error bulk update ({response.status_code}): {response.text.strip()} — datos conservados en CSV")
        except Exception as e:
            print(f"[API] Sin conexión: {e} — datos conservados en CSV para el próximo intento")

    def _redraw_charts(self):
        for field, ui in self.graficos_ui.items():
            ax, canvas, color = ui["ax"], ui["canvas"], ui["color"]
            lo, hi, _ = self.data_ranges[field]
            margin = (hi - lo) * 0.12

            data = list(self.historial_datos[field])
            ax.clear()
            ax.plot(data, color=color, linewidth=1.8)
            ax.fill_between(range(len(data)), data, alpha=0.18, color=color)
            ax.set_ylim(lo - margin, hi + margin)
            ax.grid(True, linestyle=":", alpha=0.5)
            ax.tick_params(labelsize=7)
            canvas.draw_idle()          # draw_idle es más eficiente que draw()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def setup_ui(self):
        self.side_panel = tk.Frame(self.root, bg="#2c3e50", width=200)
        self.side_panel.pack(side="left", fill="y")

        tk.Label(
            self.side_panel, text="ANDROIDE IoT", bg="#2c3e50", fg="white",
            font=("Arial", 14, "bold"),
        ).pack(pady=20, padx=10)

        self.main_area = tk.Frame(self.root, bg="white")
        self.main_area.pack(side="right", expand=True, fill="both")

        self.create_dashboard_view()
        self.create_canal_view()
        self.create_api_view()

        nav_buttons = [
            ("Dashboard",      lambda: self.show_frame("Dashboard")),
            ("Canal Androide", lambda: self.show_frame("Canal Androide")),
            ("API Keys",       lambda: self.show_frame("API Keys")),
        ]
        for text, command in nav_buttons:
            tk.Button(
                self.side_panel, text=text, bg="#34495e", fg="white",
                relief="flat", pady=10, width=20, command=command,
            ).pack(pady=5)

        self.show_frame("Dashboard")

    def show_frame(self, frame_name: str):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(expand=True, fill="both", padx=20, pady=20)

    # ── Vista 1: Dashboard ────────────────────────────────────────────────────

    def create_dashboard_view(self):
        frame = tk.Frame(self.main_area, bg="white")
        self.frames["Dashboard"] = frame

        tk.Label(
            frame, text="Dashboard de Monitorización en Tiempo Real",
            font=("Arial", 16, "bold"), bg="white", fg="#333",
        ).pack(anchor="w", pady=(0, 10))

        graficos_frame = tk.Frame(frame, bg="white")
        graficos_frame.pack(expand=True, fill="both")
        graficos_frame.grid_columnconfigure(0, weight=1)
        graficos_frame.grid_columnconfigure(1, weight=1)

        colores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

        for i, field in enumerate(self.fields):
            g_frame = tk.LabelFrame(
                graficos_frame, text=field, bg="#f8f9fa",
                font=("Arial", 9, "bold"),
            )
            g_frame.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")
            graficos_frame.grid_rowconfigure(i // 2, weight=1)

            fig = Figure(figsize=(4, 2.0), dpi=90)
            ax = fig.add_subplot(111)
            ax.grid(True, linestyle=":", alpha=0.5)
            fig.tight_layout(pad=1.2)

            canvas = FigureCanvasTkAgg(fig, master=g_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=True, fill="both")

            self.graficos_ui[field] = {"fig": fig, "ax": ax, "canvas": canvas, "color": colores[i]}

    # ── Vista 2: Canal Androide ───────────────────────────────────────────────

    def create_canal_view(self):
        frame = tk.Frame(self.main_area, bg="white")
        self.frames["Canal Androide"] = frame

        tk.Label(
            frame, text="Channel Settings: Androide",
            font=("Arial", 18, "bold"), bg="white", fg="#333",
        ).pack(anchor="w")
        tk.Label(
            frame, text=f"Channel ID: {self.channel_id} | Acceso: Público",
            bg="white", fg="gray",
        ).pack(anchor="w", pady=(0, 20))

        form_frame = tk.LabelFrame(
            frame, text="Monitoreo de Campos", padx=20, pady=20, bg="white",
        )
        form_frame.pack(fill="x")

        self.entries = {}
        for i, field in enumerate(self.fields, start=1):
            row = tk.Frame(form_frame, bg="white")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=f"Field {i}: {field}", width=25, anchor="w", bg="white").pack(side="left")
            ent = tk.Entry(row, highlightthickness=1)
            ent.pack(side="left", expand=True, fill="x", padx=10)
            self.entries[field] = ent

        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=20)
        tk.Button(
            btn_frame, text="Escritura (Enviar a Nube)", bg="#27ae60", fg="white",
            font=("Arial", 10, "bold"), padx=20, command=self.escribir_datos,
        ).pack(side="left", padx=10)
        tk.Button(
            btn_frame, text="Lectura (Consultar API)", bg="#2980b9", fg="white",
            font=("Arial", 10, "bold"), padx=20, command=self.leer_datos,
        ).pack(side="left", padx=10)

    # ── Vista 3: API Keys ─────────────────────────────────────────────────────

    def create_api_view(self):
        frame = tk.Frame(self.main_area, bg="white")
        self.frames["API Keys"] = frame

        tk.Label(
            frame, text="Configuración de APIs",
            font=("Arial", 18, "bold"), bg="white", fg="#333",
        ).pack(anchor="w", pady=(0, 20))

        info_frame = tk.Frame(frame, bg="white")
        info_frame.pack(fill="x", pady=10)

        def add_key_row(label_text, key_value):
            row = tk.Frame(info_frame, bg="white")
            row.pack(fill="x", pady=15)
            tk.Label(
                row, text=label_text, width=15, anchor="w", bg="white",
                font=("Arial", 11, "bold"),
            ).pack(side="left")
            ent = tk.Entry(row, font=("Courier", 12), bg="#f8f9fa")
            ent.pack(side="left", expand=True, fill="x", padx=10)
            ent.insert(0, key_value)
            ent.config(state="readonly")

        add_key_row("Channel ID:", self.channel_id)
        add_key_row("Write API Key:", self.write_key)
        add_key_row("Read API Key:", self.read_key)

    # ── Lógica API ThingSpeak ─────────────────────────────────────────────────

    def escribir_datos(self):
        valores = [self.entries[f].get() for f in self.fields]
        if any(v == "" for v in valores):
            messagebox.showwarning("Error", "Por favor completa todos los campos.")
            return

        url = f"https://api.thingspeak.com/update?api_key={self.write_key}"
        for i, val in enumerate(valores, start=1):
            url += f"&field{i}={val}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and response.text.strip() != "0":
                messagebox.showinfo("Éxito", f"Datos enviados al canal {self.channel_id} exitosamente.")
                for field in self.fields:
                    self.entries[field].delete(0, tk.END)
            elif response.text.strip() == "0":
                messagebox.showwarning(
                    "Aviso",
                    "ThingSpeak rechazó el envío.\n"
                    "La versión gratuita requiere esperar 15 segundos entre envíos.",
                )
            else:
                messagebox.showerror("Error", f"Error de la API. Código HTTP: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo de conexión: {e}")

    def leer_datos(self):
        url = (
            f"https://api.thingspeak.com/channels/{self.channel_id}"
            f"/feeds.json?api_key={self.read_key}&results=1"
        )
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                feeds = response.json().get("feeds", [])
                if feeds:
                    ultimo = feeds[0]
                    for i, field in enumerate(self.fields, start=1):
                        self.entries[field].delete(0, tk.END)
                        val = ultimo.get(f"field{i}")
                        if val is not None:
                            self.entries[field].insert(0, str(val))
                    messagebox.showinfo("Lectura", "Último registro recuperado de ThingSpeak.")
                else:
                    messagebox.showinfo("Lectura", "El canal no tiene datos actualmente.")
            else:
                messagebox.showerror("Error", f"Error al leer API. Código: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo de conexión: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAndroide(root)
    root.mainloop()
