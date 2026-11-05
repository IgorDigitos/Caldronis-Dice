"""Painel Windows do Caldronis Dice, empacotável sem incluir token ou banco."""

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from desktop_controller import STATES, BotController
from runtime_lock import AlreadyRunningError, InstanceLock


def project_directory() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path)
    args = parser.parse_args()
    if args.project_dir:
        return args.project_dir.resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


class ControlPanel:
    def __init__(self, root: tk.Tk, project_dir: Path):
        self.root = root
        self.controller = BotController(project_dir)
        self.closing = False
        root.title("Caldronis Dice")
        root.geometry("510x255")
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Caldronis Dice", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        self.status = tk.StringVar(value=STATES["stopped"])
        ttk.Label(frame, textvariable=self.status, wraplength=455, font=("Segoe UI", 11)).pack(
            anchor="w", pady=(14, 16)
        )
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w")
        self.start_button = ttk.Button(buttons, text="Ligar", command=self.start, width=15)
        self.start_button.pack(side="left", padx=(0, 10))
        self.stop_button = ttk.Button(buttons, text="Desligar", command=self.stop, width=15)
        self.stop_button.pack(side="left")
        ttk.Label(
            frame, text="Fechar esta janela também desliga o bot.", font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(18, 4))
        ttk.Label(frame, text=f"Projeto: {project_dir}", font=("Segoe UI", 8)).pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

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

    def refresh(self):
        state = self.controller.poll()
        self.status.set(STATES[state])
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
