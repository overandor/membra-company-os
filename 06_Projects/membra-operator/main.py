"""
MEMBRA Operator macOS App
Tkinter UI with voice, monitor, LLM, memory, and tools.
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

# Ensure our package modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from coordinator import MembraOperator

BG = "#060914"
FG = "#c9d1d9"
ACCENT = "#f59e0b"  # amber-500
SECONDARY = "#1a2035"
FONT_FAMILY = "SF Pro Display" if sys.platform == "darwin" else "Helvetica"

class OperatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MEMBRA Operator")
        self.root.configure(bg=BG)
        self.root.geometry("960x640")
        if sys.platform == "darwin":
            self.root.createcommand("tk::mac::ReopenApplication", self._reopen)

        self.operator = MembraOperator()
        self.operator.start()

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        # Sidebar
        sidebar = tk.Frame(self.root, bg=SECONDARY, width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="MEMBRA", bg=SECONDARY, fg=ACCENT, font=(FONT_FAMILY, 16, "bold")).pack(pady=12)
        tk.Label(sidebar, text="Operator", bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 10)).pack()

        self.btn_listen = tk.Button(sidebar, text="🎙 Listen", bg=ACCENT, fg=BG, font=(FONT_FAMILY, 12, "bold"),
                                     relief=tk.FLAT, cursor="hand2", command=self._toggle_listen)
        self.btn_listen.pack(fill=tk.X, padx=12, pady=8)

        tk.Button(sidebar, text="👁 Watch 3m", bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 11),
                  relief=tk.FLAT, cursor="hand2", command=self._start_watch).pack(fill=tk.X, padx=12, pady=4)

        tk.Button(sidebar, text="🎤 Interview", bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 11),
                  relief=tk.FLAT, cursor="hand2", command=self._start_interview).pack(fill=tk.X, padx=12, pady=4)

        tk.Button(sidebar, text="📋 Checklist", bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 11),
                  relief=tk.FLAT, cursor="hand2", command=self._show_checklist).pack(fill=tk.X, padx=12, pady=4)

        self.btn_reconnect = tk.Button(sidebar, text="🔄 Reconnect Ollama", bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 10),
                                        relief=tk.FLAT, cursor="hand2", command=self._reconnect_llm)
        self.btn_reconnect.pack(fill=tk.X, padx=12, pady=4)

        self.ollama_status = tk.Label(sidebar, text="Ollama: checking...", bg=SECONDARY, fg="#64748b",
                                       font=(FONT_FAMILY, 9))
        self.ollama_status.pack(side=tk.BOTTOM, pady=4)

        self.status_label = tk.Label(sidebar, text="Status: idle", bg=SECONDARY, fg="#64748b",
                                      font=(FONT_FAMILY, 9))
        self.status_label.pack(side=tk.BOTTOM, pady=4)

        # Main area
        main = tk.Frame(self.root, bg=BG)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Chat / Log
        self.log = scrolledtext.ScrolledText(main, bg=BG, fg=FG, insertbackground=FG,
                                              font=(FONT_FAMILY, 11), wrap=tk.WORD,
                                              highlightthickness=0, borderwidth=0)
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_config("user", foreground="#38bdf8")
        self.log.tag_config("bot", foreground=ACCENT)
        self.log.tag_config("system", foreground="#64748b")

        # Input bar
        input_frame = tk.Frame(main, bg=BG)
        input_frame.pack(fill=tk.X, pady=(8, 0))

        self.entry = tk.Entry(input_frame, bg=SECONDARY, fg=FG, insertbackground=FG,
                              font=(FONT_FAMILY, 12), relief=tk.FLAT, highlightthickness=1,
                              highlightbackground=SECONDARY, highlightcolor=ACCENT)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self.entry.bind("<Return>", self._on_send)

        tk.Button(input_frame, text="Send", bg=ACCENT, fg=BG, font=(FONT_FAMILY, 11, "bold"),
                  relief=tk.FLAT, cursor="hand2", command=self._on_send).pack(side=tk.RIGHT)

        # Quick actions
        qa = tk.Frame(main, bg=BG)
        qa.pack(fill=tk.X, pady=(8, 0))
        for label in ["Continue", "Build", "Test", "Deploy"]:
            tk.Button(qa, text=label, bg=SECONDARY, fg=FG, font=(FONT_FAMILY, 10),
                      relief=tk.FLAT, cursor="hand2",
                      command=lambda l=label: self._quick_action(l)).pack(side=tk.LEFT, padx=(0, 6))

        self._log("system", "MEMBRA Operator initialized.\nWorkspace: " + self.operator.workspace)
        self._update_ollama_status()
        if not self.operator.llm.connected:
            self._log("system", "⚠️ Ollama not connected. Click '🔄 Reconnect Ollama' or run: ollama serve")
        else:
            self._log("system", "Ollama connected. Say something or type a command.")

    def _log(self, tag: str, text: str):
        self.log.insert(tk.END, text + "\n", tag)
        self.log.see(tk.END)

    def _on_send(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._log("user", f"> {text}")
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()

    def _process_text(self, text: str):
        self.operator.last_user_message = text
        self.operator.memory.add_message(self.operator.session_id, "user", text)
        if not self.operator.llm.connected:
            msg = "Ollama is not connected. Please run 'ollama serve' and click '🔄 Reconnect Ollama'."
            self._log("system", msg)
            self._set_status("idle")
            self.operator.speak(msg)
            return
        self._set_status("thinking...")
        try:
            from tools import TOOL_REGISTRY
            response = self.operator.llm.tool_call(
                text, TOOL_REGISTRY, self.operator.memory.get_recent_context(self.operator.session_id, n=10)
            )
        except Exception as e:
            response = f"[Error: {e}]"
        self._set_status("idle")
        self._log("bot", f"{response}")
        self.operator.speak(response)

    def _toggle_listen(self):
        if self.operator.voice.listening:
            self.operator.voice.stop_background_listener()
            self.btn_listen.config(text="🎙 Listen")
            self._log("system", "Background listening stopped.")
        else:
            self.operator.voice.start_background_listener()
            self.btn_listen.config(text="🔴 Stop")
            self._log("system", "Background listening started. Speak to interact.")

    def _start_watch(self):
        self._log("system", "Starting 3-minute watch mode...")
        threading.Thread(target=self.operator.start_watch_mode, args=(180,), daemon=True).start()

    def _start_interview(self):
        self._log("system", "Starting interview mode...")
        threading.Thread(target=self.operator.start_interview, daemon=True).start()

    def _show_checklist(self):
        items = self.operator.memory.get_checklist()
        lines = [f"{'✅' if i['status']=='passed' else '⏳'} {i['checkpoint']}" for i in items]
        messagebox.showinfo("Production Readiness", "\n".join(lines))

    def _quick_action(self, label: str):
        mapping = {
            "Continue": "Continue the most obvious next step based on the workspace.",
            "Build": "Build the project. Run any necessary build commands.",
            "Test": "Run tests or smoke checks. Report results.",
            "Deploy": "Check deployment config and prepare for release.",
        }
        self._log("user", f"> {label}")
        threading.Thread(target=self._process_text, args=(mapping[label],), daemon=True).start()

    def _set_status(self, text: str):
        self.status_label.config(text=f"Status: {text}")
        self.operator.status = text

    def _update_loop(self):
        self._update_ollama_status()
        self.root.after(2000, self._update_loop)

    def _update_ollama_status(self):
        connected = self.operator.llm._check_health()
        model = self.operator.llm.model
        if connected:
            self.ollama_status.config(text=f"Ollama: {model}", fg="#22c55e")
        else:
            self.ollama_status.config(text="Ollama: offline", fg="#ef4444")

    def _reconnect_llm(self):
        self._log("system", "Reconnecting to Ollama...")
        if self.operator.llm._check_health():
            self._log("system", f"Ollama connected ({self.operator.llm.model}).")
        else:
            self._log("system", "Ollama still unreachable. Make sure 'ollama serve' is running.")

    def _reopen(self):
        self.root.lift()
        self.root.focus_force()

    def on_close(self):
        self.operator.stop()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = OperatorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
