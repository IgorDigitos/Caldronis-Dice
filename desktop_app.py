"""Painel Windows do Caldronis Dice, empacotável sem incluir token ou banco."""

import argparse
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from desktop_controller import STATES, BotController
from runtime_lock import AlreadyRunningError, InstanceLock

COLORS = {
    "bg": "#12141a",
    "card": "#1b1e27",
    "border": "#2a2e3b",
    "text": "#e7e9f0",
    "muted": "#8a90a2",
    "log_bg": "#0e1015",
    "accent": "#b48cff",
    "ok": "#3ecf8e",
    "warn": "#f5b544",
    "error": "#f2555a",
    "idle": "#5d6274",
    "start": "#2f9e6e",
    "start_hover": "#36b47d",
    "stop": "#c2414a",
    "stop_hover": "#d94b55",
    "ghost": "#262a36",
    "ghost_hover": "#313646",
    "disabled": "#23262f",
    "disabled_text": "#5b6070",
}
STATE_COLORS = {
    "starting": "warn",
    "online": "ok",
    "reconnecting": "warn",
    "stopping": "warn",
    "stopped": "idle",
}
BLINKING = {"starting", "reconnecting", "stopping"}
LOG_LEVELS = {"info", "ok", "warn", "error"}
MAX_LOG_LINES = 500
FONT = "Segoe UI"
MONO = "Consolas"


