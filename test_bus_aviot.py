#!/usr/bin/env python3
"""
Test de Bus Modbus - Aviot
Herramienta de diagnóstico: escanea el bus RS485 buscando todas las sondas
conectadas (IDs 1-247) y muestra resultado visual con detección de colisiones.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import struct
import time
import threading
import sys
import os


# ───────── Recursos PyInstaller ─────────
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ───────── Modbus helpers ─────────
def crc16_modbus(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def send_recv(ser, frame_data, timeout=0.15):
    """Envía trama y devuelve respuesta cruda."""
    crc = crc16_modbus(frame_data)
    frame = frame_data + struct.pack('<H', crc)
    ser.reset_input_buffer()
    ser.write(frame)
    time.sleep(timeout)
    return ser.read(100)


def leer_temp_hum(ser, slave_id):
    """Lee temperatura y humedad de la sonda (registros 0x0000 y 0x0001).
    Devuelve (temp, hum) o None si no responde / CRC inválido / colisión."""
    resp = send_recv(ser, bytes([slave_id, 0x03, 0x00, 0x00, 0x00, 0x02]))
    if not resp:
        return ('NO_RESP', None)
    if len(resp) < 9:
        return ('SHORT', f"{len(resp)} bytes")
    if resp[0] != slave_id:
        return ('WRONG_ID', resp[0])
    # CRC check
    body = resp[:7]
    crc_recv = (resp[8] << 8) | resp[7]
    crc_calc = crc16_modbus(body)
    if crc_recv != crc_calc:
        return ('CRC_ERR', '¿colisión?')
    if resp[1] & 0x80:  # error code
        return ('MODBUS_ERR', resp[2])
    hum = ((resp[3] << 8) | resp[4]) / 10.0
    temp = ((resp[5] << 8) | resp[6]) / 10.0
    return ('OK', (temp, hum))


# ───────── Branding Aviot ─────────
AVIOT_NARANJA = "#f39200"
AVIOT_NARANJA_HOVER = "#e08500"
AVIOT_OSCURO = "#1d1d1b"
AVIOT_BLANCO = "#ffffff"
AVIOT_GRIS_CLARO = "#f5f5f5"
AVIOT_GRIS = "#e0e0e0"
AVIOT_VERDE = "#4CAF50"
AVIOT_ROJO = "#e53935"
AVIOT_AMARILLO = "#fbc02d"


def show_splash(root):
    """Splash screen con instrucciones."""
    splash = tk.Toplevel(root)
    splash.configure(bg=AVIOT_BLANCO)
    splash.title("Test de Bus Modbus - Aviot")

    w, h = 700, 700
    x = (splash.winfo_screenwidth() - w) // 2
    y = max(20, (splash.winfo_screenheight() - h) // 2)
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.minsize(w, h)

    border = tk.Frame(splash, bg=AVIOT_NARANJA, padx=3, pady=3)
    border.pack(fill="both", expand=True)

    container = tk.Frame(border, bg=AVIOT_BLANCO)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=AVIOT_BLANCO, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas, bg=AVIOT_BLANCO)
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())
    inner.bind("<Configure>", on_configure)
    canvas.bind("<Configure>", on_configure)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # Logo
    try:
        logo_path = resource_path("logo_aviot.png")
        splash.logo_img = tk.PhotoImage(file=logo_path)
        scale = max(splash.logo_img.width() // 200, splash.logo_img.height() // 60, 1)
        splash.logo_small = splash.logo_img.subsample(scale, scale)
        tk.Label(inner, image=splash.logo_small, bg=AVIOT_BLANCO).pack(pady=(20, 5))
    except Exception:
        pass

    tk.Label(inner, text="TEST DE BUS MODBUS",
             font=("Arial", 24, "bold"), fg=AVIOT_NARANJA, bg=AVIOT_BLANCO).pack(pady=(5, 2))

    tk.Label(inner, text="Diagnóstico de bus RS485  |  Modbus RTU  |  v1.0",
             font=("Arial", 12), fg="#888", bg=AVIOT_BLANCO).pack(pady=(0, 5))

    tk.Frame(inner, height=3, bg=AVIOT_NARANJA).pack(fill="x", padx=30, pady=8)

    tk.Label(inner, text="¿Qué hace este programa?",
             font=("Arial", 14, "bold"), fg=AVIOT_OSCURO, bg=AVIOT_BLANCO,
             anchor="w").pack(fill="x", padx=30)

    desc = (
        "Esta herramienta escanea TODO el bus RS485 buscando sondas\n"
        "Modbus en los IDs 1 al 247. Muestra cuáles responden, sus\n"
        "lecturas de temperatura y humedad, y detecta colisiones de\n"
        "ID (dos sondas con el mismo ID compitiendo en el bus).\n\n"
        "Sirve para verificar que toda la instalación está correcta\n"
        "tras un montaje, reemplazo de sonda o avería."
    )
    tk.Label(inner, text=desc, font=("Arial", 12), fg="#555", bg=AVIOT_BLANCO,
             justify="left", anchor="w").pack(fill="x", padx=30, pady=(2, 8))

    tk.Frame(inner, height=1, bg=AVIOT_GRIS).pack(fill="x", padx=30, pady=3)

    tk.Label(inner, text="¿Cómo conectar?",
             font=("Arial", 14, "bold"), fg=AVIOT_OSCURO, bg=AVIOT_BLANCO,
             anchor="w").pack(fill="x", padx=30, pady=(5, 0))

    pasos = (
        "1. Conecta el adaptador USB-Modbus al portátil.\n"
        "2. Conéctalo en paralelo al bus RS485 de la instalación\n"
        "    (cable A+ y cable B-) en CUALQUIER punto del bus.\n"
        "3. NO desconectes ninguna sonda: queremos ver el bus completo.\n"
        "4. Verifica que el bus tiene su alimentación 12-24V activa."
    )
    tk.Label(inner, text=pasos, font=("Arial", 12), fg="#555",
             bg=AVIOT_BLANCO, justify="left", anchor="w").pack(fill="x", padx=30, pady=(2, 8))

    tk.Frame(inner, height=1, bg=AVIOT_GRIS).pack(fill="x", padx=30, pady=3)

    tk.Label(inner, text="Lectura de resultados",
             font=("Arial", 14, "bold"), fg=AVIOT_OSCURO, bg=AVIOT_BLANCO,
             anchor="w").pack(fill="x", padx=30, pady=(5, 0))

    leyenda = (
        "  ✓ Verde   — sonda detectada, lectura OK\n"
        "  · Gris    — sin respuesta (no hay sonda en ese ID)\n"
        "  ⚠ Amarillo — respuesta corrupta o CRC inválido\n"
        "                (posible colisión: 2 sondas con el mismo ID)\n"
        "  ✗ Rojo    — error Modbus reportado por la sonda"
    )
    tk.Label(inner, text=leyenda, font=("Consolas", 11), fg="#555",
             bg=AVIOT_BLANCO, justify="left", anchor="w").pack(fill="x", padx=30, pady=(2, 5))

    tk.Frame(inner, height=3, bg=AVIOT_NARANJA).pack(fill="x", padx=30, pady=(10, 10))

    def comenzar():
        canvas.unbind_all("<MouseWheel>")
        splash.destroy()
        root.deiconify()

    btn = tk.Button(inner, text="COMENZAR", font=("Arial", 18, "bold"),
                    bg=AVIOT_NARANJA, fg=AVIOT_BLANCO,
                    activebackground=AVIOT_NARANJA_HOVER, activeforeground=AVIOT_BLANCO,
                    relief="flat", padx=40, pady=10, cursor="hand2",
                    command=comenzar)
    btn.pack(pady=(0, 15))

    tk.Label(inner, text="Aviot - Always Safe  |  Ingeniatic Desarrollo S.L.",
             font=("Arial", 8), fg="#ccc", bg=AVIOT_BLANCO).pack(pady=(0, 15))

    splash.lift()
    splash.focus_force()

    try:
        logo_path = resource_path("logo_aviot.png")
        splash.iconphoto(True, tk.PhotoImage(file=logo_path))
    except Exception:
        pass

    splash.protocol("WM_DELETE_WINDOW", comenzar)
    root.withdraw()
    return splash


# ───────── App principal ─────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Test de Bus Modbus - Aviot")
        self.root.configure(bg=AVIOT_BLANCO)
        self.root.geometry("900x720")
        self.root.minsize(800, 600)

        self.ser = None
        self.escaneando = False
        self.resultados = {}  # id -> dict(status, temp, hum, raw)

        try:
            self.logo_img = tk.PhotoImage(file=resource_path("logo_aviot.png"))
            self.root.iconphoto(True, self.logo_img)
        except Exception:
            self.logo_img = None

        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=AVIOT_BLANCO, foreground=AVIOT_OSCURO)
        style.configure("TFrame", background=AVIOT_BLANCO)
        style.configure("TLabelframe", background=AVIOT_BLANCO)
        style.configure("TLabelframe.Label", background=AVIOT_BLANCO,
                        foreground=AVIOT_NARANJA, font=("Arial", 11, "bold"))
        style.configure("Aviot.TButton", font=("Arial", 13, "bold"),
                        padding=10, background=AVIOT_NARANJA, foreground=AVIOT_BLANCO)
        style.map("Aviot.TButton",
                  background=[('active', AVIOT_NARANJA_HOVER), ('pressed', AVIOT_OSCURO)])
        style.configure("Header.TLabel", font=("Arial", 18, "bold"),
                        foreground=AVIOT_NARANJA, background=AVIOT_BLANCO)
        style.configure("Sub.TLabel", font=("Arial", 10),
                        foreground="#888", background=AVIOT_BLANCO)
        style.configure("OK.TLabel", font=("Arial", 12, "bold"),
                        foreground=AVIOT_VERDE, background=AVIOT_BLANCO)
        style.configure("Error.TLabel", font=("Arial", 12, "bold"),
                        foreground=AVIOT_ROJO, background=AVIOT_BLANCO)
        style.configure("Aviot.Horizontal.TProgressbar",
                        troughcolor=AVIOT_GRIS, background=AVIOT_NARANJA, thickness=20)

        main = ttk.Frame(root, padding=15)
        main.pack(fill="both", expand=True)

        # Header
        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))
        if self.logo_img:
            try:
                small_logo = self.logo_img.subsample(
                    max(1, self.logo_img.width() // 180),
                    max(1, self.logo_img.height() // 50)
                )
                self.small_logo = small_logo
                ttk.Label(header, image=self.small_logo, background=AVIOT_BLANCO).pack()
            except Exception:
                pass
        ttk.Label(header, text="TEST DE BUS MODBUS", style="Header.TLabel").pack()
        ttk.Label(header, text="Diagnóstico de bus RS485  |  Modbus RTU", style="Sub.TLabel").pack()

        tk.Frame(main, height=3, bg=AVIOT_NARANJA).pack(fill="x", pady=(0, 10))

        # Conexión
        frame_con = ttk.LabelFrame(main, text=" Conexión ", padding=10)
        frame_con.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_con, text="Puerto:", font=("Arial", 11)).grid(row=0, column=0, sticky="w")
        self.combo_puerto = ttk.Combobox(frame_con, width=35, font=("Arial", 11), state="readonly")
        self.combo_puerto.grid(row=0, column=1, padx=5)
        ttk.Button(frame_con, text="Actualizar", command=self.actualizar_puertos).grid(row=0, column=2, padx=5)

        ttk.Label(frame_con, text="Baudrate:", font=("Arial", 11)).grid(row=0, column=3, padx=(15, 5), sticky="w")
        self.combo_baud = ttk.Combobox(frame_con, width=8, font=("Arial", 11), state="readonly",
                                       values=["4800", "9600", "19200", "38400", "57600", "115200"])
        self.combo_baud.grid(row=0, column=4)
        self.combo_baud.set("4800")

        # Rango de IDs
        frame_rango = ttk.LabelFrame(main, text=" Rango de escaneo ", padding=10)
        frame_rango.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_rango, text="Desde ID:", font=("Arial", 11)).grid(row=0, column=0, sticky="w")
        self.spin_desde = ttk.Spinbox(frame_rango, from_=1, to=247, width=5, font=("Arial", 12))
        self.spin_desde.grid(row=0, column=1, padx=5)
        self.spin_desde.set(1)

        ttk.Label(frame_rango, text="Hasta ID:", font=("Arial", 11)).grid(row=0, column=2, padx=(15, 5), sticky="w")
        self.spin_hasta = ttk.Spinbox(frame_rango, from_=1, to=247, width=5, font=("Arial", 12))
        self.spin_hasta.grid(row=0, column=3, padx=5)
        self.spin_hasta.set(128)

        self.btn_escanear = ttk.Button(frame_rango, text="ESCANEAR BUS", style="Aviot.TButton",
                                        command=self.toggle_escaneo)
        self.btn_escanear.grid(row=0, column=4, padx=15)

        # Progreso
        self.progress = ttk.Progressbar(main, mode='determinate',
                                        style="Aviot.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 5))

        self.lbl_progreso = ttk.Label(main, text="Listo para escanear", font=("Arial", 10),
                                       foreground="#888", background=AVIOT_BLANCO)
        self.lbl_progreso.pack(anchor="w", pady=(0, 10))

        # Tabla resultados
        frame_tabla = ttk.LabelFrame(main, text=" Resultados ", padding=10)
        frame_tabla.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "estado", "temperatura", "humedad", "detalle")
        self.tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("temperatura", text="Temperatura")
        self.tree.heading("humedad", text="Humedad")
        self.tree.heading("detalle", text="Detalle")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("estado", width=120, anchor="center")
        self.tree.column("temperatura", width=110, anchor="center")
        self.tree.column("humedad", width=110, anchor="center")
        self.tree.column("detalle", width=300, anchor="w")

        self.tree.tag_configure("ok", background="#e8f5e9", foreground=AVIOT_VERDE)
        self.tree.tag_configure("warn", background="#fff8e1", foreground="#e65100")
        self.tree.tag_configure("err", background="#ffebee", foreground=AVIOT_ROJO)
        self.tree.tag_configure("empty", foreground="#bbb")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Resumen
        self.frame_resumen = tk.Frame(main, bg=AVIOT_GRIS_CLARO, padx=10, pady=8)
        self.frame_resumen.pack(fill="x", pady=(0, 5))

        self.lbl_resumen = tk.Label(self.frame_resumen,
                                     text="Aún no se ha realizado ningún escaneo.",
                                     font=("Arial", 11), bg=AVIOT_GRIS_CLARO, fg="#555",
                                     justify="left", anchor="w")
        self.lbl_resumen.pack(fill="x")

        # Footer
        ttk.Label(main, text="Aviot - Always Safe  |  aviot.es  |  Ingeniatic Desarrollo S.L.",
                  font=("Arial", 9), foreground="#aaa", background=AVIOT_BLANCO).pack(pady=(5, 0))

        self.actualizar_puertos()

    # ─── Métodos ───
    def actualizar_puertos(self):
        puertos = serial.tools.list_ports.comports()
        encontrados = []
        for p in puertos:
            texto = f"{p.device} {p.description} {p.hwid}".lower()
            if 'usb' in texto or 'serial' in texto or 'ch340' in texto or 'cp210' in texto or 'ftdi' in texto:
                encontrados.append(f"{p.device} - {p.description}")
        self.combo_puerto['values'] = encontrados if encontrados else ["No se detectan puertos"]
        if encontrados:
            self.combo_puerto.current(0)

    def conectar(self):
        if self.ser and self.ser.is_open:
            return True
        puerto_sel = self.combo_puerto.get()
        if not puerto_sel or "No se detectan" in puerto_sel:
            messagebox.showerror("Error", "Conecta el adaptador USB-Modbus y pulsa Actualizar.")
            return False
        puerto = puerto_sel.split(" - ")[0].strip()
        try:
            self.ser = serial.Serial(
                port=puerto, baudrate=int(self.combo_baud.get()),
                parity='N', stopbits=1, bytesize=8, timeout=0.2)
            return True
        except serial.SerialException as e:
            messagebox.showerror("Error", f"No se pudo abrir el puerto:\n{e}")
            return False

    def toggle_escaneo(self):
        if self.escaneando:
            self.escaneando = False
            self.btn_escanear.config(text="ESCANEAR BUS")
            return

        if not self.conectar():
            return

        try:
            id_desde = int(self.spin_desde.get())
            id_hasta = int(self.spin_hasta.get())
        except ValueError:
            messagebox.showerror("Error", "Rango de IDs inválido.")
            return
        if not (1 <= id_desde <= 247) or not (1 <= id_hasta <= 247) or id_desde > id_hasta:
            messagebox.showerror("Error", "Rango debe estar entre 1 y 247, y desde ≤ hasta.")
            return

        # Limpiar tabla
        for it in self.tree.get_children():
            self.tree.delete(it)
        self.resultados.clear()

        self.escaneando = True
        self.btn_escanear.config(text="PARAR")
        self.progress['value'] = 0
        self.progress['maximum'] = id_hasta - id_desde + 1

        threading.Thread(target=self._scan_loop, args=(id_desde, id_hasta), daemon=True).start()

    def _scan_loop(self, id_desde, id_hasta):
        ok_count = 0
        warn_count = 0
        err_count = 0
        sonda_ids = []
        col_ids = []

        for sid in range(id_desde, id_hasta + 1):
            if not self.escaneando:
                break

            self.root.after(0, lambda s=sid, d=id_desde, h=id_hasta: self._update_progress(s, d, h))
            kind, data = leer_temp_hum(self.ser, sid)

            if kind == 'OK':
                temp, hum = data
                self.root.after(0, lambda s=sid, t=temp, hm=hum: self._add_row(s, 'OK', f'{t} °C', f'{hm} %', '-', 'ok'))
                ok_count += 1
                sonda_ids.append(sid)
            elif kind == 'NO_RESP':
                pass  # no rellenamos la tabla con vacíos para no saturar (opcional)
            elif kind in ('CRC_ERR', 'WRONG_ID'):
                self.root.after(0, lambda s=sid, k=kind, d=str(data): self._add_row(s, k, '—', '—', d, 'warn'))
                warn_count += 1
                col_ids.append(sid)
            else:
                self.root.after(0, lambda s=sid, k=kind, d=str(data): self._add_row(s, k, '—', '—', d, 'err'))
                err_count += 1

        self.root.after(0, lambda: self._scan_done(ok_count, warn_count, err_count, sonda_ids, col_ids))

    def _update_progress(self, sid, id_desde, id_hasta):
        self.progress['value'] = sid - id_desde + 1
        self.lbl_progreso.config(text=f"Probando ID {sid} ({sid - id_desde + 1}/{id_hasta - id_desde + 1})")

    def _add_row(self, sid, estado, temp, hum, detalle, tag):
        prefix = {'ok': '✓', 'warn': '⚠', 'err': '✗', 'empty': '·'}.get(tag, '')
        self.tree.insert('', 'end', values=(f"{prefix} {sid}", estado, temp, hum, detalle), tags=(tag,))

    def _scan_done(self, ok, warn, err, sonda_ids, col_ids):
        self.escaneando = False
        self.btn_escanear.config(text="ESCANEAR BUS")
        self.lbl_progreso.config(text="Escaneo completado.")

        resumen = []
        resumen.append(f"✅  Sondas detectadas: {ok}")
        if sonda_ids:
            resumen.append(f"     IDs: {', '.join(str(i) for i in sonda_ids)}")
        if warn:
            resumen.append(f"⚠️  Posibles colisiones / CRC inválido: {warn}  (IDs: {', '.join(str(i) for i in col_ids)})")
        if err:
            resumen.append(f"❌  Errores Modbus: {err}")

        if not ok and not warn and not err:
            resumen.append("⚠️  No se ha detectado NINGUNA sonda en el rango.")
            resumen.append("    Comprueba: cable A/B, alimentación 12-24V, baudrate, terminación 120Ω.")

        self.lbl_resumen.config(text="\n".join(resumen))


# ───────── Main ─────────
if __name__ == "__main__":
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Aviot.Horizontal.TProgressbar",
                    troughcolor=AVIOT_GRIS, background=AVIOT_NARANJA, thickness=20)

    app_holder = {}

    def on_splash_close():
        if not app_holder:
            app_holder['app'] = App(root)

    splash = show_splash(root)
    root.bind("<Map>", lambda e: on_splash_close())
    root.mainloop()
