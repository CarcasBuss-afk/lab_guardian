"""Spike B1 - prototipo dell'overlay del gate (solo UI + login).

Finestra senza bordi che copre TUTTI i monitor (desktop virtuale): messaggio,
pulsante di login, stato. Al clic esegue il flusso OAuth validato nello Spike A
e, a login riuscito, mostra l'utente e "sblocca" (chiude la finestra).

NON include il servizio SYSTEM ne' il watchdog (= Spike B2, da provare sul PC di
laboratorio). Qui validiamo la UX del gate, la copertura multi-monitor e
l'integrazione del login.

Uso:
    agent\\.buildenv\\Scripts\\python.exe agent\\spike_overlay.py

Note:
- durante il login l'overlay smette temporaneamente di forzare il "topmost" per
  lasciare in primo piano la finestra del browser; se la finestra del browser
  finisce dietro l'overlay, il pulsante "Annulla" interrompe il login e
  ripristina lo stato iniziale;
- scorciatoia di emergenza SOLO per il prototipo (non esistera' nel prodotto):
  Ctrl+Shift+Q.
"""

import ctypes
import threading
import tkinter as tk
from tkinter import font as tkfont

from spike_oauth import login

# Vuoto in test; in produzione "ciacdidattica.it" (vedi Spike A / PROGETTO_SESSIONI.md)
HD_DOMAIN = ""

BG = "#0f172a"
FG_TITLE = "#ffffff"
FG_BODY = "#cbd5e1"
FG_MUTED = "#94a3b8"
FG_OK = "#4ade80"
FG_ERR = "#f87171"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
CANCEL_BG = "#1e293b"
CANCEL_HOVER = "#334155"

# Indici GetSystemMetrics
SM_CXSCREEN, SM_CYSCREEN = 0, 1  # monitor primario
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77  # origine desktop virtuale
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79  # dimensioni desktop virtuale


def virtual_screen():
    """Bounding box di TUTTI i monitor (x, y, larghezza, altezza) e primario."""
    gm = ctypes.windll.user32.GetSystemMetrics
    vx, vy = gm(SM_XVIRTUALSCREEN), gm(SM_YVIRTUALSCREEN)
    vw, vh = gm(SM_CXVIRTUALSCREEN), gm(SM_CYVIRTUALSCREEN)
    pw, ph = gm(SM_CXSCREEN), gm(SM_CYSCREEN)
    return vx, vy, vw, vh, pw, ph


class GateOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lab Guardian")
        self.root.configure(bg=BG)
        self.cancel_event = threading.Event()

        # Copre l'INTERO desktop virtuale (tutti i monitor), senza bordi.
        vx, vy, vw, vh, pw, ph = virtual_screen()
        self.root.overrideredirect(True)
        self.root.geometry(f"{vw}x{vh}+{vx}+{vy}")
        self.root.attributes("-topmost", True)

        # Neutralizza la chiusura della finestra (best effort nel prototipo)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        # Uscita di emergenza SOLO per il prototipo
        self.root.bind("<Control-Shift-Q>", lambda e: self.root.destroy())
        self.root.focus_force()

        title_font = tkfont.Font(family="Segoe UI", size=30, weight="bold")
        body_font = tkfont.Font(family="Segoe UI", size=15)
        btn_font = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        status_font = tkfont.Font(family="Segoe UI", size=12)

        box = tk.Frame(self.root, bg=BG)
        # Centra il contenuto sul monitor PRIMARIO (origine a 0,0 nello spazio schermo;
        # nella finestra e' a offset -vx,-vy), non a cavallo tra i monitor.
        box.place(x=-vx + pw // 2, y=-vy + ph // 2, anchor="center")

        tk.Label(box, text="Accesso richiesto", font=title_font,
                 fg=FG_TITLE, bg=BG).pack(pady=(0, 14))
        tk.Label(
            box,
            text="Accedi con il tuo account scolastico per usare questo PC.\n"
                 "La sessione e' monitorata.",
            font=body_font, fg=FG_BODY, bg=BG, justify="center",
        ).pack(pady=(0, 30))

        self.button = tk.Button(
            box, text="Accedi con l'account scolastico", font=btn_font,
            fg="white", bg=ACCENT, activebackground=ACCENT_HOVER,
            activeforeground="white", relief="flat", padx=26, pady=13,
            cursor="hand2", command=self.on_login,
        )
        self.button.pack()

        # Pulsante di annullamento: visibile solo durante il login (reset)
        self.cancel_button = tk.Button(
            box, text="Annulla e riprova", font=body_font,
            fg=FG_BODY, bg=CANCEL_BG, activebackground=CANCEL_HOVER,
            activeforeground="white", relief="flat", padx=18, pady=8,
            cursor="hand2", command=self.on_cancel,
        )

        self.status = tk.Label(box, text="", font=status_font, fg=FG_MUTED, bg=BG)
        self.status.pack(pady=(22, 0))

        # Re-assert periodico del topmost (anticipa il watchdog del prodotto).
        self._enforce_top = True
        self._keep_on_top()

    def _keep_on_top(self):
        if self._enforce_top:
            self.root.attributes("-topmost", True)
            self.root.lift()
        self.root.after(1000, self._keep_on_top)

    def set_status(self, text, color=FG_MUTED):
        # tkinter non e' thread-safe: aggiorna sempre dal main thread via after()
        self.root.after(0, lambda: self.status.config(text=text, fg=color))

    def on_login(self):
        self.cancel_event = threading.Event()
        self.button.config(state="disabled")
        self.cancel_button.pack(pady=(14, 0))
        # Smette di forzare il topmost: lascia in primo piano il browser di login
        self._enforce_top = False
        self.root.attributes("-topmost", False)
        threading.Thread(target=self._do_login, daemon=True).start()

    def on_cancel(self):
        # Interrompe l'attesa del login nel worker; il reset avviene in _do_login
        self.cancel_event.set()

    def _do_login(self):
        try:
            claims = login(hd_domain=HD_DOMAIN, status=self.set_status,
                           cancel_event=self.cancel_event)
        except Exception as e:  # noqa: BLE001 - prototipo: mostra qualsiasi errore
            if self.cancel_event.is_set():
                self.set_status("Login annullato. Puoi riprovare.", FG_MUTED)
            else:
                self.set_status(f"Login fallito: {e}", FG_ERR)
            self.root.after(0, self._reset)
            return
        email = claims.get("email", "?")
        self.set_status(f"Accesso riuscito - {email}. Sblocco...", FG_OK)
        # Simula lo sblocco: chiude l'overlay dopo 2.5s
        self.root.after(2500, self.root.destroy)

    def _reset(self):
        """Ripristina lo stato iniziale: overlay topmost, pulsante login attivo."""
        self._enforce_top = True
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.cancel_button.pack_forget()
        self.button.config(state="normal")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    GateOverlay().run()