def project_directory() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path)
    args = parser.parse_args()
    if args.project_dir:
        return args.project_dir.resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def configure_styles(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")
    c = COLORS
    style.configure(".", background=c["bg"], foreground=c["text"], font=(FONT, 10))
    style.configure("Card.TFrame", background=c["card"])
    style.configure("Bg.TFrame", background=c["bg"])
    style.configure("Title.TLabel", background=c["bg"], font=(FONT, 20, "bold"))
    style.configure("Subtitle.TLabel", background=c["bg"], foreground=c["muted"])
    style.configure("Status.TLabel", background=c["card"], font=(FONT, 13, "bold"))
    style.configure("CardMuted.TLabel", background=c["card"], foreground=c["muted"])
    style.configure("Section.TLabel", background=c["card"], font=(FONT, 11, "bold"))
    style.configure("Footer.TLabel", background=c["bg"], foreground=c["muted"], font=(FONT, 9))
    for name, base, hover in (
        ("Start", c["start"], c["start_hover"]),
        ("Stop", c["stop"], c["stop_hover"]),
        ("Ghost", c["ghost"], c["ghost_hover"]),
    ):
        small = name == "Ghost"
        style.configure(
            f"{name}.TButton",
            background=base,
            foreground=c["text"],
            borderwidth=0,
            focusthickness=0,
            padding=(10, 4) if small else (18, 9),
            font=(FONT, 9 if small else 10, "normal" if small else "bold"),
        )
        style.map(
            f"{name}.TButton",
            background=[("disabled", c["disabled"]), ("active", hover)],
            foreground=[("disabled", c["disabled_text"])],
        )
    style.configure(
        "Log.Vertical.TScrollbar",
        background=c["ghost"],
        troughcolor=c["log_bg"],
        bordercolor=c["log_bg"],
        arrowcolor=c["muted"],
        relief="flat",
    )
    style.map("Log.Vertical.TScrollbar", background=[("active", c["ghost_hover"])])


class ControlPanel:
    def __init__(self, root: tk.Tk, project_dir: Path):
        self.root = root
        self.controller = BotController(project_dir)
        self.closing = False
        self._blink = False
        self._ticks = 0
        self._last_state = None
        root.title("Caldronis Dice")
        root.geometry("760x560")
        root.minsize(620, 460)
        root.configure(background=COLORS["bg"])
        configure_styles(root)

        outer = ttk.Frame(root, style="Bg.TFrame", padding=(24, 20, 24, 14))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="Bg.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Caldronis Dice", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Painel de controle do bot de dados", style="Subtitle.TLabel").pack(
            anchor="w"
        )

        status_card = self._card(outer, pady=(16, 12))
        status_row = ttk.Frame(status_card, style="Card.TFrame")
        status_row.pack(fill="x")
        self.dot = tk.Canvas(
            status_row, width=14, height=14, highlightthickness=0, background=COLORS["card"]
        )
        self.dot_item = self.dot.create_oval(1, 1, 13, 13, fill=COLORS["idle"], outline="")
        self.dot.pack(side="left", padx=(0, 10))
        self.status = tk.StringVar(value=STATES["stopped"])
        ttk.Label(status_row, textvariable=self.status, style="Status.TLabel", wraplength=520).pack(
            side="left", fill="x", expand=True
        )
        self.uptime = tk.StringVar(value="")
        ttk.Label(status_row, textvariable=self.uptime, style="CardMuted.TLabel").pack(side="right")

        buttons = ttk.Frame(status_card, style="Card.TFrame")
        buttons.pack(anchor="w", pady=(14, 0))
        self.start_button = ttk.Button(
            buttons, text="▶  Ligar", style="Start.TButton", command=self.start, cursor="hand2"
        )
        self.start_button.pack(side="left", padx=(0, 10))
        self.stop_button = ttk.Button(
            buttons, text="■  Desligar", style="Stop.TButton", command=self.stop, cursor="hand2"
        )
        self.stop_button.pack(side="left")

        log_card = self._card(outer, expand=True)
        log_header = ttk.Frame(log_card, style="Card.TFrame")
        log_header.pack(fill="x", pady=(0, 8))
        ttk.Label(log_header, text="Atividade", style="Section.TLabel").pack(side="left")
        ttk.Button(log_header, text="Limpar", style="Ghost.TButton", command=self.clear_log).pack(
            side="right"
        )
        ttk.Button(log_header, text="Copiar", style="Ghost.TButton", command=self.copy_log).pack(
            side="right", padx=(0, 6)
        )

        log_frame = tk.Frame(
            log_card,
            background=COLORS["log_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(
            log_frame,
            background=COLORS["log_bg"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["ghost_hover"],
            font=(MONO, 10),
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            wrap="word",
            height=10,
            state="disabled",
            cursor="arrow",
        )
        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log.yview, style="Log.Vertical.TScrollbar"
        )
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.tag_configure("time", foreground=COLORS["muted"])
        for level, color in (
            ("info", COLORS["text"]),
            ("ok", COLORS["ok"]),
            ("warn", COLORS["warn"]),
            ("error", COLORS["error"]),
        ):
            self.log.tag_configure(level, foreground=color)

        footer = ttk.Frame(outer, style="Bg.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(
            footer, text="Fechar esta janela também desliga o bot.", style="Footer.TLabel"
        ).pack(side="left")
        ttk.Label(footer, text=f"Projeto: {project_dir}", style="Footer.TLabel").pack(side="right")

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.append_log("info", "Painel aberto. Clique em Ligar para iniciar o bot.")
        self.refresh()

    def _card(self, parent, pady=(0, 0), expand=False):
        border = tk.Frame(parent, background=COLORS["border"])
        border.pack(fill="both" if expand else "x", expand=expand, pady=pady)
        card = ttk.Frame(border, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True, padx=1, pady=1)
        return card

    def append_log(self, level: str, text: str, moment: str | None = None):
        moment = moment or time.strftime("%H:%M:%S")
        at_bottom = self.log.yview()[1] >= 0.999
        self.log.configure(state="normal")
        self.log.insert("end", moment + "  ", "time")
        self.log.insert("end", text + "\n", level if level in LOG_LEVELS else "info")
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > MAX_LOG_LINES:
            self.log.delete("1.0", f"{lines - MAX_LOG_LINES}.0")
        self.log.configure(state="disabled")
        if at_bottom:
            self.log.see("end")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log.get("1.0", "end-1c"))
        self.append_log("info", "Registro copiado para a área de transferência.")

    def start(self):
        try:
            self.controller.start()
        except OSError:
            messagebox.showerror(
                "Não foi possível ligar", "Confira a pasta do projeto e o ambiente Python .venv."
            )

    def stop(self):
        self.controller.stop()

    def close(self):
        self.closing = True
        self.controller.stop()

    def _show_state(self, state: str):
        self.status.set(STATES[state])
        color_key = STATE_COLORS.get(state, "error")
        color = COLORS[color_key]
        if state in BLINKING and self._blink:
            color = COLORS["idle"]
        self.dot.itemconfigure(self.dot_item, fill=color)
        since = getattr(self.controller, "online_since", None)
        if state == "online" and isinstance(since, (int, float)):
            self.uptime.set("Ligado há " + format_uptime(time.monotonic() - since))
        else:
            self.uptime.set("")

    def refresh(self):
        logs = self.controller.take_logs()
        state = self.controller.poll()
        for entry in logs if isinstance(logs, list) else ():
            self.append_log(entry.level, entry.text, entry.time.strftime("%H:%M:%S"))
        self._ticks += 1
        if self._ticks % 4 == 0:
            self._blink = not self._blink
        self._show_state(state)
        running = self.controller.running
        self.start_button.configure(state="disabled" if running or self.closing else "normal")
        self.stop_button.configure(
            state="normal" if running and state != "stopping" else "disabled"
        )
        if self.closing and not running:
            self.root.destroy()
            return
        self.root.after(150, self.refresh)


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    try:
        project_dir = project_directory()
        if not (project_dir / "bot.py").is_file():
            messagebox.showerror(
                "Projeto não encontrado", "O atalho precisa apontar para a pasta do projeto."
            )
            return 1
        with InstanceLock(project_dir / "data" / ".panel.lock"):
            ControlPanel(root, project_dir)
            root.deiconify()
            root.mainloop()
    except AlreadyRunningError:
        messagebox.showinfo("Caldronis Dice", "O painel já está aberto para este projeto.")
    except OSError:
        messagebox.showerror("Caldronis Dice", "Não foi possível acessar a pasta do projeto.")
        return 1
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
